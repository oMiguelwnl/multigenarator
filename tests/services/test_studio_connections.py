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


def test_luna_api_parameters_and_output_cap(monkeypatch):
    from multilang.services import provider_text_adapters as adapters
    from multilang.settings import Settings

    captured = {}
    monkeypatch.setattr(adapters, "_litellm_completion", lambda **kwargs: captured.update(kwargs))
    settings = Settings(
        _env_file=None, studio_api_max_output_tokens=512, studio_connections_enabled=True
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
