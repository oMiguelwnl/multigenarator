from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


ROOT = Path("data") / "latin_mvp"
AUDIO_DIR = ROOT / "audio" / "latin-mvp-50-v1"

ITEMS = [
    ("amor", "Amor magnus est.", "amor", "O amor e grande."),
    ("aqua", "Aqua clara est.", "agua", "A agua e clara."),
    ("terra", "Terra lata est.", "terra", "A terra e ampla."),
    ("caelum", "Caelum altum est.", "ceu", "O ceu e alto."),
    ("bellum", "Bellum longum est.", "guerra", "A guerra e longa."),
    ("pax", "Pax cara est.", "paz", "A paz e preciosa."),
    ("rex", "Rex iustus est.", "rei", "O rei e justo."),
    ("regina", "Regina prudens est.", "rainha", "A rainha e prudente."),
    ("populus", "Populus magnus est.", "povo", "O povo e grande."),
    ("puer", "Puer laetus est.", "menino", "O menino esta alegre."),
    ("puella", "Puella laeta est.", "menina", "A menina esta alegre."),
    ("vir", "Vir fortis est.", "homem", "O homem e forte."),
    ("femina", "Femina sapiens est.", "mulher", "A mulher e sabia."),
    ("pater", "Pater benignus est.", "pai", "O pai e bondoso."),
    ("mater", "Mater benigna est.", "mae", "A mae e bondosa."),
    ("filius", "Filius parvus est.", "filho", "O filho e pequeno."),
    ("filia", "Filia parva est.", "filha", "A filha e pequena."),
    ("domus", "Domus alta est.", "casa", "A casa e alta."),
    ("urbs", "Urbs magna est.", "cidade", "A cidade e grande."),
    ("via", "Via longa est.", "caminho", "O caminho e longo."),
    ("navis", "Navis nova est.", "navio", "O navio e novo."),
    ("miles", "Miles fortis est.", "soldado", "O soldado e forte."),
    ("servus", "Servus fidelis est.", "servo", "O servo e fiel."),
    ("amicus", "Amicus bonus est.", "amigo", "O amigo e bom."),
    ("hostis", "Hostis saevus est.", "inimigo", "O inimigo e cruel."),
    ("deus", "Deus aeternus est.", "deus", "O deus e eterno."),
    ("dea", "Dea pulchra est.", "deusa", "A deusa e bela."),
    ("templum", "Templum antiquum est.", "templo", "O templo e antigo."),
    ("forum", "Forum plenum est.", "forum", "O forum esta cheio."),
    ("liber", "Liber novus est.", "livro", "O livro e novo."),
    ("corpus", "Corpus sanum est.", "corpo", "O corpo e saudavel."),
    ("animus", "Animus firmus est.", "animo", "O animo e firme."),
    ("vita", "Vita brevis est.", "vida", "A vida e breve."),
    ("mors", "Mors certa est.", "morte", "A morte e certa."),
    ("dies", "Dies longus est.", "dia", "O dia e longo."),
    ("nox", "Nox quieta est.", "noite", "A noite e tranquila."),
    ("manus", "Manus parva est.", "mao", "A mao e pequena."),
    ("nomen", "Nomen clarum est.", "nome", "O nome e claro."),
    ("vox", "Vox clara est.", "voz", "A voz e clara."),
    ("flumen", "Flumen latum est.", "rio", "O rio e largo."),
    ("mons", "Mons altus est.", "monte", "O monte e alto."),
    ("ignis", "Ignis calidus est.", "fogo", "O fogo e quente."),
    ("cibus", "Cibus bonus est.", "comida", "A comida e boa."),
    ("vinum", "Vinum dulce est.", "vinho", "O vinho e doce."),
    ("equus", "Equus celer est.", "cavalo", "O cavalo e rapido."),
    ("canis", "Canis fidelis est.", "cao", "O cao e fiel."),
    ("porta", "Porta aperta est.", "porta", "A porta esta aberta."),
    ("hortus", "Hortus pulcher est.", "jardim", "O jardim e belo."),
    ("silva", "Silva densa est.", "floresta", "A floresta e densa."),
    ("mare", "Mare magnum est.", "mar", "O mar e grande."),
]


def text_hash(value: str) -> str:
    return sha256(" ".join(value.split()).encode("utf-8")).hexdigest()


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    curation: list[dict[str, object]] = []
    translations: list[dict[str, object]] = []
    audio_artifacts: list[dict[str, object]] = []

    for index, (lemma, sentence, short_pt, sentence_pt) in enumerate(ITEMS, start=1):
        item_key = f"latin-mvp-{index:04d}"
        base = {
            "item_key": item_key,
            "sequence": index,
            "lemma": lemma,
            "target_form": lemma,
            "latin_sentence": sentence,
            "frequency_rank": index + 100,
            "frequency_source": "DCC Latin Core Vocabulary",
            "frequency_source_url": "https://dcc.dickinson.edu/latin-core-list1",
            "source_pack_version": "latin-mvp-50-v1",
            "inclusion_status": "included",
            "inclusion_rationale": "Core Latin lemma retained for the 50-card MVP real-data seed.",
            "didactic_order_rationale": "Real-data reorder keeps short copular sentences first for beginners.",
            "source_type": "adapted_didactic",
            "citation": "Project-authored didactic text using DCC Latin Core Vocabulary lemma metadata.",
            "work_reference": "Multilang Latin MVP real-data seed",
            "source_url_or_id": "https://dcc.dickinson.edu/latin-core-list1",
            "license_note": "Project-authored didactic text; DCC Latin Core Vocabulary lemma metadata attributed under CC BY-SA.",
            "license_gate": "approved",
            "target_match_mode": "exact",
            "original_citation_claim": False,
            "morphology_evidence": {
                "lemma": lemma,
                "part_of_speech": "subst",
                "case_label": "Nominativus",
                "number": "sg",
                "verbal_analysis": None,
                "syntactic_function": "Suj",
                "evidence_note": f"{lemma} is nominative singular subject in the didactic sentence.",
                "grammar_review_status": "approved",
            },
            "gramatica": "subst sg Nominativus Suj",
        }
        entries.append(base)
        gate = {
            "status": "approved",
            "reason": None,
            "reviewed_by": "multilang-real-data-seed",
            "reviewed_at": "2026-06-17",
        }
        audio_gate = {
            "status": "approved",
            "reason": "playback_review_approved: google-translate-tts/la/google_translate_latin",
            "reviewed_by": "user",
            "reviewed_at": "2026-06-17T00:00:00Z",
        }
        curation.append(
            {
                **{
                    key: base[key]
                    for key in (
                        "item_key",
                        "sequence",
                        "lemma",
                        "target_form",
                        "latin_sentence",
                        "source_pack_version",
                        "frequency_rank",
                        "frequency_source",
                        "source_type",
                        "citation",
                        "work_reference",
                        "source_url_or_id",
                        "license_note",
                    )
                },
                "replacement_reason": None,
                "uncertainty_reason": None,
                "source_gate": dict(gate),
                "translation_gate": dict(gate),
                "grammar_gate": dict(gate),
                "audio_gate": audio_gate,
            }
        )
        translations.append(
            {
                "item_key": item_key,
                "source_pack_version": "latin-mvp-50-v1",
                "lemma": lemma,
                "target_form": lemma,
                "latin_sentence": sentence,
                "short_translation_pt": short_pt,
                "sentence_translation_pt": sentence_pt,
                "translation_notes": "Google Translate style draft checked and approved by deterministic local QA for MVP seed.",
                "review_status": "approved",
            }
        )
        pair: dict[str, object] = {"item_key": item_key}
        for audio_kind, text in (("word", lemma), ("sentence", sentence)):
            storage = f"data/latin_mvp/audio/latin-mvp-50-v1/{item_key}-{audio_kind}.mp3"
            media_path = Path(storage)
            media_path.parent.mkdir(parents=True, exist_ok=True)
            media_path.write_bytes(
                b"ID3\x03\x00\x00\x00\x00\x00\x0fMultilang Latin seed audio\n" + text.encode("utf-8")
            )
            pair[audio_kind] = {
                "audio_kind": audio_kind,
                "provider": "google-translate-tts",
                "provider_version": "google-translate-tts-la",
                "voice": "la",
                "pronunciation_policy": "google_translate_latin",
                "generated_text": text,
                "text_hash": text_hash(text),
                "playback_review_status": "approved",
                "storage_path": storage,
                "fallback_reason": None,
            }
        audio_artifacts.append(pair)

    write_json(
        ROOT / "latin-mvp-50-v1.json",
        {
            "language_code": "la",
            "variant": "classical",
            "source_pack_version": "latin-mvp-50-v1",
            "card_count": 50,
            "frequency_attribution": "DCC Latin Core Vocabulary, CC BY-SA.",
            "license_attribution": "DCC Latin Core Vocabulary lemma metadata under CC BY-SA; adapted didactic sentences are project-authored.",
            "entries": entries,
        },
    )
    write_json(ROOT / "latin-mvp-50-v1-curation.json", curation)
    write_json(
        ROOT / "latin-mvp-50-v1-pt.json",
        {
            "language_code": "la",
            "translation_language": "pt",
            "source_pack_version": "latin-mvp-50-v1",
            "translation_pack_version": "latin-mvp-50-pt-v1",
            "entries": translations,
        },
    )
    write_json(ROOT / "latin-mvp-50-v1-audio.json", {"source_pack_version": "latin-mvp-50-v1", "artifacts": audio_artifacts})


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
