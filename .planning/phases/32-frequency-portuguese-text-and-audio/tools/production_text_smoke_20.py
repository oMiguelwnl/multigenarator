from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from functools import partial
from hashlib import sha256
from itertools import combinations
from typing import Any, Iterable

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from multilang.db.models import (
    AudioAssetModel,
    CardExportModel,
    DeckExportModel,
    GenerationJob,
    LexicalCandidate,
    ProviderCallLogModel,
    TextQualityRecordModel,
)
from multilang.db.provisioning import ensure_database_schema
from multilang.domain.jobs import JobStage, JobStatus, SupportedLanguage
from multilang.domain.korean import KoreanFrequencyJobAuthority, canonical_json_sha256
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
from multilang.repositories.provider_call_log_repository import summarize_provider_call_records
from multilang.runtime import (
    KoreanFrequencyTextRuntimeAuthority,
    build_korean_frequency_text_runtime_service,
    build_runtime_service,
)
from multilang.services.korean_foundation_snapshot_fallback import (
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
)
from multilang.services.korean_frequency import load_korean_final_frequency_entries
from multilang.services.frequency_decks import build_frequency_level
from multilang.settings import Settings


PHASE_DIR = pathlib.Path(".planning/phases/32-frequency-portuguese-text-and-audio")
EVIDENCE_DIR = PHASE_DIR / "evidence-inbox"
AUTHORIZATION_PATH = EVIDENCE_DIR / "production-text-smoke-20-authorization.md"
PREFLIGHT_PATH = EVIDENCE_DIR / "production-text-smoke-20-preflight.json"
RESULT_PATH = EVIDENCE_DIR / "production-text-smoke-20-result.json"
RECOVERY_AUTHORIZATION_PATH = EVIDENCE_DIR / "production-text-smoke-20-recovery-authorization.md"
RECOVERY_PREFLIGHT_PATH = EVIDENCE_DIR / "production-text-smoke-20-recovery-preflight.json"
RECOVERY_INVOCATION_PATH = EVIDENCE_DIR / "production-text-smoke-20-recovery-invocation.json"
RECOVERY_RESULT_PATH = EVIDENCE_DIR / "production-text-smoke-20-recovery-result.json"
POLICY_PATH = EVIDENCE_DIR / "provider-policy.json"
PRIOR_BINDING_PATH = EVIDENCE_DIR / "production-database-job-binding.json"
BUNDLE_ROOT = pathlib.Path(".multilang/phase32/bundles/multilang-korean-frequency-v1")

JOB_ID = "phase32-prod-text-smoke-20"
RUN_KEY = f"ko-frequency-{JOB_ID}"
PRIOR_JOB_ID = "phase32-prod-freq-pilot-base"
TOTAL_ITEMS = 20
UNIT_SIZE = 10
EXPECTED_HEAD = "20260828_19"
EXPECTED_LOCATOR_SHA256 = "19871fdb496eed265952e0358b94fa795d1b74c37d89a674b0189ee1381f32b6"
PROVIDER_POLICY_SHA256 = "6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79"
PRIOR_AUTHORITY_SHA256 = "8c20274b95ff93360a0295090d865b4627a86eb0cf6955e96f6e97967179b797"
RATE_LIMITED_ERROR_CODE_SHA256 = "6bd8d9ee79d486f950481bd8e126006aa620bb4e8437c992532d1be65c83979a"
PROVIDER_RETRY_ERROR_CODE_SHA256 = "86225aa74257218b8bfd199c108f5ddc44c967f59f9d4f8f442437c7c626d12c"
PROTECTED_PLAN_32_54_PATHS = {
    "authorization": AUTHORIZATION_PATH,
    "preflight": PREFLIGHT_PATH,
    "result": RESULT_PATH,
    "summary": PHASE_DIR / "32-54-SUMMARY.md",
}
PROTECTED_PLAN_32_54_SHA256 = {
    "authorization": "af26bd4e93a11020de01093403f04aa9f66c9804e8aac45662d548f0c32fbdab",
    "preflight": "3d4e1392289ba0228ae27354fcb6701e3362e095de6b1c837a53f98b468038b4",
    "result": "d512dd36cf528eb7d6904a0e1459b44d7b4916e5895ac7cd48f5f1433be914e8",
    "summary": "5bad3bf992c0cd788b77334d9174bd5831e71792cdcee5d9ac27cf613a500125",
}
RECOVERY_ARTIFACTS = (
    PHASE_DIR / "32-55-PLAN.md",
    RECOVERY_AUTHORIZATION_PATH,
    RECOVERY_PREFLIGHT_PATH,
    RECOVERY_INVOCATION_PATH,
    RECOVERY_RESULT_PATH,
    PHASE_DIR / "32-55-SUMMARY.md",
    PHASE_DIR / "tools/production_text_smoke_20.py",
    pathlib.Path("tests/planning/test_phase32_production_text_smoke_recovery.py"),
    pathlib.Path(".planning/SPEC.md"),
    pathlib.Path(".planning/.state-fingerprint.json"),
)
RECOVERY_COOLDOWN_SECONDS = 60

PHASE31_ACTIVE_POINTER_SHA256 = "2727c85c12c7c793b4e431356b7e7acf5cca90cec3ec288a6b26f674a996170b"
PHASE31_ACTIVE_POINTER_CONTENT_SHA256 = "b8704d2bbcc390a2cd4ee9b1119928e83c9a75aaa3cf82da98bf2474c8e7c516"
PHASE31_VALIDATION_RECEIPT_SHA256 = "8c2e9108e51c23f26ae29635105bbf3e3017b64284d835c73c2718aa03019705"
PHASE31_SNAPSHOT_MANIFEST_SHA256 = "1ee31613d347c301fc8584382a565f841d0c1bd9c4073f38ee9291eb05aea5f5"
PHASE31_SNAPSHOT_ROOT_SHA256 = "852208b32422eb70aec70772ce92fa3284acfa2eb365acc1f40f218ad5c7d8f4"
FREQUENCY_BUNDLE_MANIFEST_SHA256 = "161aac380bab58b25725e1cd914a7df2e1c43baee3970b0e870d8e03aa724465"
FREQUENCY_BUNDLE_CONTENT_SHA256 = "d235d962f706ce95822b00ec4dc65d4fa55b96b4e28238720adf0df5cf86582a"
SOURCE_RETRIEVAL_SHA256 = "3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064"
SOURCE_BUILD_RESULT_SHA256 = "b6beb6d5e49a8616d77a8a7515cdcc07cdfbd017eae564297a5c2f6614d15b6c"
SOURCE_REVIEW_AGGREGATE_SHA256 = "24fb03999ea744be64c445bb9de704e40c29ad24ee4120e430a110fcfa0fa35a"

REQUIRED_ENV_ALIASES = {
    "database_url": ("MULTILANG_DATABASE_URL",),
    "openai_api_key": ("MULTILANG_OPENAI_API_KEY", "OPENAI_API_KEY"),
    "deepl_api_key": ("MULTILANG_DEEPL_API_KEY", "DEEPL_API_KEY"),
}
PLAN_ARTIFACTS = (
    pathlib.Path(".planning/SPEC.md"),
    pathlib.Path(".planning/.state-fingerprint.json"),
    PHASE_DIR / "32-54-PLAN.md",
    AUTHORIZATION_PATH,
    PHASE_DIR / "tools/production_text_smoke_20.py",
    PREFLIGHT_PATH,
    RESULT_PATH,
    PHASE_DIR / "32-54-SUMMARY.md",
)


class ControlledBlock(RuntimeError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class ForbiddenAudioAdapter:
    provider = "forbidden"

    def synthesize(self, *_: object, **__: object) -> object:
        raise ControlledBlock("audio_invocation_forbidden")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return canonical_json_sha256(value)


def atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = pathlib.Path(raw_temp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o600)
        temp_path.replace(path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def parse_dotenv(body: str) -> dict[str, str]:
    found: dict[str, list[str]] = {name: [] for aliases in REQUIRED_ENV_ALIASES.values() for name in aliases}
    assignment = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
    for raw_line in body.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = assignment.match(raw_line)
        if match and match.group(1) in found:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            found[match.group(1)].append(value)
    resolved: dict[str, str] = {}
    for logical_name, aliases in REQUIRED_ENV_ALIASES.items():
        matches = [(alias, value) for alias in aliases for value in found[alias]]
        if not matches:
            raise ControlledBlock(f"missing_{logical_name}")
        if len(matches) != 1:
            raise ControlledBlock(f"duplicate_{logical_name}")
        if not matches[0][1].strip():
            raise ControlledBlock(f"blank_{logical_name}")
        resolved[logical_name] = matches[0][1]
    return resolved


def load_secrets() -> dict[str, str]:
    env_path = pathlib.Path(".env")
    if not env_path.is_file() or env_path.is_symlink():
        raise ControlledBlock("missing_env_file")
    values = parse_dotenv(env_path.read_text(encoding="utf-8"))
    try:
        parsed = make_url(values["database_url"])
    except Exception as exc:
        raise ControlledBlock("malformed_database_url") from exc
    if parsed.get_backend_name() != "postgresql":
        raise ControlledBlock("target_not_postgresql")
    return values


def locator_components(raw_url: str) -> set[str]:
    parsed = make_url(raw_url)
    values = {raw_url, parsed.render_as_string(hide_password=False)}
    values.update(str(part) for part in (parsed.username, parsed.password, parsed.host, parsed.port, parsed.database) if part)
    for key, value in parsed.query.items():
        if isinstance(value, (tuple, list)):
            values.update(f"{key}={item}" for item in value if item)
        elif value:
            values.add(f"{key}={value}")
    return {value for value in values if value}


def scan_text(
    body: str,
    *,
    secrets: Iterable[str],
    runtime_log: bool = False,
    rendered_evidence: bool = True,
    check_hangul: bool = True,
) -> None:
    if re.search(r"postgres(?:ql)?(?:\+[a-z0-9_]+)?://", body, re.I):
        raise ControlledBlock("raw_locator_leak")
    for value in secrets:
        if value and value in body:
            raise ControlledBlock("secret_or_locator_component_leak")
    if check_hangul and re.search(r"[\uac00-\ud7a3]", body):
        raise ControlledBlock("learner_content_leak")
    anchored = re.compile(
        r"(?im)(?:^|[,{\s])(?:\"?(?:prompt|completion|payload|body|generated_(?:content|text)|"
        r"example_sentence|translation_text|definitions_html)\"?)\s*[:=]\s*(?!\s*(?:false|true|null|none)\b)"
    )
    if rendered_evidence and anchored.search(body):
        raise ControlledBlock("provider_or_generated_value_leak")
    if runtime_log and re.search(r"(?im)^.*(?:prompt|completion|payload|response body|generated content).*$", body):
        raise ControlledBlock("provider_runtime_log_leak")
    home_prefix = str(pathlib.Path.home()) + os.sep
    if home_prefix in body:
        raise ControlledBlock("private_absolute_path_leak")


def scan_artifacts(values: dict[str, str], paths: Iterable[pathlib.Path] = PLAN_ARTIFACTS) -> None:
    forbidden = set(values.values()) | locator_components(values["database_url"])
    for path in paths:
        if path.exists():
            scan_text(
                path.read_text(encoding="utf-8"),
                secrets=forbidden,
                rendered_evidence=path.suffix == ".json" or path.name.endswith("SUMMARY.md"),
                check_hangul=path.name != "SPEC.md",
            )


def authorization_payload() -> dict[str, Any]:
    body = AUTHORIZATION_PATH.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", body, re.S)
    if match is None:
        raise ControlledBlock("authorization_missing_json")
    payload = json.loads(match.group(1))
    expected = {
        "authority_kind": "production-text-smoke",
        "authority_stage": "pilot_base",
        "authorized_item_count": 20,
        "unit_count": 2,
        "max_items_per_unit": 10,
        "job_id": JOB_ID,
        "language": "ko",
        "source_type": "frequency",
        "model": "gpt-4.1-mini",
        "text_provider": "litellm-openai",
        "translation": "deepl-api-PT-BR",
        "max_attempts": 2,
        "max_concurrency": 1,
        "fallback": "none",
        "missing_only": True,
        "audio": False,
        "azure_allowed": False,
        "full_run_authorized": False,
        "maximum_total_items_authorized": 20,
        "terminal_state": "wait_for_user_before_3000_item_execution",
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ControlledBlock("authorization_drift")
    return payload


def validate_protected_plan_32_54_artifacts() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, path in PROTECTED_PLAN_32_54_PATHS.items():
        if not path.is_file() or path.is_symlink():
            raise ControlledBlock(f"protected_plan_32_54_{name}_missing")
        observed[name] = sha256_bytes(path.read_bytes())
        if observed[name] != PROTECTED_PLAN_32_54_SHA256[name]:
            raise ControlledBlock(f"protected_plan_32_54_{name}_drift")
    return observed


def recovery_authorization_payload() -> dict[str, Any]:
    if not RECOVERY_AUTHORIZATION_PATH.is_file() or RECOVERY_AUTHORIZATION_PATH.is_symlink():
        raise ControlledBlock("recovery_authorization_missing")
    body = RECOVERY_AUTHORIZATION_PATH.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", body, re.S)
    if match is None:
        raise ControlledBlock("recovery_authorization_missing_json")
    payload = json.loads(match.group(1))
    expected = {
        "authority_kind": "production-text-smoke-recovery",
        "decision": "Autorizar retry",
        "job_id": JOB_ID,
        "authorized_ranks": list(range(1, 21)),
        "original_result_sha256": PROTECTED_PLAN_32_54_SHA256["result"],
        "recovery_invocations": 1,
        "max_attempts_per_operation": 2,
        "unit_1_max_items": 10,
        "unit_2_gate_text_records": 10,
        "missing_only": True,
        "audio": False,
        "fallback": "none",
        "full_run_authorized": False,
        "terminal_state": "wait_for_user_before_3000_item_execution",
    }
    if payload != expected:
        raise ControlledBlock("recovery_authorization_drift")
    validate_protected_plan_32_54_artifacts()
    return payload


def create_recovery_invocation_marker(payload: dict[str, Any]) -> None:
    RECOVERY_INVOCATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(RECOVERY_INVOCATION_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ControlledBlock("recovery_invocation_already_claimed") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(RECOVERY_INVOCATION_PATH, 0o600)
    except Exception:
        # The marker intentionally remains after a post-create failure: creation consumes the one-shot lease.
        raise


def split_units(item_count: int) -> list[int]:
    if item_count != TOTAL_ITEMS:
        raise ControlledBlock("invalid_smoke_denominator")
    units = [UNIT_SIZE, UNIT_SIZE]
    if sum(units) != item_count or any(unit > UNIT_SIZE for unit in units):
        raise ControlledBlock("invalid_unit_split")
    return units


def load_policy() -> KoreanProviderPolicy:
    policy = KoreanProviderPolicy.model_validate_json(POLICY_PATH.read_text(encoding="utf-8"))
    if policy.policy_sha256 != PROVIDER_POLICY_SHA256 or policy.fallback_policy != "none":
        raise ControlledBlock("provider_policy_drift")
    expected = {
        KoreanProviderTask.DEFINITION: ("openai", "gpt-4.1-mini"),
        KoreanProviderTask.SENTENCE_GENERATION: ("openai", "gpt-4.1-mini"),
        KoreanProviderTask.REPAIR: ("openai", "gpt-4.1-mini"),
        KoreanProviderTask.TRANSLATION: ("deepl", "deepl-api-PT-BR"),
    }
    for task, route_identity in expected.items():
        route = policy.route_for(task)
        if (route.provider, route.model) != route_identity:
            raise ControlledBlock("provider_route_drift")
        if route.budget.max_attempts != 2 or route.budget.max_concurrency != 1 or route.budget.max_batch_items != 10:
            raise ControlledBlock("provider_budget_drift")
    for task in (KoreanProviderTask.WORD_AUDIO, KoreanProviderTask.SENTENCE_AUDIO):
        if policy.route_for(task).enabled:
            raise ControlledBlock("audio_route_enabled")
    return policy


def build_settings(values: dict[str, str]) -> Settings:
    settings = Settings(
        _env_file=None,
        database_url=values["database_url"],
        text_generation_provider="litellm",
        text_generation_model="gpt-4.1-mini",
        translation_provider="deepl",
        default_retry_attempts=2,
        korean_provider_max_attempts=2,
        tatoeba_enabled=False,
        audio_fallback_providers=[],
        openai_api_key=values["openai_api_key"],
        deepl_api_key=values["deepl_api_key"],
    )
    if (
        settings.text_generation_provider != "litellm"
        or settings.text_generation_model != "gpt-4.1-mini"
        or settings.translation_provider != "deepl"
        or settings.default_retry_attempts != 2
        or settings.tatoeba_enabled
        or settings.audio_fallback_providers
    ):
        raise ControlledBlock("runtime_settings_drift")
    return settings


def build_authority() -> KoreanFrequencyJobAuthority:
    return KoreanFrequencyJobAuthority(
        stage="pilot_base",
        phase31_pointer_locator_sha256=PHASE31_ACTIVE_POINTER_SHA256,
        phase31_pointer_content_sha256=PHASE31_ACTIVE_POINTER_CONTENT_SHA256,
        phase31_validation_receipt_sha256=PHASE31_VALIDATION_RECEIPT_SHA256,
        phase31_snapshot_manifest_sha256=PHASE31_SNAPSHOT_MANIFEST_SHA256,
        phase31_snapshot_root_sha256=PHASE31_SNAPSHOT_ROOT_SHA256,
        frequency_bundle_locator_sha256=FREQUENCY_BUNDLE_MANIFEST_SHA256,
        frequency_bundle_content_sha256=FREQUENCY_BUNDLE_CONTENT_SHA256,
        source_retrieval_sha256=SOURCE_RETRIEVAL_SHA256,
        source_build_result_sha256=SOURCE_BUILD_RESULT_SHA256,
        source_review_aggregate_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
        provider_policy_sha256=PROVIDER_POLICY_SHA256,
        pilot_authority_sha256=sha256_bytes(AUTHORIZATION_PATH.read_bytes()),
    )


def verify_phase31(authority: KoreanFrequencyJobAuthority) -> None:
    report = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=authority.phase31_validation_receipt_sha256
    )
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    if any(getattr(report, field, None) != value for field, value in expected.items()):
        raise ControlledBlock("phase31_authority_drift")


def db_locator_hash(raw_url: str) -> str:
    parsed = make_url(raw_url)
    locator = "|".join(str(part or "") for part in (parsed.get_backend_name(), parsed.host, parsed.port, parsed.database))
    return sha256_bytes(locator.encode("utf-8"))


def current_head(session: Session) -> str | None:
    return session.execute(text("select version_num from public.alembic_version")).scalar_one_or_none()


def controlled_job_hash(job: GenerationJob, authority_sha256: str | None) -> str:
    return sha256_json(
        {
            "id": job.id,
            "run_key": job.run_key,
            "language": job.language,
            "source_type": job.source_type,
            "source_fingerprint": job.source_fingerprint,
            "status": job.status,
            "current_stage": job.current_stage,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "retrying_items": job.retrying_items,
            "skipped_duplicates": job.skipped_duplicates,
            "authority_sha256": authority_sha256,
        }
    )


def prior_job_snapshot(repository: JobRepository) -> dict[str, str]:
    binding = json.loads(PRIOR_BINDING_PATH.read_text(encoding="utf-8"))
    if binding.get("status") != "bound" or binding.get("job_id") != PRIOR_JOB_ID:
        raise ControlledBlock("prior_binding_evidence_drift")
    job = repository.get_job(PRIOR_JOB_ID)
    if job is None:
        raise ControlledBlock("prior_job_missing")
    authority = repository.load_korean_authority(PRIOR_JOB_ID)
    authority_hash = sha256_json(authority.model_dump(mode="json", exclude_none=True))
    if authority_hash != PRIOR_AUTHORITY_SHA256 or authority_hash != binding.get("authority_sha256"):
        raise ControlledBlock("prior_job_authority_drift")
    return {"authority_sha256": authority_hash, "row_sha256": controlled_job_hash(job, authority_hash)}


def job_counts(session: Session, job_id: str) -> dict[str, int]:
    def count(model: Any) -> int:
        return int(session.scalar(select(func.count(model.id)).where(model.job_id == job_id)) or 0)

    return {
        "candidate_count": count(LexicalCandidate),
        "text_record_count": count(TextQualityRecordModel),
        "provider_attempt_count": count(ProviderCallLogModel),
        "audio_asset_count": count(AudioAssetModel),
        "card_export_count": count(CardExportModel),
        "deck_export_count": count(DeckExportModel),
    }


def candidate_identity_root(session: Session) -> str:
    rows = session.execute(
        select(LexicalCandidate.item_key, LexicalCandidate.lemma_key, LexicalCandidate.frequency_rank)
        .where(LexicalCandidate.job_id == JOB_ID)
        .order_by(LexicalCandidate.item_key)
    ).all()
    return sha256_json([{"item_key_sha256": sha256_bytes(a.encode()), "lemma_key_sha256": sha256_bytes(b.encode()), "rank": c} for a, b, c in rows])


def text_identity_root(session: Session) -> str:
    rows = session.execute(
        select(TextQualityRecordModel.item_key, TextQualityRecordModel.review_status)
        .where(TextQualityRecordModel.job_id == JOB_ID)
        .order_by(TextQualityRecordModel.item_key)
    ).all()
    return sha256_json([{"item_key_sha256": sha256_bytes(a.encode()), "review_status": b} for a, b in rows])


def verify_job_contract(job: GenerationJob, authority: KoreanFrequencyJobAuthority, repository: JobRepository) -> None:
    if (job.total_items, job.language, job.source_type, job.run_key) != (20, "ko", "frequency", RUN_KEY):
        raise ControlledBlock("persisted_job_contract_drift")
    loaded = repository.load_korean_authority(JOB_ID)
    if loaded.model_dump(mode="json", exclude_none=True) != authority.model_dump(mode="json", exclude_none=True):
        raise ControlledBlock("smoke_job_authority_drift")


def selected_candidates(authority: KoreanFrequencyJobAuthority) -> list[tuple[str, str, Any]]:
    entries = load_korean_final_frequency_entries(
        job_id=JOB_ID,
        bundle_root=BUNDLE_ROOT,
        binding_receipt_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
        authority=authority,
        repo_root=pathlib.Path.cwd(),
    )
    candidates = build_frequency_level(
        SupportedLanguage.KO,
        level=1,
        required_count_per_level=1000,
        korean_final_entries=entries,
        source_review_receipt_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
        source_review_aggregate_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
    )[:20]
    ranks = [candidate.frequency_rank for candidate in candidates]
    if len(candidates) != 20 or ranks != list(range(1, 21)) or any(candidate.frequency_level != 1 for candidate in candidates):
        raise ControlledBlock("deterministic_selection_drift")
    return [(f"level-1-rank-{rank:04d}", candidate.lemma_key, candidate) for rank, candidate in enumerate(candidates, 1)]


def ensure_smoke_setup(values: dict[str, str]) -> dict[str, Any]:
    authorization_payload()
    units = split_units(TOTAL_ITEMS)
    policy = load_policy()
    build_settings(values)
    authority = build_authority()
    verify_phase31(authority)
    if db_locator_hash(values["database_url"]) != EXPECTED_LOCATOR_SHA256:
        raise ControlledBlock("production_locator_drift")
    if ScriptDirectory.from_config(Config("alembic.ini")).get_heads() != [EXPECTED_HEAD]:
        raise ControlledBlock("alembic_head_drift")

    engine = create_engine(values["database_url"])
    try:
        ensure_database_schema(engine, values["database_url"])
        with Session(engine) as session:
            repository = JobRepository(session)
            prior_before = prior_job_snapshot(repository)
            if current_head(session) != EXPECTED_HEAD:
                raise ControlledBlock("database_revision_drift")
            counts_before = job_counts(session, JOB_ID)
            job = repository.get_job(JOB_ID)
            if job is None:
                if any(counts_before.values()):
                    raise ControlledBlock("orphan_smoke_rows")
                session.add(
                    GenerationJob(
                        id=JOB_ID,
                        run_key=RUN_KEY,
                        language="ko",
                        source_type="frequency",
                        source_fingerprint=FREQUENCY_BUNDLE_CONTENT_SHA256,
                        status=JobStatus.PENDING.value,
                        current_stage=JobStage.INGEST.value,
                        total_items=20,
                        completed_items=0,
                        failed_items=0,
                        retrying_items=0,
                        skipped_duplicates=0,
                        resume_state={},
                    )
                )
                session.commit()
                repository.bind_execution_authority(JOB_ID, authority)
                LexicalRepository(session).upsert_candidates(
                    job_id=JOB_ID,
                    run_key=RUN_KEY,
                    source_type="frequency",
                    candidates=selected_candidates(authority),
                )
                item_keys = [f"level-1-rank-{rank:04d}" for rank in range(1, 21)]
                repository.record_item_successes(JOB_ID, item_keys=item_keys, completed_stage=JobStage.INGEST)
                repository.advance_job_to_stage(JOB_ID, JobStage.GENERATE_TEXT)
            else:
                verify_job_contract(job, authority, repository)
                if counts_before["candidate_count"] != 20:
                    raise ControlledBlock("existing_candidate_denominator_drift")
            job = repository.get_job(JOB_ID)
            assert job is not None
            verify_job_contract(job, authority, repository)
            counts = job_counts(session, JOB_ID)
            if counts["candidate_count"] != 20:
                raise ControlledBlock("candidate_denominator_drift")
            if counts["text_record_count"] not in (0, 20):
                raise ControlledBlock("partial_replay_forbidden")
            if counts["text_record_count"] == 0 and counts["provider_attempt_count"] != 0:
                raise ControlledBlock("preexisting_provider_attempts")
            if counts["audio_asset_count"] or counts["card_export_count"] or counts["deck_export_count"]:
                raise ControlledBlock("downstream_side_effect_present")
            prior_after = prior_job_snapshot(repository)
            if prior_before != prior_after:
                raise ControlledBlock("prior_job_changed")
            root = candidate_identity_root(session)
    finally:
        engine.dispose()
    return {
        "schema_version": "phase32-production-text-smoke-20-preflight-v1",
        "status": "ready" if counts["text_record_count"] == 0 else "idempotent_complete",
        "database_kind": "production_postgresql_reclassified",
        "database_locator_sha256": EXPECTED_LOCATOR_SHA256,
        "alembic_head": EXPECTED_HEAD,
        "job_id": JOB_ID,
        "authority_stage": "pilot_base",
        "authorization_file_sha256": sha256_bytes(AUTHORIZATION_PATH.read_bytes()),
        "authority_sha256": sha256_json(authority.model_dump(mode="json", exclude_none=True)),
        "provider_policy_sha256": policy.policy_sha256,
        "model": "gpt-4.1-mini",
        "text_provider": "litellm-openai",
        "translation_provider": "deepl-api-PT-BR",
        "fallback_policy": "none",
        "max_attempts": 2,
        "max_concurrency": 1,
        "total_items": 20,
        "language": "ko",
        "source_type": "frequency",
        "units": units,
        "selected_level": 1,
        "selected_rank_min": 1,
        "selected_rank_max": 20,
        "selected_identity_root_sha256": root,
        **counts,
        "required_credentials_present": {"database": True, "openai": True, "deepl": True},
        "prior_job_id": PRIOR_JOB_ID,
        "prior_job_authority_sha256": prior_after["authority_sha256"],
        "prior_job_row_sha256": prior_after["row_sha256"],
        "prior_job_unchanged": True,
        "audio_synthesis_enabled": False,
        "azure_call_count": 0,
        "full_run_authorized": False,
        "full_run_attempted": False,
        "created_at_utc": utc_now(),
    }


def preflight_setup() -> int:
    values = load_secrets()
    try:
        payload = ensure_smoke_setup(values)
        if payload["status"] != "ready":
            raise ControlledBlock("same_job_already_complete")
        atomic_json(PREFLIGHT_PATH, payload)
        scan_artifacts(values)
    except ControlledBlock as exc:
        atomic_json(PREFLIGHT_PATH, sanitized_failure("preflight", exc.reason))
        scan_artifacts(values)
        return 2
    print("production_text_smoke_preflight_status=ready candidate_count=20 provider_attempt_count=0")
    return 0


def require_preflight(values: dict[str, str], *, allow_complete: bool = False) -> dict[str, Any]:
    evidence = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    fresh = ensure_smoke_setup(values)
    allowed_status = {"ready", "idempotent_complete"} if allow_complete else {"ready"}
    if evidence.get("status") != "ready" or fresh.get("status") not in allowed_status:
        raise ControlledBlock("preflight_not_ready")
    stable_keys = (
        "database_locator_sha256",
        "alembic_head",
        "job_id",
        "authority_sha256",
        "provider_policy_sha256",
        "model",
        "text_provider",
        "translation_provider",
        "total_items",
        "language",
        "source_type",
        "units",
        "selected_identity_root_sha256",
        "prior_job_authority_sha256",
        "prior_job_row_sha256",
    )
    if any(evidence.get(key) != fresh.get(key) for key in stable_keys):
        raise ControlledBlock("preflight_evidence_drift")
    return fresh


def verify_preflight() -> int:
    values = load_secrets()
    evidence = require_preflight(values)
    exact = {
        "status": "ready",
        "database_locator_sha256": EXPECTED_LOCATOR_SHA256,
        "alembic_head": EXPECTED_HEAD,
        "job_id": JOB_ID,
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "total_items": 20,
        "language": "ko",
        "source_type": "frequency",
        "candidate_count": 20,
        "text_record_count": 0,
        "provider_attempt_count": 0,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "units": [10, 10],
        "audio_synthesis_enabled": False,
        "full_run_authorized": False,
        "full_run_attempted": False,
    }
    if any(evidence.get(key) != value for key, value in exact.items()):
        raise ControlledBlock("preflight_assertion_failed")
    if evidence.get("required_credentials_present") != {"database": True, "openai": True, "deepl": True}:
        raise ControlledBlock("credential_presence_evidence_drift")
    scan_artifacts(values)
    print("production_text_smoke_preflight_verification_status=passed")
    return 0


def build_runtime(values: dict[str, str], policy: KoreanProviderPolicy, authority: KoreanFrequencyJobAuthority) -> Any:
    settings = build_settings(values)
    runtime_authority = KoreanFrequencyTextRuntimeAuthority(
        job_id=JOB_ID,
        bundle_root=BUNDLE_ROOT,
        binding_receipt_sha256=SOURCE_REVIEW_AGGREGATE_SHA256,
        authority=authority,
    )
    builder = partial(build_runtime_service, audio_adapter=ForbiddenAudioAdapter())
    return build_korean_frequency_text_runtime_service(
        settings=settings,
        runtime_authority=runtime_authority,
        phase31_provenance_verifier=verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
        runtime_builder=builder,
        korean_provider_policy=policy,
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def provider_row_id_root(rows: Iterable[Any]) -> str:
    return sha256_json(sorted(str(row.id) for row in rows))


def validate_historical_telemetry(rows: list[Any], *, now: datetime | None = None) -> dict[str, Any]:
    if len(rows) != 3 or len({str(row.id) for row in rows}) != 3:
        raise ControlledBlock("historical_telemetry_row_count_drift")
    retry_rows = [row for row in rows if row.error_code == "rate_limited"]
    aggregate_rows = [row for row in rows if row.error_code == "ProviderRetryError"]
    if (
        len(retry_rows) != 2
        or sorted(row.attempt for row in retry_rows) != [1, 2]
        or len(aggregate_rows) != 1
        or aggregate_rows[0].attempt != 1
        or any(row.status != "failure" for row in rows)
    ):
        raise ControlledBlock("historical_telemetry_shape_drift")
    basic_identities = {
        (row.job_id, row.item_key, row.operation, row.provider, row.model) for row in rows
    }
    if basic_identities != {(JOB_ID, rows[0].item_key, rows[0].operation, "litellm", "gpt-4.1-mini")}:
        raise ControlledBlock("historical_telemetry_identity_drift")
    latest = max(_aware_utc(row.created_at) for row in rows)
    checked_at = _aware_utc(now or datetime.now(UTC))
    cooldown_seconds = int((checked_at - latest).total_seconds())
    if cooldown_seconds < RECOVERY_COOLDOWN_SECONDS:
        raise ControlledBlock("provider_cooldown_not_satisfied")
    return {
        "historical_provider_row_id_root_sha256": provider_row_id_root(rows),
        "historical_provider_row_count": 3,
        "external_attempt_count": 2,
        "aggregate_failure_count": 1,
        "cooldown_seconds": cooldown_seconds,
        "cooldown_satisfied": True,
    }


def _operation_identity(row: Any) -> tuple[str, ...]:
    required_hashes = (
        "route_policy_sha256",
        "budget_snapshot_sha256",
        "cache_key_sha256",
        "response_schema_sha256",
    )
    if not row.item_key or any(not getattr(row, field, None) for field in required_hashes):
        raise ControlledBlock("recovery_telemetry_hash_missing")
    return (
        sha256_bytes(row.item_key.encode("utf-8")),
        row.operation,
        row.provider,
        row.model or "",
        *(getattr(row, field) for field in required_hashes),
    )


def classify_recovery_telemetry(rows: list[Any], *, historical_row_ids: set[str]) -> dict[str, Any]:
    new_rows = [row for row in rows if str(row.id) not in historical_row_ids]
    if len({str(row.id) for row in new_rows}) != len(new_rows):
        raise ControlledBlock("duplicate_recovery_telemetry_row")
    groups: dict[tuple[str, ...], list[Any]] = {}
    for row in new_rows:
        if row.job_id != JOB_ID or row.provider not in {"litellm", "openai", "deepl"}:
            raise ControlledBlock("unexplained_recovery_telemetry")
        if row.model and row.model != "gpt-4.1-mini":
            raise ControlledBlock("unapproved_recovery_model")
        groups.setdefault(_operation_identity(row), []).append(row)

    retryable_codes = {"rate_limited", "timeout", "provider_unavailable", "transient_provider_error"}
    permanent_codes = {
        "quota_exceeded",
        "authentication_error",
        "invalid_request",
        "content_policy",
        "permanent_provider_failure",
    }
    external_count = aggregate_count = surrogate_count = 0
    identity_summaries: list[dict[str, Any]] = []
    for identity, identity_rows in groups.items():
        aggregates = [row for row in identity_rows if row.error_code == "ProviderRetryError"]
        retry_rows = [row for row in identity_rows if row.error_code in retryable_codes]
        successes = [row for row in identity_rows if row.status == "success" and row.error_code is None]
        surrogates = [row for row in identity_rows if row.status == "failure" and row.error_code in permanent_codes]
        classified_ids = {id(row) for row in aggregates + retry_rows + successes + surrogates}
        if len(classified_ids) != len(identity_rows):
            raise ControlledBlock("unexplained_recovery_telemetry")
        if surrogates and (retry_rows or successes or aggregates or len(surrogates) != 1):
            raise ControlledBlock("ambiguous_non_retryable_surrogate")
        if aggregates and (not retry_rows or successes or len(aggregates) != 1):
            raise ControlledBlock("ambiguous_aggregate_rows")
        external = retry_rows + successes + surrogates
        ordinals = sorted(row.attempt for row in external)
        if ordinals != list(range(1, len(ordinals) + 1)) or len(ordinals) > 2:
            raise ControlledBlock("recovery_attempt_prefix_invalid")
        external_count += len(external)
        aggregate_count += len(aggregates)
        surrogate_count += len(surrogates)
        identity_summaries.append(
            {
                "operation_identity_sha256": sha256_json(list(identity)),
                "external_attempt_count": len(external),
                "aggregate_row_count": len(aggregates),
                "non_retryable_surrogate_count": len(surrogates),
                "attempt_ordinals": ordinals,
            }
        )
    return {
        "new_provider_row_count": len(new_rows),
        "external_attempt_count": external_count,
        "aggregate_row_count": aggregate_count,
        "non_retryable_surrogate_count": surrogate_count,
        "operation_identity_count": len(groups),
        "operation_summaries_sha256": sha256_json(sorted(identity_summaries, key=lambda item: item["operation_identity_sha256"])),
    }


def telemetry_evidence(session: Session) -> dict[str, Any]:
    rows = list(
        session.scalars(
            select(ProviderCallLogModel)
            .where(ProviderCallLogModel.job_id == JOB_ID)
            .order_by(ProviderCallLogModel.created_at, ProviderCallLogModel.operation)
        )
    )
    required_hashes = ("route_policy_sha256", "budget_snapshot_sha256", "cache_key_sha256", "response_schema_sha256")
    missing = sum(1 for row in rows for field in required_hashes if not getattr(row, field))
    attempts_over_policy = sum(1 for row in rows if row.attempt < 1 or row.attempt > 2)
    providers = sorted({row.provider for row in rows})
    models = sorted({row.model for row in rows if row.model})
    if any(provider not in {"litellm", "openai", "deepl"} for provider in providers):
        raise ControlledBlock("unapproved_provider_telemetry")
    if any(model != "gpt-4.1-mini" for model in models):
        raise ControlledBlock("unapproved_model_telemetry")
    summaries = summarize_provider_call_records(rows)
    return {
        "provider_attempt_count": len(rows),
        "required_telemetry_hash_count": len(rows) * len(required_hashes),
        "missing_required_telemetry_hash_count": missing,
        "attempts_over_policy_count": attempts_over_policy,
        "provider_identifiers": providers,
        "model_identifiers": models,
        "input_tokens": sum(row.input_tokens or 0 for row in rows),
        "output_tokens": sum(row.output_tokens or 0 for row in rows),
        "total_tokens": sum(row.total_tokens or 0 for row in rows),
        "estimated_cost_usd": round(sum(row.estimated_cost or 0.0 for row in rows), 8),
        "aggregate_telemetry_sha256": sha256_json(summaries),
    }


def unit_snapshot(values: dict[str, str], expected_text_count: int) -> dict[str, Any]:
    fresh = require_preflight(values, allow_complete=True)
    if fresh["text_record_count"] != expected_text_count:
        raise ControlledBlock("unit_text_count_drift")
    engine = create_engine(values["database_url"])
    try:
        with Session(engine) as session:
            counts = job_counts(session, JOB_ID)
            accepted = int(
                session.scalar(
                    select(func.count(TextQualityRecordModel.id)).where(
                        TextQualityRecordModel.job_id == JOB_ID,
                        TextQualityRecordModel.review_status == "accepted",
                    )
                )
                or 0
            )
            telemetry = telemetry_evidence(session)
            text_root = text_identity_root(session)
    finally:
        engine.dispose()
    if counts["audio_asset_count"] or counts["card_export_count"] or counts["deck_export_count"]:
        raise ControlledBlock("downstream_side_effect_present")
    return {
        "text_record_count": counts["text_record_count"],
        "accepted_items": accepted,
        "review_required_items": counts["text_record_count"] - accepted,
        "text_identity_root_sha256": text_root,
        **telemetry,
    }


def result_payload(units: list[dict[str, Any]], values: dict[str, str]) -> dict[str, Any]:
    final = unit_snapshot(values, 20)
    if final["missing_required_telemetry_hash_count"] or final["attempts_over_policy_count"]:
        raise ControlledBlock("provider_telemetry_incomplete")
    return {
        "schema_version": "phase32-production-text-smoke-20-result-v1",
        "status": "passed",
        "job_id": JOB_ID,
        "total_items": 20,
        "processed_items": 20,
        "accepted_items": final["accepted_items"],
        "review_required_items": final["review_required_items"],
        "candidate_count": 20,
        "text_record_count": final["text_record_count"],
        "candidate_identity_root_sha256": json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))["selected_identity_root_sha256"],
        "text_identity_root_sha256": final["text_identity_root_sha256"],
        "units": units,
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "model": "gpt-4.1-mini",
        "text_provider": "litellm-openai",
        "translation_provider": "deepl-api-PT-BR",
        "max_attempts": 2,
        "max_concurrency": 1,
        "fallback_policy": "none",
        "audio_synthesis_enabled": False,
        "azure_call_count": 0,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "full_run_attempted": False,
        "full_run_authorized": False,
        "captured_log_scan_status": "passed",
        "captured_logs_removed": True,
        "terminal_state": "wait_for_user_before_3000_item_execution",
        **{key: value for key, value in final.items() if key not in {"text_record_count", "accepted_items", "review_required_items", "text_identity_root_sha256"}},
        "created_at_utc": utc_now(),
    }


def execute_worker() -> int:
    values = load_secrets()
    units: list[dict[str, Any]] = []
    try:
        fresh = require_preflight(values, allow_complete=True)
        if fresh["text_record_count"] == 20:
            raise ControlledBlock("already_complete_use_idempotent_verification")
        if fresh["text_record_count"] != 0 or fresh["provider_attempt_count"] != 0:
            raise ControlledBlock("partial_replay_forbidden")
        policy = load_policy()
        authority = build_authority()
        runtime = build_runtime(values, policy, authority)
        result_one = runtime.generate_text(
            job_id=JOB_ID,
            deck_language=SupportedLanguage.KO,
            missing_only=True,
            max_items=10,
            synthesize_audio=False,
            concurrency=1,
        )
        snap_one = unit_snapshot(values, 10)
        if result_one.processed_items != 10 or snap_one["text_record_count"] != 10:
            raise ControlledBlock("unit_1_incomplete")
        units.append(
            {
                "unit": 1,
                "processed_items": 10,
                "accepted_items": snap_one["accepted_items"],
                "review_required_items": snap_one["review_required_items"],
                "text_record_count_after_unit": 10,
                "provider_attempt_count_after_unit": snap_one["provider_attempt_count"],
            }
        )
        require_preflight(values, allow_complete=True)
        result_two = runtime.generate_text(
            job_id=JOB_ID,
            deck_language=SupportedLanguage.KO,
            missing_only=True,
            max_items=10,
            synthesize_audio=False,
            concurrency=1,
        )
        snap_two = unit_snapshot(values, 20)
        if result_two.processed_items != 10 or snap_two["text_record_count"] != 20:
            raise ControlledBlock("unit_2_incomplete")
        units.append(
            {
                "unit": 2,
                "processed_items": 10,
                "accepted_items": snap_two["accepted_items"] - snap_one["accepted_items"],
                "review_required_items": snap_two["review_required_items"] - snap_one["review_required_items"],
                "text_record_count_after_unit": 20,
                "provider_attempt_count_after_unit": snap_two["provider_attempt_count"],
            }
        )
        atomic_json(RESULT_PATH, result_payload(units, values))
        scan_artifacts(values)
        return 0
    except ControlledBlock as exc:
        atomic_json(RESULT_PATH, sanitized_failure("execute", exc.reason, units=units))
        scan_artifacts(values)
        return 2
    except Exception:
        atomic_json(RESULT_PATH, sanitized_failure("execute", "sanitized_worker_failure", units=units))
        scan_artifacts(values)
        return 2


def sanitized_failure(stage: str, reason: str, *, units: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "phase32-production-text-smoke-20-failure-v1",
        "status": "failed",
        "failure_stage": stage,
        "blocked_reason": reason,
        "job_id": JOB_ID,
        "total_items": 20,
        "completed_units": units or [],
        "audio_synthesis_enabled": False,
        "azure_call_count": 0,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "full_run_attempted": False,
        "terminal_state": "blocked_before_3000_item_execution",
        "created_at_utc": utc_now(),
    }


def record_current_failure_state() -> None:
    """Replace failed result evidence with a content-free snapshot; never invokes providers."""
    values = load_secrets()
    existing = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    if existing.get("status") != "failed":
        raise ControlledBlock("failure_evidence_not_present")
    engine = create_engine(values["database_url"])
    try:
        with Session(engine) as session:
            counts = job_counts(session, JOB_ID)
            accepted = int(
                session.scalar(
                    select(func.count(TextQualityRecordModel.id)).where(
                        TextQualityRecordModel.job_id == JOB_ID,
                        TextQualityRecordModel.review_status == "accepted",
                    )
                )
                or 0
            )
            attempts = list(
                session.scalars(
                    select(ProviderCallLogModel)
                    .where(ProviderCallLogModel.job_id == JOB_ID)
                    .order_by(ProviderCallLogModel.created_at, ProviderCallLogModel.operation)
                )
            )
            status_counts: dict[str, int] = {}
            for row in attempts:
                status_counts[row.status] = status_counts.get(row.status, 0) + 1
            retry_attempt_rows = [
                row
                for row in attempts
                if row.error_code
                and sha256_bytes(row.error_code.encode("utf-8")) == RATE_LIMITED_ERROR_CODE_SHA256
            ]
            outer_failure_rows = [
                row
                for row in attempts
                if row.error_code
                and sha256_bytes(row.error_code.encode("utf-8")) == PROVIDER_RETRY_ERROR_CODE_SHA256
            ]
            common_attempt_identity_count = len(
                {(row.job_id, row.item_key, row.operation, row.provider, row.model) for row in attempts}
            )
            log_shape_supported = (
                len(attempts) == 3
                and len(retry_attempt_rows) == 2
                and sorted(row.attempt for row in retry_attempt_rows) == [1, 2]
                and len(outer_failure_rows) == 1
                and outer_failure_rows[0].attempt == 1
                and common_attempt_identity_count == 1
            )
            payload = {
                **existing,
                **counts,
                "processed_items": counts["text_record_count"],
                "accepted_items": accepted,
                "review_required_items": counts["text_record_count"] - accepted,
                "provider_attempt_status_counts": status_counts,
                "external_provider_attempt_count": len(retry_attempt_rows),
                "outer_aggregate_failure_log_count": len(outer_failure_rows),
                "provider_log_shape_supported": log_shape_supported,
                "provider_failure_classifications": ["rate_limited", "ProviderRetryError"],
                "provider_identifiers": sorted({row.provider for row in attempts}),
                "model_identifiers": sorted({row.model for row in attempts if row.model}),
                "provider_error_code_sha256s": sorted(
                    {sha256_bytes(row.error_code.encode("utf-8")) for row in attempts if row.error_code}
                ),
                "provider_calls_occurred": bool(attempts),
                "unit_1_complete": counts["text_record_count"] == 10,
                "unit_2_attempted": False,
                "captured_log_scan_status": "passed",
                "captured_logs_removed": True,
                "evidence_refreshed_at_utc": utc_now(),
            }
    finally:
        engine.dispose()
    atomic_json(RESULT_PATH, payload)
    scan_artifacts(values)


def _provider_rows(session: Session) -> list[ProviderCallLogModel]:
    return list(
        session.scalars(
            select(ProviderCallLogModel)
            .where(ProviderCallLogModel.job_id == JOB_ID)
            .order_by(ProviderCallLogModel.created_at, ProviderCallLogModel.id)
        )
    )


def _recovery_database_state(values: dict[str, str]) -> dict[str, Any]:
    validate_protected_plan_32_54_artifacts()
    recovery_authorization_payload()
    policy = load_policy()
    build_settings(values)
    authority = build_authority()
    if authority.pilot_authority_sha256 != PROTECTED_PLAN_32_54_SHA256["authorization"]:
        raise ControlledBlock("original_job_authority_binding_drift")
    verify_phase31(authority)
    if db_locator_hash(values["database_url"]) != EXPECTED_LOCATOR_SHA256:
        raise ControlledBlock("production_locator_drift")
    if ScriptDirectory.from_config(Config("alembic.ini")).get_heads() != [EXPECTED_HEAD]:
        raise ControlledBlock("alembic_head_drift")
    engine = create_engine(values["database_url"])
    try:
        with Session(engine) as session:
            if current_head(session) != EXPECTED_HEAD:
                raise ControlledBlock("database_revision_drift")
            repository = JobRepository(session)
            job = repository.get_job(JOB_ID)
            if job is None:
                raise ControlledBlock("smoke_job_missing")
            verify_job_contract(job, authority, repository)
            counts = job_counts(session, JOB_ID)
            if counts["candidate_count"] != 20:
                raise ControlledBlock("candidate_denominator_drift")
            if counts["text_record_count"] < 0 or counts["text_record_count"] > 20:
                raise ControlledBlock("text_record_count_invalid")
            if counts["audio_asset_count"] or counts["card_export_count"] or counts["deck_export_count"]:
                raise ControlledBlock("downstream_side_effect_present")
            candidate_root = candidate_identity_root(session)
            original_preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
            if candidate_root != original_preflight.get("selected_identity_root_sha256"):
                raise ControlledBlock("candidate_identity_root_drift")
            prior = prior_job_snapshot(repository)
            rows = _provider_rows(session)
            authority_hash = sha256_json(authority.model_dump(mode="json", exclude_none=True))
            job_root = controlled_job_hash(job, authority_hash)
    finally:
        engine.dispose()
    return {
        "counts": counts,
        "rows": rows,
        "candidate_identity_root_sha256": candidate_root,
        "authority_sha256": authority_hash,
        "job_state_root_sha256": sha256_json(
            {
                "job_row_sha256": job_root,
                "authority_sha256": authority_hash,
                "candidate_identity_root_sha256": candidate_root,
                "counts": counts,
            }
        ),
        "prior_job_authority_sha256": prior["authority_sha256"],
        "prior_job_row_sha256": prior["row_sha256"],
        "provider_policy_sha256": policy.policy_sha256,
    }


def _historical_rows_from_root(rows: list[Any], expected_root: str) -> list[Any]:
    matches = [list(group) for group in combinations(rows, 3) if provider_row_id_root(group) == expected_root]
    if len(matches) != 1:
        raise ControlledBlock("historical_provider_row_root_unresolvable")
    return matches[0]


def recovery_preflight() -> int:
    values = load_secrets()
    try:
        if RECOVERY_INVOCATION_PATH.exists() or RECOVERY_RESULT_PATH.exists():
            raise ControlledBlock("recovery_already_started")
        before = _recovery_database_state(values)
        if before["counts"] != {
            "candidate_count": 20,
            "text_record_count": 0,
            "provider_attempt_count": 3,
            "audio_asset_count": 0,
            "card_export_count": 0,
            "deck_export_count": 0,
        }:
            raise ControlledBlock("recovery_starting_counts_drift")
        historical = validate_historical_telemetry(before["rows"])
        after = _recovery_database_state(values)
        if before["job_state_root_sha256"] != after["job_state_root_sha256"]:
            raise ControlledBlock("recovery_preflight_database_delta")
        protected = validate_protected_plan_32_54_artifacts()
        payload = {
            "schema_version": "phase32-production-text-smoke-20-recovery-preflight-v1",
            "status": "ready",
            "job_id": JOB_ID,
            "total_items": 20,
            "candidate_count": 20,
            "text_record_count": 0,
            "audio_asset_count": 0,
            "card_export_count": 0,
            "deck_export_count": 0,
            "historical_provider_row_count": 3,
            "historical_external_attempt_count": 2,
            "historical_aggregate_failure_count": 1,
            "historical_provider_row_id_root_sha256": historical["historical_provider_row_id_root_sha256"],
            "cooldown_seconds": historical["cooldown_seconds"],
            "cooldown_satisfied": True,
            "database_locator_sha256": EXPECTED_LOCATOR_SHA256,
            "alembic_head": EXPECTED_HEAD,
            "authority_sha256": before["authority_sha256"],
            "original_pilot_authority_sha256": PROTECTED_PLAN_32_54_SHA256["authorization"],
            "recovery_authorization_sha256": sha256_bytes(RECOVERY_AUTHORIZATION_PATH.read_bytes()),
            "protected_plan_32_54_sha256": protected,
            "candidate_identity_root_sha256": before["candidate_identity_root_sha256"],
            "database_state_root_sha256": before["job_state_root_sha256"],
            "provider_policy_sha256": before["provider_policy_sha256"],
            "model": "gpt-4.1-mini",
            "text_provider": "litellm-openai",
            "translation_provider": "deepl-api-PT-BR",
            "fallback_policy": "none",
            "max_attempts_per_operation": 2,
            "max_concurrency": 1,
            "unit_1_max_items": 10,
            "unit_2_gate_text_records": 10,
            "audio_synthesis_enabled": False,
            "azure_call_count": 0,
            "full_run_authorized": False,
            "invocation_marker_exists": False,
            "recovery_result_exists": False,
            "required_credentials_present": {"database": True, "openai": True, "deepl": True},
            "preflight_database_delta_count": 0,
            "terminal_state": "wait_for_user_before_3000_item_execution",
            "created_at_utc": utc_now(),
        }
        atomic_json(RECOVERY_PREFLIGHT_PATH, payload)
        scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
    except ControlledBlock as exc:
        atomic_json(RECOVERY_PREFLIGHT_PATH, sanitized_failure("recovery_preflight", exc.reason))
        scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
        return 2
    print("production_text_smoke_recovery_preflight_status=ready candidate_count=20 historical_external_attempts=2")
    return 0


def require_recovery_preflight(values: dict[str, str], *, before_marker: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = json.loads(RECOVERY_PREFLIGHT_PATH.read_text(encoding="utf-8"))
    if evidence.get("status") != "ready":
        raise ControlledBlock("recovery_preflight_not_ready")
    validate_protected_plan_32_54_artifacts()
    recovery_authorization_payload()
    state = _recovery_database_state(values)
    stable = {
        "authority_sha256": state["authority_sha256"],
        "candidate_identity_root_sha256": state["candidate_identity_root_sha256"],
        "provider_policy_sha256": state["provider_policy_sha256"],
        "recovery_authorization_sha256": sha256_bytes(RECOVERY_AUTHORIZATION_PATH.read_bytes()),
        "protected_plan_32_54_sha256": PROTECTED_PLAN_32_54_SHA256,
    }
    if any(evidence.get(key) != value for key, value in stable.items()):
        raise ControlledBlock("recovery_preflight_evidence_drift")
    if before_marker:
        if RECOVERY_INVOCATION_PATH.exists() or RECOVERY_RESULT_PATH.exists():
            raise ControlledBlock("recovery_already_started")
        if state["job_state_root_sha256"] != evidence.get("database_state_root_sha256"):
            raise ControlledBlock("recovery_database_state_drift")
        historical = validate_historical_telemetry(state["rows"])
        if historical["historical_provider_row_id_root_sha256"] != evidence.get("historical_provider_row_id_root_sha256"):
            raise ControlledBlock("historical_provider_row_root_drift")
    return evidence, state


def verify_recovery_preflight() -> int:
    values = load_secrets()
    evidence, state = require_recovery_preflight(values, before_marker=True)
    required = {
        "status": "ready",
        "job_id": JOB_ID,
        "total_items": 20,
        "candidate_count": 20,
        "text_record_count": 0,
        "historical_provider_row_count": 3,
        "historical_external_attempt_count": 2,
        "historical_aggregate_failure_count": 1,
        "cooldown_satisfied": True,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "azure_call_count": 0,
        "full_run_authorized": False,
        "invocation_marker_exists": False,
        "recovery_result_exists": False,
        "preflight_database_delta_count": 0,
    }
    if any(evidence.get(key) != value for key, value in required.items()):
        raise ControlledBlock("recovery_preflight_assertion_failed")
    if state["counts"]["provider_attempt_count"] != 3:
        raise ControlledBlock("historical_telemetry_count_drift")
    scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
    print("production_text_smoke_recovery_preflight_verification_status=passed status=ready")
    return 0


def _recovery_result_from_database(
    values: dict[str, str],
    *,
    units: list[dict[str, Any]],
    unit_2_attempted: bool,
) -> dict[str, Any]:
    preflight = json.loads(RECOVERY_PREFLIGHT_PATH.read_text(encoding="utf-8"))
    state = _recovery_database_state(values)
    historical_rows = _historical_rows_from_root(
        state["rows"], preflight["historical_provider_row_id_root_sha256"]
    )
    historical_ids = {str(row.id) for row in historical_rows}
    recovery_telemetry = classify_recovery_telemetry(state["rows"], historical_row_ids=historical_ids)
    engine = create_engine(values["database_url"])
    try:
        with Session(engine) as session:
            accepted = int(
                session.scalar(
                    select(func.count(TextQualityRecordModel.id)).where(
                        TextQualityRecordModel.job_id == JOB_ID,
                        TextQualityRecordModel.review_status == "accepted",
                    )
                )
                or 0
            )
            text_root = text_identity_root(session)
    finally:
        engine.dispose()
    text_count = state["counts"]["text_record_count"]
    recovered = (
        text_count == 20
        and len(units) == 2
        and [unit.get("processed_items") for unit in units] == [10, 10]
    )
    if recovery_telemetry["aggregate_row_count"]:
        failure_classification = "retryable_attempts_exhausted"
    elif recovery_telemetry["non_retryable_surrogate_count"]:
        failure_classification = "non_retryable_provider_failure"
    else:
        failure_classification = None if recovered else "controlled_execution_failure"
    marker_sha256 = sha256_bytes(RECOVERY_INVOCATION_PATH.read_bytes())
    return {
        "schema_version": "phase32-production-text-smoke-20-recovery-result-v1",
        "status": "recovered" if recovered else "bounded_refailure",
        "failure_classification": failure_classification,
        "job_id": JOB_ID,
        "total_items": 20,
        "processed_items": text_count,
        "candidate_count": state["counts"]["candidate_count"],
        "text_record_count": text_count,
        "accepted_items": accepted,
        "review_required_items": text_count - accepted,
        "units": units,
        "unit_2_attempted": unit_2_attempted,
        "candidate_identity_root_sha256": state["candidate_identity_root_sha256"],
        "text_identity_root_sha256": text_root,
        "authority_sha256": state["authority_sha256"],
        "original_pilot_authority_sha256": PROTECTED_PLAN_32_54_SHA256["authorization"],
        "recovery_authorization_sha256": sha256_bytes(RECOVERY_AUTHORIZATION_PATH.read_bytes()),
        "recovery_preflight_sha256": sha256_bytes(RECOVERY_PREFLIGHT_PATH.read_bytes()),
        "recovery_invocation_sha256": marker_sha256,
        "invocation_marker_count": 1,
        "historical_provider_row_count": 3,
        "historical_provider_row_id_root_sha256": preflight["historical_provider_row_id_root_sha256"],
        "protected_plan_32_54_sha256": validate_protected_plan_32_54_artifacts(),
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "model": "gpt-4.1-mini",
        "text_provider": "litellm-openai",
        "translation_provider": "deepl-api-PT-BR",
        "max_attempts_per_operation": 2,
        "max_concurrency": 1,
        "fallback_policy": "none",
        **recovery_telemetry,
        "audio_synthesis_enabled": False,
        "azure_call_count": 0,
        "audio_asset_count": state["counts"]["audio_asset_count"],
        "card_export_count": state["counts"]["card_export_count"],
        "deck_export_count": state["counts"]["deck_export_count"],
        "full_run_attempted": False,
        "captured_log_scan_status": "pending",
        "captured_logs_removed": False,
        "terminal_state": "wait_for_user_before_3000_item_execution",
        "created_at_utc": utc_now(),
    }


def execute_recovery_worker() -> int:
    values = load_secrets()
    units: list[dict[str, Any]] = []
    unit_2_attempted = False
    marker_created = False
    try:
        preflight, state = require_recovery_preflight(values, before_marker=True)
        historical = validate_historical_telemetry(state["rows"])
        marker = {
            "schema_version": "phase32-production-text-smoke-20-recovery-invocation-v1",
            "status": "claimed",
            "job_id": JOB_ID,
            "invocation_ordinal": 1,
            "recovery_authorization_sha256": preflight["recovery_authorization_sha256"],
            "protected_plan_32_54_sha256": PROTECTED_PLAN_32_54_SHA256,
            "historical_provider_row_id_root_sha256": historical["historical_provider_row_id_root_sha256"],
            "database_state_root_sha256": state["job_state_root_sha256"],
            "authority_sha256": state["authority_sha256"],
            "candidate_identity_root_sha256": state["candidate_identity_root_sha256"],
            "provider_policy_sha256": PROVIDER_POLICY_SHA256,
            "max_attempts_per_operation": 2,
            "max_concurrency": 1,
            "audio_synthesis_enabled": False,
            "full_run_authorized": False,
            "created_at_utc": utc_now(),
        }
        create_recovery_invocation_marker(marker)
        marker_created = True

        # Provider construction is deliberately after the irreversible one-shot marker.
        runtime = build_runtime(values, load_policy(), build_authority())
        result_one = runtime.generate_text(
            job_id=JOB_ID,
            deck_language=SupportedLanguage.KO,
            missing_only=True,
            max_items=10,
            synthesize_audio=False,
            concurrency=1,
        )
        snap_one = _recovery_database_state(values)
        if result_one.processed_items != 10 or snap_one["counts"]["text_record_count"] != 10:
            raise ControlledBlock("unit_1_incomplete")
        units.append({"unit": 1, "processed_items": 10, "text_record_count_after_unit": 10})

        # Unit 2 is impossible unless both the runtime result and persisted count prove Unit 1 complete.
        if snap_one["counts"]["text_record_count"] != 10:
            raise ControlledBlock("unit_2_gate_not_satisfied")
        unit_2_attempted = True
        result_two = runtime.generate_text(
            job_id=JOB_ID,
            deck_language=SupportedLanguage.KO,
            missing_only=True,
            max_items=10,
            synthesize_audio=False,
            concurrency=1,
        )
        snap_two = _recovery_database_state(values)
        if result_two.processed_items != 10 or snap_two["counts"]["text_record_count"] != 20:
            raise ControlledBlock("unit_2_incomplete")
        units.append({"unit": 2, "processed_items": 10, "text_record_count_after_unit": 20})
    except Exception:
        if not marker_created:
            raise
    payload = _recovery_result_from_database(values, units=units, unit_2_attempted=unit_2_attempted)
    atomic_json(RECOVERY_RESULT_PATH, payload)
    return 0 if payload["status"] == "recovered" else 2


def public_execute_recovery() -> int:
    values = load_secrets()
    pathlib.Path("/tmp/opencode").mkdir(mode=0o700, parents=True, exist_ok=True)
    stdout_fd, stdout_name = tempfile.mkstemp(prefix="phase32-recovery-out-", dir="/tmp/opencode")
    stderr_fd, stderr_name = tempfile.mkstemp(prefix="phase32-recovery-err-", dir="/tmp/opencode")
    stdout_path, stderr_path = pathlib.Path(stdout_name), pathlib.Path(stderr_name)
    os.chmod(stdout_path, 0o600)
    os.chmod(stderr_path, 0o600)
    environment = os.environ.copy()
    environment.update(
        {
            "MULTILANG_DATABASE_URL": values["database_url"],
            "MULTILANG_OPENAI_API_KEY": values["openai_api_key"],
            "MULTILANG_DEEPL_API_KEY": values["deepl_api_key"],
            "LITELLM_LOG": "ERROR",
            "LITELLM_LOGGING": "false",
        }
    )
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("DEEPL_API_KEY", None)
    scan_passed = False
    returncode = 2
    try:
        with os.fdopen(stdout_fd, "wb") as stdout_handle, os.fdopen(stderr_fd, "wb") as stderr_handle:
            completed = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__)), "--execute-recovery-worker"],
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                env=environment,
                check=False,
                timeout=1800,
            )
        returncode = completed.returncode
        forbidden = set(values.values()) | locator_components(values["database_url"])
        for path in (stdout_path, stderr_path):
            scan_text(path.read_text(encoding="utf-8"), secrets=forbidden, runtime_log=True)
        scan_passed = True
    except (ControlledBlock, UnicodeDecodeError, subprocess.TimeoutExpired):
        scan_passed = False
    finally:
        secure_unlink(stdout_path)
        secure_unlink(stderr_path)

    if not RECOVERY_RESULT_PATH.exists() and RECOVERY_INVOCATION_PATH.exists():
        fallback = _recovery_result_from_database(values, units=[], unit_2_attempted=False)
        atomic_json(RECOVERY_RESULT_PATH, fallback)
    result = json.loads(RECOVERY_RESULT_PATH.read_text(encoding="utf-8"))
    result["captured_log_scan_status"] = "passed" if scan_passed else "failed"
    result["captured_logs_removed"] = not stdout_path.exists() and not stderr_path.exists()
    atomic_json(RECOVERY_RESULT_PATH, result)
    scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
    outcome = result.get("status", "bounded_refailure")
    print(f"production_text_smoke_recovery_status={outcome} processed_items={result.get('processed_items', 0)}")
    return 0 if returncode == 0 and scan_passed and outcome == "recovered" else 2


def validate_recovery_result_envelope(result: dict[str, Any]) -> str:
    common = {
        "job_id": JOB_ID,
        "candidate_count": 20,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "azure_call_count": 0,
        "full_run_attempted": False,
        "invocation_marker_count": 1,
        "terminal_state": "wait_for_user_before_3000_item_execution",
    }
    if any(result.get(key) != value for key, value in common.items()):
        raise ControlledBlock("recovery_result_boundary_drift")
    status = result.get("status")
    text_count = result.get("text_record_count")
    if not isinstance(text_count, int) or not 0 <= text_count <= 20 or result.get("processed_items") != text_count:
        raise ControlledBlock("recovery_result_count_drift")
    units = result.get("units")
    if not isinstance(units, list):
        raise ControlledBlock("recovery_unit_result_drift")
    if status == "recovered":
        if text_count != 20 or len(units) != 2 or [unit.get("processed_items") for unit in units] != [10, 10]:
            raise ControlledBlock("recovered_result_incomplete")
    elif status == "bounded_refailure":
        if result.get("unit_2_attempted") and text_count < 10:
            raise ControlledBlock("unit_2_gate_violated")
        if len(units) > 1 or (units and units[0].get("processed_items") != 10):
            raise ControlledBlock("bounded_refailure_unit_drift")
    else:
        raise ControlledBlock("recovery_result_status_invalid")
    return status


def verify_recovery_result() -> int:
    values = load_secrets()
    result = json.loads(RECOVERY_RESULT_PATH.read_text(encoding="utf-8"))
    outcome = validate_recovery_result_envelope(result)
    if result.get("captured_log_scan_status") != "passed" or result.get("captured_logs_removed") is not True:
        raise ControlledBlock("recovery_log_containment_failed")
    if not RECOVERY_INVOCATION_PATH.is_file() or RECOVERY_INVOCATION_PATH.is_symlink():
        raise ControlledBlock("recovery_invocation_marker_missing")
    marker = json.loads(RECOVERY_INVOCATION_PATH.read_text(encoding="utf-8"))
    if marker.get("invocation_ordinal") != 1 or marker.get("status") != "claimed":
        raise ControlledBlock("recovery_invocation_marker_drift")
    if sha256_bytes(RECOVERY_INVOCATION_PATH.read_bytes()) != result.get("recovery_invocation_sha256"):
        raise ControlledBlock("recovery_invocation_binding_drift")
    state = _recovery_database_state(values)
    if state["counts"]["text_record_count"] != result.get("text_record_count"):
        raise ControlledBlock("recovery_database_result_drift")
    preflight = json.loads(RECOVERY_PREFLIGHT_PATH.read_text(encoding="utf-8"))
    historical = _historical_rows_from_root(state["rows"], preflight["historical_provider_row_id_root_sha256"])
    telemetry = classify_recovery_telemetry(state["rows"], historical_row_ids={str(row.id) for row in historical})
    for key, value in telemetry.items():
        if result.get(key) != value:
            raise ControlledBlock("recovery_telemetry_evidence_drift")
    scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
    print(f"production_text_smoke_recovery_result_verification_status=passed outcome={outcome}")
    return 0


def verify_recovery_artifacts() -> int:
    values = load_secrets()
    validate_protected_plan_32_54_artifacts()
    for path in RECOVERY_ARTIFACTS:
        if not path.is_file() or path.is_symlink():
            raise ControlledBlock("recovery_artifact_missing")
    verify_recovery_result()
    scan_artifacts(values, (*PLAN_ARTIFACTS, *RECOVERY_ARTIFACTS))
    print("production_text_smoke_recovery_artifact_verification_status=passed")
    return 0


def secure_unlink(path: pathlib.Path) -> None:
    try:
        size = path.stat().st_size
        with path.open("r+b", buffering=0) as handle:
            handle.write(b"\0" * size)
            handle.flush()
            os.fsync(handle.fileno())
        path.unlink()
    except FileNotFoundError:
        pass


def public_execute() -> int:
    values = load_secrets()
    pathlib.Path("/tmp/opencode").mkdir(mode=0o700, parents=True, exist_ok=True)
    stdout_fd, stdout_name = tempfile.mkstemp(prefix="phase32-smoke-out-", dir="/tmp/opencode")
    stderr_fd, stderr_name = tempfile.mkstemp(prefix="phase32-smoke-err-", dir="/tmp/opencode")
    stdout_path, stderr_path = pathlib.Path(stdout_name), pathlib.Path(stderr_name)
    os.chmod(stdout_path, 0o600)
    os.chmod(stderr_path, 0o600)
    environment = os.environ.copy()
    environment.update(
        {
            "MULTILANG_DATABASE_URL": values["database_url"],
            "MULTILANG_OPENAI_API_KEY": values["openai_api_key"],
            "MULTILANG_DEEPL_API_KEY": values["deepl_api_key"],
            "LITELLM_LOG": "ERROR",
            "LITELLM_LOGGING": "false",
        }
    )
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("DEEPL_API_KEY", None)
    try:
        with os.fdopen(stdout_fd, "wb") as stdout_handle, os.fdopen(stderr_fd, "wb") as stderr_handle:
            completed = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__)), "--execute-worker"],
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                env=environment,
                check=False,
                timeout=1800,
            )
        out_bytes = stdout_path.read_bytes()
        err_bytes = stderr_path.read_bytes()
        for captured in (out_bytes, err_bytes):
            scan_text(captured.decode("utf-8", errors="strict"), secrets=set(values.values()) | locator_components(values["database_url"]), runtime_log=True)
        scan_artifacts(values)
        if completed.returncode != 0:
            print("production_text_smoke_status=failed processed_items=bounded provider_calls_may_have_occurred=true")
            return 2
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if result.get("status") != "passed" or result.get("processed_items") != 20:
            raise ControlledBlock("worker_result_invalid")
        print("production_text_smoke_status=passed processed_items=20 units=2 audio_items=0 export_items=0")
        return 0
    except UnicodeDecodeError:
        print("production_text_smoke_status=failed captured_log_scan=unscannable")
        return 2
    finally:
        secure_unlink(stdout_path)
        secure_unlink(stderr_path)


def verify_result() -> int:
    values = load_secrets()
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    exact = {
        "status": "passed",
        "job_id": JOB_ID,
        "total_items": 20,
        "processed_items": 20,
        "candidate_count": 20,
        "text_record_count": 20,
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "max_attempts": 2,
        "max_concurrency": 1,
        "fallback_policy": "none",
        "audio_synthesis_enabled": False,
        "azure_call_count": 0,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "full_run_attempted": False,
        "captured_log_scan_status": "passed",
        "captured_logs_removed": True,
        "terminal_state": "wait_for_user_before_3000_item_execution",
        "missing_required_telemetry_hash_count": 0,
        "attempts_over_policy_count": 0,
    }
    if any(result.get(key) != value for key, value in exact.items()):
        raise ControlledBlock("result_assertion_failed")
    units = result.get("units")
    if not isinstance(units, list) or len(units) != 2 or any(unit.get("processed_items") != 10 for unit in units):
        raise ControlledBlock("unit_result_drift")
    if result.get("accepted_items", -1) + result.get("review_required_items", -1) != 20:
        raise ControlledBlock("review_denominator_drift")
    fresh = ensure_smoke_setup(values)
    if fresh["status"] != "idempotent_complete" or fresh["text_record_count"] != 20:
        raise ControlledBlock("database_result_drift")
    scan_artifacts(values)
    print("production_text_smoke_result_verification_status=passed")
    return 0


def verify_idempotent() -> int:
    values = load_secrets()
    before = ensure_smoke_setup(values)
    if before["status"] != "idempotent_complete":
        raise ControlledBlock("idempotent_state_incomplete")
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    engine = create_engine(values["database_url"])
    try:
        with Session(engine) as session:
            before_attempts = job_counts(session, JOB_ID)["provider_attempt_count"]
            candidate_root = candidate_identity_root(session)
            text_root = text_identity_root(session)
    finally:
        engine.dispose()
    after = ensure_smoke_setup(values)
    if (
        before_attempts != after["provider_attempt_count"]
        or candidate_root != result.get("candidate_identity_root_sha256")
        or text_root != result.get("text_identity_root_sha256")
    ):
        raise ControlledBlock("idempotent_verification_drift")
    scan_artifacts(values)
    print("production_text_smoke_idempotent_verification_status=passed provider_attempt_delta=0")
    return 0


def expect_block(callable_: Any, reason: str) -> None:
    try:
        callable_()
    except ControlledBlock as exc:
        if exc.reason != reason:
            raise
    else:
        raise ControlledBlock("self_check_expected_block_missing")


def self_check() -> int:
    if split_units(20) != [10, 10]:
        raise ControlledBlock("self_check_split_failed")
    expect_block(lambda: split_units(19), "invalid_smoke_denominator")
    expect_block(lambda: split_units(21), "invalid_smoke_denominator")
    sample_url = "postgresql" + "://self_user:self_password@self-host.invalid:6543/self_db"
    parsed = parse_dotenv(
        "MULTILANG_DATABASE_URL='"
        + sample_url
        + "'\nOPENAI_API_KEY=self-openai-value\nDEEPL_API_KEY=self-deepl-value\n"
    )
    if set(parsed) != {"database_url", "openai_api_key", "deepl_api_key"}:
        raise ControlledBlock("self_check_env_parse_failed")
    expect_block(
        lambda: parse_dotenv("MULTILANG_DATABASE_URL=a\nOPENAI_API_KEY=x\nMULTILANG_OPENAI_API_KEY=y\nDEEPL_API_KEY=z\n"),
        "duplicate_openai_api_key",
    )
    fake_job = type("Job", (), {"total_items": 19, "language": "ko", "source_type": "frequency", "run_key": RUN_KEY})()
    fake_repo = type("Repo", (), {"load_korean_authority": lambda *_: build_authority()})()
    expect_block(lambda: verify_job_contract(fake_job, build_authority(), fake_repo), "persisted_job_contract_drift")
    policy = load_policy()
    if policy.route_for(KoreanProviderTask.SENTENCE_GENERATION).model != "gpt-4.1-mini":
        raise ControlledBlock("self_check_model_failed")
    forbidden_audio = ForbiddenAudioAdapter()
    expect_block(lambda: forbidden_audio.synthesize(), "audio_invocation_forbidden")
    partial = {"text_record_count": 10}
    if partial["text_record_count"] in (0, 20):
        raise ControlledBlock("self_check_partial_replay_failed")

    safe_policy = "Policy prose: prompt/completion/payload/body/generated content are forbidden. /tmp/opencode is approved."
    scan_text(safe_policy, secrets={"not-present"})
    fixtures = (
        "exact-secret-fixture",
        "postgresql" + "://example.invalid/db",
        "self-host.invalid",
        "MULTILANG_OPENAI_API_KEY=assigned-value",
        "\uD55C\uAE00",
        '{"prompt":"serialized-value"}',
        "completion=serialized-value",
        '{"payload":{"value":1}}',
        "body=serialized-value",
        str(pathlib.Path.home()) + "/private-value",
    )
    for fixture in fixtures:
        try:
            scan_text(fixture, secrets={"exact-secret-fixture", "self-host.invalid", "assigned-value"}, runtime_log=True)
        except ControlledBlock:
            pass
        else:
            raise ControlledBlock("self_check_leak_fixture_not_rejected")

    pathlib.Path("/tmp/opencode").mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="phase32-self-check-", dir="/tmp/opencode")
    path = pathlib.Path(name)
    try:
        os.chmod(path, 0o600)
        os.write(fd, b"sanitized runtime status")
        os.close(fd)
        scan_text(path.read_text(encoding="utf-8"), secrets={"not-present"}, runtime_log=True)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        secure_unlink(path)
    if path.exists():
        raise ControlledBlock("self_check_log_removal_failed")
    rendered = json.dumps({"status": "passed", "count": 20})
    scan_text(rendered, secrets={"not-present"})
    print("production_text_smoke_self_check_status=passed")
    return 0


def self_check_recovery() -> int:
    validate_protected_plan_32_54_artifacts()
    recovery_authorization_payload()
    if build_authority().pilot_authority_sha256 != PROTECTED_PLAN_32_54_SHA256["authorization"]:
        raise ControlledBlock("self_check_original_authority_rebound")

    def row(row_id: str, attempt: int, status: str, error_code: str | None) -> Any:
        digest = sha256_bytes(b"self-check")
        return type(
            "TelemetryRow",
            (),
            {
                "id": row_id,
                "job_id": JOB_ID,
                "item_key": "self-check-item",
                "operation": "definition",
                "provider": "litellm",
                "model": "gpt-4.1-mini",
                "attempt": attempt,
                "status": status,
                "error_code": error_code,
                "route_policy_sha256": digest,
                "budget_snapshot_sha256": digest,
                "cache_key_sha256": digest,
                "response_schema_sha256": digest,
                "created_at": datetime.now(UTC) - timedelta(seconds=61),
            },
        )()

    historical = [
        row("historical-1", 1, "failure", "rate_limited"),
        row("historical-2", 2, "failure", "rate_limited"),
        row("historical-aggregate", 1, "failure", "ProviderRetryError"),
    ]
    if validate_historical_telemetry(historical)["external_attempt_count"] != 2:
        raise ControlledBlock("self_check_historical_attempt_count_failed")
    expect_block(
        lambda: validate_historical_telemetry(historical, now=datetime.now(UTC) - timedelta(seconds=2)),
        "provider_cooldown_not_satisfied",
    )
    if classify_recovery_telemetry([row("success", 1, "success", None)], historical_row_ids=set())[
        "external_attempt_count"
    ] != 1:
        raise ControlledBlock("self_check_recovery_success_classification_failed")
    expect_block(
        lambda: classify_recovery_telemetry(
            [row("non-prefix", 2, "failure", "rate_limited")], historical_row_ids=set()
        ),
        "recovery_attempt_prefix_invalid",
    )
    validate_recovery_result_envelope(
        {
            "status": "bounded_refailure",
            "job_id": JOB_ID,
            "candidate_count": 20,
            "text_record_count": 0,
            "processed_items": 0,
            "units": [],
            "unit_2_attempted": False,
            "invocation_marker_count": 1,
            "audio_asset_count": 0,
            "card_export_count": 0,
            "deck_export_count": 0,
            "azure_call_count": 0,
            "full_run_attempted": False,
            "terminal_state": "wait_for_user_before_3000_item_execution",
        }
    )
    print("production_text_smoke_recovery_self_check_status=passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded Phase 32 production text smoke helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--preflight-setup", action="store_true")
    group.add_argument("--verify-preflight", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--execute-worker", action="store_true", help=argparse.SUPPRESS)
    group.add_argument("--verify-result", action="store_true")
    group.add_argument("--verify-idempotent", action="store_true")
    group.add_argument("--self-check-recovery", action="store_true")
    group.add_argument("--preflight-recovery", action="store_true")
    group.add_argument("--verify-recovery-preflight", action="store_true")
    group.add_argument("--execute-recovery", action="store_true")
    group.add_argument("--execute-recovery-worker", action="store_true", help=argparse.SUPPRESS)
    group.add_argument("--verify-recovery-result", action="store_true")
    group.add_argument("--verify-recovery-artifacts", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_check:
        return self_check()
    if args.preflight_setup:
        return preflight_setup()
    if args.verify_preflight:
        return verify_preflight()
    if args.execute:
        return public_execute()
    if args.execute_worker:
        return execute_worker()
    if args.verify_result:
        return verify_result()
    if args.verify_idempotent:
        return verify_idempotent()
    if args.self_check_recovery:
        return self_check_recovery()
    if args.preflight_recovery:
        return recovery_preflight()
    if args.verify_recovery_preflight:
        return verify_recovery_preflight()
    if args.execute_recovery:
        return public_execute_recovery()
    if args.execute_recovery_worker:
        return execute_recovery_worker()
    if args.verify_recovery_result:
        return verify_recovery_result()
    if args.verify_recovery_artifacts:
        return verify_recovery_artifacts()
    raise ControlledBlock("missing_mode")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlledBlock as exc:
        print("blocked: " + exc.reason, file=sys.stderr)
        raise SystemExit(2)
    except SystemExit:
        raise
    except Exception:
        print("blocked: sanitized production text smoke helper failure", file=sys.stderr)
        raise SystemExit(2)
