"""Build and validate deterministic frequency assets from wordfreq seeds."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import tempfile
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
    KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
    KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT,
    KOREAN_FREQUENCY_SCHEMA_VERSION,
    KOREAN_FREQUENCY_SOURCE_ID,
    KoreanFrequencyBuildPolicy,
    KoreanFrequencyBuildResult,
    KoreanFrequencyBundleManifest,
    KoreanFrequencyBundleMember,
    KoreanFrequencyEntry,
    canonical_json_sha256,
    raw_bytes_sha256,
    validate_korean_frequency_accounting,
)
from multilang.services.frequency_decks import (
    CURATED_COLUMNS,
    REJECTION_COLUMNS,
    VALID_REJECTION_REASON_CODES,
    _is_curated_token,
    is_curated_token_for_language,
    load_curated_frequency_entries,
    normalize_frequency_token_for_language,
)
from multilang.services.mandarin_orthography import script_counts
from multilang.settings import (
    APPROVED_FREQUENCY_ASSET_LANGUAGES,
    DEFAULT_SUPPORTED_LANGUAGES,
)
from wordfreq import iter_wordlist

_WORDFREQ_LANGUAGE_ALIASES = {"hr": "sh"}
_KOREAN_BUNDLE_FILES = {
    "source-snapshot": "source-snapshot.txt",
    "curated-inventory": "curated-inventory.jsonl",
    "rejections": "rejections.jsonl",
    "attribution": "attribution.txt",
    "curation-report": "curation-report.json",
}

FsyncFn = Callable[[int], None]
FailureInjector = Callable[[str, Path], bool]


def _rejection_reason(token: str, *, language: SupportedLanguage | None = None) -> str | None:
    if not token:
        return "empty"
    if any(ch.isdigit() for ch in token):
        return "digit"
    lower = token.lower()
    if lower in {"http", "https", "www", "nbsp"}:
        return "web_noise"
    if "." in token:
        return "contains_dot"
    if token != lower:
        return "uppercase"
    if language is SupportedLanguage.ZH:
        counts = script_counts(token)
        if counts.han == 0:
            return "non_han"
        if counts.kana or counts.latin:
            return "invalid_script"
        if not is_curated_token_for_language(language, token):
            return "invalid_script"
    elif not _is_curated_token(token):
        return "punctuation"
    return None


def build_assets(
    *,
    assets_dir: Path,
    version: str,
    scan_limit: int = 25000,
    language_code: str | None = None,
) -> None:
    for code in _language_codes(language_code):
        _build_language_asset(code=code, assets_dir=assets_dir, version=version, scan_limit=scan_limit)


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_json_bytes(row) for row in rows)


def _safe_korean_bundle_version(version: str) -> str:
    if (
        not isinstance(version, str)
        or not version
        or version != version.strip()
        or version.startswith(".")
        or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in version)
    ):
        raise ValueError("Korean frequency bundle version is unsafe")
    return version


def _ensure_safe_directory(path: Path) -> Path:
    if path.exists() and (not path.is_dir() or path.is_symlink()):
        raise ValueError("Korean frequency bundle root is unsafe")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Korean frequency bundle root is unsafe")
    return path


def _read_build_policy(policy_file: Path) -> KoreanFrequencyBuildPolicy:
    try:
        return KoreanFrequencyBuildPolicy.model_validate_json(
            Path(policy_file).read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise ValueError("Korean frequency build policy is invalid") from exc


def _validate_rejection_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    accepted_source_ranks: set[int],
) -> tuple[dict[str, Any], ...]:
    if len(rows) != KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT:
        raise ValueError("Korean frequency rejections must contain exactly 2965 rows")
    normalized: list[dict[str, Any]] = []
    source_ranks: set[int] = set()
    forbidden = {"token", "source_form", "private_path", "path", "note", "reviewer_note"}
    for row in rows:
        if forbidden & set(row):
            raise ValueError("Korean frequency rejection row contains unsafe content")
        source_rank = row.get("source_rank")
        reason_code = row.get("reason_code")
        source_form_sha256 = row.get("source_form_sha256")
        if (
            not isinstance(source_rank, int)
            or source_rank < 1
            or source_rank > KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT
            or source_rank in accepted_source_ranks
            or source_rank in source_ranks
            or not isinstance(reason_code, str)
            or not reason_code
            or not isinstance(source_form_sha256, str)
            or len(source_form_sha256) != 64
            or any(character not in "0123456789abcdef" for character in source_form_sha256)
        ):
            raise ValueError("Korean frequency rejection row is invalid")
        source_ranks.add(source_rank)
        normalized.append(
            {
                "reason_code": reason_code,
                "source_form_sha256": source_form_sha256,
                "source_rank": source_rank,
            }
        )
    if accepted_source_ranks | source_ranks != set(range(1, KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT + 1)):
        raise ValueError("Korean frequency source dispositions must be complete")
    return tuple(sorted(normalized, key=lambda row: row["source_rank"]))


def _materialize_korean_bundle_payloads(
    *,
    retrieval_result_file: Path,
    source_file: Path,
    policy_file: Path,
    inventory_rows: Sequence[Mapping[str, Any]],
    rejection_rows: Sequence[Mapping[str, Any]],
    attribution_text: str,
    curation_report: Mapping[str, Any],
    version: str,
) -> tuple[dict[str, bytes], KoreanFrequencyBuildResult, KoreanFrequencyBundleManifest]:
    from multilang.services.korean_frequency import validate_korean_source_retrieval_result

    retrieval = validate_korean_source_retrieval_result(
        retrieval_result_file,
        source_file=source_file,
    )
    policy = _read_build_policy(policy_file)
    source_bytes = Path(source_file).read_bytes()
    source_hash = raw_bytes_sha256(source_bytes)
    if policy.retrieval_sha256 != retrieval.source_bytes_sha256:
        raise ValueError("Korean frequency policy retrieval hash drift")
    if policy.source_bytes_sha256 != source_hash:
        raise ValueError("Korean frequency policy source hash drift")
    entries = tuple(KoreanFrequencyEntry.model_validate(row) for row in inventory_rows)
    if len(entries) != KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT:
        raise ValueError("Korean frequency inventory must contain exactly 3000 rows")
    if {entry.version for entry in entries} != {version}:
        raise ValueError("Korean frequency inventory version drift")
    if {entry.bundle_sha256 for entry in entries} != {source_hash}:
        raise ValueError("Korean frequency inventory source binding drift")
    level_counts = validate_korean_frequency_accounting(
        entries,
        source_candidate_count=KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT,
        rejection_count=KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
    )
    rejections = _validate_rejection_rows(
        rejection_rows,
        accepted_source_ranks={entry.source_rank for entry in entries},
    )
    if not isinstance(attribution_text, str) or not attribution_text.strip():
        raise ValueError("Korean frequency attribution is required")
    if any(fragment in attribution_text for fragment in ("/home/", "\\", "..")):
        raise ValueError("Korean frequency attribution contains unsafe content")
    report = dict(curation_report)
    report.update(
        {
            "accepted_count": KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
            "rejection_count": KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
            "level_counts": {str(key): value for key, value in level_counts.items()},
        }
    )
    payloads = {
        _KOREAN_BUNDLE_FILES["source-snapshot"]: source_bytes,
        _KOREAN_BUNDLE_FILES["curated-inventory"]: _jsonl_bytes(
            [entry.model_dump(mode="json") for entry in entries]
        ),
        _KOREAN_BUNDLE_FILES["rejections"]: _jsonl_bytes(rejections),
        _KOREAN_BUNDLE_FILES["attribution"]: f"{attribution_text.strip()}\n".encode("utf-8"),
        _KOREAN_BUNDLE_FILES["curation-report"]: _canonical_json_bytes(report),
    }
    kind_by_file = {filename: kind for kind, filename in _KOREAN_BUNDLE_FILES.items()}
    row_counts = {
        _KOREAN_BUNDLE_FILES["source-snapshot"]: KOREAN_FREQUENCY_EXPECTED_SOURCE_COUNT,
        _KOREAN_BUNDLE_FILES["curated-inventory"]: KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
        _KOREAN_BUNDLE_FILES["rejections"]: KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
        _KOREAN_BUNDLE_FILES["attribution"]: 1,
        _KOREAN_BUNDLE_FILES["curation-report"]: 1,
    }
    members = tuple(
        KoreanFrequencyBundleMember(
            relative_path=filename,
            sha256=raw_bytes_sha256(payload),
            byte_count=len(payload),
            row_count=row_counts[filename],
            kind=kind_by_file[filename],
        )
        for filename, payload in sorted(payloads.items())
    )
    manifest_payload = {
        "analyzer_fingerprint": policy.analyzer_fingerprint.model_dump(mode="json"),
        "entry_count": KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
        "inventory_sha256": raw_bytes_sha256(payloads[_KOREAN_BUNDLE_FILES["curated-inventory"]]),
        "language": "ko",
        "level_counts": level_counts,
        "license_decision": "approved-local-use"
        if policy.redistribution == "not-approved"
        else "approved-redistribution",
        "members": [member.model_dump(mode="json") for member in members],
        "rejection_count": KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
        "rejection_sha256": raw_bytes_sha256(payloads[_KOREAN_BUNDLE_FILES["rejections"]]),
        "report_sha256": raw_bytes_sha256(payloads[_KOREAN_BUNDLE_FILES["curation-report"]]),
        "schema_version": KOREAN_FREQUENCY_SCHEMA_VERSION,
        "source_id": KOREAN_FREQUENCY_SOURCE_ID,
        "source_version": policy.source_version,
        "storage_disposition": policy.storage_disposition,
        "synthetic": policy.allowed_use == "test-fixture",
        "version": version,
    }
    bundle_sha256 = canonical_json_sha256(manifest_payload)
    manifest = KoreanFrequencyBundleManifest(
        **manifest_payload,
        bundle_sha256=bundle_sha256,
    )
    result = KoreanFrequencyBuildResult(
        policy=policy,
        retrieval_sha256=policy.retrieval_sha256,
        source_bytes_sha256=policy.source_bytes_sha256,
        accepted_count=KOREAN_FREQUENCY_EXPECTED_ENTRY_COUNT,
        rejection_count=KOREAN_FREQUENCY_EXPECTED_REJECTION_COUNT,
        level_counts=level_counts,
        inventory_sha256=manifest.inventory_sha256,
        rejection_sha256=manifest.rejection_sha256,
        report_sha256=manifest.report_sha256,
        bundle_sha256=manifest.bundle_sha256,
        active=False,
    )
    payloads["manifest.json"] = _canonical_json_bytes(manifest.model_dump(mode="json"))
    payloads["build-result.json"] = _canonical_json_bytes(result.model_dump(mode="json"))
    return payloads, result, manifest


def _write_stage_file(path: Path, payload: bytes, *, fsync: FsyncFn) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, payload)
        fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path, *, fsync: FsyncFn) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        fsync(descriptor)
    finally:
        os.close(descriptor)


def _cleanup_owned_stage(stage: Path, target_root: Path) -> None:
    try:
        metadata = stage.lstat()
    except OSError:
        return
    if stage.parent != target_root or not stage.name.startswith(".staging-"):
        return
    if stage.is_symlink() or not stage.is_dir() or metadata.st_nlink < 1:
        return
    shutil.rmtree(stage)


def build_korean_frequency_assets(
    *,
    retrieval_result_file: Path,
    source_file: Path,
    policy_file: Path,
    inventory_rows: Sequence[Mapping[str, Any]],
    rejection_rows: Sequence[Mapping[str, Any]],
    attribution_text: str,
    curation_report: Mapping[str, Any],
    target_root: Path,
    version: str,
    fsync: FsyncFn = os.fsync,
    failure_injector: FailureInjector | None = None,
) -> KoreanFrequencyBuildResult:
    """Build one inactive immutable Korean frequency bundle without pointer changes."""

    from multilang.services.korean_frequency import validate_korean_source_build_result

    safe_version = _safe_korean_bundle_version(version)
    root = _ensure_safe_directory(Path(target_root))
    payloads, expected_result, _manifest = _materialize_korean_bundle_payloads(
        retrieval_result_file=retrieval_result_file,
        source_file=source_file,
        policy_file=policy_file,
        inventory_rows=inventory_rows,
        rejection_rows=rejection_rows,
        attribution_text=attribution_text,
        curation_report=curation_report,
        version=safe_version,
    )
    target = root / safe_version
    if target.exists():
        existing = validate_korean_source_build_result(
            target / "build-result.json",
            bundle_dir=target,
        )
        if existing != expected_result:
            raise ValueError("Korean frequency bundle target collision")
        return existing

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".staging-{expected_result.bundle_sha256[:16]}-",
            dir=root,
        )
    )
    try:
        for filename, payload in payloads.items():
            boundary = f"before-member:{filename.removesuffix('.jsonl').removesuffix('.txt').removesuffix('.json')}"
            if failure_injector is not None and failure_injector(boundary, stage / filename):
                raise ValueError("Korean frequency bundle build interrupted")
            _write_stage_file(stage / filename, payload, fsync=fsync)
            kind = next(
                (
                    key
                    for key, value in _KOREAN_BUNDLE_FILES.items()
                    if value == filename
                ),
                filename.removesuffix(".json"),
            )
            boundary = f"after-member:{kind}"
            if failure_injector is not None and failure_injector(boundary, stage / filename):
                raise ValueError("Korean frequency bundle build interrupted")
        _fsync_directory(stage, fsync=fsync)
        validate_korean_source_build_result(stage / "build-result.json", bundle_dir=stage)
        if target.exists() or target.is_symlink():
            raise ValueError("Korean frequency bundle target collision")
        os.replace(stage, target)
        _fsync_directory(root, fsync=fsync)
        return validate_korean_source_build_result(target / "build-result.json", bundle_dir=target)
    except Exception as exc:
        _cleanup_owned_stage(stage, root)
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Korean frequency bundle build failed") from exc


def _language_codes(language_code: str | None) -> tuple[str, ...]:
    if language_code is None:
        return APPROVED_FREQUENCY_ASSET_LANGUAGES
    if language_code == SupportedLanguage.KO.value:
        raise RuntimeError(
            "Korean frequency assets require approved source, attribution, and "
            "redistribution terms before build or check operations"
        )
    return (language_code,)


def _build_language_asset(*, code: str, assets_dir: Path, version: str, scan_limit: int) -> None:
    language = SupportedLanguage(code)
    target_dir = assets_dir / code
    target_dir.mkdir(parents=True, exist_ok=True)
    curated_rows: list[dict[str, object]] = []
    rejection_rows: list[dict[str, object]] = []
    seen_lemmas: set[str] = set()
    seen_displays: set[str] = set()
    if code == "la":
        # Latin uses custom frequency list from the site (e.g. https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim )
        # Expect a file assets/frequency/la/source-list.txt with one lemma per line, in frequency order.
        source_list_path = target_dir / "source-list.txt"
        if not source_list_path.exists():
            print(f"Warning: {source_list_path} not found. Using sample data. Download the list from the site and save as source-list.txt (one word per line).")
            tokens = ["sum", "et", "in", "non", "qui", "hic", "esse", "cum", "ego", "is"]  # minimal sample
        else:
            with source_list_path.open(encoding="utf-8") as f:
                tokens = [line.strip() for line in f if line.strip()]
        source_rank = 0
        for token in tokens:
            source_rank += 1
            if source_rank > scan_limit or len(curated_rows) >= 3000:
                break
            reason = _rejection_reason(token, language=language)
            lemma_key = token.casefold()
            display_key = token.casefold()
            if reason is None and lemma_key in seen_lemmas:
                reason = "duplicate_lemma_key"
            if reason is None and display_key in seen_displays:
                reason = "duplicate_display_form"
            if reason is not None:
                rejection_rows.append(_rejection_row(language, version, source_rank, token, reason))
                continue
            rank = len(curated_rows) + 1
            seen_lemmas.add(lemma_key)
            seen_displays.add(display_key)
            curated_rows.append({
                "language": code,
                "frequency_list_version": version,
                "level": ((rank - 1) // 1000) + 1,
                "rank": rank,
                "source_rank": source_rank,
                "display_form": token,
                "lemma": token,
                "lemma_key": lemma_key,
                "part_of_speech": "unknown",
                "definition_seed": token,
                "source_provenance": f"mylittlewordland:{code}",
                "curation_flags": "mylittlewordland_seeded;deterministically_filtered;structurally_curated",
            })
    else:
        wordfreq_code = _wordfreq_language_code(code)
        for source_rank, raw_token in enumerate(iter_wordlist(wordfreq_code), start=1):
            if source_rank > scan_limit or len(curated_rows) >= 3000:
                break
            token, normalized_to_simplified = normalize_frequency_token_for_language(language, raw_token)
            reason = _rejection_reason(token, language=language)
            lemma_key = token.casefold()
            display_key = token.casefold()
            if reason is None and lemma_key in seen_lemmas:
                reason = "duplicate_lemma_key"
            if reason is None and display_key in seen_displays:
                reason = "duplicate_display_form"
            if reason is not None:
                rejection_rows.append(_rejection_row(language, version, source_rank, raw_token, reason))
                continue
            rank = len(curated_rows) + 1
            seen_lemmas.add(lemma_key)
            seen_displays.add(display_key)
            curated_rows.append(
                {
                    "language": code,
                    "frequency_list_version": version,
                    "level": ((rank - 1) // 1000) + 1,
                    "rank": rank,
                    "source_rank": source_rank,
                    "display_form": token,
                    "lemma": token,
                    "lemma_key": lemma_key,
                    "part_of_speech": "unknown",
                    "definition_seed": token,
                    "source_provenance": f"wordfreq:{wordfreq_code}",
                    "curation_flags": ";".join(
                        [
                            "wordfreq_seeded",
                            "deterministically_filtered",
                            "structurally_curated",
                            *(
                                ["simplified_normalized", "traditional_to_simplified"]
                                if code == "zh" and normalized_to_simplified
                                else ["simplified_normalized"]
                                if code == "zh"
                                else []
                            ),
                        ]
                    ),
                }
            )
    if code != "la" and len(curated_rows) != 3000:
        raise RuntimeError(f"could not build 3000 rows for {code}; got {len(curated_rows)}")
    if code == "la" and len(curated_rows) == 0:
        print("No curated rows for la; add source-list.txt from the site to generate.")
    _write_csv(target_dir / f"curated-{version}.csv", CURATED_COLUMNS, curated_rows)
    if not rejection_rows:
        rejection_rows.append(_rejection_row(language, version, 1, "__none__", "punctuation"))
    assert all(row["reason_code"] in VALID_REJECTION_REASON_CODES for row in rejection_rows)
    _write_csv(target_dir / f"rejections-{version}.csv", REJECTION_COLUMNS, rejection_rows)
    load_curated_frequency_entries(language, version=version, assets_dir=assets_dir)


def _rejection_row(language: SupportedLanguage, version: str, source_rank: int, token: str, reason: str) -> dict[str, object]:
    return {
        "language": language.value,
        "frequency_list_version": version,
        "source_rank": source_rank,
        "token": token or "<empty>",
        "reason_code": reason,
    }


def _wordfreq_language_code(language_code: str) -> str:
    return _WORDFREQ_LANGUAGE_ALIASES.get(language_code, language_code)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check_assets(*, assets_dir: Path, version: str, language_code: str | None = None) -> None:
    for code in _language_codes(language_code):
        load_curated_frequency_entries(SupportedLanguage(code), version=version, assets_dir=assets_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-dir", type=Path, default=Path("assets/frequency"))
    parser.add_argument("--version", default="v1")
    parser.add_argument("--language", choices=DEFAULT_SUPPORTED_LANGUAGES, help="Build or check one language code only.")
    parser.add_argument("--scan-limit", type=int, default=25000)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_assets(assets_dir=args.assets_dir, version=args.version, language_code=args.language)
    else:
        build_assets(
            assets_dir=args.assets_dir,
            version=args.version,
            scan_limit=args.scan_limit,
            language_code=args.language,
        )


if __name__ == "__main__":
    main()
