"""Stable CLI defaults shared by command families."""

from pathlib import Path

from multilang.domain.jobs import SupportedLanguage

TEST_MODE_CARDS_PER_LEVEL = 3

LOCAL_SMOKE_LANGUAGE = SupportedLanguage.EN

LOCAL_SMOKE_FIXTURE_DIR = Path(".multilang/live-smoke-azure")

LOCAL_SMOKE_WORDS = ("harbor", "lantern", "meadow")
