import importlib.util
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

from multilang.settings import Settings


def test_native_cli_flag_blocks_operations_before_database(tmp_path):
    assert importlib.util.find_spec("multilang.native_cli") is not None, "native commands missing"
    from multilang.native_cli import create_native_app

    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'never.db'}")
    app = create_native_app(settings=settings)
    runner = CliRunner()
    assert runner.invoke(app, ["status"]).exit_code == 0
    result = runner.invoke(app, ["search", "run"])
    assert result.exit_code == 1
    assert not (tmp_path / "never.db").exists()


def test_native_cli_search_uses_shared_facade(tmp_path):
    assert importlib.util.find_spec("multilang.native_cli") is not None, "native commands missing"
    from multilang.native_cli import create_native_app

    settings = Settings(
        _env_file=None, roadmap_4_enabled=True, database_url=f"sqlite:///{tmp_path / 'native.db'}"
    )

    class Facade:
        def search(
            self, query, language=None, limit=50, owner_id=None, min_rank=None, max_rank=None
        ):
            return [{"lemma": query, "owner": owner_id, "ranks": [min_rank, max_rank]}]

    app = create_native_app(settings=settings, facade_factory=lambda session, settings: Facade())
    result = CliRunner().invoke(
        app, ["search", "run", "--actor", "alice", "--min-rank", "1", "--max-rank", "10"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == [{"lemma": "run", "owner": "alice", "ranks": [1, 10]}]


@pytest.mark.parametrize(
    "command,operation",
    [
        ("approve-review", "approve_review"),
        ("import-history", "import_history"),
        ("register-history-aliases", "register_history_aliases"),
        ("update-learner-state", "update_learner_state"),
        ("adaptive-queue", "adaptive_queue"),
        ("preview-legacy-aliases", "preview_legacy_aliases"),
        ("apply-legacy-aliases", "apply_legacy_aliases"),
    ],
)
def test_native_local_json_commands_share_facade(tmp_path, command, operation):
    from multilang.native_cli import create_native_app

    settings = Settings(_env_file=None, roadmap_4_enabled=True, database_url="sqlite://")
    seen = []
    payload = {"fixture": "local-path-allowed"}
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload))

    class Facade:
        def run(self, value, actor):
            seen.append((value, actor))
            return {"status": "accepted"}

    setattr(Facade, operation, Facade.run)
    app = create_native_app(settings=settings, facade_factory=lambda session, settings: Facade())
    result = CliRunner().invoke(app, [command, str(path), "--actor", "alice"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"status": "accepted"}
    assert seen == [(payload, "alice")]


def test_native_backup_and_isolated_restore_include_optional_files(tmp_path):
    from multilang.native_cli import create_native_app

    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'source.db'}")
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE fixture (id INTEGER PRIMARY KEY, value TEXT)"))
        connection.execute(text("INSERT INTO fixture VALUES (1, 'preserved')"))
    engine.dispose()
    media = tmp_path / "audio.mp3"
    media.write_bytes(b"fixture-audio")
    files = tmp_path / "files.json"
    files.write_text(json.dumps({"media/audio.mp3": str(media)}))
    app = create_native_app(settings=settings)
    runner = CliRunner()
    snapshot = runner.invoke(
        app, ["backup", str(tmp_path / "backup"), "--files-manifest", str(files)]
    )
    assert snapshot.exit_code == 0, snapshot.output
    manifest = tmp_path / "backup" / "manifest.json"
    assert json.loads(manifest.read_text())["files"][0]["relative_path"] == "media/audio.mp3"
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"database_url": f"sqlite:///{tmp_path / 'restored.db'}"}))
    restored_files = tmp_path / "restored-files"
    restored = runner.invoke(
        app,
        ["restore-backup", str(manifest), str(target), "--files-destination", str(restored_files)],
    )
    assert restored.exit_code == 0, restored.output
    assert json.loads(restored.stdout)["status"] == "restored"
    assert (restored_files / "media" / "audio.mp3").read_bytes() == b"fixture-audio"
    restored_engine = create_engine(f"sqlite:///{tmp_path / 'restored.db'}")
    with restored_engine.connect() as connection:
        assert connection.scalar(text("SELECT value FROM fixture")) == "preserved"
    restored_engine.dispose()


@pytest.mark.timeout(120)
def test_native_legacy_adoption_requires_printed_confirmation(tmp_path):
    from multilang.db.provisioning import ensure_database_schema
    from multilang.native_cli import create_native_app
    from multilang.services.native_migration import LegacyAdoptionPreview

    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'legacy.db'}")
    engine = create_engine(settings.database_url)
    ensure_database_schema(engine, settings.database_url)
    engine.dispose()
    runner = CliRunner(mix_stderr=False)
    app = create_native_app(settings=settings)
    backup = tmp_path / "backup"
    assert runner.invoke(app, ["backup", str(backup)]).exit_code == 0
    manifest = backup / "manifest.json"
    preview = runner.invoke(app, ["preview-legacy-adoption", str(manifest)])
    assert preview.exit_code == 0, preview.output
    contract = LegacyAdoptionPreview.model_validate_json(preview.stdout)
    assert contract.confirmation_sha256 in preview.stderr
    path = tmp_path / "preview.json"
    path.write_text(preview.stdout)
    rejected = runner.invoke(
        app, ["adopt-legacy-schema", str(path), str(manifest), "--confirm", "0" * 64]
    )
    assert rejected.exit_code == 1
    result = runner.invoke(
        app,
        [
            "adopt-legacy-schema",
            str(path),
            str(manifest),
            "--confirm",
            contract.confirmation_sha256,
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["new_snapshot_required"] is True


@pytest.mark.timeout(300)
def test_native_migration_rollback_cli_preserves_original_database(tmp_path):
    from multilang.native_cli import create_native_app
    from multilang.services.native_migration import RollbackPreview

    fixtures_path = Path(__file__).parents[1] / "services" / "test_native_migration.py"
    spec = importlib.util.spec_from_file_location("native_migration_fixtures", fixtures_path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)

    engine = fixtures.database(tmp_path / "source.db")
    service, backup, preview, arguments = fixtures.prepared_migration(engine, tmp_path)
    result = service.apply(preview, backup, **arguments)
    settings = Settings(_env_file=None, database_url=str(engine.url))
    engine.dispose()
    runner = CliRunner(mix_stderr=False)
    app = create_native_app(settings=settings)
    manifest = tmp_path / "backup" / "manifest.json"
    output = runner.invoke(app, ["preview-rollback", str(manifest), result["migration_id"]])
    assert output.exit_code == 0, (output.output, repr(output.exception))
    contract = RollbackPreview.model_validate_json(output.stdout)
    path = tmp_path / "rollback.json"
    path.write_text(output.stdout)
    rolled_back = runner.invoke(
        app,
        ["rollback-migration", str(path), str(manifest), "--confirm", contract.confirmation_sha256],
    )
    assert rolled_back.exit_code == 0, rolled_back.output
    assert json.loads(rolled_back.stdout)["status"] == "rolled_back"
