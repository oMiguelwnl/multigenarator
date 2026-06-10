from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CANDIDATES_PATH = PROJECT_ROOT / "data" / "latin_mvp" / "source_candidates.json"


def _load_candidates() -> dict[str, object]:
    return json.loads(SOURCE_CANDIDATES_PATH.read_text(encoding="utf-8"))


def test_latin_source_candidates_file_is_fail_closed() -> None:
    payload = _load_candidates()

    assert payload["status"] == "candidate_only"
    assert payload["runtime_enabled"] is False
    assert payload["decision"] == "unreviewed"

    for candidate in payload["candidates"]:
        assert candidate["status"] == "candidate_only"
        assert candidate["runtime_enabled"] is False
        assert candidate["decision"] == "unreviewed"
        assert candidate["source_input"] == "new2.md"


def test_latin_source_candidates_preserve_new2_links() -> None:
    payload = _load_candidates()
    urls = {candidate["url"] for candidate in payload["candidates"] if candidate["url"]}

    assert urls == {
        "https://finevoice.ai/voicelibrary/latin",
        "https://mylittlewordland.com/course/415114/as-mil-palavras-mais-frequentes-do-latim",
        "https://bridge.haverford.edu/",
        "https://dcc.dickinson.edu/latin-core-list1",
        "https://dcc.dickinson.edu/greek-core-list",
        "https://dcc.dickinson.edu/pt/latin-core-list1",
    }


def test_latin_source_candidates_do_not_fabricate_mentioned_provider_urls() -> None:
    payload = _load_candidates()
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}

    assert candidates["audio-google-translate-latin-mention"]["url"] is None
    assert candidates["audio-google-translate-latin-mention"]["classification"] == "audio_provider_mention"
    assert candidates["audio-elevenlabs-italian-mention"]["url"] is None
    assert candidates["audio-elevenlabs-italian-mention"]["classification"] == "audio_provider_mention"


def test_latin_source_candidates_mark_greek_as_related_reference_only() -> None:
    payload = _load_candidates()
    candidates = {candidate["id"]: candidate for candidate in payload["candidates"]}

    greek = candidates["reference-dcc-greek-core-list"]

    assert greek["url"] == "https://dcc.dickinson.edu/greek-core-list"
    assert greek["category"] == "reference"
    assert greek["classification"] == "related_reference_only"


def test_latin_source_candidates_do_not_mark_any_source_active_or_approved() -> None:
    payload = _load_candidates()

    forbidden_decisions = {"approved", "active", "enabled"}
    for candidate in payload["candidates"]:
        assert candidate["decision"] not in forbidden_decisions
        assert candidate["status"] != "approved"
        assert candidate["runtime_enabled"] is False
