"""Explicit trusted adapter registration, without evaluating user import paths."""

import re
from typing import Literal

PluginKind = Literal["language", "provider", "importer", "analyzer", "module"]


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[tuple[str, str, str], object] = {}

    def register(self, *, kind: PluginKind, name: str, version: str, plugin: object) -> None:
        if kind not in {"language", "provider", "importer", "analyzer", "module"}:
            raise ValueError("unknown plugin kind")
        if not all(re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value) for value in (name, version)):
            raise ValueError("plugin names and versions must be bounded identifiers")
        key = (kind, name, version)
        if key in self._plugins and self._plugins[key] is not plugin:
            raise ValueError("plugin version already registered")
        self._plugins[key] = plugin

    def get(self, kind: PluginKind, name: str, version: str) -> object:
        try:
            return self._plugins[(kind, name, version)]
        except KeyError:
            raise ValueError("plugin not registered") from None

    def inventory(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(sorted(self._plugins))
