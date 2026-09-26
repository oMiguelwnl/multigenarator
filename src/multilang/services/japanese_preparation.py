"""Join Japanese frequency candidates to dictionary evidence for existing review.

The join proposes lexical evidence only; it never distributes aggregate counts
across senses, signs reviews, or replaces the shipped production inventory.
"""

from __future__ import annotations

import json
import math
import os
import unicodedata
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.japanese_sources import read_tubelex
from multilang.services.vocabulary_acquisition import _plain_path
from multilang.services.vocabulary_preparation import _file_hash, _OutputBudget, prepare_vocabulary
from multilang.services.vocabulary_sources import SourceLimits


def prepare_japanese_vocabulary(
    *, dictionary: Path, dictionary_sha256: str, frequency: Path, frequency_sha256: str,
    output: Path, candidate_limit: int = 6000, frequency_variant: str = "unidic310-base",
    limits: SourceLimits | None = None,
) -> dict:
    from wordfreq import get_frequency_dict, top_n_list

    if not 1 <= candidate_limit <= 30000:
        raise ValueError("Japanese candidate limit must be 1..30000")
    if frequency_variant not in {"unidic310-base", "unidic310-lemma"}:
        raise ValueError("declare a catalogued Japanese frequency variant")
    limits = limits or SourceLimits(max_unique_entries=1_000_000)
    output = _plain_path(output)
    if output.exists():
        raise ValueError("Japanese preparation requires a new output directory")
    counts = sorted(read_tubelex(frequency, expected_sha256=frequency_sha256, limits=limits),
                    key=lambda row: (-row.count, -row.channels, row.word))
    total_count = len(counts)
    selected = counts[:candidate_limit]
    # Source normalization is preserved; NFC is used only for the dictionary
    # selection. Multiple evidence candidates remain explicitly unresolved.
    words = {unicodedata.normalize("NFC", row.word) for row in selected}
    old_ranks = {word: rank for rank, word in enumerate(top_n_list("ja", max(3000, candidate_limit)), 1)}
    # Compare the published token tables directly. Calling zipf_frequency would
    # retokenize Japanese with wordfreq's independent MeCab/IPADIC pipeline.
    old_frequencies = get_frequency_dict("ja")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".japanese-prepare-", dir=output.parent) as temporary:
        staging = Path(temporary) / "prepared"
        manifest = prepare_vocabulary(language="ja", dictionary=dictionary,
            dictionary_sha256=dictionary_sha256, output=staging, dictionary_format="jmdict",
            lemmas=words, limits=limits)
        evidence = defaultdict(set)
        with (staging / "candidates.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                candidate = json.loads(line)
                # Never infer a stable sense from this spelling join.
                evidence[candidate["lemma"]].add(candidate["candidate_id"])
                for sound in candidate["sounds"]:
                    evidence[sound["reading"]].add(candidate["candidate_id"])
        rows = []
        missing = []
        for rank, row in enumerate(selected, 1):
            ids = sorted(evidence[unicodedata.normalize("NFC", row.word)])
            if not ids:
                missing.append(row.word)
            rows.append({"source_rank": rank, **row.model_dump(), "candidate_ids": ids,
                "wordfreq_rank": old_ranks.get(row.word),
                "wordfreq_zipf": round(math.log10(old_frequencies[row.word]) + 9, 2)
                if row.word in old_frequencies else None,
                "decision": "pending", "selected_candidate_id": None,
                "reason": "source_sense_review_required" if ids else "no_dictionary_evidence"})
        report = {
            "schema_version": 1, "source_id": "tubelex-ja-" + frequency_variant,
            "source_sha256": frequency_sha256, "source_entry_count": total_count,
            "source_normalization": "upstream NFKC/lowercase retained; NFC dictionary lookup",
            "ranking_policy": "count-desc-channels-desc-word-v1",
            "comparison_policy": "wordfreq-published-token-table-exact-match-v1",
            "selected_count": len(rows), "with_lexical_evidence": len(rows) - len(missing),
            "without_lexical_evidence": missing,
            "ambiguous_candidate_count": sum(len(row["candidate_ids"]) > 1 for row in rows),
            "target_core_count": 3000, "approved_core_count": 0, "production_eligible": False,
            "rows": rows,
        }
        budget = _OutputBudget(limits.max_output_bytes - sum(p.stat().st_size for p in staging.iterdir()))
        budget.dump(staging / "frequency-comparison.json", report)
        manifest["frequency"] = {k: v for k, v in report.items() if k not in {"rows", "without_lexical_evidence"}}
        manifest["files"]["frequency-comparison.json"] = _file_hash(staging / "frequency-comparison.json")
        manifest.pop("preparation_sha256")
        manifest["preparation_sha256"] = canonical_sha256(manifest)
        budget.dump(staging / "manifest.json", manifest)
        if output.exists():
            raise ValueError("Japanese output created concurrently")
        os.rename(staging, output)
    return manifest
