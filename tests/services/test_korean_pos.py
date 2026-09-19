"""Native tag projections remain conservative outside documented categories."""

import pytest


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("SN", "NUM"),
        ("JKS", "ADP"),
        ("JKC", "ADP"),
        ("JKG", "ADP"),
        ("JKO", "ADP"),
        ("JKB", "ADP"),
        ("JKV", "ADP"),
        ("JKQ", "ADP"),
        ("JX", "ADP"),
        ("JC", "CCONJ"),
    ],
)
def test_documented_numeric_and_postposition_tags_have_a_direct_projection(tag, expected):
    from multilang.services.korean_pos import kiwi_to_upos

    assert kiwi_to_upos(tag) == expected


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("NNG", "NOUN"),
        ("NNP", "PROPN"),
        ("NR", "NUM"),
        ("VV", "VERB"),
        ("VX", "AUX"),
        ("VA", "ADJ"),
    ],
)
def test_existing_lexical_categories_keep_their_projection(tag, expected):
    from multilang.services.korean_pos import kiwi_to_upos

    assert kiwi_to_upos(tag) == expected


@pytest.mark.parametrize(
    "tag", ["SL", "SH", "SW", "XR", "XSV", "XSA", "XSN", "XPN", "EC", "W_URL", "jks", "SN+NNG", ""]
)
def test_foreign_scripts_derivation_and_unknown_categories_do_not_guess_pos(tag):
    from multilang.services.korean_pos import kiwi_to_upos

    assert kiwi_to_upos(tag) == "X"


@pytest.mark.parametrize(
    ("tag", "surface"),
    [("SSO", "<"), ("SSC", ">"), ("SO", "~"), ("SS", "<“"), ("SF", "!"), ("SW", "•")],
)
def test_native_punctuation_role_includes_documented_unicode_symbols(tag, surface):
    from multilang.services.korean_pos import is_kiwi_punctuation

    assert is_kiwi_punctuation(tag, surface)


@pytest.mark.parametrize(
    ("tag", "surface"),
    [
        ("SW", "~"),
        ("SW", "🛸"),
        ("SW", "ひらがな"),
        ("SL", "<"),
        ("SH", "<"),
        ("NNG", "<"),
        ("SSO", "학교"),
        ("SSO", "<학교"),
        ("SSO", "< "),
        ("SSO", ""),
        ("SSO+NNG", "<"),
        ("sso", "<"),
    ],
)
def test_punctuation_requires_a_known_native_role_and_only_allowed_characters(tag, surface):
    from multilang.services.korean_pos import is_kiwi_punctuation

    assert not is_kiwi_punctuation(tag, surface)
