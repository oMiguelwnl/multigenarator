"""Native operator commands; share services with HTTP, never provision implicitly."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from time import sleep
from typing import Annotated

import typer
from pydantic import BaseModel, ConfigDict, SecretStr
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from multilang.settings import Settings


def _read_object(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("JSON input is missing or exceeds 32 MiB")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def _print(value) -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    typer.echo(json.dumps(value, ensure_ascii=False, default=str))


class _DatabaseTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    database_url: SecretStr


def _print_preview(value: BaseModel) -> None:
    _print(value)
    typer.echo(f"Confirmation SHA256: {value.confirmation_sha256}", err=True)


def create_native_app(*, settings: Settings | None = None, facade_factory=None) -> typer.Typer:
    cli = typer.Typer(help="Native lexical datasets, evidence, jobs and migration operations.")
    from multilang.vocabulary_cli import create_vocabulary_app

    cli.add_typer(create_vocabulary_app(settings=settings), name="vocabulary")

    def configuration(*, require_enabled=True):
        config = settings or Settings()
        if require_enabled and not config.roadmap_4_enabled:
            typer.echo("Native operations are disabled; set MULTILANG_ROADMAP_4_ENABLED=true.")
            raise typer.Exit(1)
        return config

    @contextmanager
    def database(*, require_enabled=True):
        config = configuration(require_enabled=require_enabled)
        engine = create_engine(config.database_url, pool_pre_ping=True)
        try:
            yield config, engine
        except (ValueError, OSError, SQLAlchemyError) as exc:
            typer.echo(f"Operation rejected ({type(exc).__name__}); validate inputs and evidence.")
            raise typer.Exit(1) from None
        finally:
            engine.dispose()

    def facade(session, config):
        if facade_factory is not None:
            return facade_factory(session, config)
        from multilang.native_runtime import build_native_facade

        return build_native_facade(session, config)

    @cli.command("status")
    def status():
        config = configuration(require_enabled=False)
        _print(
            {
                "roadmap_4_enabled": config.roadmap_4_enabled,
                "provider_calls_enabled": config.native_provider_calls_enabled,
            }
        )

    @cli.command("search")
    def search(
        query: str,
        language: str | None = None,
        limit: Annotated[int, typer.Option(min=1, max=100)] = 50,
        actor: str = "local-operator",
        min_rank: Annotated[int | None, typer.Option(min=1)] = None,
        max_rank: Annotated[int | None, typer.Option(min=1)] = None,
    ):
        with database() as (config, engine), Session(engine) as session:
            if min_rank is not None and max_rank is not None and min_rank > max_rank:
                raise ValueError("minimum rank exceeds maximum rank")
            _print(
                facade(session, config).search(
                    query,
                    language=language,
                    limit=limit,
                    owner_id=actor,
                    min_rank=min_rank,
                    max_rank=max_rank,
                )
            )

    @cli.command("datasets")
    def datasets():
        with database() as (config, engine), Session(engine) as session:
            _print(facade(session, config).list_datasets())

    def run_operation(operation, path, actor):
        with database() as (config, engine), Session(engine) as session, session.begin():
            result = getattr(facade(session, config), operation)(_read_object(path), actor)
        _print(result)

    @cli.command("import-dataset")
    def import_dataset(path: Path, actor: str = "local-operator"):
        run_operation("import_dataset", path, actor)

    @cli.command("import-reviewed-vocabulary")
    def import_reviewed_vocabulary(
        path: Path,
        sha256: str,
        language: str,
        profile_version: str,
        version: str,
        namespace: str = "core",
        actor: str = "local-operator",
    ):
        from multilang.native_runtime import _evidence_store
        from multilang.services.vocabulary_review import load_compiled_vocabulary

        with database() as (config, engine), Session(engine) as session, session.begin():
            service = facade(session, config)
            profile = service._profile(language, profile_version)
            bundle = load_compiled_vocabulary(
                path, expected_sha256=sha256, profile=profile, verifier=_evidence_store(config)
            )
            result = service.import_dataset(
                {
                    "format": "reviewed-vocabulary",
                    "profile_version": profile_version,
                    "version": version,
                    "namespace": namespace,
                    "bundle": bundle.model_dump(mode="json"),
                },
                actor,
            )
        _print(result)

    @cli.command("import-contextual-bindings")
    def import_contextual_bindings(path: Path, actor: str = "local-operator"):
        run_operation("import_contextual_bindings", path, actor)

    @cli.command("rank")
    def rank(path: Path, actor: str = "local-operator"):
        run_operation("calculate_ranking", path, actor)

    @cli.command("generate-content")
    def content(path: Path, actor: str = "local-operator"):
        run_operation("generate_content", path, actor)

    @cli.command("draft-content")
    def draft_content(path: Path, output: Path, actor: str = "local-operator"):
        from multilang.services.vocabulary_review import _plain_path

        with database() as (config, engine), Session(engine) as session:
            target = _plain_path(output)
            if target.exists():
                raise ValueError("draft output already exists")
            draft = facade(session, config).draft_content(_read_object(path), actor)
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(draft, ensure_ascii=False, indent=2) + "\n")
        _print(
            {
                "draft_sha256": draft["draft_sha256"],
                "output": str(output),
                "review_status": "pending",
            }
        )

    @cli.command("complete-content-draft")
    def complete_content_draft(path: Path, actor: str = "local-operator"):
        run_operation("complete_content_draft", path, actor)

    @cli.command("generate-audio")
    def audio(path: Path, actor: str = "local-operator"):
        run_operation("generate_audio", path, actor)

    @cli.command("freeze-edition")
    def freeze_edition(path: Path, actor: str = "local-operator"):
        run_operation("freeze_edition", path, actor)

    @cli.command("export-anki")
    def anki(path: Path, actor: str = "local-operator"):
        run_operation("export_anki", path, actor)

    @cli.command("approve-review")
    def approve_review(path: Path, actor: str = "local-operator"):
        run_operation("approve_review", path, actor)

    @cli.command("import-history")
    def import_history(path: Path, actor: str = "local-operator"):
        run_operation("import_history", path, actor)

    @cli.command("register-history-aliases")
    def register_history_aliases(path: Path, actor: str = "local-operator"):
        run_operation("register_history_aliases", path, actor)

    @cli.command("update-learner-state")
    def update_learner_state(path: Path, actor: str = "local-operator"):
        run_operation("update_learner_state", path, actor)

    @cli.command("adaptive-queue")
    def adaptive_queue(path: Path, actor: str = "local-operator"):
        run_operation("adaptive_queue", path, actor)

    @cli.command("preview-legacy-aliases")
    def preview_legacy_aliases(path: Path, actor: str = "local-operator"):
        run_operation("preview_legacy_aliases", path, actor)

    @cli.command("apply-legacy-aliases")
    def apply_legacy_aliases(path: Path, actor: str = "local-operator"):
        run_operation("apply_legacy_aliases", path, actor)

    @cli.command("enqueue")
    def enqueue(kind: str, path: Path, idempotency_key: str, actor: str = "local-operator"):
        from multilang.api import task_projection
        from multilang.jobs.queue import TaskQueue

        with database() as (config, engine), Session(engine) as session:
            _print(
                task_projection(
                    TaskQueue(session).enqueue(
                        kind,
                        _read_object(path),
                        owner_id=actor,
                        idempotency_key=idempotency_key,
                        max_attempts=config.native_task_max_attempts,
                    )
                )
            )

    @cli.command("job")
    def job(task_id: str, actor: str = "local-operator"):
        from multilang.api import task_projection
        from multilang.jobs.queue import TaskQueue

        with database() as (config, engine), Session(engine) as session:
            task = TaskQueue(session).get(task_id, owner_id=actor)
            if task is None:
                raise ValueError("task not found")
            _print(task_projection(task))

    @cli.command("worker")
    def worker(loop: bool = False, max_tasks: Annotated[int, typer.Option(min=1)] = 1):
        from multilang.jobs.handlers import build_handlers
        from multilang.jobs.worker import Worker
        from multilang.observability import configure_logging

        with database() as (config, engine):
            if config.native_telemetry_enabled:
                configure_logging()
            runner = Worker(
                sessionmaker(engine),
                build_handlers(config, facade_factory=facade_factory),
                lease_seconds=config.native_worker_lease_seconds,
                telemetry_enabled=config.native_telemetry_enabled,
            )
            count = 0
            try:
                while loop or count < max_tasks:
                    if runner.run_once():
                        count += 1
                    elif not loop:
                        break
                    else:
                        sleep(config.native_worker_poll_seconds)
            except KeyboardInterrupt:
                pass
            _print({"processed_tasks": count})

    @cli.command("serve")
    def serve(host: str = "127.0.0.1", port: Annotated[int, typer.Option(min=1, max=65535)] = 8000):
        import uvicorn

        from multilang.api import create_app

        uvicorn.run(
            create_app(settings=configuration(require_enabled=False)),
            host=host,
            port=port,
            access_log=False,
        )

    @cli.command("backup")
    def backup(destination: Path, files_manifest: Path | None = None):
        from multilang.services.native_migration import BackupService

        with database(require_enabled=False) as (config, engine):
            files = _read_object(files_manifest) if files_manifest else {}
            if not all(isinstance(path, str) and path for path in files.values()):
                raise ValueError("backup files manifest must map relative names to local paths")
            _print(
                BackupService(engine).snapshot(
                    destination, files={name: Path(path) for name, path in files.items()}
                )
            )

    @cli.command("restore-backup")
    def restore(backup_manifest: Path, target_config: Path, files_destination: Path | None = None):
        from multilang.services.native_migration import BackupManifest, BackupService

        with database(require_enabled=False) as (config, engine):
            target = _DatabaseTarget.model_validate(_read_object(target_config))
            clone = create_engine(target.database_url.get_secret_value(), pool_pre_ping=True)
            try:
                BackupService(engine).restore_to(
                    BackupManifest.model_validate(_read_object(backup_manifest)),
                    clone,
                    files_destination=files_destination,
                )
                _print({"status": "restored"})
            finally:
                clone.dispose()

    @cli.command("rehearse-migration")
    def rehearse(
        backup_manifest: Path,
        clone_path: Annotated[Path | None, typer.Argument()] = None,
        target_config: Path | None = None,
    ):
        from multilang.services.native_migration import BackupManifest, MigrationService

        with database(require_enabled=False) as (config, engine):
            if (clone_path is None) == (target_config is None):
                raise ValueError("provide one isolated clone path or target config")
            clone = None
            if target_config is not None:
                target = _DatabaseTarget.model_validate(_read_object(target_config))
                clone = create_engine(target.database_url.get_secret_value(), pool_pre_ping=True)
            try:
                _print(
                    MigrationService(engine).rehearse(
                        BackupManifest.model_validate(_read_object(backup_manifest)),
                        clone_path,
                        clone_engine=clone,
                    )
                )
            finally:
                if clone is not None:
                    clone.dispose()

    def topology_input(path):
        from multilang.domain.anki_semantics import TopologyDecision

        return TopologyDecision.model_validate(_read_object(path)) if path else None

    @cli.command("preview-migration")
    def preview(backup_manifest: Path, topology: Path | None = None, rehearsal: Path | None = None):
        from multilang.services.native_migration import BackupManifest, MigrationService

        with database(require_enabled=False) as (config, engine):
            _print_preview(
                MigrationService(engine).preview(
                    BackupManifest.model_validate(_read_object(backup_manifest)),
                    topology=topology_input(topology),
                    rehearsal=_read_object(rehearsal) if rehearsal else None,
                )
            )

    @cli.command("apply-migration")
    def apply(
        preview_file: Path,
        backup_manifest: Path,
        topology: Path,
        rehearsal: Path,
        confirm: Annotated[str, typer.Option("--confirm")],
        actor: str = "local-admin",
    ):
        from multilang.domain.migration import MigrationPreview
        from multilang.services.native_evidence import EvidenceStore
        from multilang.services.native_migration import BackupManifest, MigrationService

        with database() as (config, engine):
            secret = config.native_evidence_signing_key
            store = EvidenceStore(
                config.native_evidence_dir,
                key=secret.get_secret_value().encode() if secret else None,
            )
            _print(
                MigrationService(engine).apply(
                    MigrationPreview.model_validate(_read_object(preview_file)),
                    BackupManifest.model_validate(_read_object(backup_manifest)),
                    confirmation_sha256=confirm,
                    topology=topology_input(topology),
                    topology_verifier=store.verify_topology,
                    rehearsal=_read_object(rehearsal),
                    actor=actor,
                )
            )

    @cli.command("preview-legacy-adoption")
    def preview_adoption(backup_manifest: Path):
        from multilang.services.native_migration import BackupManifest, MigrationService

        with database(require_enabled=False) as (config, engine):
            _print_preview(
                MigrationService(engine).adoption_preview(
                    BackupManifest.model_validate(_read_object(backup_manifest))
                )
            )

    @cli.command("adopt-legacy-schema")
    def adopt(
        preview_file: Path,
        backup_manifest: Path,
        confirm: Annotated[str, typer.Option("--confirm")],
    ):
        from multilang.services.native_migration import (
            BackupManifest,
            LegacyAdoptionPreview,
            MigrationService,
        )

        with database(require_enabled=False) as (config, engine):
            _print(
                MigrationService(engine).adopt_legacy_schema(
                    LegacyAdoptionPreview.model_validate(_read_object(preview_file)),
                    BackupManifest.model_validate(_read_object(backup_manifest)),
                    confirmation_sha256=confirm,
                )
            )

    @cli.command("preview-rollback")
    def preview_rollback(backup_manifest: Path, migration_id: str):
        from multilang.services.native_migration import BackupManifest, MigrationService

        with database(require_enabled=False) as (config, engine):
            _print_preview(
                MigrationService(engine).rollback_preview(
                    BackupManifest.model_validate(_read_object(backup_manifest)), migration_id
                )
            )

    @cli.command("rollback-migration")
    def rollback(
        preview_file: Path,
        backup_manifest: Path,
        confirm: Annotated[str, typer.Option("--confirm")],
        actor: str = "local-admin",
    ):
        from multilang.services.native_migration import (
            BackupManifest,
            MigrationService,
            RollbackPreview,
        )

        with database(require_enabled=False) as (config, engine):
            _print(
                MigrationService(engine).rollback(
                    RollbackPreview.model_validate(_read_object(preview_file)),
                    BackupManifest.model_validate(_read_object(backup_manifest)),
                    confirmation_sha256=confirm,
                    actor=actor,
                )
            )

    @cli.command("register-profile")
    def register_profile(path: Path, receipt_id: str):
        from multilang.domain.language_profiles import LanguageProfile
        from multilang.repositories.native_repository import NativeRepository
        from multilang.services.native_evidence import EvidenceStore

        with database() as (config, engine), Session(engine) as session, session.begin():
            profile = LanguageProfile.model_validate(_read_object(path))
            secret = config.native_evidence_signing_key
            store = EvidenceStore(
                config.native_evidence_dir,
                key=secret.get_secret_value().encode() if secret else None,
            )
            if not store.verify(
                receipt_id, profile.model_dump(mode="json"), purpose="language-profile"
            ):
                raise ValueError("profile evidence is not valid")
            result = NativeRepository(session).put_profile(profile)
        _print(result)

    return cli
