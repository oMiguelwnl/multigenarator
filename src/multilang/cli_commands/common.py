"""Stable CLI defaults shared by command families."""

from multilang.domain.jobs import SupportedLanguage
from multilang.output_paths import DEFAULT_OUTPUT_DIR

TEST_MODE_CARDS_PER_LEVEL = 3

LOCAL_SMOKE_LANGUAGE = SupportedLanguage.EN

LOCAL_SMOKE_FIXTURE_DIR = DEFAULT_OUTPUT_DIR / "examples" / "local-smoke"

LOCAL_SMOKE_WORDS = ("harbor", "lantern", "meadow")
