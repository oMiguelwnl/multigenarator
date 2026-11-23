from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from multilang.studio.productions import ProductionService, production_router


def setup_service(root, run):
    service = ProductionService(root, run_command=run)
    app = FastAPI()
    app.include_router(production_router(service))
    return service, TestClient(app)


def test_file_generation_runs_once_and_reopens_export(tmp_path):
    job_id = str(uuid4())
    calls = []

    def run(args, observe):
        calls.append(args)
        if args[0] == "generate":
            source = Path(args[args.index("--input-file") + 1])
            assert source.read_text(encoding="utf-8") == "bonjour"
            assert args[args.index("--support-language") + 1] == "es"
            observe("job_id=" + job_id)
        else:
            output = Path(args[args.index("--output-dir") + 1]) / (job_id + ".apkg")
            output.write_bytes(b"offline-fixture")
            observe(f"artifact_path={output}")
            observe("card_count=1")

    service, client = setup_service(tmp_path, run)
    payload = dict(id=str(uuid4()), name="Francês", language="fr", supportLanguage="es",
                   kind="word-list", sourceText="bonjour", sourceExtension="txt")
    endpoint = "/studio-api/productions"
    assert client.post(endpoint, json=payload).status_code == 202
    service.close()
    service, client = setup_service(tmp_path, run)
    assert client.post(endpoint, json=payload).json()["status"] == "completed"
    assert client.post(endpoint, json=payload | {"name": "Alterada"}).status_code == 409
    result = client.get(endpoint).json()[0]
    assert result["jobId"] == job_id and result["canDownload"]
    assert service.resolve_package(UUID(payload["id"])).read_bytes() == b"offline-fixture"
    service.resolve_package(UUID(payload["id"])).unlink()
    assert not client.get(endpoint).json()[0]["canDownload"]
    assert not client.get(f"{endpoint}/{payload['id']}").json()["canDownload"]
    assert len(calls) == 2
    assert not list(tmp_path.rglob("source.txt"))
    service.close()


def test_repair_rebuilds_snapshots_once_without_replaying_upload(tmp_path):
    job_id = str(uuid4())
    calls = []
    endpoint = "/studio-api/productions"
    payload = dict(id=str(uuid4()), name="Personal", language="fr", supportLanguage="en",
                   kind="word-list", sourceExtension="txt", sourceText="private vocabulary")

    def run(args, observe):
        calls.append(args)
        if args[0] == "generate":
            observe(f"job_id={job_id}")
            raise RuntimeError(payload["sourceText"])
        if args[0] == "export":
            dest = Path(args[args.index("--output-dir") + 1]) / f"{job_id}.apkg"
            dest.write_bytes(b"repaired")
            observe(f"artifact_path={dest}")
            observe("card_count=1")

    service, client = setup_service(tmp_path, run)
    assert client.post(endpoint, json=payload).status_code == 202
    service.close()
    receipt = next(tmp_path.rglob("receipt.json"))
    assert payload["sourceText"] not in receipt.read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("source.txt"))
    # A crash can interrupt cleanup after the terminal receipt was written.
    (receipt.parent / "source.txt").write_text(payload["sourceText"])
    service, client = setup_service(tmp_path, run)
    assert not (receipt.parent / "source.txt").exists()
    detail = f"{endpoint}/{payload['id']}"
    assert client.get(detail).json()["status"] == "failed"
    attempt = {"id": str(uuid4())}
    assert client.post(detail + "/repair", json=attempt).status_code == 202
    service.close()
    assert client.post(detail + "/repair", json=attempt).json()["status"] == "completed"
    assert [args[0] for args in calls] == ["generate", "repair-text", "synthesize-audio", "export"]
    assert "--missing-only" in calls[2]
    assert "--refresh-snapshots" in calls[3]
    assert service.resolve_package(UUID(payload["id"])).read_bytes() == b"repaired"


@pytest.mark.parametrize("export_lines", [
    [], ["card_count=0"], ["card_count=1", "export_status=partial"],
    ["card_count=1", "artifact_path=elsewhere.apkg"],
])
def test_unconfirmed_export_never_becomes_downloadable(tmp_path, export_lines):
    def run(args, observe):
        path = Path(args[args.index("--output-path") + 1])
        path.write_bytes(b"old artifact")
        observe(f"artifact_path={path}")
        for line in export_lines:
            observe(line)

    service, client = setup_service(tmp_path, run)
    payload = dict(id=str(uuid4()), name="Sounds", language="pl", supportLanguage="pt", kind="phonetics")
    assert client.post("/studio-api/productions", json=payload).status_code == 202
    service.close()
    result = client.get("/studio-api/productions").json()[0]
    assert result["status"] == "failed" and not result["canDownload"]


def test_rejects_incompatible_requests_before_scheduling(tmp_path):
    service, client = setup_service(tmp_path, lambda *_: None)
    base = dict(id=str(uuid4()), name="Deck", language="en", supportLanguage="pt")
    for extra in [
        {"kind": "word-list"},
        {"kind": "highlights", "sourceText": "test", "sourceExtension": "../../file"},
        {"kind": "frequency", "language": "la"},
        {"kind": "foundations", "language": "ja", "supportLanguage": "es"},
        {"kind": "highlights", "language": "ko", "highlightInput": "vocabulary",
         "sourceText": "x", "sourceExtension": "txt"},
    ]:
        assert client.post("/studio-api/productions", json=base | extra).status_code == 422
    assert client.get("/studio-api/productions").json() == []
    service.close()


def test_catalog_routes_parse_with_the_registered_cli(tmp_path):
    from typer.main import get_command

    from multilang.cli import app
    from multilang.domain.jobs import SupportedLanguage

    cli = get_command(app)
    job_id = str(uuid4())

    def parse_only(args, observe):
        command = cli.commands[args[0]]
        tokens = args[1:]
        if args[0] == "korean-foundations":
            command = command.commands[tokens[0]]
            tokens = tokens[1:]
        with command.make_context(args[0], tokens) as ctx:
            if args[0] == "generate":
                observe(f"job_id={job_id}")
                return
            if args[0] == "korean-foundations":
                destination = Path(ctx.params["output"])
                observe("export_status=written")
            elif args[0] in {"export", "export-latin-mvp"}:
                name = "latin-mvp-50.apkg" if args[0] == "export-latin-mvp" else f"{job_id}.apkg"
                destination = Path(ctx.params["output_dir"]) / name
            else:
                destination = Path(ctx.params["output_path"])
            destination.write_bytes(b"fixture")
            observe(f"artifact_path={destination}")
            observe("card_count=1")

    endpoint = "/studio-api/productions"
    service, client = setup_service(tmp_path, parse_only)
    catalog = client.get(endpoint + "/catalog").json()
    service.close()
    assert set(catalog) == {lang.value for lang in SupportedLanguage}
    assert set(catalog["ko"]) == {"word-list", "highlights", "foundations", "phonetics"}
    assert set(catalog["la"]) == {"word-list", "highlights", "latin"}
    for language, kinds in catalog.items():
        for kind in kinds:
            service, client = setup_service(tmp_path / language / kind, parse_only)
            body = dict(id=str(uuid4()), name="Test", language=language, supportLanguage="pt", kind=kind)
            if kind in {"word-list", "highlights"}:
                body.update(sourceExtension="txt", sourceText="private")
            if kind == "frequency":
                body.update(level=2)
            if kind == "highlights" and language in {"zh", "la"}:
                body.update(highlightInput="vocabulary")
            assert client.post(endpoint, json=body).status_code == 202
            service.close()
            result = client.get(f"{endpoint}/{body['id']}").json()
            assert result["canDownload"], (language, kind, result)
