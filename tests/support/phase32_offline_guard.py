"""Test helper proving Phase 32 isolated suites run without live credentials."""

from __future__ import annotations


FORBIDDEN_ENV_FRAGMENTS = ("KEY", "TOKEN", "SECRET", "OPENAI", "AZURE", "DEEPL", "LITELLM")


def assert_no_live_credentials(environment: dict[str, str]) -> None:
    leaked = [name for name in environment if any(fragment in name.upper() for fragment in FORBIDDEN_ENV_FRAGMENTS)]
    if leaked:
        raise AssertionError(f"live credentials leaked into isolated Phase 32 suite: {sorted(leaked)}")
