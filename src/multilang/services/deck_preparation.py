"""Offline, evidence-preserving handoff before any content or deck generation.

These are reviewable vocabulary inventories, not approved datasets. This module
has no model, provider, database, audio or Anki dependencies and cannot generate
cards. Existing lexical decisions remain source evidence, never new approval.
"""

from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_preparation import _OutputBudget
from multilang.services.vocabulary_review import _read_bytes
from multilang.services.vocabulary_sources import (
    CorpusSentence,
    LexicalSenseCandidate,
    SourceLimits,
    _verified_lines,
)


class FileReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class VocabularyInput(FileReference):
    kind: Literal["candidates", "korean_inventory", "latin_inventory"] = "candidates"


class LanguagePreparationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    language: SupportedLanguage
    sources: tuple[VocabularyInput, ...] = Field(min_length=1, max_length=32)
    priority: FileReference | None = None
    evidence: tuple[FileReference, ...] = Field(default=(), max_length=64)
    diagnostic_corpora: tuple[FileReference, ...] = Field(default=(), max_length=8)
    notes: tuple[str, ...] = Field(default=(), max_length=32)


class DeckPreparationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    schema_version: Literal["deck-preparation-request-1"] = "deck-preparation-request-1"
    languages: tuple[LanguagePreparationInput, ...] = Field(min_length=1, max_length=23)
    expected_languages: tuple[SupportedLanguage, ...] = tuple(SupportedLanguage)
    historical_reviews: tuple[FileReference, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def complete_language_coverage(self):
        actual = [item.language for item in self.languages]
        if (
            len(set(actual)) != len(actual)
            or len(set(self.expected_languages)) != len(self.expected_languages)
            or set(actual) != set(self.expected_languages)
        ):
            raise ValueError("language coverage must match the declared inventory exactly")
        return self


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _key(value: str) -> str:
    # Selection lookup only; stored lemmas/POS/senses are never casefold-merged.
    return _nfc(value).casefold()


def _reference(reference: FileReference) -> dict:
    return {"path": str(reference.path), "sha256": reference.sha256}


def _read_json(reference: FileReference, *, limit: int = 32 * 1024**2):
    return json.loads(_read_bytes(reference.path, reference.sha256, limit=limit))


def _candidate_rows(source: VocabularyInput, language: str, limits: SourceLimits):
    if source.kind == "latin_inventory":
        data = _read_json(source)
        if language != "la" or data.get("language_code") != "la":
            raise ValueError("Latin source language mismatch")
        for row in data["entries"]:
            yield {
                "language": "la",
                "lemma": row["lemma"],
                "pos": row.get("morphology_evidence", {}).get("part_of_speech", "X"),
                "candidate_id": row["item_key"],
                "source_record_sha256": canonical_sha256(row),
                "glosses": [],
                "forms": [{"form": row["target_form"], "tags": ["existing-latin-target"]}],
                "existing_source_state": {
                    key: row.get(key)
                    for key in ("sequence", "frequency_rank", "inclusion_status", "license_gate")
                },
            }
        return
    for line in _verified_lines(source.path, source.sha256, limits):
        row = json.loads(line)
        if row.get("language") != language:
            raise ValueError("candidate source language mismatch")
        if source.kind == "korean_inventory":
            if language != "ko":
                raise ValueError("Korean source language mismatch")
            identity = row["lexical_identity"]
            yield {
                "language": "ko",
                "lemma": identity["lemma"],
                "pos": identity["part_of_speech"],
                "candidate_id": "existing-korean:" + canonical_sha256(identity),
                "source_record_sha256": canonical_sha256(row),
                "source_sense_ids": [identity["sense_id"]],
                "glosses": [],
                "existing_source_state": {
                    key: row.get(key)
                    for key in (
                        "final_rank",
                        "source_rank",
                        "curation_decision",
                        "license_decision",
                    )
                },
            }
        else:
            yield LexicalSenseCandidate.model_validate(row).model_dump(mode="json")


def _load_priorities(reference: FileReference | None):
    by_form: dict[str, int] = {}
    by_candidate: dict[str, int] = {}
    if reference is None:
        return by_form, by_candidate, {"status": "missing"}
    data = _read_json(reference)
    if data.get("test_corpus_used") is True:
        raise ValueError("test corpus cannot supply vocabulary priority")
    rows = data["rows"]
    if not isinstance(rows, list) or len(rows) > 100_000:
        raise ValueError("priority record limit exceeded")
    seen_ranks = set()
    for row in rows:
        rank, form = row["rank"], row["form"]
        if type(rank) is not int or rank < 1 or rank in seen_ranks:
            raise ValueError("priority ranks must be unique positive integers")
        if not isinstance(form, str) or not 0 < len(form) <= 512:
            raise ValueError("priority form is outside bounds")
        seen_ranks.add(rank)
        key = _key(form)
        by_form[key] = min(rank, by_form.get(key, rank))
        for candidate_id in row.get("candidate_ids", []):
            by_candidate[candidate_id] = min(rank, by_candidate.get(candidate_id, rank))
    return (
        by_form,
        by_candidate,
        {
            **_reference(reference),
            "source": data.get("source"),
            "rows": len(rows),
            "status": "source_surface_priority_not_lemma_or_sense_frequency",
        },
    )


def _sentence_policy(language: str) -> dict:
    return {
        "version": "sentence-curriculum-draft-1",
        "status": "draft_requires_curriculum_review",
        "known_vocabulary_basis": "previously_introduced_not_observed_mastery",
        "known_identity_ids": [],
        "bootstrap_identity_ids": [],
        "bootstrap_status": "requires_review",
        "grammar_prerequisites_status": "requires_review",
        "goal": "one_target_concept_with_minimal_incidental_new_concepts",
        "unqualified_analysis_action": "review_required",
        "length_unit": (
            "analyzer_units_pending_calibration"
            if language in {"ja", "zh"}
            else "approximate_lexical_tokens"
        ),
        "current_frequency_length": None if language in {"ja", "zh", "la"} else [4, 12],
        "increase_length_automatically_by_level": False,
        "existing_korean_curricula_preserved": language == "ko",
        "foundation_and_highlight_paths": "separate",
        "enabled_for_generation": False,
    }


def _review_index(request: DeckPreparationRequest):
    result = {}
    for reference in request.historical_reviews:
        data = _read_json(reference)
        for group in data.get("languages", []):
            language = group.get("language")
            for item in group.get("items", []):
                candidate_id = item.get("item_id", "").removeprefix("lexical:")
                result[(language, candidate_id)] = {
                    "report": _reference(reference),
                    "decision": item,
                    "status": "historical_machine_review_not_new_approval",
                }
    return result


def _diagnostic_coverage(inputs: LanguagePreparationInput, lemmas: set[str], limits):
    """Dictionary availability on annotated test data, never final deck coverage."""
    counts = Counter()
    missing = Counter()
    seen_files = set()
    seen_sentences = set()
    used_sources = []
    for source in inputs.diagnostic_corpora:
        if source.sha256 in seen_files:
            continue
        seen_files.add(source.sha256)
        used_sources.append(_reference(source))
        for line in _verified_lines(source.path, source.sha256, limits):
            sentence = CorpusSentence.model_validate_json(line)
            if sentence.language != inputs.language:
                raise ValueError("diagnostic corpus language mismatch")
            key = (sentence.source_sha256, sentence.document_id, sentence.sentence_id)
            if key in seen_sentences:
                continue
            seen_sentences.add(key)
            for token in sentence.tokens:
                if token.pos in {"PUNCT", "SYM"}:
                    counts["excluded_punctuation_or_symbol_tokens"] += 1
                    continue
                counts["lexical_tokens"] += 1
                if not token.lemma or token.lemma == "_":
                    counts["missing_lemma_annotation_tokens"] += 1
                elif _nfc(token.lemma) in lemmas:
                    counts["matched_tokens"] += 1
                else:
                    missing[_nfc(token.lemma)] += 1
    return {
        "status": "diagnostic_only" if used_sources else "not_available",
        "sources": used_sources,
        "matching": "NFC_exact_lemma_case_and_diacritics_preserved",
        "inventory": "all_unreviewed_lemma_candidates_not_final_deck",
        "general_language_coverage": False,
        "sense_reading_or_morphology_accuracy_measured": False,
        "used_for_ranking": False,
        "corpus_representativeness": "not_established",
        "sentence_count": len(seen_sentences),
        **{
            key: counts[key]
            for key in (
                "lexical_tokens",
                "matched_tokens",
                "missing_lemma_annotation_tokens",
                "excluded_punctuation_or_symbol_tokens",
            )
        },
        "percent": (
            round(counts["matched_tokens"] * 100 / counts["lexical_tokens"], 3)
            if counts["lexical_tokens"]
            else None
        ),
        "most_frequent_missing_lemmas": [
            {"lemma": lemma, "tokens": count} for lemma, count in missing.most_common(100)
        ],
    }


def _prepare_language(inputs: LanguagePreparationInput, destination: Path, reviews: dict, budget):
    language = inputs.language.value
    limits = SourceLimits(max_bytes=1024**3, max_output_bytes=512 * 1024**2)
    for evidence in inputs.evidence:
        _read_bytes(evidence.path, evidence.sha256, limit=32 * 1024**2)
    ranks, candidate_ranks, priority_info = _load_priorities(inputs.priority)
    groups: dict[tuple[str, str], dict] = {}
    forms: dict[str, dict] = {}
    seen: dict[str, str] = {}
    counts: Counter = Counter()
    inflections = []

    def add_form(form, *, parent_ids, candidate_id, tags=(), parent_lemmas=()):
        form = _nfc(form)
        key = canonical_sha256([form, sorted(tags), sorted(parent_ids), sorted(parent_lemmas)])
        if key not in forms:
            forms[key] = {
                "form_id": key,
                "form": form,
                "tags": sorted(set(tags)),
                "parent_entry_ids": sorted(set(parent_ids)),
                "source_parent_lemmas": sorted(set(parent_lemmas)),
                "evidence_candidate_ids": set(),
                "selected_for_card": False,
                "review_status": "important_form_review_required",
            }
        forms[key]["evidence_candidate_ids"].add(candidate_id)

    for source in inputs.sources:
        for row in _candidate_rows(source, language, limits):
            candidate_id = row["candidate_id"]
            digest = canonical_sha256(row)
            if candidate_id in seen:
                if seen[candidate_id] != digest:
                    raise ValueError("conflicting candidate identity across sources")
                counts["duplicate_candidates_removed"] += 1
                continue
            seen[candidate_id] = digest
            if len(seen) > limits.max_records:
                raise ValueError("candidate record limit exceeded")
            counts["source_candidate_count"] += 1
            if row.get("kind") == "inflection":
                inflections.append(row)
                counts["inflection_record_count"] += 1
                continue
            lemma, pos = _nfc(row["lemma"]), row["pos"]
            group_key = (lemma, pos)
            if group_key not in groups:
                groups[group_key] = {
                    "entry_id": "lemma-group:" + canonical_sha256([language, lemma, pos]),
                    "lemma": lemma,
                    "pos": pos,
                    "sense_candidates": [],
                    "readings": [],
                    "source_priority": None,
                    "selected_sense_id": None,
                    "selected_for_generation": False,
                    "final_frequency_rank": None,
                    "review_status": "pending",
                    "review_reasons": ["sense_selection_required"],
                }
            entry = groups[group_key]
            counts["lexical_candidate_count"] += 1
            if (
                pos in {"X", "unknown", ""}
                and "part_of_speech_unresolved" not in entry["review_reasons"]
            ):
                entry["review_reasons"].append("part_of_speech_unresolved")
            if language == "zh" and "mandarin_scope_review_required" not in entry["review_reasons"]:
                entry["review_reasons"].append("mandarin_scope_review_required")
            sense = {
                key: row.get(key, [] if key in {"source_sense_ids", "glosses", "tags"} else None)
                for key in (
                    "candidate_id",
                    "source_record_sha256",
                    "source_sense_ids",
                    "glosses",
                    "tags",
                    "stable_sense_id",
                )
            }
            sense["review_status"] = "pending"
            if "existing_source_state" in row:
                sense["existing_source_state"] = row["existing_source_state"]
            old_review = reviews.get((language, candidate_id))
            if old_review:
                decision = old_review["decision"]
                if (
                    decision.get("original_lemma") == row["lemma"]
                    and decision.get("original_pos") == pos
                ):
                    sense["historical_review"] = old_review
                    counts["historical_reviews_linked"] += 1
            entry["sense_candidates"].append(sense)
            source_ranks = [
                ranks.get(_key(lemma)),
                candidate_ranks.get(candidate_id),
                entry["source_priority"],
            ]
            for form in row.get("forms", []):
                value = form.get("form")
                tags = form.get("tags", [])
                if (
                    not isinstance(value, str)
                    or not value
                    or any(tag in tags for tag in ("table-tags", "inflection-template"))
                ):
                    continue
                if form.get("reading"):
                    reading = {
                        "form": _nfc(value),
                        "reading": _nfc(form["reading"]),
                        "candidate_id": candidate_id,
                    }
                    if reading not in entry["readings"]:
                        entry["readings"].append(reading)
                source_ranks.append(ranks.get(_key(value)))
                if _nfc(value) != lemma:
                    add_form(
                        value, parent_ids=[entry["entry_id"]], candidate_id=candidate_id, tags=tags
                    )
            available = [rank for rank in source_ranks if rank is not None]
            entry["source_priority"] = min(available) if available else None
    by_lemma = defaultdict(list)
    for (lemma, _), entry in groups.items():
        by_lemma[lemma].append(entry)
    for row in inflections:
        parents = []
        for parent in row.get("form_of", []):
            for entry in by_lemma.get(_nfc(parent), []):
                if row["pos"] in {entry["pos"], "X"}:
                    parents.append(entry)
        for entry in parents:
            rank = ranks.get(_key(row["lemma"]))
            if rank is not None:
                entry["source_priority"] = min(rank, entry["source_priority"] or rank)
        add_form(
            row["lemma"],
            parent_ids=[entry["entry_id"] for entry in parents],
            candidate_id=row["candidate_id"],
            tags=row.get("tags", []),
            parent_lemmas=row.get("form_of", []),
        )
    entries = sorted(
        groups.values(),
        key=lambda e: (
            e["source_priority"] is None,
            e["source_priority"] or 0,
            e["lemma"],
            e["pos"],
            e["entry_id"],
        ),
    )
    for order, entry in enumerate(entries, 1):
        entry["provisional_order"] = order
        entry["proposed_band"] = (
            f"core-{(order - 1) // 1000 + 1}"
            if order <= 3000
            else f"expansion-{(order - 3001) // 1000 + 1}"
        )
        entry["sense_candidates"].sort(key=lambda s: s["candidate_id"])
        entry["readings"].sort(key=lambda r: (r["form"], r["reading"], r["candidate_id"]))
    coverage = {
        "target_percent": 90,
        "status": "not_measured_on_final_inventory",
        "spoken_percent": None,
        "written_percent": None,
        "target_achieved": None,
        "reason": "reviewed_inventory_and_independent_representative_corpora_required",
    }
    vocabulary = {
        "schema_version": "deck-vocabulary-preparation-1",
        "language": language,
        "path": "classical_latin" if language == "la" else "modern_frequency",
        "status": "prepared_for_review",
        "production_eligible": False,
        "generation_status": "deferred_by_user",
        "sources": [s.model_dump(mode="json") for s in inputs.sources],
        "evidence": [_reference(e) for e in inputs.evidence],
        "notes": inputs.notes,
        "ordering": {
            "policy": "lowest_attested_surface_priority_then_exact_lemma_pos",
            "source": priority_info,
            "reviewed_curriculum": False,
            "sense_counts_aggregated": False,
            "test_corpus_used": False,
            "bands_are_provisional_lemma_groups_not_selected_senses": True,
        },
        "sentence_policy": _sentence_policy(language),
        "coverage": coverage,
        "entries": entries,
    }
    report = {
        "language": language,
        "status": "prepared_for_review",
        **dict(counts),
        "lemma_group_count": len(entries),
        "distinct_lemma_count": len(by_lemma),
        "possible_form_count": len(forms),
        "selected_additional_form_count": 0,
        "ambiguous_lemma_group_count": sum(len(e["sense_candidates"]) > 1 for e in entries),
        "unranked_lemma_group_count": sum(e["source_priority"] is None for e in entries),
        "coverage": coverage,
        "diagnostic_lemma_availability": _diagnostic_coverage(inputs, set(by_lemma), limits),
        "production_eligible": False,
        "generation_status": "deferred_by_user",
        "provider_calls_executed": 0,
        "blockers": [
            "reviewed_sense_selection",
            "reviewed_frequency_and_curriculum",
            "independent_coverage_measurement",
            "important_form_selection",
            "sentence_policy_qualification",
            "user_deferred_generation",
        ],
    }
    destination.mkdir()
    budget.dump(destination / "vocabulary.json", vocabulary)
    with (destination / "forms.jsonl").open("w", encoding="utf-8") as handle:
        for ident in sorted(forms):
            form = forms[ident]
            form["evidence_candidate_ids"] = sorted(form["evidence_candidate_ids"])
            budget.write(handle, json.dumps(form, ensure_ascii=False, sort_keys=True) + "\n")
    budget.dump(destination / "report.json", report)
    return report


def prepare_deck_inputs(request: DeckPreparationRequest, *, output: Path) -> dict:
    output = Path(output).absolute()
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("output must not traverse symlinks")
    if output.exists():
        raise ValueError("preparation requires a new output path")
    reviews = _review_index(request)
    output.parent.mkdir(parents=True, exist_ok=True)
    budget = _OutputBudget(2 * 1024**3)
    with TemporaryDirectory(prefix=".deck-preparation-", dir=output.parent) as temporary:
        staging = Path(temporary) / "delivery"
        staging.mkdir()
        reports = [
            _prepare_language(item, staging / item.language.value, reviews, budget)
            for item in request.languages
        ]
        summary = {
            "schema_version": "deck-preparation-summary-1",
            "status": "prepared_for_review",
            "languages": reports,
            "language_count": len(reports),
            "generation": {
                "status": "deferred_by_user",
                "notify_before_generation": True,
                "provider_calls_executed": 0,
                "cards_generated": 0,
                "audio_generated": 0,
                "decks_generated": 0,
                "resume_requires_user_instruction": True,
            },
            "coverage_target_percent": 90,
            "production_eligible": False,
            "request_sha256": canonical_sha256(request.model_dump(mode="json")),
        }
        budget.dump(staging / "summary.json", summary)
        budget.dump(staging / "request.json", request.model_dump(mode="json"))
        lines = [
            "# Vocabulário preparado — geração adiada",
            "",
            "Os arquivos reutilizam lemas existentes e preservam sentidos alternativos e formas.",
            "A ordem é provisória. Nenhuma pendência virou aprovação automática.",
            "Não foram gerados textos novos de cartões, traduções, áudio ou decks.",
            "",
            "A cobertura de 90% continua uma meta. Fala e escrita ainda precisam de avaliação",
            "sobre a seleção final em corpora representativos independentes.",
            "",
            "| Idioma | Lemas distintos | Grupos lema/classe | Sentidos candidatos | Formas possíveis |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for report in reports:
            language = report["language"]
            lines.append(
                f"| [{language}]({language}/vocabulary.json) | {report['distinct_lemma_count']} | "
                f"{report['lemma_group_count']} | {report.get('lexical_candidate_count', 0)} | "
                f"{report['possible_form_count']} |"
            )
        lines += [
            "",
            "## Arquivos por idioma",
            "",
            "- `vocabulary.json`: lemas, possíveis sentidos, leituras, fontes e ordem provisória.",
            "- `forms.jsonl`: formas com vínculo aos lemas; não são cartões selecionados.",
            "- `report.json`: contagens, pendências e estado da cobertura.",
            "",
            "`sentence_policy` é a proposta para a próxima etapa. Seu currículo e sua validação",
            "ainda precisam ser qualificados; a preparação não ativa a geração automaticamente.",
            "",
            "O latim preserva seu percurso clássico. Kana, Hangul e highlights mantêm seus caminhos.",
            "",
            "Para retomar: revisar seleção/sentidos e currículo, qualificar as regras de frases,",
            "medir cobertura e então executar um piloto de conteúdo. A geração permanece adiada",
            "até nova instrução do usuário; nenhuma chave do .env está nestes arquivos.",
            "",
        ]
        with (staging / "README.md").open("w", encoding="utf-8") as handle:
            budget.write(handle, "\n".join(lines))
        checksums = {}
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                with path.open("rb") as handle:
                    checksums[str(path.relative_to(staging))] = hashlib.file_digest(
                        handle, "sha256"
                    ).hexdigest()
        budget.dump(
            staging / "manifest.json",
            {"schema_version": "deck-preparation-files-1", "files": checksums},
        )
        if output.exists():
            raise ValueError("preparation requires a new output path")
        os.rename(staging, output)
    return summary


def prepare_deck_inputs_file(request_path: Path, request_sha256: str, *, output: Path) -> dict:
    request = DeckPreparationRequest.model_validate_json(
        _read_bytes(request_path, request_sha256, limit=4 * 1024**2)
    )
    return prepare_deck_inputs(request, output=output)
