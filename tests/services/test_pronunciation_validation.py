"""Syntax checks reject unusable pronunciation without inferring accuracy."""

import pytest


@pytest.mark.parametrize("value", ["/haʊs/", "[bɐlʲˈʂuju]", "/a/", "/ˈt͡ʃaː.ɾa/", "/β θ χ/", "/ni˧˥/"])
def test_usable_ipa_accepts_transcription_structure(value):
    from multilang.services.pronunciation_validation import is_usable_ipa

    assert is_usable_ipa(value)


@pytest.mark.parametrize("value", [None, "", "house", "//", "/ /", "/???/", "/haʊs", "[haʊs/", "/<script>/", "/ha\nʊs/", "/你好/", "/хаус/", "/N/A/", "/haʊs\u200b/"])
def test_usable_ipa_rejects_missing_or_malformed_transcription(value):
    from multilang.services.pronunciation_validation import is_usable_ipa

    assert not is_usable_ipa(value)
