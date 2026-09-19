import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.repositories.job_repository import JobRepository
from multilang.services.korean_learning_runtime import KoreanLearningRuntime


def policy(model="fixture"):
    budget = KoreanProviderBudget(max_attempts=1, max_input_tokens=10000, max_output_tokens=1024,
        max_total_tokens=11024, max_estimated_cost_usd=1, max_latency_ms=1000,
        timeout_seconds=1, max_batch_items=1, max_concurrency=1)
    return KoreanProviderPolicy(routes=tuple(KoreanProviderRoute(task=task, provider="fake", model=model,
        budget=budget, cache_namespace="binding-test", response_schema_sha256="a" * 64) for task in KoreanProviderTask))


def test_cli_binds_policy_durably_and_refuses_silent_replacement(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'policy.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        runtime = KoreanLearningRuntime(session)
        job = JobRepository(session).create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
            run_key="binding", source_fingerprint="fixture", total_items=1)
        job_id = job.id
        source = tmp_path / "policy.json"
        source.write_text(policy().model_dump_json(), encoding="utf-8")
        command = ["korean", "bind-provider-policy", "--job-id", job_id, "--provider-policy-file", str(source)]
        app = create_app(korean_learning_service=runtime)
        first = CliRunner().invoke(app, command)
        assert first.exit_code == 0, first.output
        assert json.loads(first.output)["provider_policy_sha256"] == policy().policy_sha256
        assert CliRunner().invoke(app, command).exit_code == 0
        source.write_text(policy("changed").model_dump_json(), encoding="utf-8")
        refused = CliRunner().invoke(app, command)
        assert refused.exit_code != 0
        assert "provider_policy_conflict" in refused.output
    with Session(engine) as observer:
        stored = JobRepository(observer).get_job(job_id)
        assert stored.korean_provider_policy_sha256 == policy().policy_sha256
        assert KoreanProviderPolicy.model_validate(stored.korean_provider_policy) == policy()


def test_hash_only_existing_authority_must_match_full_policy(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'authority.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        runtime = KoreanLearningRuntime(session)
        job = JobRepository(session).create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
            run_key="binding", source_fingerprint="fixture", total_items=1)
        job.korean_provider_policy_sha256 = policy().policy_sha256
        job.korean_provider_policy = {"provider_policy_sha256": policy().policy_sha256}
        session.commit()
        with pytest.raises(ValueError, match="provider_policy_conflict"):
            runtime.bind_provider_policy(job_id=job.id, provider_policy=policy("changed"))
        assert runtime.bind_provider_policy(job_id=job.id, provider_policy=policy())["provider_policy_sha256"] == policy().policy_sha256
