import importlib.util
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from multilang.db.task_models import NativeTask
from multilang.settings import Settings

TOKENS = {
    "admin-token": {"subject": "admin", "role": "Admin"},
    "alice-token": {"subject": "alice", "role": "User"},
    "bob-token": {"subject": "bob", "role": "User"},
    "linguist-token": {"subject": "linguist", "role": "Linguist"},
}


def app_factory(**kwargs):
    assert importlib.util.find_spec("multilang.api") is not None, "versioned HTTP interface missing"
    from multilang.api import create_app

    return create_app(**kwargs)


def settings_for(tmp_path, **values):
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'http.db'}",
        native_api_credentials=SecretStr(json.dumps(TOKENS)),
        **values,
    )


def authorization(token):
    return {"Authorization": f"Bearer {token}"}


def test_disabled_flag_does_not_initialize_or_mutate_database(tmp_path):
    settings = settings_for(tmp_path)
    with TestClient(app_factory(settings=settings)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert (
            client.get("/api/v2/datasets", headers=authorization("admin-token")).status_code == 404
        )
    assert not (tmp_path / "http.db").exists()


@pytest.fixture
def client(tmp_path):
    settings = settings_for(tmp_path, roadmap_4_enabled=True)
    engine = create_engine(settings.database_url)
    NativeTask.__table__.create(engine)
    seen = []

    class Facade:
        def search(
            self, query, language=None, limit=50, owner_id=None, min_rank=None, max_rank=None
        ):
            seen.append(owner_id)
            return [{"lemma": query, "language": language, "ranks": [min_rank, max_rank]}]

        def list_datasets(self):
            return [{"id": "published-dataset"}]

    with TestClient(
        app_factory(
            settings=settings, engine=engine, facade_factory=lambda session, settings: Facade()
        )
    ) as client:
        yield client, engine, seen
    engine.dispose()


def test_api_credentials_permissions_and_owner_isolation(client):
    client, engine, seen = client
    assert client.get("/api/v2/datasets").status_code == 401
    assert (
        client.post(
            "/api/v2/datasets/import",
            json={"dataset_id": "one"},
            headers=authorization("alice-token"),
        ).status_code
        == 403
    )
    response = client.get("/api/v2/search?q=run&language=en", headers=authorization("alice-token"))
    assert response.status_code == 200
    assert seen == ["alice"]
    response = client.post(
        "/api/v2/jobs",
        json={"kind": "anki", "payload": {"dataset_id": "one"}},
        headers={**authorization("alice-token"), "Idempotency-Key": "export-one"},
    )
    assert response.status_code == 202
    task_id = response.json()["id"]
    assert "payload" not in response.json()
    assert (
        client.get(f"/api/v2/jobs/{task_id}", headers=authorization("bob-token")).status_code == 404
    )
    assert (
        client.get(f"/api/v2/jobs/{task_id}", headers=authorization("alice-token")).status_code
        == 200
    )
    with Session(engine) as session:
        assert session.get(NativeTask, task_id).owner_id == "alice"


def test_api_rejects_paths_role_injection_and_large_bodies(client):
    client, _, _ = client
    headers = {**authorization("admin-token"), "Idempotency-Key": "bad"}
    for payload in (
        {"input_file": "/etc/passwd"},
        {"actor": "victim"},
        {"nested": {"output_path": "../../file"}},
    ):
        response = client.post(
            "/api/v2/jobs", json={"kind": "import", "payload": payload}, headers=headers
        )
        assert response.status_code == 422
        assert "/etc/passwd" not in response.text
    assert client.post("/api/v2/jobs", content=b"x" * 1048577, headers=headers).status_code == 413
    assert (
        client.get(
            "/api/v2/search?q=run&limit=10000", headers=authorization("admin-token")
        ).status_code
        == 422
    )


def test_native_search_rank_range_is_validated_and_forwarded(client):
    client, _, _ = client
    headers = authorization("alice-token")
    response = client.get("/api/v2/search?q=run&min_rank=1&max_rank=10", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["ranks"] == [1, 10]
    for query in ("min_rank=0", "max_rank=-1", "min_rank=10&max_rank=1"):
        assert client.get(f"/api/v2/search?q=run&{query}", headers=headers).status_code == 422


def test_rate_limit_and_unknown_errors_do_not_leak(tmp_path):
    settings = settings_for(tmp_path, roadmap_4_enabled=True, native_api_requests_per_minute=1)

    class BrokenFacade:
        def list_datasets(self):
            raise RuntimeError("secret=provider-token /private/source")

    with TestClient(
        app_factory(settings=settings, facade_factory=lambda session, settings: BrokenFacade()),
        raise_server_exceptions=False,
    ) as client:
        first = client.get("/api/v2/datasets", headers=authorization("admin-token"))
        assert first.status_code == 500
        assert "secret" not in first.text
        assert (
            client.get("/api/v2/datasets", headers=authorization("admin-token")).status_code == 429
        )
    assert inspect(create_engine(settings.database_url)).get_table_names() == []
