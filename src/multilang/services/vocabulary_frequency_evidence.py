"""Bounded offline extraction of source-scoped Croatian frequency evidence.

hrLex 1.3 documents counts for (wordform, lemma, MSD) triples, not independent
token IDs. Exact duplicate triples are counted once; conflicting duplicates
fail closed. Distinct analyses remain distinct. Their summed mass is explicitly
NOT certified as unique corpus occurrences or as general-language frequency.
The relative-frequency column is validated but never used to rank or rescale.
Temporary SQLite is only a bounded scratch index, never production storage.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import re
import sqlite3
import stat
import unicodedata
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.lexical_identity import canonical_sha256

UPOS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN PUNCT SCONJ SYM VERB X _".split()
)
RANK_EXCLUSIONS = frozenset({"PUNCT", "SYM", "X", "_"})


def _digest(stream, maximum):
    stream.seek(0)
    digest, size = hashlib.sha256(), 0
    while block := stream.read(1024 * 1024):
        size += len(block)
        if size > maximum:
            raise ValueError("compressed byte limit exceeded")
        digest.update(block)
    stream.seek(0)
    return digest.hexdigest()


def derive_hrlex_counts(
    path: Path,
    *,
    expected_sha256: str,
    scratch_dir: Path,
    max_rows: int = 7_000_000,
    max_uncompressed_bytes: int = 1_500_000_000,
    max_compressed_bytes: int = 64 * 1024 * 1024,
    max_line_bytes: int = 16_384,
) -> dict:
    """Validate a pinned gzip and return ranked NFC lemma+UPOS count evidence.

    No network, inventory mutation, frequency imputation or semantic admission.
    Paths are local caller-selected files/directories, never source-row fields.
    Scratch database is private and deleted on success or any exception.
    Source SHA256 is verified before and after reading the same open descriptor.
    """
    limits = (max_rows, max_uncompressed_bytes, max_compressed_bytes, max_line_bytes)
    if any(type(limit) is not int or limit <= 0 for limit in limits):
        raise ValueError("limits must be positive integers")
    if not isinstance(expected_sha256, str) or not re.fullmatch("[0-9a-f]{64}", expected_sha256):
        raise ValueError("invalid expected SHA256")
    counts, excluded, by_pos = Counter(), Counter(), Counter()
    input_rows = duplicates = positive = total_bytes = 0
    with Path(path).open("rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("source must be a regular file")
        if _digest(source, max_compressed_bytes) != expected_sha256:
            raise ValueError("source SHA256 mismatch")
        with TemporaryDirectory(prefix="hrlex-", dir=Path(scratch_dir)) as directory:
            connection = sqlite3.connect(str(Path(directory) / "tuples.sqlite"))
            try:
                connection.execute("PRAGMA journal_mode=OFF")
                connection.execute("PRAGMA max_page_count=524288")
                connection.execute(
                    "CREATE TABLE seen (form TEXT, lemma TEXT, msd TEXT, payload BLOB, PRIMARY KEY(form,lemma,msd)) WITHOUT ROWID"
                )
                with gzip.GzipFile(fileobj=source, mode="rb") as zipped:
                    while raw := zipped.readline(max_line_bytes + 1):
                        input_rows += 1
                        total_bytes += len(raw)
                        if (
                            input_rows > max_rows
                            or total_bytes > max_uncompressed_bytes
                            or len(raw) > max_line_bytes
                        ):
                            raise ValueError("decompressed input limit exceeded")
                        try:
                            line = raw.decode("utf-8").rstrip("\r\n")
                            columns = line.split("\t")
                            if len(columns) != 8 or any(not columns[i] for i in (0, 1, 2)):
                                raise ValueError("invalid row fields")
                            form, lemma, msd, _, upos, _, absolute, relative = columns
                            if upos not in UPOS or not re.fullmatch(r"[0-9]{1,18}", absolute):
                                raise ValueError("invalid UPOS or absolute count")
                            count, proportion = int(absolute), Decimal(relative)
                            if not proportion.is_finite() or proportion < 0:
                                raise ValueError("invalid relative count")
                        except (UnicodeDecodeError, InvalidOperation, ValueError) as exc:
                            raise ValueError(f"malformed hrLex row {input_rows}: {exc}") from exc
                        key = (form, lemma, msd)
                        payload = hashlib.sha256(line.encode("utf-8")).digest()
                        cursor = connection.execute(
                            "INSERT OR IGNORE INTO seen VALUES (?, ?, ?, ?)", (*key, payload)
                        )
                        if cursor.rowcount == 0:
                            previous = connection.execute(
                                "SELECT payload FROM seen WHERE form=? AND lemma=? AND msd=?", key
                            ).fetchone()[0]
                            if previous != payload:
                                raise ValueError(f"conflicting tuple at row {input_rows}")
                            duplicates += 1
                            continue
                        by_pos[upos] += count
                        if count == 0:
                            continue
                        positive += 1
                        if upos in RANK_EXCLUSIONS:
                            excluded[upos] += count
                        else:
                            counts[(unicodedata.normalize("NFC", lemma), upos)] += count
            finally:
                connection.close()
        if _digest(source, max_compressed_bytes) != expected_sha256:
            raise ValueError("source SHA256 changed during extraction")
    entries, last_count, rank = [], None, 0
    for index, ((lemma, upos), count) in enumerate(
        sorted(counts.items(), key=lambda item: (-item[1], item[0])), 1
    ):
        if count != last_count:
            rank = index
        entries.append({"lemma": lemma, "upos": upos, "count": count, "source_rank": rank})
        last_count = count
    return {
        "schema_version": "hrlex-source-frequency-evidence-1",
        "language": "hr",
        "source_id": "hrlex-1.3",
        "source_sha256": expected_sha256,
        "source_version": "1.3",
        "source_corpus": "hrWaC 2.2",
        "modality": "written_web",
        "source_documentation": "https://www.clarin.si/repository/xmlui/handle/11356/1232",
        "license": "CC-BY-SA-4.0",
        "attribution": "Nikola Ljubešić (2019), Inflectional lexicon hrLex 1.3, CLARIN.SI",
        "frequency_unit": "sum_of_attested_wordform_lemma_msd_counts",
        "normalization": "NFC lemma only; original tuple keys and case preserved",
        "ranking": "descending absolute count; competition ties; lexical order only for deterministic serialization",
        "excluded_upos": sorted(RANK_EXCLUSIONS),
        "excluded_count_by_upos": dict(excluded),
        "input_rows": input_rows,
        "duplicate_rows": duplicates,
        "positive_unique_tuples": positive,
        "uncompressed_bytes": total_bytes,
        "attested_tuple_count_sum": sum(by_pos.values()),
        "count_by_upos": dict(by_pos),
        "ranked_tuple_count_sum": sum(counts.values()),
        "ranked_identities": len(entries),
        "unique_token_mass_certified": False,
        "general_frequency_certified": False,
        "evaluation_holdout": False,
        "production_eligible": False,
        "relative_frequency_used": False,
        "entries": entries,
    }


def bind_source_counts(identities: list[dict], evidence: dict) -> dict:
    """Bind exact keys to immutable identity hashes without assigning final ranks.

    Callers must verify the files producing both arguments. A source lemma+POS
    frequency belongs to the shared lexical key, never separately to its senses
    or to multiple dictionary records. Missing keys remain explicitly unranked.
    """
    if (
        evidence.get("schema_version") != "hrlex-source-frequency-evidence-1"
        or evidence.get("language") != "hr"
    ):
        raise ValueError("unsupported evidence schema or language")
    source = {}
    for row in evidence["entries"]:
        key = (row["lemma"], row["upos"])
        if key in source:
            raise ValueError("duplicate source key")
        if (
            not isinstance(key[0], str)
            or not key[0]
            or key[1] not in UPOS
            or key[1] in RANK_EXCLUSIONS
        ):
            raise ValueError("invalid source identity")
        if (
            type(row["count"]) is not int
            or row["count"] <= 0
            or type(row["source_rank"]) is not int
            or row["source_rank"] <= 0
        ):
            raise ValueError("invalid source count or rank")
        source[key] = row
    bindings, unmatched, matched_keys, ids = [], [], set(), set()
    for identity in identities:
        if identity.get("language") != "hr":
            raise ValueError("identity language mismatch")
        identifier = identity["identity_id"]
        if identifier in ids:
            raise ValueError("duplicate identity ID")
        ids.add(identifier)
        key = (unicodedata.normalize("NFC", identity["lemma"]), identity.get("pos"))
        binding = {
            "identity_id": identifier,
            "identity_sha256": canonical_sha256(identity),
            "lemma": key[0],
            "pos": key[1],
        }
        if key not in source:
            unmatched.append({**binding, "reason": "no exact attested lemma+UPOS key"})
            continue
        row = source[key]
        matched_keys.add(key)
        bindings.append(
            {
                **binding,
                "source_id": evidence["source_id"],
                "source_sha256": evidence["source_sha256"],
                "source_count": row["count"],
                "source_rank": row["source_rank"],
                "frequency_unit": evidence["frequency_unit"],
                "scope": "shared lemma+UPOS across senses and source identities",
                "sense_frequency": None,
                "final_frequency_rank": None,
                "production_eligible": False,
            }
        )
    return {
        "schema_version": "source-count-identity-bindings-1",
        "language": "hr",
        "matched_identity_rows": len(bindings),
        "unmatched_identity_rows": len(unmatched),
        "matched_unique_lemma_upos": len(matched_keys),
        "matched_source_count_sum": sum(source[key]["count"] for key in matched_keys),
        "is_coverage_measurement": False,
        "general_frequency_certified": False,
        "bindings": bindings,
        "unmatched": unmatched,
    }
