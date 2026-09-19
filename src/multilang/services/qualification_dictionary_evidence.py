"""Recover original dictionary qualifiers as additive, immutable review evidence.

Legacy candidates intentionally keep their existing schema and hashes. This
boundary reconstructs each selected candidate with the preparation parser before
exposing its original sense, without assigning any linguistic approval.
"""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_revision import MachineRevisionSupplement
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact, read_json
from multilang.services.qualification_machine_sources import VerifiedReviewExcerpt
from multilang.services.qualification_pilot import _lexical_item
from multilang.services.qualification_pipeline import ArtifactReference
from multilang.services.qualification_review import ReviewPacket, _json
from multilang.services.vocabulary_review import _plain_path
from multilang.services.vocabulary_sources import (
    SourceLimits,
    _verified_lines,
    wiktextract_record_candidates,
)

_RECORD_FIELDS = (
    "word",
    "pos",
    "lang_code",
    "raw_glosses",
    "topics",
    "raw_tags",
    "categories",
    "tags",
)
_EXCERPT_FILE_LIMIT = 16 * 1024**2


class DictionaryEvidenceInput(NativeContract):
    schema_version: Literal[1] = 1
    packet: ArtifactReference
    dictionary: ArtifactReference
    limits: SourceLimits = Field(default_factory=SourceLimits)


def _match_candidate(item, candidate, dictionary_sha256, source_pos):
    digest = canonical_sha256(candidate.model_dump(mode="json"))
    projected = _lexical_item(
        candidate,
        {"dictionary_sha256": dictionary_sha256},
        {candidate.source_record_sha256: source_pos},
    )
    if digest != item.candidate_sha256 or (
        item.lemma,
        item.pos,
        item.glosses,
        item.source_sense_ids,
    ) != (projected.lemma, projected.pos, projected.glosses, projected.source_sense_ids):
        raise ValueError("dictionary candidate checksum or identity mismatch")
    if not any(
        source.record_id == candidate.candidate_id and source.source_sha256 == dictionary_sha256
        for source in item.sources
    ):
        raise ValueError("dictionary candidate source binding mismatch")
    return digest


def _recover(packet, config):
    if any(item.kind != "lexical" for item in packet.items):
        raise ValueError("dictionary evidence requires lexical review items")
    if len(packet.items) > 128:
        raise ValueError("dictionary evidence supplement limit is 128 items per revision")
    targets = {item.candidate_id: item for item in packet.items}
    if len(targets) != len(packet.items):
        raise ValueError("duplicate dictionary candidate target")
    if len(targets) > config.limits.max_unique_entries:
        raise ValueError("dictionary evidence entry limit exceeded")
    # Packet lemmas already satisfy NFC; normalize the lookup set once per scan.
    lemma_filter = {item.lemma.casefold() for item in packet.items}
    recovered, total = {}, 0
    for line in _verified_lines(config.dictionary.path, config.dictionary.sha256, config.limits):
        if not line.strip():
            continue
        record = _json(line.encode("utf-8"))
        for index, candidate in wiktextract_record_candidates(
            record, language=packet.language.value, lemma_filter=lemma_filter
        ):
            item = targets.get(candidate.candidate_id)
            if item is None:
                continue
            if candidate.candidate_id in recovered:
                raise ValueError("duplicate source dictionary candidate")
            digest = _match_candidate(item, candidate, config.dictionary.sha256, record.get("pos"))
            payload = {
                "schema_version": "original-dictionary-sense-evidence-1",
                "transformation": "JSON-escaped-original-dictionary-fields-v1",
                "scope": "complete-selected-sense-and-listed-record-fields",
                "record_fields": list(_RECORD_FIELDS),
                "dictionary_sha256": config.dictionary.sha256,
                "candidate_id": candidate.candidate_id,
                "candidate_sha256": digest,
                "source_record_sha256": candidate.source_record_sha256,
                "sense_index": index,
                "record": {key: record[key] for key in _RECORD_FIELDS if key in record},
                "sense": record["senses"][index],
                "production_eligible": False,
            }
            # ASCII JSON preserves original NFD code points while the excerpt
            # itself meets the review contract's NFC requirement. Never truncate.
            excerpt = json.dumps(
                payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            if len(excerpt) > 64000:
                raise ValueError("original dictionary sense exceeds review excerpt limit")
            total += len(excerpt) + 1
            if total > min(_EXCERPT_FILE_LIMIT, config.limits.max_output_bytes):
                raise ValueError("dictionary evidence output byte limit exceeded")
            recovered[candidate.candidate_id] = (excerpt, candidate.source_record_sha256, index)
    missing = targets.keys() - recovered.keys()
    if missing:
        raise ValueError("dictionary candidate missing for exact packet language and identity")
    return recovered


def prepare_dictionary_evidence(input: Path, input_sha256: str, output: Path) -> dict:
    """Verify INPUT and referenced sources, then publish reusable revision supplements."""
    output = _plain_path(output)
    config = DictionaryEvidenceInput.model_validate(read_json(input, input_sha256))
    packet = ReviewPacket.model_validate(read_json(config.packet.path, config.packet.sha256))
    recovered = _recover(packet, config)
    text = "".join(recovered[item.candidate_id][0] + "\n" for item in packet.items)
    evidence = text.encode("ascii")
    file_sha256 = hashlib.sha256(evidence).hexdigest()
    supplements, provenance, offset = [], [], 0
    for item in packet.items:
        excerpt, record_sha256, sense_index = recovered[item.candidate_id]
        supplements.append(
            MachineRevisionSupplement(
                reference=VerifiedReviewExcerpt(
                    path=output / "evidence.jsonl",
                    file_sha256=file_sha256,
                    source_id="original-dictionary-sense",
                    record_id=record_sha256,
                    language=packet.language,
                    start=offset,
                    end=offset + len(excerpt),
                ),
                item_ids=(item.item_id,),
            )
        )
        provenance.append(
            {
                "item_id": item.item_id,
                "item_sha256": item.item_sha256,
                "candidate_id": item.candidate_id,
                "candidate_sha256": item.candidate_sha256,
                "source_record_sha256": record_sha256,
                "sense_index": sense_index,
                "source_sense_sha256": canonical_sha256(json.loads(excerpt)["sense"]),
            }
        )
        offset += len(excerpt) + 1
    supplement_data = {"supplements": [row.model_dump(mode="json") for row in supplements]}
    metadata = {
        "schema_version": "machine-dictionary-evidence-1",
        "input": {"path": str(_plain_path(input)), "sha256": input_sha256},
        "packet": config.packet.model_dump(mode="json"),
        "dictionary": config.dictionary.model_dump(mode="json"),
        "limits": config.limits.model_dump(mode="json"),
        "packet_sha256": packet.packet_sha256,
        "language": packet.language.value,
        "items": provenance,
        "evidence_sha256": file_sha256,
        "supplements_sha256": canonical_sha256(supplement_data),
        "production_eligible": False,
    }
    files = {
        "evidence.jsonl": evidence,
        "supplements.json": json_bytes(supplement_data),
        "provenance.json": json_bytes(metadata),
    }
    if sum(map(len, files.values())) > config.limits.max_output_bytes:
        raise ValueError("dictionary evidence output byte limit exceeded")
    return persist_artifact(
        output, kind="machine-dictionary-evidence", binding=canonical_sha256(metadata), files=files
    )
