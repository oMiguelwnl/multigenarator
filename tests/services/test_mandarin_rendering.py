"""Mandarin annotations must retain the frozen reading and exact visible text."""

import csv
from html import escape
from html.parser import HTMLParser

import pytest

from multilang.domain.exporting import (
    MANDARIN_EXPORT_CARD_FIELD_NAMES,
    ExportArtifactFormat,
    ExportCardIdentity,
    ExportCardRow,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import policy_for_language
from multilang.services import mandarin_orthography
from multilang.services.export_anki_package import build_multilang_note
from multilang.services.export_tabular_bundle import write_export_tabular_bundle


class RubyText(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.in_rt = False
        self.visible = ""
        self.readings = []
        self.tones = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        if tag == "rt":
            self.in_rt = True
        if tag == "ruby":
            self.tones.append(dict(attrs)["class"].split()[-1])

    def handle_endtag(self, tag):
        if tag == "rt":
            self.in_rt = False

    def handle_data(self, data):
        if self.in_rt:
            self.readings.append(data)
        else:
            self.visible += data


def render(sentence, pinyin, **kwargs):
    renderer = getattr(mandarin_orthography, "render_mandarin_sentence", None)
    assert callable(renderer), "Missing Mandarin ruby renderer"
    return renderer(sentence=sentence, sentence_pinyin=pinyin, **kwargs)


def reference_row(source_type="frequency"):
    return ExportCardRow(
        identity=ExportCardIdentity(
            language="zh", source_type=source_type, job_id="ruby-fixture",
            item_key="下载", lemma_key="下载", sort_index=1,
        ),
        word="下载", front_of_card="下载", definitions="verb: transferir um arquivo para o dispositivo",
        example_sentence="他下载了很多电影。", translation="Ele baixou muitos filmes.",
        word_audio="[sound:word.mp3]", sentence_audio="[sound:sentence.mp3]",
        mandarin_word_pinyin="xià zài", mandarin_word_traditional="下載",
        mandarin_sentence_pinyin="tā xià zài le hěn duō diàn yǐng。",
        mandarin_sentence_traditional="他下載了很多電影。",
    )


def test_reference_sentence_has_one_matching_reading_and_color_per_character():
    value = RubyText(render("他下载了很多电影。", "tā xià zài le hěn duō diàn yǐng。"))
    assert value.visible == "他下载了很多电影。"
    assert value.readings == ["tā", "xià", "zài", "le", "hěn", "duō", "diàn", "yǐng"]
    assert value.tones == [f"tone-{tone}" for tone in (1, 4, 4, 5, 3, 1, 4, 3)]


@pytest.mark.parametrize("pinyin", ["mā má mǎ mà ma。", "ma1 ma2 ma3 ma4 ma5。"])
def test_all_five_tones_share_the_same_visual_policy(pinyin):
    value = RubyText(render("妈麻马骂吗。", pinyin))
    assert value.readings == ["mā", "má", "mǎ", "mà", "ma"]
    assert value.tones == [f"tone-{n}" for n in range(1, 6)]


def test_saved_contextual_reading_is_used_without_rerunning_the_dictionary(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Export must not derive a new reading")

    monkeypatch.setattr(mandarin_orthography, "lazy_pinyin", forbidden)
    assert RubyText(render("行。", "háng。")).readings == ["háng"]


@pytest.mark.parametrize(
    "sentence,pinyin",
    [
        ("“银行”，我去。", "“yín háng”, wǒ qù。"),
        ("我有2本书。", "wǒ yǒu2 běn shū。"),
        ("看了2次。", "kàn le2 cì。"),
        ("看了2次。", "kan4 le5 2 ci4。"),
        ("看。", "Kàn."),
        ("我 & 你。", "wǒ & nǐ。"),
        ("西安。", "Xī'ān。"),
    ],
)
def test_punctuation_numbers_and_spaces_do_not_shift_readings(sentence, pinyin):
    value = render(sentence, pinyin)
    assert RubyText(value).visible == sentence
    if "&" in sentence:
        assert "&amp;" in value


def test_generated_neutral_reading_keeps_a_following_literal_number():
    sentence = "看了2次。"
    value = RubyText(render(sentence, mandarin_orthography.tonal_pinyin(sentence)))
    assert value.visible == sentence
    assert value.readings == ["kàn", "le", "cì"]
    assert value.tones == ["tone-4", "tone-5", "tone-4"]


@pytest.mark.parametrize(
    "sentence,pinyin",
    [
        ("银行。", "yín。"),
        ("银行。", "yín háng hǎo。"),
        ("银行。", "yínháng。"),
        ("银行！", "yín háng。"),
        ("银行。", "银行。"),
        ("银行。", "yín <script>alert(1)</script>。"),
        ("<img onerror=alert(1)>银行。", "yín háng。"),
        ("银行\x1f。", "yín háng。"),
    ],
)
def test_invalid_or_misaligned_readings_fail_closed(sentence, pinyin):
    with pytest.raises(ValueError):
        render(sentence, pinyin)


def test_cloze_keeps_one_wrapper_around_the_target_and_its_readings():
    value = render("我去银行。", "wǒ qù yín háng。", cloze_span=(2, 4))
    assert value.count('class="semantic-cloze-target"') == 1
    target = value.split('<span class="semantic-cloze-target">', 1)[1].split("</span>", 1)[0]
    assert RubyText(target).visible == "银行"
    assert RubyText(target).readings == ["yín", "háng"]


@pytest.mark.parametrize("source_type", ["frequency", "word-list"])
@pytest.mark.parametrize("format", [ExportArtifactFormat.CSV, ExportArtifactFormat.TSV])
def test_package_and_tabular_exports_use_identical_static_ruby(tmp_path, source_type, format):
    row = reference_row(source_type)
    before = row.model_dump()
    note = build_multilang_note(row)
    fields = dict(zip(MANDARIN_EXPORT_CARD_FIELD_NAMES, note.fields, strict=True))
    assert "<ruby" in fields["Example Sentence"]
    assert RubyText(fields["Example Sentence"]).visible == row.example_sentence
    assert fields["Pinyin"] == row.mandarin_word_pinyin
    assert fields["Sentence Pinyin"] == row.mandarin_sentence_pinyin
    assert row.model_dump() == before
    result = write_export_tabular_bundle(
        rows=[row], export_format=format, output_dir=tmp_path,
        deck_name="Mandarin", note_type_name="Multilang::Mandarin Card",
    )
    delimiter = "\t" if format is ExportArtifactFormat.TSV else ","
    values = list(csv.reader(result.output_path.read_text().splitlines()[5:], delimiter=delimiter))[0]
    assert values == [str(v) for v in note.fields]


def test_html_entities_are_decoded_once_then_escaped_for_rendering():
    row = reference_row().model_copy(update={
        "example_sentence": escape("我 & 你。"),
        "mandarin_sentence_pinyin": escape("wǒ & nǐ。"),
    })
    fields = dict(zip(MANDARIN_EXPORT_CARD_FIELD_NAMES, build_multilang_note(row).fields, strict=True))
    assert RubyText(fields["Example Sentence"]).visible == "我 & 你。"
    assert "&amp;amp;" not in fields["Example Sentence"]


def test_new_mandarin_content_uses_portuguese_policy():
    policy = policy_for_language(SupportedLanguage.ZH)
    assert policy.definition_language == "pt"
    assert policy.translation_target_language == "pt"
    assert policy_for_language(SupportedLanguage.FR).translation_target_language == "en"
