"""Loopback-only, same-origin settings UI. Not a hosted/multi-user server."""

from __future__ import annotations

import hmac
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from multilang.studio.codex import CodexBridge, network_allowed
from multilang.studio.connections import SECRET_FIELDS, ConnectionConfig, ConnectionStore


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    token: SecretStr = Field(max_length=256)


def create_studio_app(*, root: Path, token: str, port: int = 8765) -> FastAPI:
    store = ConnectionStore(root / ".multilang/studio/connections.dpapi")
    bridge = CodexBridge(root / ".multilang/studio/codex")
    origin = f"http://127.0.0.1:{port}"
    session = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await bridge.close()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.headers.get("host") != f"127.0.0.1:{port}":
            return JSONResponse({"detail": "Invalid host"}, 403)
        if request.url.path.startswith("/studio-api/"):
            if request.method != "GET" and request.headers.get("origin") != origin:
                return JSONResponse({"detail": "Invalid origin"}, 403)
            if request.url.path != "/studio-api/session" and not hmac.compare_digest(
                request.cookies.get("multilang_studio", ""), session
            ):
                return JSONResponse(
                    {"detail": "Abra o estúdio pelo atalho local para autenticar."}, 401
                )
            size = 0
            chunks = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 32768:
                    return JSONResponse({"detail": "Request too large"}, 413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({"detail": "Configuração inválida. Confira os campos."}, 422)

    @app.exception_handler(Exception)
    async def failed(request, error):
        # Neither provider responses nor raw exceptions can expose credentials.
        return JSONResponse(
            {"detail": "Não foi possível concluir. Confira a configuração e a conexão."}, 503
        )

    @app.post("/studio-api/session")
    async def authenticate(payload: SessionRequest):
        if not hmac.compare_digest(payload.token.get_secret_value(), token):
            raise HTTPException(401, "Invalid session")
        response = JSONResponse({"connected": True})
        response.set_cookie(
            "multilang_studio", session, httponly=True, samesite="strict", max_age=28800
        )
        return response

    @app.get("/studio-api/connections")
    def read():
        return store.public()

    @app.put("/studio-api/connections")
    def update(payload: ConnectionConfig):
        patch = payload.model_dump(exclude_unset=True)
        for name in SECRET_FIELDS:
            if name in patch:
                patch[name] = getattr(payload, name).get_secret_value().strip()
        return store.update(patch)

    @app.delete("/studio-api/keys/{name}")
    def remove(name: str):
        if name not in SECRET_FIELDS:
            raise HTTPException(404)
        with store.lock:
            config = store.load()
            setattr(config, name, SecretStr(""))
            store.save(config)
        return store.public()

    async def probe(provider: str):
        network_allowed()
        config = store.load()
        if provider == "openai":
            key = config.openai_api_key.get_secret_value()
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {key}"}
        elif provider == "deepl":
            key = config.deepl_api_key.get_secret_value()
            host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
            url = f"https://{host}/v2/usage"
            headers = {"Authorization": f"DeepL-Auth-Key {key}"}
        elif provider == "azure":
            key = config.azure_speech_key.get_secret_value()
            url = f"https://{config.azure_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
            headers = {"Ocp-Apim-Subscription-Key": key}
        else:
            raise HTTPException(404)
        if not key:
            raise HTTPException(409, "Salve a chave antes de verificar.")
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            async with client.stream("GET", url, headers=headers) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        400, "Conexão recusada. Confira a chave, a região e os limites da conta."
                    )
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 4_000_000:
                        raise HTTPException(502, "Resposta do provedor excedeu o limite.")
                import json

                return json.loads(data)

    @app.post("/studio-api/check/{provider}")
    async def check(provider: str):
        await probe(provider)
        return {"message": "Conexão verificada, sem gerar conteúdo."}

    @app.post("/studio-api/models")
    async def models():
        if store.load().transport == "codex":
            if not (await bridge.status())["connected"]:
                raise HTTPException(409, "Conclua o login ChatGPT antes de consultar os modelos.")
            return await bridge.models()
        data = await probe("openai")
        return [
            {"id": row["id"], "name": row["id"]}
            for row in data["data"]
            if row["id"].startswith("gpt-")
        ]

    @app.post("/studio-api/codex/login")
    async def login():
        await bridge.start()
        result = await bridge.rpc("account/login/start", {"type": "chatgpt"})
        url = result.get("authUrl", "")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "auth.openai.com":
            raise HTTPException(502, "O Codex não retornou uma página oficial de login.")
        return {"url": url}

    @app.post("/studio-api/codex/status")
    async def status():
        return await bridge.status()

    @app.post("/studio-api/codex/logout")
    async def logout():
        await bridge.start()
        await bridge.rpc("account/logout")
        return {"connected": False}

    dist = root / "frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="studio")
    return app


def main():
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Multilang local settings studio")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This local credential store requires Windows")
    if not 1024 <= args.port <= 65535:
        parser.error("Use a port between 1024 and 65535")
    root = Path.cwd()
    if not (root / "frontend/dist/index.html").is_file():
        parser.error("Build the frontend first: npm --prefix frontend run build")
    token = secrets.token_urlsafe(32)
    print(f"Abra no navegador: http://127.0.0.1:{args.port}/#conexoes?session={token}", flush=True)
    uvicorn.run(
        create_studio_app(root=root, token=token, port=args.port),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )


if __name__ == "__main__":
    main()
