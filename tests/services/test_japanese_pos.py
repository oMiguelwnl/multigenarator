import pytest


def project(pos1, pos2, lemma):
    from multilang.services.japanese_pos import unidic_to_upos

    return unidic_to_upos(pos1, pos2, lemma)


@pytest.mark.parametrize(
    ("pos1", "pos2", "lemma", "expected"),
    [
        ("接頭辞", "*", "御", "NOUN"),
        ("接尾辞", "名詞的", "者", "NOUN"),
        ("接尾辞", "名詞的", "つ", "NOUN"),
        ("接尾辞", "名詞的", "中", "NOUN"),
        ("接尾辞", "名詞的", "化", "NOUN"),
        ("接尾辞", "名詞的", "さ", "PART"),
        ("接尾辞", "名詞的", "ぽい", "NOUN"),
        ("接尾辞", "形状詞的", "的", "PART"),
        ("接尾辞", "形状詞的", "放し", "PART"),
        ("接尾辞", "形容詞的", "易い", "AUX"),
        ("接尾辞", "形容詞的", "ぽい", "PART"),
        ("接尾辞", "形容詞的", "っぽい", "PART"),
        ("接尾辞", "動詞的", "めく", "PART"),
        ("接尾辞", "動詞的", "染みる", "PART"),
    ],
)
def test_affixes_follow_context_independent_japanese_ud_rules(pos1, pos2, lemma, expected):
    assert project(pos1, pos2, lemma) == expected


@pytest.mark.parametrize(
    ("pos1", "pos2", "lemma", "expected"),
    [
        ("名詞", "普通名詞", "学校", "NOUN"),
        ("名詞", "固有名詞", "東京", "PROPN"),
        ("名詞", "数詞", "一", "NUM"),
        ("代名詞", "*", "私", "PRON"),
        ("動詞", "一般", "行く", "VERB"),
        ("形容詞", "一般", "赤い", "ADJ"),
        ("形状詞", "一般", "静か", "ADJ"),
        ("副詞", "*", "既に", "ADV"),
        ("助詞", "格助詞", "に", "PART"),
        ("助動詞", "*", "です", "AUX"),
        ("連体詞", "*", "此の", "DET"),
        ("接続詞", "*", "しかし", "CCONJ"),
        ("感動詞", "一般", "ああ", "INTJ"),
        ("補助記号", "句点", "。", "PUNCT"),
        ("記号", "一般", "〇", "SYM"),
    ],
)
def test_existing_projection_is_preserved_without_claiming_full_ud_conversion(
    pos1, pos2, lemma, expected
):
    assert project(pos1, pos2, lemma) == expected


@pytest.mark.parametrize(
    ("pos1", "pos2", "lemma"),
    [
        ("接尾辞", "未定義", "者"),
        ("接尾辞", "*", "さ"),
        ("接尾辞", None, "ぽい"),
        ("接尾辞", "", "的"),
        ("未定義", "名詞的", "者"),
        (None, None, None),
        ("", "", ""),
    ],
)
def test_unrecognized_categories_remain_unresolved(pos1, pos2, lemma):
    assert project(pos1, pos2, lemma) == "X"


@pytest.fixture(scope="module")
def japanese_tagger():
    import unidic_lite
    from fugashi import Tagger

    return Tagger(f'-d "{unidic_lite.DICDIR}"')


@pytest.mark.parametrize(
    ("sentence", "surface", "lemma", "orth_base", "pos"),
    [
        ("お茶が好きです。", "お", "御", "お", "NOUN"),
        ("研究者が帰った。", "者", "者", "者", "NOUN"),
        ("二つの道がある。", "つ", "つ", "つ", "NOUN"),
        ("今日も勉強中です。", "中", "中", "中", "NOUN"),
        ("素材を電子化した。", "化", "化", "化", "NOUN"),
        ("庭の静かさが好きです。", "さ", "さ", "さ", "PART"),
        ("科学的な説明です。", "的", "的", "的", "PART"),
        ("料理を作りっぱなしにした。", "っぱなし", "放し", "っぱなし", "PART"),
        ("この本は読みやすい。", "やすい", "易い", "やすい", "AUX"),
        ("子供っぽく話した。", "っぽく", "ぽい", "っぽい", "PART"),
        ("空が春めいてきた。", "めい", "めく", "めく", "PART"),
    ],
)
def test_real_unidic_affixes_use_dictionary_lemma_without_rewriting_features(
    japanese_tagger, sentence, surface, lemma, orth_base, pos
):
    token = next(token for token in japanese_tagger(sentence) if token.surface == surface)
    features = token.feature
    original = features._asdict()
    assert not token.is_unk
    assert (features.lemma, features.orthBase) == (lemma, orth_base)
    assert project(features.pos1, features.pos2, features.lemma) == pos
    assert features._asdict() == original
