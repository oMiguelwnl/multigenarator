"""Verified, bounded offline diagnostic reports for evaluator v3 artifacts."""

from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import stat
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.contextual_morphology import ContextualAnalysis
from multilang.services.vocabulary.diagnostics import diagnose_observation, pair_checks
from multilang.services.vocabulary_sources import CorpusSentence

MAX_INPUT_BYTES = 256 * 1024**2
MAX_OUTPUT_BYTES = 128 * 1024**2
MAX_CASES = 100_000
MAX_CHECKS = 250_000
_SHA = re.compile(r"[0-9a-f]{64}")
_ARTIFACT = re.compile(r"artifacts/[0-9]{2}-[a-z]{2,3}/(?:fast|balanced|accurate)")


def _plain(path: Path) -> Path:
    path = Path(path).absolute()
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("diagnostic path cannot traverse symlinks or parents")
    return path


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("nonfinite JSON value")

    result = json.loads(data, object_pairs_hook=unique, parse_constant=invalid_constant)
    if not isinstance(result, dict):
        raise ValueError("artifact must be a JSON object")
    return result


class _Reader:
    def __init__(self):
        self.remaining = MAX_INPUT_BYTES

    def read(self, path: Path, digest: str, *, limit=128 * 1024**2) -> bytes:
        if not isinstance(digest, str) or not _SHA.fullmatch(digest):
            raise ValueError("malformed artifact checksum")
        path = _plain(path)
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("artifact must be a regular file")
            limit = min(limit, self.remaining)
            if before.st_size > limit:
                raise ValueError("input byte limit exceeded")
            data = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
        if len(data) > limit or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("artifact changed or input limit exceeded")
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("artifact checksum mismatch")
        self.remaining -= len(data)
        return data


def _manifest(data: bytes, hash_key: str) -> dict:
    value = _json(data)
    if value.get("schema_version") != 1 or value.get("evaluator_version") != "3":
        raise ValueError("unsupported evaluation schema")
    if value.get(hash_key) != canonical_sha256({k: v for k, v in value.items() if k != hash_key}):
        raise ValueError("manifest content checksum mismatch")
    return value


class _Cases:
    def __init__(self, handle):
        self.handle = handle
        self.count = self.size = 0
        self.digest = hashlib.sha256()

    def write(self, case: dict) -> dict:
        case = {**case, "case_id": canonical_sha256(case)}
        data = (
            json.dumps(case, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        self.size += len(data)
        self.count += 1
        if self.size > MAX_OUTPUT_BYTES or self.count > MAX_CASES:
            raise ValueError("diagnostic output limit exceeded")
        self.handle.write(data)
        self.digest.update(data)
        return case


def _group_summary(cases, checks, feature_checks, sentence_count, predicted_count, gold_count):
    opportunities = Counter()
    for check in checks:
        if check["correct"] is not None:
            opportunities[(check["metric"], check["reference_pos"])] += 1
    for check in feature_checks:
        if check["correct"] is not None:
            opportunities[(check["field"], check["reference_pos"])] += 1
    groups = {}
    for case in cases:
        key = (case["category"], case["field"], case["reference_pos"])
        if key not in groups:
            category, field, pos = key
            metric = {
                "lemma_different": "lemma_accuracy",
                "pos_different": "pos_accuracy",
                "token_unmatched": "exact_span_recall",
            }.get(category, field)
            eligible = opportunities[(metric, pos)]
            denominator = "aligned_reference_tokens_by_pos"
            if category.startswith("analysis_"):
                eligible, denominator = sentence_count, "sentences"
            elif category == "reference_span_missing":
                eligible, denominator = gold_count, "reference_tokens"
            elif category == "predicted_token_unmatched":
                eligible, denominator = predicted_count, "predicted_tokens"
            elif category == "blocked_span":
                eligible, denominator = None, "not_a_token_accuracy"
            elif category.startswith("feature_"):
                denominator = "exactly_aligned_tokens_with_reference_field_by_pos"
            groups[key] = {
                "category": category,
                "field": field,
                "reference_pos": pos,
                "count": 0,
                "eligible": eligible,
                "denominator": denominator,
                "examples": [],
                "confusions": Counter(),
            }
        group = groups[key]
        group["count"] += 1
        confusion = (
            json.dumps(case["expected"], ensure_ascii=False, sort_keys=True),
            json.dumps(case["actual"], ensure_ascii=False, sort_keys=True),
        )
        group["confusions"][confusion] += 1
        if len(group["examples"]) < 3:
            group["examples"].append(
                {
                    key: case[key]
                    for key in (
                        "case_id",
                        "word",
                        "sentence",
                        "expected",
                        "actual",
                        "evidence",
                    )
                }
            )
    result = []
    for group in groups.values():
        group["rate"] = group["count"] / group["eligible"] if group["eligible"] else None
        group["confusions"] = [
            {"expected": json.loads(pair[0]), "actual": json.loads(pair[1]), "count": count}
            for pair, count in sorted(
                group["confusions"].items(), key=lambda item: (-item[1], item[0])
            )
        ]
        result.append(group)
    return sorted(
        result, key=lambda g: (-g["count"], g["category"], g["field"], g["reference_pos"] or "")
    )


def _validate_metrics(manifest, checks, *, gold_count, predicted_count):
    """Reconcile the original counts, including missing and incompatible predictions."""
    fields = {
        "exact_span_recall": ("exact_span_matches", "aligned_gold_tokens"),
        "lemma_accuracy": ("lemma_correct", "lemma_eligible_tokens"),
        "pos_accuracy": ("pos_correct", "pos_eligible_tokens"),
        "annotated_features_accuracy": ("features_correct", "features_eligible_tokens"),
    }
    counts = Counter({"gold_tokens": gold_count, "predicted_tokens": predicted_count})
    for check in checks:
        numerator, denominator = fields[check["metric"]]
        expected, actual = check["expected"], check["actual"]
        correct = actual is not None and (
            all(actual.get(k) == v for k, v in expected.items())
            if isinstance(expected, dict)
            else expected == actual
        )
        counts[denominator] += 1
        counts[numerator] += bool(correct)
    counts["unaligned_gold_tokens"] = gold_count - counts["aligned_gold_tokens"]
    for name in {key for pair in fields.values() for key in pair} | set(counts):
        if manifest["counts"].get(name, 0) != counts[name]:
            raise ValueError("evaluation metric count mismatch")
    fields["exact_span_precision"] = ("exact_span_matches", "predicted_tokens")
    if set(manifest["metric_compatibility"]) != set(fields):
        raise ValueError("evaluation metric compatibility mismatch")
    for metric, (numerator, denominator) in fields.items():
        raw = counts[numerator] / counts[denominator] if counts[denominator] else None
        comparable = manifest["metric_compatibility"][metric]["comparable"]
        expected = raw if comparable else None
        if (
            manifest["metrics"].get(metric) != expected
            or manifest["raw_annotation_metrics"].get(metric) != raw
        ):
            raise ValueError("evaluation metric value mismatch")


def _evaluation(reader, root, digest, *, profile, dataset_id, writer, metadata=None):
    data = reader.read(root / "manifest.json", digest, limit=1024**2)
    manifest = _manifest(data, "evaluation_sha256")
    if manifest.get("corpus_split") not in {"dev", "test"}:
        raise ValueError("invalid corpus split")
    if metadata is not None:
        for name in (
            "language",
            "corpus_sha256",
            "corpus_split",
            "model_fingerprints",
            "counts",
            "metrics",
            "metric_compatibility",
            "sample_sentence_count",
            "source_sentence_count",
            "analysis_statuses",
        ):
            if manifest.get(name) != metadata.get(name):
                raise ValueError("comparison/evaluation metadata mismatch")
        if manifest["observations_sha256"] != metadata.get("artifact_observations_sha256"):
            raise ValueError("comparison observation checksum mismatch")
    compatibility = manifest.get("metric_compatibility")
    if not isinstance(compatibility, dict) or not all(
        isinstance(v, dict) and type(v.get("comparable")) is bool for v in compatibility.values()
    ):
        raise ValueError("invalid metric compatibility")
    observations = reader.read(root / "observations.jsonl", manifest.get("observations_sha256"))
    references, checks, feature_checks, cases = [], [], [], []
    statuses, reasons, blockers = Counter(), Counter(), Counter()
    seen = set()
    predicted_count = gold_count = 0
    for line_number, line in enumerate(io.BytesIO(observations), 1):
        if line_number > 5000 or len(line) > 16 * 1024**2:
            raise ValueError("observation count or line limit exceeded")
        payload = _json(line)
        reference = CorpusSentence.model_validate(payload.get("reference"))
        analysis = ContextualAnalysis.model_validate(payload.get("analysis"))
        if (
            reference.language.value != manifest["language"]
            or reference.source_sha256 != manifest["corpus_sha256"]
            or analysis.model_fingerprint not in manifest["model_fingerprints"]
        ):
            raise ValueError("observation identity mismatch")
        reference_data = reference.model_dump(mode="json")
        identity = canonical_sha256(reference_data)
        if identity in seen:
            raise ValueError("duplicate reference observation")
        seen.add(identity)
        references.append(reference_data)
        diagnosed = diagnose_observation(reference, analysis, compatibility=compatibility)
        evidence = {
            "artifact": metadata["artifact_path"] if metadata else ".",
            "observations_sha256": manifest["observations_sha256"],
            "line": line_number,
        }
        for case in diagnosed["cases"]:
            cases.append(
                writer.write(
                    {
                        **case,
                        "kind": "occurrence",
                        "dataset_id": dataset_id,
                        "profile": profile,
                        "model_fingerprint": analysis.model_fingerprint,
                        "evidence": evidence,
                    }
                )
            )
        checks.extend(
            {**check, "evidence": evidence, "model_fingerprint": analysis.model_fingerprint}
            for check in diagnosed["checks"]
        )
        feature_checks.extend(diagnosed["feature_checks"])
        if len(checks) + len(feature_checks) > MAX_CHECKS:
            raise ValueError("diagnostic check limit exceeded")
        statuses[analysis.status] += 1
        reasons[(analysis.status, analysis.reason)] += 1
        blockers.update(block.reason for block in analysis.blocked_spans)
        predicted_count += len(analysis.tokens)
        gold_count += len(reference.tokens)
    if not references or len(references) != manifest.get("sample_sentence_count"):
        raise ValueError("observation count mismatch")
    sample = canonical_sha256(references)
    if metadata is not None and sample != metadata.get("sample_sha256"):
        raise ValueError("observation sample checksum mismatch")
    if dict(statuses) != manifest.get("analysis_statuses"):
        raise ValueError("analysis status counts mismatch")
    _validate_metrics(manifest, checks, gold_count=gold_count, predicted_count=predicted_count)
    analysis_available = any(status not in {"unavailable", "unsupported"} for status in statuses)
    source_status = metadata["status"] if metadata else "recorded"
    run = {
        "dataset_id": dataset_id,
        "profile": profile,
        "status": "diagnosed",
        "source_status": source_status,
        "pairing_eligible": analysis_available and source_status in {"completed", "equivalent"},
        "language": manifest["language"],
        "corpus_sha256": manifest["corpus_sha256"],
        "corpus_split": manifest["corpus_split"],
        "sample_sha256": sample,
        "sample_sentence_count": len(references),
        "source_sentence_count": manifest["source_sentence_count"],
        "model_fingerprints": manifest["model_fingerprints"],
        "artifact_manifest_sha256": digest,
        "metrics": manifest["metrics"],
        "counts": manifest["counts"],
        "metric_compatibility": compatibility,
        "analysis_statuses": dict(statuses),
        "analysis_reasons": [
            {"status": s, "reason": r, "count": n} for (s, r), n in sorted(reasons.items())
        ],
        "blocked_span_reasons": dict(sorted(blockers.items())),
        "incompatible_metrics": {
            k: v["reason"] for k, v in compatibility.items() if not v["comparable"]
        },
        "groups": _group_summary(
            cases, checks, feature_checks, len(references), predicted_count, gold_count
        ),
        "case_count": len(cases),
    }
    return run, checks


def _text(value) -> str:
    """Keep corpus text inert in Markdown, including links, HTML and controls."""
    value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    value = " ".join(value.split())[:300]
    value = "".join(c for c in value if c.isprintable())
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", html.escape(value, quote=False))


def _markdown(result: dict) -> str:
    lines = [
        "# Diagnóstico morfológico",
        "",
        "Divergências com a referência; causas ainda não confirmadas. Métricas originais preservadas.",
        "Nenhum modelo foi selecionado, ativado ou qualificado.",
        "",
        "Para investigar: consulte a linha de observations.jsonl indicada pelo caso, confira a anotação",
        "e compare a saída original do analisador com a normalização. Se ela não estiver registrada,",
        "reproduza apenas a frase selecionada com o mesmo modelo e registre essa evidência separadamente.",
        "Use desenvolvimento para corrigir e um conjunto independente para validar.",
        "",
    ]
    for run in result["runs"]:
        lines.extend([f"## {_text(run['language'])} / {_text(run['profile'])}", ""])
        if run["status"] != "diagnosed":
            lines.extend([f"Análise indisponível: {_text(run.get('reason'))}.", ""])
            continue
        lines.extend(
            [
                f"Frases: {run['sample_sentence_count']}; split: {_text(run['corpus_split'])}.",
                "",
                "| Métrica original | Valor |",
                "|---|---|",
            ]
        )
        for name, value in run["metrics"].items():
            lines.append(
                f"| {_text(name)} | {'não comparável' if value is None else f'{value:.4%}'} |"
            )
        for name, reason in run["incompatible_metrics"].items():
            lines.append(f"\n{_text(name)}: {_text(reason)}.")
        lines.extend(
            ["", "| Divergência | Campo | Classe | Casos / elegíveis |", "|---|---|---|---|"]
        )
        for group in run["groups"][:25]:
            lines.append(
                f"| {_text(group['category'])} | {_text(group['field'])} | "
                f"{_text(group['reference_pos'])} | {group['count']} / {group['eligible']} |"
            )
        lines.extend(
            [
                "",
                "Os denominadores por grupo estão descritos em diagnostics.json; contagens de campos",
                "usam somente tokens alinhados e não substituem a acurácia por conjunto de traços.",
                "",
            ]
        )
        for group in run["groups"][:10]:
            example = group["examples"][0]
            lines.extend(
                [
                    f"- {_text(group['category'])}: {_text(example['sentence'])}. "
                    f"Esperado: {_text(example['expected'])}; observado: {_text(example['actual'])}. "
                    f"Caso: {example['case_id']}."
                ]
            )
        lines.append("")
    for pair in result["pairs"]:
        lines.extend(
            [f"## {_text(pair['language'])}: fast → {_text(pair['candidate_profile'])}", ""]
        )
        if pair["status"] != "paired":
            lines.extend([f"Pareamento indisponível: {_text(pair['reason'])}.", ""])
            continue
        lines.extend(
            [
                "| Métrica | Resolvidos | Introduzidos | Persistentes | Elegíveis |",
                "|---|---|---|---|---|",
            ]
        )
        for metric, values in pair["metrics"].items():
            lines.append(
                f"| {_text(metric)} | {values['resolved']} | {values['introduced']} | "
                f"{values['persistent']} | {values['eligible']} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def diagnose_report(report: Path, *, manifest_sha256: str, output: Path) -> dict:
    """Publish diagnostics from a comparison or standalone evaluation, offline."""
    root, output = _plain(report), _plain(output)
    if output.exists():
        raise ValueError("diagnostic output already exists")
    if output == root or root in output.parents:
        raise ValueError("output must be outside the source artifact")
    reader = _Reader()
    source = reader.read(root / "manifest.json", manifest_sha256, limit=8 * 1024**2)
    is_comparison = "comparison_sha256" in _json(source)
    manifest = _manifest(source, "comparison_sha256" if is_comparison else "evaluation_sha256")
    datasets = manifest.get("datasets") if is_comparison else [None]
    if not isinstance(datasets, list) or not 1 <= len(datasets) <= 22:
        raise ValueError("invalid dataset count")
    output.parent.mkdir(parents=True, exist_ok=True)
    _plain(output.parent)
    with TemporaryDirectory(prefix=".morphology-diagnostics-", dir=output.parent) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir()
        runs, pairs = [], []
        with (staging / "cases.jsonl").open("wb") as handle:
            writer = _Cases(handle)
            for index, dataset in enumerate(datasets):
                dataset_id = f"{index:02d}"
                if dataset is None:
                    run, _ = _evaluation(
                        reader,
                        root,
                        manifest_sha256,
                        profile="recorded",
                        dataset_id=dataset_id,
                        writer=writer,
                    )
                    runs.append(run)
                    continue
                candidates = dataset.get("runs")
                if not isinstance(candidates, list) or not 1 <= len(candidates) <= 3:
                    raise ValueError("invalid run count")
                profiles, diagnosed = set(), {}
                for item in candidates:
                    profile = item.get("profile")
                    if profile not in {"fast", "balanced", "accurate"} or profile in profiles:
                        raise ValueError("invalid or duplicate profile")
                    profiles.add(profile)
                    if item.get("artifact_path") is None:
                        runs.append(
                            {
                                "dataset_id": dataset_id,
                                "profile": profile,
                                "language": dataset["language"],
                                "status": "unavailable",
                                "reason": item.get("reason"),
                                "source_status": item.get("status"),
                            }
                        )
                        continue
                    path = item["artifact_path"]
                    if not isinstance(path, str) or not _ARTIFACT.fullmatch(path):
                        raise ValueError("invalid evaluation artifact path")
                    metadata = {
                        **item,
                        **{k: dataset[k] for k in ("language", "corpus_sha256", "corpus_split")},
                    }
                    run, checks = _evaluation(
                        reader,
                        root / path,
                        item.get("artifact_manifest_sha256"),
                        profile=profile,
                        dataset_id=dataset_id,
                        writer=writer,
                        metadata=metadata,
                    )
                    runs.append(run)
                    diagnosed[profile] = (run, checks)
                for profile in sorted(profiles - {"fast"}):
                    pair = {
                        "dataset_id": dataset_id,
                        "language": dataset["language"],
                        "baseline_profile": "fast",
                        "candidate_profile": profile,
                    }
                    if "fast" not in diagnosed or profile not in diagnosed:
                        pairs.append(
                            {**pair, "status": "unavailable", "reason": "evaluation_unavailable"}
                        )
                        continue
                    baseline, baseline_checks = diagnosed["fast"]
                    candidate, candidate_checks = diagnosed[profile]
                    if not baseline["pairing_eligible"] or not candidate["pairing_eligible"]:
                        pairs.append(
                            {**pair, "status": "unavailable", "reason": "analyzer_unavailable"}
                        )
                        continue
                    if baseline["sample_sha256"] != candidate["sample_sha256"] or (
                        baseline["source_sentence_count"] != candidate["source_sentence_count"]
                    ):
                        pairs.append(
                            {**pair, "status": "unavailable", "reason": "incompatible_sample"}
                        )
                        continue
                    paired = pair_checks(baseline_checks, candidate_checks)
                    candidate_evidence = {
                        c["occurrence_id"]: c["evidence"] for c in candidate_checks
                    }
                    for case in paired["cases"]:
                        writer.write(
                            {
                                **case,
                                **pair,
                                "kind": "transition",
                                "baseline_fingerprints": baseline["model_fingerprints"],
                                "candidate_fingerprints": candidate["model_fingerprints"],
                                "candidate_evidence": candidate_evidence[case["occurrence_id"]],
                            }
                        )
                    pairs.append({**pair, "status": "paired", "metrics": paired["metrics"]})
        result = {
            "schema_version": 1,
            "diagnostic_version": "1",
            "evaluator_version": "3",
            "source_kind": "comparison" if is_comparison else "evaluation",
            "source_manifest_sha256": manifest_sha256,
            "runs": runs,
            "pairs": pairs,
            "case_count": writer.count,
            "activation": False,
            "qualification": False,
            "recommendation": None,
            "cause_status": "unreviewed",
            "limitations": [
                "reference_annotations_may_be_wrong",
                "raw_backend_output_may_require_replay",
                "test_data_cannot_select_models",
                "native_annotation_incompatibilities_preserved",
            ],
            "files": {"cases.jsonl": writer.digest.hexdigest()},
        }
        markdown = _markdown(result).encode()
        result["files"]["report.md"] = hashlib.sha256(markdown).hexdigest()
        result["diagnostics_sha256"] = canonical_sha256(result)
        encoded = (
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        ).encode()
        if writer.size + len(encoded) + len(markdown) > MAX_OUTPUT_BYTES:
            raise ValueError("diagnostic output limit exceeded")
        (staging / "report.md").write_bytes(markdown)
        (staging / "diagnostics.json").write_bytes(encoded)
        _plain(output)
        if output.exists():
            raise ValueError("diagnostic output created concurrently")
        os.rename(staging, output)
    return result
