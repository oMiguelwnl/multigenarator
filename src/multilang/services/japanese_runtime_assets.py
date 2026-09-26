"""Bridge verified JMdict reviews into existing frequency and highlight services."""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.frequency_decks import (
    CURATED_COLUMNS,
    REJECTION_COLUMNS,
    load_curated_frequency_entries,
)
from multilang.services.japanese_sources import read_tubelex
from multilang.services.lexical_lookup import LexicalRecord, normalize_lexical_key
from multilang.services.vocabulary_acquisition import _plain_path
from multilang.services.vocabulary_preparation import _file_hash
from multilang.services.vocabulary_review import verify_compiled_vocabulary
from multilang.services.vocabulary_sources import SourceLimits

_CREDIT = """# Japanese lexical data

JMdict Japanese-English dictionary, Electronic Dictionary Research and Development
Group. https://www.edrdg.org/wiki/JMdict-EDICT_Dictionary_Project.html
Licensed under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/
Terms and update procedure: https://www.edrdg.org/edrdg/licence.html
Adaptation: selected spelling/reading/sense records normalized for Multilang.
The manifest identifies the exact source snapshot and reviewed selection.
Generated card content and the manual image field are separate from this data.
"""


def _reviewed_records(bundle, profile, verifier):
    bundle = verify_compiled_vocabulary(bundle, profile=profile, verifier=verifier)
    if bundle.language is not SupportedLanguage.JA or bundle.preparation_manifest["dictionary_format"] != "jmdict":
        raise ValueError("Japanese runtime assets require verified JMdict evidence")
    identities = {item.lexical_identity_id: item for item in bundle.identities}
    candidates = {item.candidate_id: item for item in bundle.candidates}
    records = {}
    for evidence in bundle.source_evidence:
        if evidence.kind != "identity":
            continue
        candidate = candidates[evidence.record_id]
        identity = identities[evidence.object_id]
        readings = {sound.get("reading") for sound in candidate.sounds if sound.get("source") == "jmdict"}
        if len(readings) != 1 or not next(iter(readings)):
            raise ValueError("reviewed JMdict candidate requires one explicit reading")
        records[candidate.candidate_id] = (identity, candidate, LexicalRecord(
            term=candidate.lemma, display_form=candidate.lemma, lemma=candidate.lemma,
            definitions=list(candidate.glosses), definition_language="en", part_of_speech=candidate.pos,
            sense_id=identity.sense_id, japanese_reading=readings.pop(), grammar_tags=list(candidate.tags),
            source="JMdict/EDRDG", source_version=bundle.review.source_version,
            source_sha256=bundle.preparation_manifest["dictionary_sha256"],
        ))
    if not records:
        raise ValueError("no reviewed Japanese lexical identities")
    return records


def _write_cache(staging, bundle, records):
    index = defaultdict(dict)
    for identity, candidate, record in records.values():
        aliases = {identity.lexical_identity_id, candidate.lemma, record.japanese_reading}
        for alias in aliases:
            index[normalize_lexical_key(alias)][record.model_dump_json()] = record.model_dump(mode="json")
    directory = staging / "lexicon" / "ja"
    directory.mkdir(parents=True)
    path = directory / "lexical-index.json"
    path.write_text(json.dumps({key: list(value.values()) for key, value in sorted(index.items())},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (staging / "ATTRIBUTION.md").write_text(_CREDIT, encoding="utf-8")
    return {"schema_version": 1, "language": "ja", "identity_count": len(records),
        "reviewed_bundle_sha256": bundle.bundle_sha256,
        "dictionary_sha256": bundle.preparation_manifest["dictionary_sha256"],
        "lexical_index_sha256": _file_hash(path), "production_deck_approved": False}


def export_japanese_lexical_cache(*, bundle, profile, verifier, output: Path) -> dict:
    records = _reviewed_records(bundle, profile, verifier)
    output = _plain_path(output)
    if output.exists():
        raise ValueError("Japanese runtime assets require a new output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".ja-cache-", dir=output.parent) as temporary:
        staging = Path(temporary) / "assets"
        report = _write_cache(staging, bundle, records)
        (staging / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        os.rename(staging, output)
    return report


def japanese_frequency_release_payload(*, bundle, frequency_sha256, selection, version="tubelex-jmdict-v1"):
    return {"schema_version": 1, "language": "ja", "version": version,
        "reviewed_bundle_sha256": bundle.bundle_sha256,
        "dictionary_sha256": bundle.preparation_manifest["dictionary_sha256"],
        "frequency_sha256": frequency_sha256, "selection_sha256": canonical_sha256(selection),
        "ranking_policy": "count-desc-channels-desc-word-v1",
        "decision": "approve-selected-JMdict-and-TUBELEX-data-redistribution-with-attribution"}


def freeze_japanese_frequency(*, bundle, profile, verifier, selection: list[dict], frequency: Path,
    frequency_sha256: str, source_receipt_id: str | None, output: Path, version="tubelex-jmdict-v1"):
    if len(selection) != 3000:
        raise ValueError("Japanese frequency release requires exactly 3000 reviewed selections")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", version):
        raise ValueError("invalid Japanese frequency version")
    records = _reviewed_records(bundle, profile, verifier)
    payload = japanese_frequency_release_payload(bundle=bundle, frequency_sha256=frequency_sha256,
        selection=selection, version=version)
    if not source_receipt_id or not verifier.verify(source_receipt_id, payload, purpose="japanese-frequency-source"):
        raise ValueError("Japanese frequency source redistribution review is missing or invalid")
    counts = list(read_tubelex(frequency, expected_sha256=frequency_sha256,
        limits=SourceLimits(max_unique_entries=1_000_000)))
    ordered = sorted(counts, key=lambda row: (-row.count, -row.channels, row.word))
    by_word = {row.word: (rank, row) for rank, row in enumerate(ordered, 1)}
    selected, displays, words, ids = [], set(), set(), set()
    for choice in selection:
        if set(choice) != {"candidate_id", "frequency_word"}:
            raise ValueError("frequency selection requires candidate_id and frequency_word")
        record = records.get(choice["candidate_id"])
        counted = by_word.get(choice["frequency_word"])
        if record is None or counted is None:
            raise ValueError("frequency selection references missing reviewed evidence")
        identity, candidate, lexical = record
        source_rank, count = counted
        if unicodedata.normalize("NFC", count.word) not in {candidate.lemma, lexical.japanese_reading}:
            raise ValueError("frequency spelling does not match reviewed JMdict evidence")
        if candidate.lemma in displays or count.word in words or identity.lexical_identity_id in ids:
            raise ValueError("duplicate spelling, aggregate count or identity in frequency selection")
        displays.add(candidate.lemma)
        words.add(count.word)
        ids.add(identity.lexical_identity_id)
        selected.append((source_rank, count, record))
    selected.sort(key=lambda row: row[0])
    output = _plain_path(output)
    if output.exists():
        raise ValueError("Japanese frequency assets require a new output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".ja-frequency-", dir=output.parent) as temporary:
        staging = Path(temporary) / "assets"
        report = _write_cache(staging, bundle, records)
        root = staging / "frequency" / "ja"
        root.mkdir(parents=True)
        with (root / f"curated-{version}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(CURATED_COLUMNS)
            for rank, (source_rank, count, (identity, candidate, lexical)) in enumerate(selected, 1):
                writer.writerow(["ja", version, (rank - 1) // 1000 + 1, rank, source_rank,
                    candidate.lemma, candidate.lemma, identity.lexical_identity_id, candidate.pos,
                    "; ".join(candidate.glosses), f"tubelex:ja:{frequency_sha256};jmdict:{lexical.source_sha256}",
                    "reviewed-sense;reviewed-source;aggregate-word-count"])
        with (root / f"rejections-{version}.csv").open("w", encoding="utf-8", newline="") as handle:
            # The full selection and source tables, rather than invented reason
            # labels for every unselected token, are retained in the manifest.
            csv.writer(handle).writerow(REJECTION_COLUMNS)
        load_curated_frequency_entries(SupportedLanguage.JA, version=version, assets_dir=staging / "frequency")
        report.update({"frequency_version": version, "frequency_sha256": frequency_sha256,
            "source_receipt_id": source_receipt_id, "selection": selection,
            "frequency_card_count": 3000, "levels": {"1": 1000, "2": 1000, "3": 1000}})
        (staging / "ATTRIBUTION.md").write_text(_CREDIT + "\nFrequency: TUBELEX Japanese, https://github.com/naist-nlp/tubelex . "
            "The signed source decision and manifest record the selected snapshot.\n", encoding="utf-8")
        (staging / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.rename(staging, output)
    return report
