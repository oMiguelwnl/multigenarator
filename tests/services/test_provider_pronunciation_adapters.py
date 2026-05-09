"""Tests for provider-backed pronunciation adapters."""

from __future__ import annotations

import json

import pytest

from multilang.services.provider_pronunciation_adapters import (
    LiteLLMPronunciationAdapter,
    PronunciationGenerationRequest,
)
from multilang.settings import Settings


def test_litellm_pronunciation_adapter_uses_json_response() -> None:
    calls: list[dict[str, object]] = []

    def fake_completion(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"ipa": "/ˈkaza/", "spoken_form": "KA-za", "uncertainty_notes": []}
                        )
                    }
                }
            ]
        }

    settings = Settings(_env_file=None, text_generation_model="openai/gpt-4o-mini", openrouter_api_key="router-key")
    result = LiteLLMPronunciationAdapter(settings, completion_func=fake_completion).generate_pronunciation(
        PronunciationGenerationRequest(
            target_language="pt",
            display_form="casa",
            lemma="casa",
            definitions_html="noun: house",
        )
    )

    assert result.ipa == "/ˈkaza/"
    assert result.spoken_form == "KA-za"
    assert result.provenance["source"] == "provider-pronunciation-generator"
    assert result.provenance["provider"] == "litellm"
    assert calls[0]["temperature"] == 0.1
    assert calls[0]["response_format"] == {"type": "json_object"}
    assert "You generate pronunciation data" in calls[0]["messages"][0]["content"]
    prompt = calls[0]["messages"][1]["content"]
    assert "Target language: Portuguese (pt)" in prompt
    assert "Display form: casa" in prompt
    assert "Lemma: casa" in prompt
    assert "Definitions: noun: house" in prompt
    assert "Display form exactly" in prompt
    assert "ipa, spoken_form, uncertainty_notes" in prompt


@pytest.mark.parametrize("payload", [{"ipa": "", "spoken_form": "KA-za"}, {"ipa": "/ˈkaza/", "spoken_form": ""}])
def test_litellm_pronunciation_adapter_rejects_missing_required_values(payload: dict[str, str]) -> None:
    def fake_completion(**kwargs: object) -> dict[str, object]:
        return {"choices": [{"message": {"content": json.dumps(payload)}}]}

    adapter = LiteLLMPronunciationAdapter(Settings(_env_file=None), completion_func=fake_completion)

    with pytest.raises(ValueError):
        adapter.generate_pronunciation(
            PronunciationGenerationRequest(
                target_language="pt",
                display_form="casa",
                lemma="casa",
                definitions_html="noun: house",
            )
        )
