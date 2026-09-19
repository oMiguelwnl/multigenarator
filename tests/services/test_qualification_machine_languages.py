"""Real published pilot fixtures exercise small, source-bound language batches."""

import hashlib
import importlib
import json

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.language_profiles import default_language_profiles
from multilang.services.qualification_machine import MachineActor
from multilang.services.qualification_pilot import (
    PreparedVocabularyInput,
    prepare_qualification_pilot,
)
from multilang.services.vocabulary_preparation import prepare_vocabulary


def api():
    return importlib.import_module("multilang.services.qualification_machine_languages")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path, *, language="pt", count=3, sounds=None):
    root = tmp_path / language
    root.mkdir()
    words = tuple(f"word{chr(97 + index)}" for index in range(count))
    source = root / "dictionary.jsonl"
    source.write_text(
        "".join(
            json.dumps(
                {
                    "lang_code": language,
                    "word": word,
                    "pos": "noun",
                    "sounds": sounds
                    if sounds is not None
                    else [{"ipa": "/ka.za/", "tags": ["Brazil"]}],
                    "senses": [{"glosses": [f"Meaning of {word}"]}],
                }
            )
            + "\n"
            for word in words
        )
    )
    prepared = root / "prepared"
    prepare_vocabulary(
        language=language, dictionary=source, dictionary_sha256=sha(source), output=prepared
    )
    profile = next(p for p in default_language_profiles() if p.language.value == language)
    profile_path = root / "profile.json"
    profile_path.write_text(profile.model_dump_json())
    pilot = root / "pilot"
    prepare_qualification_pilot(
        language=language,
        prepared_inputs=(
            PreparedVocabularyInput(
                directory=prepared, manifest_sha256=sha(prepared / "manifest.json")
            ),
        ),
        seed_words=words,
        profile_sha256=canonical_sha256(profile.model_dump(mode="json")),
        rubric_sha256="b" * 64,
        output=pilot,
        headword_count=count,
        case_count=1,
        packet_item_limit=2,
    )
    return {
        "language": language,
        "pilot_directory": pilot,
        "pilot_manifest_sha256": sha(pilot / "manifest.json"),
        "profile": {"path": profile_path, "sha256": sha(profile_path)},
    }


def request(inputs, **kwargs):
    return api().LanguageExpansionRequest(
        inputs=inputs,
        actor=MachineActor(
            actor_id="language-proposer",
            context_id="offline-language-context",
            execution_surface="agent",
            provider="codex",
        ),
        **kwargs,
    )


def selected(result, language="pt"):
    return next(row for row in result.languages if row.language.value == language)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("/ka.za/", True),
        ("[ˈli.vɾi]", True),
        ("/ʃtʁaːsə/", True),
        ("/ˈmɐ̃j̃/", True),
        ("[kʰaŋ]", True),
        ("/θɪŋ/", True),
        ("/a͡ɪ/", True),
        ("/a‿b/", True),
        ("word", False),
        ("/漢字/", False),
        ("/한글/", False),
        ("/かな/", False),
        ("/слово/", False),
        ("<script>alert(1)</script>", False),
        ("/<img src=x>/", False),
        ("/a\\u0000/".replace("\\u0000", "\x00"), False),
        ("/a\n/", False),
        ("/a\u200b/", False),
        ("/a\ue000/", False),
        ("/a/ /b/", False),
        ("[ma55]", False),
        ("/ˈ./", False),
        ("/" + "a" * 512 + "/", False),
        (None, False),
        ({"ipa": "/a/"}, False),
    ],
)
def test_source_ipa_admission_is_bounded_and_excludes_other_reading_systems(value, expected):
    assert api()._is_source_ipa(value) is expected


_SINOLOGICAL_TAGS = ["Mandarin", "Standard-Chinese", "Sinological-IPA"]
_SINOLOGICAL_EXAMPLE = "/tä⁵¹ t͡ɕi̯ä⁵⁵/"


def test_sinological_tones_require_a_zh_source_and_preserve_exact_notation(tmp_path):
    input_ = fixture(
        tmp_path,
        language="zh",
        count=1,
        sounds=[{"ipa": _SINOLOGICAL_EXAMPLE, "tags": _SINOLOGICAL_TAGS}],
    )
    input_.update(variant="zh-CN", pronunciation_tags=["Mandarin", "Standard-Chinese"])
    row = selected(api().build_machine_language_expansion(request([input_])), "zh")
    assert row.status == "prepared"
    assert row.selected[0].pronunciation.ipa == _SINOLOGICAL_EXAMPLE
    assert row.selected[0].candidate.sounds[0]["ipa"] == _SINOLOGICAL_EXAMPLE
    assert row.selected[0].pronunciation.tags == tuple(_SINOLOGICAL_TAGS)
    assert api()._is_source_ipa(_SINOLOGICAL_EXAMPLE) is False


@pytest.mark.parametrize(
    "language,tags",
    [
        ("pt", _SINOLOGICAL_TAGS),
        ("ja", _SINOLOGICAL_TAGS),
        ("ko", _SINOLOGICAL_TAGS),
        ("zh", ["Mandarin", "Standard-Chinese"]),
        ("zh", ["Mandarin", "Sinological-IPA"]),
        ("zh", ["Standard-Chinese", "Sinological-IPA"]),
        ("zh", ["mandarin", "Standard-Chinese", "Sinological-IPA"]),
    ],
)
def test_sinological_tones_do_not_leak_to_other_languages_or_untagged_sounds(
    tmp_path, language, tags
):
    input_ = fixture(
        tmp_path, language=language, count=1, sounds=[{"ipa": _SINOLOGICAL_EXAMPLE, "tags": tags}]
    )
    row = selected(api().build_machine_language_expansion(request([input_])), language)
    assert row.status == "blocked"
    assert row.request is None
    assert row.exclusion_counts["missing_matching_ipa"] == 1


@pytest.mark.parametrize(
    "notation,expected",
    [
        ("/a¹²³⁴⁵⁰⁻/", True),
        (_SINOLOGICAL_EXAMPLE, True),
        ("/¹²³⁴⁵⁰⁻/", False),
        ("tä⁵¹ t͡ɕi̯ä⁵⁵", False),
        ("大家", False),
        ("/大家⁵⁵/", False),
        ("dàjiā", False),
        ("/かな⁵⁵/", False),
        ("/한글⁵⁵/", False),
        ("/<script>⁵⁵/", False),
        ("/a⁵⁵\n/", False),
        ("/ma55/", False),
        ("/a⁶/", False),
        ("/a⁻<img>/", False),
    ],
)
def test_sinological_notation_keeps_bounded_phonetic_admission(notation, expected):
    assert api()._is_source_ipa(notation, allow_sinological_tones=True) is expected


@pytest.mark.parametrize("change", ["language", "tags"])
def test_serialized_sinological_proof_rechecks_language_and_source_tags(tmp_path, change):
    input_ = fixture(
        tmp_path,
        language="zh",
        count=1,
        sounds=[{"ipa": _SINOLOGICAL_EXAMPLE, "tags": _SINOLOGICAL_TAGS}],
    )
    row = selected(api().build_machine_language_expansion(request([input_])), "zh")
    assert row.status == "prepared"
    raw = row.selected[0].model_dump(mode="json", exclude_computed_fields=True)
    if change == "language":
        raw["candidate"]["language"] = "pt"
    else:
        raw["candidate"]["sounds"][0]["tags"].remove("Sinological-IPA")
        raw["pronunciation"]["tags"] = raw["candidate"]["sounds"][0]["tags"]
    raw["pronunciation"]["candidate_sha256"] = canonical_sha256(raw["candidate"])
    raw["item"]["candidate_sha256"] = raw["pronunciation"]["candidate_sha256"]
    raw["pronunciation"]["sound_sha256"] = canonical_sha256(raw["candidate"]["sounds"][0])
    with pytest.raises(ValueError, match="pronunciation source sound"):
        api().LanguageLexicalSelection.model_validate(raw)


def refresh_manifest(input_):
    path = input_["pilot_directory"] / "manifest.json"
    data = json.loads(path.read_text())
    data["pilot_sha256"] = canonical_sha256({k: v for k, v in data.items() if k != "pilot_sha256"})
    path.write_text(json.dumps(data))
    input_["pilot_manifest_sha256"] = sha(path)


def test_source_bound_small_batch_and_all_language_inventory(tmp_path):
    input_ = fixture(tmp_path, count=12)
    input_["variant"] = "pt-BR"
    input_["pronunciation_tags"] = ["Brazil"]
    result = api().build_machine_language_expansion(request([input_]))
    pt = selected(result)
    assert len(result.languages) == len(SupportedLanguage) == 23
    assert pt.status == "prepared"
    assert len(pt.selected) == len(pt.request.packet.items) == 10
    assert len({item.candidate.lemma for item in pt.selected}) == 10
    assert pt.eligible_ipa_count == 12
    assert pt.evaluation_case_count == 0
    assert pt.measured_form_count == 0
    assert "missing_calibration_corpus" in pt.blockers
    assert pt.request.phase == "proposal"
    assert pt.request.packet.split == "calibration"
    manifest = json.loads((input_["pilot_directory"] / "manifest.json").read_text())
    packet_for_item = {}
    for row in manifest["packets"]:
        if row["kind"] == "lexical":
            packet = json.loads(
                (input_["pilot_directory"] / row["path"] / "packet.json").read_text()
            )
            packet_for_item.update(
                {item["item_id"]: row["packet_sha256"] for item in packet["items"]}
            )
    for item in pt.selected:
        assert item.pronunciation.ipa == "/ka.za/"
        assert item.pronunciation.tags == ("Brazil",)
        assert item.pronunciation.source_record_sha256 == item.candidate.source_record_sha256
        assert item.pronunciation.candidate_sha256 == canonical_sha256(
            item.candidate.model_dump(mode="json")
        )
        assert item.parent_packet_sha256 == packet_for_item[item.item.item_id]
        assert item.item.sources[-1].source_id == "prepared-pronunciation"
    assert selected(result, "la").status == "separate_pipeline"
    assert selected(result, "en").status == "missing_input"
    assert result.production_eligible is False
    assert result.qualified is False
    assert result.redistribution_approved is False
    assert result.provider_calls_executed == 0


@pytest.mark.parametrize(
    "language", [language.value for language in SupportedLanguage if language.value != "la"]
)
def test_every_modern_language_uses_its_exact_profile_and_packet(tmp_path, language):
    result = api().build_machine_language_expansion(request([fixture(tmp_path, language=language)]))
    row = selected(result, language)
    assert row.request.packet.language.value == language
    assert len(row.selected) == 3
    assert row.profile_sha256 == row.request.packet.profile_sha256


@pytest.mark.parametrize(
    "sounds", [[], [{"ipa": "spelling"}], [{"ipa": "/kaza/", "tags": ["Portugal"]}]]
)
def test_missing_or_mismatched_variant_ipa_blocks_instead_of_guessing(tmp_path, sounds):
    input_ = fixture(tmp_path, sounds=sounds)
    input_["variant"] = "pt-BR"
    input_["pronunciation_tags"] = ["Brazil"]
    pt = selected(api().build_machine_language_expansion(request([input_])))
    assert pt.status == "blocked"
    assert pt.request is None
    assert not pt.selected
    assert pt.exclusion_counts["missing_matching_ipa"] == 3
    assert "no_source_bound_ipa" in pt.blockers


def test_rejects_pilot_bytes_profile_and_candidate_source_drift(tmp_path):
    input_ = fixture(tmp_path)
    path = input_["pilot_directory"] / "candidates.jsonl"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        api().build_machine_language_expansion(request([input_]))


def test_rejects_profile_of_another_language(tmp_path):
    pt, en = fixture(tmp_path), fixture(tmp_path, language="en")
    pt["profile"] = en["profile"]
    with pytest.raises(ValueError, match="profile"):
        api().build_machine_language_expansion(request([pt]))


def test_rejects_mixed_candidate_even_when_outer_file_hash_is_updated(tmp_path):
    input_ = fixture(tmp_path)
    path = input_["pilot_directory"] / "candidates.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["language"] = "en"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    manifest_path = input_["pilot_directory"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["candidates.jsonl"] = sha(path)
    manifest_path.write_text(json.dumps(manifest))
    refresh_manifest(input_)
    with pytest.raises(ValueError, match="candidate.*language"):
        api().build_machine_language_expansion(request([input_]))


def test_rejects_source_record_change_despite_refreshed_inventory(tmp_path):
    input_ = fixture(tmp_path)
    path = input_["pilot_directory"] / "candidates.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["source_record_sha256"] = "f" * 64
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    manifest_path = input_["pilot_directory"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["candidates.jsonl"] = sha(path)
    manifest_path.write_text(json.dumps(manifest))
    refresh_manifest(input_)
    with pytest.raises(ValueError, match="candidate.*(checksum|binding)"):
        api().build_machine_language_expansion(request([input_]))


def test_rejects_inventory_traversal_and_symlink(tmp_path):
    input_ = fixture(tmp_path)
    path = input_["pilot_directory"] / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["../dictionary.jsonl"] = "a" * 64
    path.write_text(json.dumps(manifest))
    refresh_manifest(input_)
    with pytest.raises(ValueError, match="path"):
        api().build_machine_language_expansion(request([input_]))


def test_request_rejects_duplicate_languages_latin_and_excessive_selection(tmp_path):
    input_ = fixture(tmp_path)
    for inputs, options in [
        ([input_, input_], {}),
        ([{**input_, "language": "la"}], {}),
        ([input_], {"item_limit": 11}),
    ]:
        with pytest.raises(ValueError):
            request(inputs, **options)


def test_export_is_idempotent_and_modified_child_or_config_fails(tmp_path):
    input_ = fixture(tmp_path)
    result = api().build_machine_language_expansion(request([input_]))
    output = tmp_path / "languages"
    first = api().export_machine_language_expansion(result, output)
    assert api().export_machine_language_expansion(result, output) == first
    assert first["prepared_languages"] == 1
    assert first["request_count"] == 1
    assert (output / "language-la" / "manifest.json").is_file()
    assert (output / "language-en" / "batch.json").is_file()
    child = output / first["requests"][0]["path"] / "request.json"
    child.write_text("{}")
    with pytest.raises(ValueError):
        api().export_machine_language_expansion(result, output)


def test_export_rejects_catalog_change_between_build_and_replay(tmp_path, monkeypatch):
    input_ = fixture(tmp_path, count=1)
    catalog = api().source_catalog("pt")
    monkeypatch.setattr(api(), "source_catalog", lambda language: catalog)
    result = api().build_machine_language_expansion(request([input_]))
    restored = api().MachineLanguageExpansion.model_validate(result.model_dump(mode="json"))
    assert api().build_machine_language_expansion(restored.configuration) == restored

    # Another local preparation can update even ancillary source metadata while
    # a long expansion runs. This is real evidence drift, not JSON round-trip drift.
    changed = {
        **catalog,
        "corpus": {**catalog["corpus"], "dev_urls": ["https://example.invalid/dev.conllu"]},
    }
    monkeypatch.setattr(api(), "source_catalog", lambda language: changed)
    rebuilt = api().build_machine_language_expansion(restored.configuration)
    before, after = selected(restored), selected(rebuilt)
    assert before.source_catalog_sha256 != after.source_catalog_sha256
    assert before.model_dump(exclude={"source_catalog_sha256"}) == after.model_dump(
        exclude={"source_catalog_sha256"}
    )
    output = tmp_path / "languages"
    with pytest.raises(ValueError, match="language expansion source or selection drift"):
        api().export_machine_language_expansion(restored, output)
    assert not output.exists()


def test_blocks_missing_ipa_with_its_own_manifest_and_no_request(tmp_path):
    result = api().build_machine_language_expansion(request([fixture(tmp_path, sounds=[])]))
    output = tmp_path / "languages"
    index = api().export_machine_language_expansion(result, output)
    assert index["request_count"] == 0
    assert (output / "language-pt" / "manifest.json").is_file()
    batch = json.loads((output / "language-pt" / "batch.json").read_text())
    assert batch["status"] == "blocked"
    assert not (output / "request-pt").exists()


def test_limits_files_and_rejects_variant_without_source_tags(tmp_path, monkeypatch):
    input_ = fixture(tmp_path)
    with pytest.raises(ValueError, match="variant"):
        request([{**input_, "variant": "pt-BR"}])
    monkeypatch.setattr(api(), "_MAX_FILE_BYTES", 1)
    with pytest.raises(ValueError, match="bounded|limit"):
        api().build_machine_language_expansion(request([input_]))


def test_symlink_candidate_is_not_read_and_html_escapes_variant(tmp_path):
    input_ = fixture(tmp_path)
    input_["variant"] = "<script>unsafe</script>"
    input_["pronunciation_tags"] = ["Brazil"]
    result = api().build_machine_language_expansion(request([input_]))
    html = api().render_machine_language_expansion(result)
    assert "<script>unsafe</script>" not in html
    assert "&lt;script&gt;unsafe&lt;/script&gt;" in html
    path = input_["pilot_directory"] / "candidates.jsonl"
    data = path.read_bytes()
    path.unlink()
    real = tmp_path / "outside-candidates.jsonl"
    real.write_bytes(data)
    path.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        api().build_machine_language_expansion(request([input_]))


def test_manifest_model_inventory_is_not_runtime_verification(tmp_path):
    input_ = fixture(tmp_path)
    model = tmp_path / "models.json"
    model.write_text(
        json.dumps(
            [
                {
                    "language": "pt",
                    "backend": "stanza",
                    "available": True,
                    "qualified": False,
                    "manifest_sha256": "c" * 64,
                }
            ]
        )
    )
    result = api().build_machine_language_expansion(
        request([input_], model_inventory={"path": model, "sha256": sha(model)})
    )
    row = selected(result)
    assert row.model_snapshot["backend"] == "stanza"
    assert row.model_runtime_revalidated is False
    assert row.qualified is False
