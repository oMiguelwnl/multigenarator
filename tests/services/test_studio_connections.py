import os

import pytest
from fastapi.testclient import TestClient

from multilang.studio.connections import ConnectionConfig, ConnectionStore
from multilang.studio.server import create_studio_app


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_vault_encrypts_and_never_projects_secrets(tmp_path):
    store = ConnectionStore(tmp_path / "connections.dpapi")
    store.save(ConnectionConfig(openai_api_key="private-test-key"))
    assert b"private-test-key" not in store.path.read_bytes()
    assert store.load().openai_api_key.get_secret_value() == "private-test-key"
    assert "private-test-key" not in str(store.public())


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_additional_key_can_be_edited_and_survives_restart(tmp_path):
    path = tmp_path / "connections.dpapi"
    store = ConnectionStore(path)
    saved = store.add_key("openai_api_key", "Original", "first-secret")
    key_id = saved["extra_keys"][0]["id"]

    edited = store.update_key("openai_api_key", key_id, label="Renamed", value="")
    assert edited["extra_keys"][0]["label"] == "Renamed"
    assert "first-secret" not in str(edited)
    assert ConnectionStore(path).load().additional_keys[0].value.get_secret_value() == "first-secret"

    store.update_key("openai_api_key", key_id, label="Renamed", value="second-secret")
    restarted = ConnectionStore(path)
    assert restarted.load().additional_keys[0].value.get_secret_value() == "second-secret"
    assert b"second-secret" not in path.read_bytes()
    with pytest.raises(KeyError):
        store.update_key("deepl_api_key", key_id, label="Wrong provider", value="")


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_additional_key_edit_route_preserves_secret_and_identity(tmp_path):
    origin = "http://127.0.0.1:8765"
    app = create_studio_app(root=tmp_path, token="token", port=8765)
    with TestClient(app, base_url=origin, headers={"Origin": origin}) as client:
        client.post("/studio-api/session", json={"token": "token"})
        created = client.post(
            "/studio-api/keys/deepl_api_key", json={"label": "Old", "value": "private-key"}
        )
        key_id = created.json()["extra_keys"][0]["id"]
        path = f"/studio-api/keys/deepl_api_key/{key_id}"
        edited = client.patch(path, json={"label": "New", "value": ""})
        assert edited.status_code == 200
        assert edited.json()["extra_keys"][0]["id"] == key_id
        assert edited.json()["extra_keys"][0]["active"]
        assert "private-key" not in edited.text
        assert client.post(path + "/reveal").json() == {"value": "private-key"}
        assert client.patch(path, json={"label": "  ", "value": ""}).status_code == 400
        assert client.patch(path, json={"label": "New", "value": "replacement"}).status_code == 200

    restarted = create_studio_app(root=tmp_path, token="new-token", port=8765)
    with TestClient(restarted, base_url=origin, headers={"Origin": origin}) as client:
        client.post("/studio-api/session", json={"token": "new-token"})
        assert client.get("/studio-api/connections").json()["extra_keys"][0]["label"] == "New"
        assert client.post(path + "/reveal").json() == {"value": "replacement"}


def test_local_api_requires_session_and_same_origin(tmp_path):
    app = create_studio_app(root=tmp_path, token="test-session", port=8765)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/studio-api/connections").status_code == 401
        assert (
            client.post(
                "/studio-api/session",
                json={"token": "wrong"},
                headers={"Origin": "http://127.0.0.1:8765"},
            ).status_code
            == 401
        )
        response = client.post(
            "/studio-api/session",
            json={"token": "test-session"},
            headers={"Origin": "http://127.0.0.1:8765"},
        )
        assert response.status_code == 200
        assert "HttpOnly" in response.headers["set-cookie"]
        assert client.get("/studio-api/connections").status_code == 200
        assert (
            client.put(
                "/studio-api/connections", json={}, headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )
        assert (
            client.get("/studio-api/connections", headers={"Host": "evil.example"}).status_code
            == 403
        )


def test_config_bounds_and_no_arbitrary_endpoints():
    with pytest.raises(ValueError):
        ConnectionConfig(azure_region="example.com/path")
    with pytest.raises(ValueError):
        ConnectionConfig(endpoint="https://evil.example")
    with pytest.raises(ValueError):
        ConnectionConfig(api_max_output_tokens=0)
    with pytest.raises(ValueError):
        ConnectionConfig(database_url="sqlite:///data.db")
    with pytest.raises(ValueError):
        ConnectionConfig(database_url="postgresql+psycopg://missing-host")


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_settings_opt_in_and_secret_removal(tmp_path):
    from multilang.settings import Settings

    path = tmp_path / "vault.dpapi"
    store = ConnectionStore(path)
    store.save(
        ConnectionConfig(
            openai_api_key="test-private", model="gpt-6-luna", api_max_output_tokens=512
        )
    )
    store.update({"openai_api_key": "", "azure_region": "eastus"})
    assert store.load().openai_api_key.get_secret_value() == "test-private"
    settings = Settings(
        _env_file=None, studio_connections_enabled=True, studio_connections_path=path
    )
    assert settings.openai_api_key == "test-private"
    assert settings.text_generation_model == "openai/gpt-6-luna"
    assert settings.studio_api_max_output_tokens == 512
    assert not settings.native_provider_calls_enabled
    assert (
        Settings(_env_file=None, studio_connections_path=path).text_generation_model
        != "openai/gpt-6-luna"
    )
    store.save(
        ConnectionConfig(
            transport="openrouter",
            model="anthropic/claude-sonnet-4",
            openrouter_api_key="test-openrouter",
        )
    )
    routed = Settings(
        _env_file=None, studio_connections_enabled=True, studio_connections_path=path
    )
    assert routed.text_generation_transport == "api"
    assert routed.text_generation_model == "openrouter/anthropic/claude-sonnet-4"
    assert routed.openrouter_api_key == "test-openrouter"
    assert routed.openai_api_key is None


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_key_routes_do_not_leak_and_require_explicit_delete(tmp_path):
    app = create_studio_app(root=tmp_path, token="token", port=8765)
    with TestClient(
        app, base_url="http://127.0.0.1:8765", headers={"Origin": "http://127.0.0.1:8765"}
    ) as client:
        client.post("/studio-api/session", json={"token": "token"})
        response = client.put("/studio-api/connections", json={"openai_api_key": "private-key"})
        assert response.status_code == 200
        assert "private-key" not in response.text
        assert response.json()["configured"]["openai_api_key"]
        response = client.put(
            "/studio-api/connections", json={"openrouter_api_key": "private-openrouter-key"}
        )
        assert response.status_code == 200
        assert "private-openrouter-key" not in response.text
        assert response.json()["configured"]["openrouter_api_key"]
        assert client.put("/studio-api/connections", json={"openrouter_api_key": ""}).json()[
            "configured"
        ]["openrouter_api_key"]
        assert client.put("/studio-api/connections", json={"openai_api_key": ""}).json()[
            "configured"
        ]["openai_api_key"]
        assert not client.delete("/studio-api/keys/openai_api_key").json()["configured"][
            "openai_api_key"
        ]
        response = client.put(
            "/studio-api/connections", json={"openai_api_key": "private-key", "endpoint": "invalid"}
        )
        assert response.status_code == 422
        assert "private-key" not in response.text
        assert client.post("/studio-api/session", content="x" * 40000).status_code == 413


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_database_credential_is_encrypted_and_revealed_only_on_request(tmp_path):
    from multilang.settings import Settings

    url = "postgresql+psycopg://student:private-password@127.0.0.1:5432/multilang"
    app = create_studio_app(root=tmp_path, token="token", port=8765)
    vault = tmp_path / ".multilang/studio/connections.dpapi"
    with TestClient(
        app, base_url="http://127.0.0.1:8765", headers={"Origin": "http://127.0.0.1:8765"}
    ) as client:
        assert client.post("/studio-api/keys/database_url/reveal").status_code == 401
        client.post("/studio-api/session", json={"token": "token"})
        saved = client.put("/studio-api/connections", json={"database_url": url})
        assert saved.status_code == 200
        assert saved.json()["configured"]["database_url"]
        assert url not in saved.text
        assert url not in client.get("/studio-api/connections").text
        assert url.encode() not in vault.read_bytes()
        assert client.post("/studio-api/keys/database_url/reveal").json() == {"value": url}
        assert client.post("/studio-api/keys/database_url/reveal").headers["cache-control"] == "no-store"
        assert client.post("/studio-api/keys/unknown/reveal").status_code == 404
        assert client.post("/studio-api/keys/database_url/reveal", headers={"Origin": "https://evil.example"}).status_code == 403
        settings = Settings(_env_file=None, studio_connections_enabled=True, studio_connections_path=vault)
        assert settings.database_url == url


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_database_probe_runs_read_only_query_with_short_timeout(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from multilang.studio import server

    observed = {}

    class Engine:
        @contextmanager
        def connect(self):
            class Connection:
                def execute(self, statement):
                    observed["query"] = str(statement)

            yield Connection()

        def dispose(self):
            observed["disposed"] = True

    def fake_engine(url, **kwargs):
        observed["url"] = url
        observed["options"] = kwargs
        return Engine()

    monkeypatch.setattr(server, "create_engine", fake_engine)
    app = create_studio_app(root=tmp_path, token="token", port=8765)
    with TestClient(app, base_url="http://127.0.0.1:8765", headers={"Origin": "http://127.0.0.1:8765"}) as client:
        client.post("/studio-api/session", json={"token": "token"})
        assert client.post("/studio-api/check/database").status_code == 409
        url = "postgresql+psycopg://student:secret@127.0.0.1:5432/multilang"
        client.put("/studio-api/connections", json={"database_url": url})
        assert client.post("/studio-api/check/database").status_code == 200
    assert observed == {"url": url, "options": {"connect_args": {"connect_timeout": 5}, "pool_pre_ping": True}, "query": "SELECT 1", "disposed": True}


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_model_list_includes_every_model_returned_by_provider(tmp_path, monkeypatch):
    import json

    from multilang.studio import server

    class Response:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def aiter_bytes(self):
            yield json.dumps({"data": [
                {"id": "gpt-test", "name": "GPT Test"},
                {"id": "o-test", "name": "Reasoning Test"},
            ]}).encode()

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        def stream(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(server.httpx, "AsyncClient", lambda **_kwargs: Client())
    app = create_studio_app(root=tmp_path, token="token", port=8765)
    with TestClient(app, base_url="http://127.0.0.1:8765", headers={"Origin": "http://127.0.0.1:8765"}) as client:
        client.post("/studio-api/session", json={"token": "token"})
        client.put("/studio-api/connections", json={"openai_api_key": "fixture-key"})
        response = client.post("/studio-api/models")
        assert response.status_code == 200
        assert response.json() == [
            {"id": "gpt-test", "name": "GPT Test"},
            {"id": "o-test", "name": "Reasoning Test"},
        ]


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
def test_additional_provider_keys_preserve_primary_and_switch_active_key(tmp_path, monkeypatch):
    from multilang.settings import Settings
    from multilang.studio import server

    observed = {}

    class Response:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def aiter_bytes(self):
            yield b"{}"

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        def stream(self, _method, _url, *, headers):
            observed["authorization"] = headers["Authorization"]
            return Response()

    monkeypatch.setattr(server.httpx, "AsyncClient", lambda **_kwargs: Client())

    app = create_studio_app(root=tmp_path, token="token", port=8765)
    vault = tmp_path / ".multilang/studio/connections.dpapi"
    with TestClient(app, base_url="http://127.0.0.1:8765", headers={"Origin": "http://127.0.0.1:8765"}) as client:
        client.post("/studio-api/session", json={"token": "token"})
        client.put("/studio-api/connections", json={"openai_api_key": "primary-fixture"})
        added = client.post("/studio-api/keys/openai_api_key", json={"label": "Reserva", "value": "backup-fixture"})
        assert added.status_code == 200
        assert "backup-fixture" not in added.text
        extra = added.json()["extra_keys"]
        assert len(extra) == 1
        assert extra[0]["label"] == "Reserva"
        key_id = extra[0]["id"]
        assert not extra[0]["active"]
        assert b"backup-fixture" not in vault.read_bytes()
        assert "backup-fixture" not in client.get("/studio-api/connections").text
        settings = Settings(_env_file=None, studio_connections_enabled=True, studio_connections_path=vault)
        assert settings.openai_api_key == "primary-fixture"
        activated = client.post(f"/studio-api/keys/openai_api_key/{key_id}/activate")
        assert activated.status_code == 200
        assert activated.json()["extra_keys"][0]["active"]
        settings = Settings(_env_file=None, studio_connections_enabled=True, studio_connections_path=vault)
        assert settings.openai_api_key == "backup-fixture"
        assert client.post("/studio-api/check/openai").status_code == 200
        assert observed["authorization"] == "Bearer backup-fixture"
        assert client.post(f"/studio-api/keys/openai_api_key/{key_id}/reveal").json() == {"value": "backup-fixture"}
        assert client.post(f"/studio-api/keys/deepl_api_key/{key_id}/reveal").status_code == 404
        assert client.post(f"/studio-api/keys/openai_api_key/{key_id}/reveal", headers={"Origin": "https://evil.example"}).status_code == 403

        assert client.put("/studio-api/connections", json={"model": "gpt-test"}).json()["extra_keys"][0]["id"] == key_id

        removed = client.delete(f"/studio-api/keys/openai_api_key/{key_id}")
        assert removed.status_code == 200
        assert not removed.json()["extra_keys"]
        settings = Settings(_env_file=None, studio_connections_enabled=True, studio_connections_path=vault)
        assert settings.openai_api_key == "primary-fixture"


@pytest.mark.skipif(os.name != "nt", reason="Windows credential protection")
@pytest.mark.parametrize(
    "provider,transport,setting",
    [
        ("openai_api_key", "api", "openai_api_key"),
        ("openrouter_api_key", "openrouter", "openrouter_api_key"),
        ("deepl_api_key", "api", "deepl_api_key"),
        ("azure_speech_key", "api", "azure_speech_key"),
    ],
)
def test_each_service_uses_its_selected_additional_key(tmp_path, provider, transport, setting):
    from multilang.settings import Settings

    path = tmp_path / "credentials.dpapi"
    store = ConnectionStore(path)
    store.save(ConnectionConfig(transport=transport))
    added = store.add_key(provider, "Reserva", "provider-fixture")
    key_id = added["extra_keys"][0]["id"]
    store.activate_key(provider, key_id)
    settings = Settings(_env_file=None, studio_connections_enabled=True, studio_connections_path=path)
    assert getattr(settings, setting) == "provider-fixture"


def test_codex_transport_uses_existing_validation_adapter_without_api_key():
    from multilang.services.provider_text_adapters import (
        _litellm_api_key,
        can_use_litellm,
        configured_completion,
    )
    from multilang.settings import Settings

    settings = Settings(
        _env_file=None,
        text_generation_provider="litellm",
        text_generation_transport="codex",
        openai_api_key="must-not-pass",
    )
    assert _litellm_api_key(settings) is None
    assert can_use_litellm(settings)
    assert callable(configured_completion(settings))


def test_codex_offline_guard_prevents_process_start(monkeypatch, tmp_path):
    import asyncio

    from multilang.studio.codex import CodexBridge

    monkeypatch.setenv("MULTILANG_FORBID_NETWORK", "1")
    with pytest.raises(RuntimeError, match="disabled"):
        asyncio.run(CodexBridge(tmp_path).start())


def test_luna_api_parameters_and_output_cap(monkeypatch, tmp_path):
    from multilang.services import provider_text_adapters as adapters
    from multilang.settings import Settings

    captured = {}
    monkeypatch.setattr(adapters, "_litellm_completion", lambda **kwargs: captured.update(kwargs))
    settings = Settings(
        _env_file=None, studio_api_max_output_tokens=512, studio_connections_enabled=True,
        studio_connections_path=tmp_path / "no-vault.dpapi",
    )
    adapters.configured_completion(settings)(
        model="openai/gpt-6-luna", temperature=0.2, max_tokens=1500
    )
    assert "temperature" not in captured
    assert "max_tokens" not in captured
    assert captured["max_completion_tokens"] == 512


@pytest.mark.parametrize(
    "output,accepted", [('{"sentence":"A sample."}', True), ("not JSON", False)]
)
def test_codex_completion_requires_structured_output(tmp_path, output, accepted):
    import asyncio

    from multilang.studio.codex import CodexBridge

    class FakeBridge(CodexBridge):
        async def status(self):
            return {"connected": True}

        async def models(self):
            return [{"id": "gpt-6-luna", "name": "Luna"}]

        async def rpc(self, method, params=None):
            if method == "thread/start":
                assert params["sandbox"] == "read-only"
                assert params["ephemeral"]
                assert params["approvalPolicy"] == "never"
                return {"thread": {"id": "thread"}}
            if method == "turn/start":
                await self.events.put(
                    {
                        "method": "item/completed",
                        "params": {
                            "threadId": "thread",
                            "item": {"type": "agentMessage", "text": output},
                        },
                    }
                )
                await self.events.put(
                    {
                        "method": "turn/completed",
                        "params": {"threadId": "thread", "turn": {"status": "completed"}},
                    }
                )
                return {"turn": {"id": "turn"}}
            assert method == "turn/interrupt"
            return {}

    async def run():
        return await FakeBridge(tmp_path).complete(
            model="gpt-6-luna", messages=[{"role": "user", "content": "JSON"}]
        )

    if accepted:
        assert asyncio.run(run())["choices"][0]["message"]["content"] == output
    else:
        with pytest.raises(ValueError):
            asyncio.run(run())
