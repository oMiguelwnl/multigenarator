"""Worktree-local credentials encrypted with Windows user-scoped DPAPI."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
from threading import RLock
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, SecretStr

SECRET_FIELDS = ("openai_api_key", "openrouter_api_key", "deepl_api_key", "azure_speech_key")


class ConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    transport: Literal["api", "openrouter", "codex"] = "api"
    model: str = Field(default="gpt-6-luna", pattern=r"^[a-zA-Z0-9._:/-]{1,240}$")
    openai_api_key: SecretStr = Field(default=SecretStr(""), max_length=4096)
    openrouter_api_key: SecretStr = Field(default=SecretStr(""), max_length=4096)
    deepl_api_key: SecretStr = Field(default=SecretStr(""), max_length=4096)
    azure_speech_key: SecretStr = Field(default=SecretStr(""), max_length=4096)
    azure_region: str = Field(default="brazilsouth", pattern=r"^[a-z][a-z0-9]{1,39}$")
    api_max_output_tokens: int = Field(default=2048, ge=256, le=8192)


def protect(data: bytes, *, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Credential storage requires Windows DPAPI")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_uint32), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    result = Blob()
    library = ctypes.WinDLL("crypt32", use_last_error=True)
    operation = library.CryptUnprotectData if decrypt else library.CryptProtectData
    operation.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(Blob),
    ]
    operation.restype = ctypes.c_int
    if not operation(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise RuntimeError("Windows credential protection failed")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


class ConnectionStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = RLock()

    def load(self) -> ConnectionConfig:
        with self.lock:
            if not self.path.exists():
                return ConnectionConfig()
            if self.path.stat().st_size > 65536:
                raise RuntimeError("Invalid credential store")
            return ConnectionConfig.model_validate_json(
                protect(self.path.read_bytes(), decrypt=True)
            )

    def save(self, config: ConnectionConfig) -> None:
        with self.lock:
            data = config.model_dump()
            for field in SECRET_FIELDS:
                data[field] = getattr(config, field).get_secret_value()
            encrypted = protect(json.dumps(data).encode())
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(f".connections-{uuid4().hex}.tmp")
            try:
                temporary.write_bytes(encrypted)
                os.replace(temporary, self.path)
            finally:
                temporary.unlink(missing_ok=True)

    def public(self) -> dict:
        config = self.load()
        data = config.model_dump(exclude=set(SECRET_FIELDS))
        data["configured"] = {
            field: bool(getattr(config, field).get_secret_value()) for field in SECRET_FIELDS
        }
        return data

    def update(self, patch: dict) -> dict:
        with self.lock:
            config = self.load()
            data = config.model_dump()
            for key, value in patch.items():
                # Blank secret preserves an existing key; DELETE explicitly removes it.
                if key in SECRET_FIELDS and value == "":
                    continue
                data[key] = value
            self.save(ConnectionConfig.model_validate(data))
            return self.public()


def apply_connections(settings):
    """Explicit opt-in only. Workers reload per task; never enable generation here."""
    if not settings.studio_connections_enabled:
        return settings
    store = ConnectionStore(settings.studio_connections_path)
    if not store.path.exists():
        return settings
    config = store.load()
    uses_codex = config.transport == "codex"
    uses_openrouter = config.transport == "openrouter"
    model = config.model
    if uses_openrouter and not model.startswith("openrouter/"):
        model = f"openrouter/{model}"
    elif not uses_codex and not uses_openrouter:
        model = f"openai/{model}"
    return settings.model_copy(
        update={
            "text_generation_provider": "litellm",
            "text_generation_transport": "codex" if uses_codex else "api",
            "text_generation_model": model,
            "openai_api_key": (
                config.openai_api_key.get_secret_value() or None
                if config.transport == "api"
                else None
            ),
            "litellm_api_key": None,
            "openrouter_api_key": (
                config.openrouter_api_key.get_secret_value() or None if uses_openrouter else None
            ),
            "deepl_api_key": config.deepl_api_key.get_secret_value() or None,
            "translation_provider": "deepl",
            "audio_provider": "azure",
            "azure_speech_key": config.azure_speech_key.get_secret_value() or None,
            "azure_speech_region": config.azure_region,
            "studio_api_max_output_tokens": config.api_max_output_tokens,
        }
    )
