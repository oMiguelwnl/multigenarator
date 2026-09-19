"""Assemble grammar notes only from current reviewed curriculum and exact media."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean_grammar import (
    KoreanGrammarBundle,
    grammar_content_hash,
    korean_grammar_canonical_json_sha256,
)
from multilang.domain.korean_grammar_bootstrap import KoreanGrammarBootstrapCard
from multilang.services.audio.media_validation import inspect_local_mp3
from multilang.services.korean_foundation_snapshot import resolve_active_korean_foundation_snapshot
from multilang.services.korean_grammar import (
    KoreanGrammarBundleBuilder,
    validate_korean_grammar_production_readiness,
)


@dataclass(frozen=True)
class KoreanGrammarExportRows:
    rows: list[ExportCardRow]
    media_index: dict[str, Path]
    bundle_sha256: str


def grammar_candidate_sha256(entry) -> str:
    """Bind linguistic review to content without a circular review hash."""
    payload = entry.model_dump(mode="json", by_alias=True)
    for key in ("content_hash", "review_binding", "word_media_binding", "sentence_media_binding", "ready_state"):
        payload.pop(key, None)
    return korean_grammar_canonical_json_sha256(payload)


def grammar_review_curriculum_sha256(bundle: KoreanGrammarBundle) -> str:
    """Review the graph and foundation independently of its review receipts."""
    payload = {
        "phase31_binding": bundle.phase31_binding.model_dump(mode="json"),
        "imported_concepts": [item.model_dump(mode="json") for item in bundle.imported_concepts],
        "overlay_concepts": [item.model_dump(mode="json") for item in bundle.overlay_concepts],
    }
    if bundle.orientation_entries:
        payload["orientation_concept_ids"] = [entry.target_concept_id for entry in bundle.orientation_entries]
    return korean_grammar_canonical_json_sha256(payload)


def assemble_korean_grammar_export_rows(
    *,
    bundle: KoreanGrammarBundle,
    job_id: str,
    media_paths: Mapping[str, Path],
    bootstrap_cards: Sequence[KoreanGrammarBootstrapCard] = (),
    active_snapshot_resolver: Callable[[], object] = resolve_active_korean_foundation_snapshot,
) -> KoreanGrammarExportRows:
    """Recheck all content and media before allowing the shared exporters to run.

    ``media_paths`` maps artifact SHA-256 to caller-selected files. The curriculum
    never supplies arbitrary filesystem paths. Reviewed lexical teaching cards
    are delivered first in the same package, in the bundle's prerequisite order.
    """
    bundle = KoreanGrammarBundle.model_validate(bundle.model_dump(mode="json", by_alias=True))
    if not job_id.strip() or not (bundle.orientation_entries or bundle.grammar_entries):
        raise ValueError("grammar export requires a job and nonempty curriculum")
    entry_ids = [entry.entry_id for entry in (*bundle.lexical_bootstrap, *bundle.orientation_entries, *bundle.grammar_entries)]
    if len(entry_ids) != len(set(entry_ids)):
        raise ValueError("grammar entry identifiers must be unique")
    teaching_cards = tuple(KoreanGrammarBootstrapCard.model_validate(card.model_dump(mode="json")) for card in bootstrap_cards)
    teaching = {card.entry_id: card for card in teaching_cards}
    if len(teaching) != len(teaching_cards) or set(teaching) != {entry.entry_id for entry in bundle.lexical_bootstrap}:
        raise ValueError("grammar export requires exact reviewed lexical bootstrap inventory")
    current = KoreanGrammarBundleBuilder(active_snapshot_resolver=active_snapshot_resolver).build_bundle(
        lexical_bootstrap=bundle.lexical_bootstrap, orientation_entries=bundle.orientation_entries,
        grammar_entries=bundle.grammar_entries,
    )
    if current != bundle:
        raise ValueError("grammar bundle or active foundation evidence drift")
    readiness = validate_korean_grammar_production_readiness(bundle)
    if readiness.ready_state != "learner_ready":
        raise ValueError("grammar export blocked: " + ",".join(readiness.blocked_reason_codes))

    rows = []
    media_index = {}
    profiles = set()

    def include_media(binding, text, role):
        if binding.text_sha256 != sha256(text.encode("utf-8")).hexdigest():
            raise ValueError(f"grammar {role} audio text drift")
        path = media_paths.get(binding.artifact_sha256)
        if path is None or not path.is_file() or path.is_symlink():
            raise ValueError(f"grammar {role} audio file missing or unsafe")
        if not 0 < path.stat().st_size <= 20_000_000 or sha256(path.read_bytes()).hexdigest() != binding.artifact_sha256:
            raise ValueError(f"grammar {role} audio bytes drift")
        if (path.suffix.lower() not in {".mp3", ".wav", ".ogg"}
                or path.name != path.name.strip()
                or any(not (c.isalnum() or c in "._- ") for c in path.name)):
            raise ValueError("grammar audio basename is unsafe")
        # The approved Korean Azure profile produces MP3. Receipts cannot turn
        # truncated or undecodable bytes into learner-ready audio.
        measured = inspect_local_mp3(path) if path.suffix.lower() == ".mp3" else None
        if measured is None or measured.artifact_sha256 != binding.artifact_sha256:
            raise ValueError("grammar audio must be decodable MP3")
        tag = f"[sound:{path.name}]"
        if tag in media_index and media_index[tag] != path:
            raise ValueError("grammar audio basename collision")
        media_index[tag] = path
        profiles.add(binding.voice_profile_sha256)
        return tag

    for entry in sorted(bundle.lexical_bootstrap, key=lambda entry: entry.sequence):
        card = teaching[entry.entry_id]
        if (entry.content_hash != grammar_content_hash(entry)
                or card.bootstrap_sha256 != entry.content_hash
                or entry.source_binding.content_hash != grammar_content_hash(entry.source_binding)
                or card.review_binding.source_sha256 != entry.source_binding.content_hash
                or card.review_binding.curriculum_sha256 != bundle.bundle_sha256):
            raise ValueError("bootstrap source or curriculum review drift")
        rows.append(ExportCardRow(
            identity=ExportCardIdentity(language=SupportedLanguage.KO, source_type="korean-grammar", job_id=job_id,
                item_key=entry.entry_id, lemma_key=entry.target_concept_id, sort_index=len(rows) + 1),
            word=escape(entry.canonical_nfc), front_of_card=escape(entry.canonical_nfc), ipa=escape(card.ipa),
            definitions=escape(card.definitions), example_sentence=escape(card.example_sentence),
            translation=escape(card.portuguese_translation),
            word_audio=include_media(card.word_media_binding, entry.canonical_nfc, "word"),
            sentence_audio=include_media(card.sentence_media_binding, card.example_sentence, "sentence"),
        ))
    orientation_ids = {entry.entry_id for entry in bundle.orientation_entries}
    for entry in (*bundle.orientation_entries, *bundle.grammar_entries):
        review = entry.review_binding
        bindings = (entry.source_binding, review, entry.word_media_binding, entry.sentence_media_binding)
        if any(binding.content_hash != grammar_content_hash(binding) for binding in bindings):
            raise ValueError("grammar review binding content drift")
        if (review.candidate_sha256 != grammar_candidate_sha256(entry)
                or review.source_sha256 != entry.source_binding.content_hash
                or review.curriculum_sha256 != grammar_review_curriculum_sha256(bundle)
                or review.media_sha256 != korean_grammar_canonical_json_sha256([
                    entry.word_media_binding.content_hash, entry.sentence_media_binding.content_hash])):
            raise ValueError("grammar review is stale for content, source, curriculum or media")
        sounds = {}
        for role, binding, text in (
            ("word", entry.word_media_binding, entry.spoken_sample),
            ("sentence", entry.sentence_media_binding, entry.example_sentence),
        ):
            sounds[role] = include_media(binding, text, role)
        definitions = "<br>".join(
            f"<b>{label}:</b> {escape(value)}" for label, value in (
                ("Função", entry.function), ("Uso", entry.attachment_rule),
                ("Registro", entry.register), ("Pronúncia", entry.pronunciation_sample),
                ("Áudio", entry.spoken_sample),
            )
        )
        if entry.entry_id in orientation_ids:
            definitions = "<b>Introdução guiada</b><br>" + definitions
        rows.append(ExportCardRow(
            identity=ExportCardIdentity(
                language=SupportedLanguage.KO, source_type="korean-grammar", job_id=job_id,
                item_key=entry.entry_id, lemma_key=entry.target_concept_id,
                sort_index=(len(rows) + 1 if bundle.orientation_entries
                    else len(bundle.lexical_bootstrap) + entry.sequence),
            ),
            word=escape(entry.form), front_of_card=escape(entry.form), definitions=definitions,
            example_sentence=escape(entry.example_sentence), translation=escape(entry.portuguese_translation),
            word_audio=sounds["word"], sentence_audio=sounds["sentence"],
        ))
    if len(profiles) != 1:
        raise ValueError("grammar audio voice profile drift")
    return KoreanGrammarExportRows(rows=rows, media_index=media_index, bundle_sha256=bundle.bundle_sha256)
