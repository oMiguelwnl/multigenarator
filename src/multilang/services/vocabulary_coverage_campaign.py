"""Offline, source-bound lexical coverage diagnostics; never a generation gate.

The counting unit is an annotated word occurrence, not a sense or a card.
Corpora already inspected for expansion cannot be used as untouched holdouts.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import groupby
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import Field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_selection_snapshot import snapshot_records
from multilang.services.vocabulary_sources import CorpusSentence, SourceLimits, _verified_lines

LEXICAL_POS = {
    "ADJ",
    "ADP",
    "ADV",
    "AUX",
    "CCONJ",
    "DET",
    "INTJ",
    "NOUN",
    "NUM",
    "PART",
    "PRON",
    "SCONJ",
    "VERB",
}


def nfc(value):
    return unicodedata.normalize("NFC", value) if value else ""


class CorpusSpec(NativeContract):
    language: SupportedLanguage
    label: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    format: Literal["reference-jsonl", "token-jsonl", "conllu"]
    modality: Literal["written", "spoken", "mixed"]
    role: Literal["diagnostic", "development", "holdout"] = "diagnostic"
    previously_inspected: bool = True
    version: str
    license: str
    limitations: tuple[str, ...] = ()
    provenance: dict = Field(default_factory=dict)
    annotation_compatible: bool = True
    corpus_id: str | None = None
    filter_genre: str | None = None
    token_misc_requirements: dict[str, str] = Field(default_factory=dict)
    token_field_filters: dict[str, str] = Field(default_factory=dict)
    deduplicate_analysis_variants: bool = False

    @model_validator(mode="after")
    def untouched(self):
        if self.role == "holdout" and self.previously_inspected:
            raise ValueError("previously inspected corpus cannot be a holdout")
        return self


@dataclass
class SelectionIndex:
    keys: dict = field(default_factory=lambda: defaultdict(set))
    lemmas: set = field(default_factory=set)
    lemma_units: dict = field(default_factory=lambda: defaultdict(set))
    dispositions: dict = field(default_factory=lambda: defaultdict(set))
    source_refs: dict = field(default_factory=lambda: defaultdict(list))
    units: Counter = field(default_factory=Counter)


def build_index(rows):
    index = SelectionIndex()
    seen = set()
    for row in rows:
        lang, uid, decision = row["language"], row["review_unit_id"], row["decision"]
        if (lang, uid) in seen:
            raise ValueError("duplicate review unit")
        seen.add((lang, uid))
        index.units[lang, decision] += 1
        source = row.get("source_group") or {}
        lemma = nfc(source.get("lemma"))
        index.dispositions[lang, lemma].add(decision)
        index.source_refs[lang, lemma].append(
            {
                "review_unit_id": uid,
                "session_id": row.get("session_id"),
                "source_pos": source.get("pos"),
                "decision": decision,
                "source_binding": row.get("source_binding"),
            }
        )
        if decision != "include":
            continue
        addition = row.get("supplemental_identity")
        if addition:
            evidence = (
                addition.get("source_evidence")
                or addition.get("evidence")
                or (
                    addition.get("source_lexical_identifiers")
                    if addition.get("evidence_ids")
                    else None
                )
            )
            if (
                addition.get("decision") != "accepted_in_preparation_version"
                or not evidence
                or not all(e.get("url") for e in evidence)
            ):
                raise ValueError("addition requires source evidence")
            candidates = [addition]
        else:
            review = row.get("imported_review") or {}
            selected = set(review.get("selected_candidate_ids", []))
            available = {c["candidate_id"] for c in source.get("sense_candidates", [])}
            resolved = row.get("resolved_content")
            if resolved:
                candidates = [
                    c for c in resolved["resolved_candidates"] if c["disposition"] == "retained"
                ]
                if any(c["source_candidate_id"] not in available for c in candidates):
                    raise ValueError("resolved candidate outside source")
                if not candidates:
                    raise ValueError("derived include requires retained source candidates")
                for identity in resolved.get("derived_identities", []):
                    parents = set(identity.get("source_candidate_ids", []))
                    if not parents or not parents <= available or not identity.get("evidence"):
                        raise ValueError("derived identity requires bound source evidence")
                    candidates.append(identity)
            else:
                if not selected or not selected <= available:
                    raise ValueError("include requires selected source candidates")
                candidates = [{"lemma": lemma, "pos": review.get("pos") or source["pos"]}]
        for candidate in candidates:
            key = (lang, nfc(candidate["lemma"]), candidate["pos"])
            index.keys[key].add(uid)
            index.lemmas.add(key[:2])
            index.lemma_units[key[:2]].add(uid)
    return index


def build_preparation_index(rows):
    """Index validated finalization identities, one contiguous language at a time.

    ``snapshot_records`` emits ordered language groups. Reject a repeated group
    rather than silently losing cross-fragment evidence. Consolidation validates
    all parent/form bindings and adapts documentary resolutions before indexing.
    Source-specific identities may share a lemma/POS key for this diagnostic;
    that is not a cross-dictionary sense merge or a comprehension measurement.
    """
    from multilang.services.vocabulary_finalization import consolidate

    index = SelectionIndex()
    seen_languages = set()
    for lang, language_rows in groupby(rows, key=lambda row: row["language"]):
        if lang in seen_languages:
            raise ValueError("preparation inventory repeats a language group")
        seen_languages.add(lang)
        result = consolidate(language_rows, language=lang)
        pending = set(result["pending_review_units"]) | set(result["partially_unresolved_units"])
        findings = {r["review_unit_id"]: r for r in result["preparation_findings"]}
        for row in result["snapshot_rows"]:
            uid, decision = row["review_unit_id"], row["decision"]
            source = row.get("source_group") or row.get("supplemental_identity") or {}
            lemma = nfc(source.get("lemma"))
            index.units[lang, decision] += 1
            index.dispositions[lang, lemma].add(decision)
            if uid in pending:
                index.dispositions[lang, lemma].add("uncertain")
            index.source_refs[lang, lemma].append(
                dict(
                    review_unit_id=uid,
                    session_id=row.get("session_id"),
                    source_pos=source.get("pos"),
                    decision=decision,
                    source_binding=row.get("source_binding"),
                    preparation_pending=uid in pending,
                    preparation_findings=findings.get(uid),
                )
            )
        for identity in result["identities"]:
            if identity["pos"] not in LEXICAL_POS:
                continue
            key = (lang, nfc(identity["lemma"]), identity["pos"])
            index.keys[key].update(identity["review_unit_ids"])
            index.lemmas.add(key[:2])
            index.lemma_units[key[:2]].update(identity["review_unit_ids"])
        del result
    return index


def _exclude(row):
    kind = row.get("kind", row.get("token_kind", "word"))
    if row.get("pos") in {"PUNCT", "SYM"} or kind in {"punctuation", "symbol"}:
        return "punctuation"
    if kind in {
        "silent_pause",
        "filled_pause",
        "incomplete_word",
        "transcription_marker",
        "nonlexical_event",
    }:
        return "speech_event"
    if kind not in {"word", "source_word_or_punctuation"}:
        raise ValueError("unsupported token kind")
    if row.get("pos") == "PROPN":
        return "proper_name"
    form = row.get("form") or ""
    if any(c.isdigit() for c in form) and not any(c.isalpha() for c in form):
        return "numeric_notation"
    return None


def measure(index, language, tokens, *, role="diagnostic", links=()):
    if role not in {"diagnostic", "development", "holdout"}:
        raise ValueError("invalid corpus role")
    aliases = defaultdict(list)
    for link in links:
        target = (language, nfc(link["target_lemma"]), link["target_pos"])
        if target not in index.keys:
            raise ValueError("annotation link target absent from selected inventory")
        if not target[1] or target[2] not in LEXICAL_POS:
            raise ValueError("annotation link target requires resolved lexical POS")
        if not set(link.get("required_review_units", [])) <= index.keys[target]:
            raise ValueError("annotation link has stale target review binding")
        if not link.get("evidence_id"):
            raise ValueError("annotation link needs evidence")
        restrictions = link.get("restrictions", {})
        if not isinstance(restrictions, dict) or any(
            k not in {"form", "corpus_label", "corpus_id", "original_pos"}
            or not isinstance(values, (list, tuple))
            or not values
            or any(not isinstance(v, str) for v in values)
            for k, values in restrictions.items()
        ):
            raise ValueError("invalid annotation restriction")
        aliases[nfc(link["lemma"]), link["pos"]].append(link)
    counts = Counter(
        {
            k: 0
            for k in (
                "denominator",
                "exact_matches",
                "lemma_matches",
                "compatible_matches",
                "excluded_punctuation",
                "excluded_proper_name",
                "excluded_numeric_notation",
                "excluded_speech_event",
                "total_occurrences",
            )
        }
    )
    gaps, seen = {}, set()
    for row in tokens:
        occurrence = tuple(str(row[k]) for k in ("document_id", "sentence_id", "token_id"))
        if occurrence in seen:
            raise ValueError("duplicate occurrence")
        seen.add(occurrence)
        counts["total_occurrences"] += 1
        excluded = _exclude(row)
        if excluded:
            counts["excluded_" + excluded] += 1
            continue
        counts["denominator"] += 1
        lemma, pos = nfc(row.get("lemma")), row.get("pos")
        key = (language, lemma, pos)
        if key[:2] in index.lemmas:
            counts["lemma_matches"] += 1
        if lemma and pos in LEXICAL_POS and key in index.keys:
            counts["exact_matches"] += 1
            counts["compatible_matches"] += 1
            continue
        matched = any(
            all(row.get(k) in values for k, values in link.get("restrictions", {}).items())
            for link in aliases[lemma, pos]
        )
        if matched:
            counts["compatible_matches"] += 1
            continue
        if not lemma or lemma == "_" or pos not in LEXICAL_POS:
            category = "missing_annotation"
        elif language == "ko" and "+" in lemma:
            category = "annotation_structure"
        elif key[:2] in index.lemmas:
            category = "pos_mismatch"
        elif index.dispositions[key[:2]] & {"unreviewed", "uncertain"}:
            category = "pending_review"
        elif index.dispositions[key[:2]] & {"exclude", "quarantined"}:
            category = "previously_excluded"
        else:
            category = "candidate_absent"
        counts["gap_" + category] += 1
        if role == "holdout":
            continue
        gapkey = (lemma, pos, category)
        gap = gaps.setdefault(
            gapkey,
            {
                "language": language,
                "lemma": lemma or None,
                "pos": pos,
                "category": category,
                "occurrences": 0,
                "documents": set(),
                "examples": [],
                "decision": "needs_review",
                "frequency_rank": None,
                "existing_lemma_units": sorted(index.lemma_units[key[:2]]),
                "source_review_units": index.source_refs[key[:2]],
            },
        )
        gap["occurrences"] += 1
        gap["documents"].add(occurrence[0])
        if len(gap["examples"]) < 3:
            gap["examples"].append(
                {
                    "document_id": occurrence[0],
                    "sentence_id": occurrence[1],
                    "token_id": occurrence[2],
                    "form": row.get("form"),
                }
            )
    for gap in gaps.values():
        gap["documents"] = len(gap["documents"])
    ordered = sorted(
        gaps.values(),
        key=lambda g: (-g["occurrences"], -g["documents"], g["lemma"] or "", g["pos"] or ""),
    )
    denominator = counts["denominator"]
    return {
        "language": language,
        "role": role,
        "counts": dict(counts),
        **{
            label + "_percent": round(100 * counts[field] / denominator, 4) if denominator else None
            for label, field in (
                ("exact", "exact_matches"),
                ("lemma", "lemma_matches"),
                ("compatible", "compatible_matches"),
            )
        },
        "counting_unit": "annotated lexical word occurrence; NFC lemma and UPOS",
        "coverage_90_percent_verified": False,
        "production_eligible": False,
        "generation_status": "deferred_by_user",
        "gaps": ordered,
    }


def _conllu_tokens(spec, lines, limits):
    document, sentence, genre = "source-" + spec.sha256, None, None
    rows, variants = [], set()

    def emit():
        if not rows or (spec.filter_genre and genre != spec.filter_genre):
            return []
        signature = tuple((r["form"], r["lemma"]) for r in rows)
        if spec.deduplicate_analysis_variants:
            if signature in variants:
                return []
            variants.add(signature)
        return rows

    for line in lines:
        line = line.rstrip("\r\n")
        if not line:
            yield from emit()
            rows, sentence, genre = [], None, None
        elif line.startswith("#"):
            key, sep, value = line[1:].strip().partition(" = ")
            if sep:
                if key == "newdoc id":
                    document = value
                elif key == "sent_id":
                    sentence = value
                elif key == "genre":
                    genre = value
        else:
            cols = line.split("\t")
            if len(cols) != 10:
                raise ValueError("CoNLL-U row requires ten columns")
            if "-" in cols[0] or "." in cols[0]:
                continue
            if not cols[0].isdigit() or not sentence:
                raise ValueError("CoNLL-U requires word ID and explicit sentence ID")
            misc = dict(x.split("=", 1) for x in cols[9].split("|") if "=" in x)
            if any(misc.get(k) != v for k, v in spec.token_misc_requirements.items()):
                continue
            rows.append(
                {
                    "document_id": document,
                    "sentence_id": sentence,
                    "token_id": cols[0],
                    "form": cols[1],
                    "lemma": None if cols[2] == "_" else cols[2],
                    "pos": None if cols[3] == "_" else cols[3],
                    "original_pos": cols[4],
                    "corpus_id": spec.corpus_id,
                    "kind": "word",
                }
            )
            if len(rows) > limits.max_tokens_per_sentence:
                raise ValueError("sentence token limit exceeded")
    yield from emit()


def corpus_tokens(spec, *, limits=None):
    """Exhaust this iterator: the shared bounded reader verifies mutation at EOF."""
    limits = limits or SourceLimits()
    lines = _verified_lines(Path(spec.path), spec.sha256, limits)
    if spec.format == "conllu":
        yield from _conllu_tokens(spec, lines, limits)
        return
    count = 0
    for line in lines:
        row = json.loads(line)
        if spec.format == "reference-jsonl":
            sentence = CorpusSentence.model_validate(row)
            if sentence.language != spec.language:
                raise ValueError("corpus language differs from specification")
            if len(sentence.tokens) > limits.max_tokens_per_sentence:
                raise ValueError("sentence token limit exceeded")
            for token in sentence.tokens:
                count += 1
                if count > limits.max_records:
                    raise ValueError("corpus record limit exceeded")
                yield {
                    "document_id": sentence.document_id,
                    "sentence_id": sentence.sentence_id,
                    "token_id": str(token.index),
                    "form": token.text,
                    "lemma": token.lemma,
                    "pos": token.pos,
                    "kind": "word",
                }
        else:
            if any(row.get(k) != v for k, v in spec.token_field_filters.items()):
                continue
            if row.get("language", spec.language.value) != spec.language.value:
                raise ValueError("corpus language differs from specification")
            if any(row.get(k) in (None, "") for k in ("document_id", "sentence_id", "token_id")):
                raise ValueError("token lacks occurrence identity or form")
            kind = row.get("kind", row.get("token_kind", "word"))
            if not isinstance(row.get("form"), str) or (
                not row["form"] and kind != "transcription_marker"
            ):
                raise ValueError("token lacks form outside transcription marker")
            count += 1
            if count > limits.max_records:
                raise ValueError("corpus record limit exceeded")
            yield row


def validate_corpora(corpora, *, exposed_hashes=()):
    identifiers = set()
    exposed = set(exposed_hashes) | {c.sha256 for c in corpora if c.role != "holdout"}
    for corpus in corpora:
        key = (corpus.language, corpus.label)
        if key in identifiers:
            raise ValueError("duplicate corpus label")
        identifiers.add(key)
        if corpus.role == "holdout" and corpus.sha256 in exposed:
            raise ValueError("holdout reuses exposed source")


class OverlapGuard:
    """Conservative sentence-content overlap check, independent of document IDs.

    This catches identical token sequences, not paraphrases or related documents.
    A successful check alone never proves independence or representativeness.
    """

    def __init__(self):
        self.roles = defaultdict(set)

    def observe(self, language, role, tokens):
        previous, forms = None, []

        def check():
            if not forms:
                return
            digest = hashlib.sha256(json.dumps(forms, ensure_ascii=False).encode()).hexdigest()
            roles = self.roles[language, digest]
            if roles and (
                (role == "holdout" and roles != {"holdout"})
                or (role != "holdout" and "holdout" in roles)
            ):
                raise ValueError("holdout sentence overlap with exposed corpus")
            roles.add(role)

        for row in tokens:
            key = (row["document_id"], row["sentence_id"])
            if previous is not None and previous != key:
                check()
                forms = []
            previous = key
            forms.append(nfc(row["form"]))
            yield row
        check()


def _write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run_campaign(config_path, config_sha256, output, *, progress=None):
    """Publish a new immutable run only after every input passes validation."""
    config = json.loads(_read_bytes(_plain_path(config_path), expected=config_sha256))
    inventory_format = config.get("inventory_format", "selection-snapshot")
    if inventory_format not in {"selection-snapshot", "finalization-snapshot"}:
        raise ValueError("unsupported inventory format")
    snapshot = _plain_path(Path(config["snapshot"]))
    manifest = json.loads(
        _read_bytes(snapshot / "manifest.json", expected=config["snapshot_manifest_sha256"])
    )
    corpora = [CorpusSpec.model_validate(c) for c in config["corpora"]]
    validate_corpora(corpora, exposed_hashes=config.get("exposed_hashes", []))
    evidence = config.get("evidence", {})
    for reference in evidence.values():
        _read_bytes(_plain_path(Path(reference["path"])), expected=reference["sha256"])
    for links in config.get("links", {}).values():
        if any(link.get("evidence_id") not in evidence for link in links):
            raise ValueError("annotation link requires bound evidence file")
    index_builder = (
        build_preparation_index if inventory_format == "finalization-snapshot" else build_index
    )
    index = index_builder(snapshot_records(snapshot))
    destination = _plain_path(output)
    if destination.exists():
        raise ValueError("output already exists; choose a new version")
    destination.parent.mkdir(parents=True, exist_ok=True)
    overlap = OverlapGuard()
    with TemporaryDirectory(prefix=".coverage-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "result"
        stage.mkdir()
        _write(stage / "config.json", config)
        results = []
        queues = defaultdict(list)
        for corpus in sorted(corpora, key=lambda c: c.role == "holdout"):
            lang = corpus.language.value
            if progress:
                progress(f"Evaluating {lang}/{corpus.label}")
            tokens = ({**t, "corpus_label": corpus.label} for t in corpus_tokens(corpus))
            result = measure(
                index,
                lang,
                overlap.observe(lang, corpus.role, tokens),
                role=corpus.role,
                links=config.get("links", {}).get(lang, []),
            )
            result["corpus"] = corpus.model_dump(mode="json")
            result["inventory_decisions"] = manifest["languages"][lang]
            result["interpretation"] = (
                "annotation_alignment_required"
                if not corpus.annotation_compatible
                else "partial_inventory_diagnostic"
                if manifest["languages"][lang].get("unreviewed")
                else "reviewed_inventory_diagnostic"
            )
            for gap in result["gaps"]:
                gap["corpus_label"] = corpus.label
                gap["corpus_sha256"] = corpus.sha256
                gap["review_task_id"] = hashlib.sha256(
                    json.dumps(
                        [
                            manifest["snapshot_id"],
                            lang,
                            corpus.label,
                            corpus.sha256,
                            gap["lemma"],
                            gap["pos"],
                            gap["category"],
                        ],
                        ensure_ascii=False,
                    ).encode()
                ).hexdigest()
            queues[lang].extend(result["gaps"])
            folder = stage / lang
            folder.mkdir(exist_ok=True)
            _write(folder / (corpus.label + ".json"), result)
            results.append({k: v for k, v in result.items() if k != "gaps"})
        languages = {}
        for lang, counts in manifest["languages"].items():
            folder = stage / lang
            folder.mkdir(exist_ok=True)
            queue = sorted(
                queues[lang],
                key=lambda g: (
                    -g["occurrences"],
                    -g["documents"],
                    g["corpus_label"],
                    g["lemma"] or "",
                ),
            )
            # Corpus occurrence counts are never summed across potentially overlapping corpora.
            _write(folder / "review-queue.json", queue)
            packet = []
            for category in (
                "annotation_structure",
                "missing_annotation",
                "pos_mismatch",
                "pending_review",
                "previously_excluded",
                "candidate_absent",
            ):
                packet.extend([g for g in queue if g["category"] == category][:8])
            _write(folder / "first-review-packet.json", packet)
            modalities = {r["corpus"]["modality"] for r in results if r["language"] == lang}
            languages[lang] = {
                "selection": counts,
                "selected_lemma_pos_keys": sum(k[0] == lang for k in index.keys),
                "gap_records": len(queue),
                "first_review_records": len(packet),
                "missing_modalities": sorted({"written", "spoken"} - modalities),
                "coverage_90_percent_verified": False,
            }
        summary = {
            "schema_version": "vocabulary-coverage-campaign-1",
            "inventory_format": inventory_format,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "config_sha256": config_sha256,
            "snapshot_id": manifest["snapshot_id"],
            "languages": languages,
            "results": results,
            "production_eligible": False,
            "generation_status": "deferred_by_user",
            "coverage_90_percent_verified": False,
            "limitations": [
                "Lexical keys do not measure contextual senses or comprehension.",
                "Excluded: PROPN, PUNCT/SYM, numeric notation and non-word speech events.",
                "Missing annotations stay in the denominator; names are excluded using corpus POS.",
                "Existing corpora are diagnostics, not balanced general-use certification.",
                "Only the explicit snapshot is included; unrelated supplements require a new version.",
                "No automatic expansion approvals; review packet priority is not a vocabulary rank.",
            ],
        }
        _write(stage / "summary.json", summary)
        table = [
            "# Diagnóstico da cobertura lexical",
            "",
            "Meta: 90% em fala e escrita representativas. Nenhum resultado abaixo certifica a meta.",
            "Lema+POS mede identidade lexical, sem comprovar sentidos ou compreensão. "
            "Compatível acrescenta apenas vínculos explícitos revisados.",
            "",
            "| Idioma | Corpus | Modalidade | Ocorrências | Lema | Lema+POS | Compatível | Limite |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
        for r in results:
            percentages = [
                f"{r[k]:.2f}%" if r[k] is not None else "—"
                for k in ("lemma_percent", "exact_percent", "compatible_percent")
            ]
            table.append(
                f"| {r['language']} | {r['corpus']['label']} | "
                f"{r['corpus']['modality']} | {r['counts']['denominator']} | "
                + " | ".join(percentages)
                + " | "
                + {
                    "annotation_alignment_required": "alinhar anotação",
                    "partial_inventory_diagnostic": "inventário parcial",
                    "reviewed_inventory_diagnostic": "amostra diagnóstica",
                }[r["interpretation"]]
                + " |"
            )
        table.extend(
            [
                "",
                "Inventários parciais e incompatibilidades de anotação estão registrados "
                "em summary.json. Filas e primeiros lotes por idioma estão nos subdiretórios.",
                "As contagens de corpora não são somadas. Ausência de corpus não significa 0%.",
            ]
        )
        table.extend(
            [
                "",
                "## Inventário e trabalho restante",
                "",
                "Unidades de revisão e chaves lema/POS são contagens diferentes; nenhuma é contagem de cartões.",
                "",
                "| Idioma | Unidades incluídas | Chaves lema/POS | Não revisadas | Dúvidas | Modalidade sem corpus |",
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for lang, state in sorted(languages.items()):
            selected = state["selection"]
            table.append(
                f"| {lang} | {selected.get('include', 0)} | "
                f"{state['selected_lemma_pos_keys']} | {selected.get('unreviewed', 0)} | "
                f"{selected.get('uncertain', 0)} | "
                + (", ".join(state["missing_modalities"]) or "—")
                + " |"
            )
        table.extend(
            [
                "",
                "Próxima ação: usar first-review-packet.json de cada idioma, resolver "
                "anotações e revisões existentes antes de admitir suplementos, e obter "
                "material de fala/escrita representativo onde falta. Nenhuma fila aprova entradas.",
            ]
        )
        (stage / "SUMMARY.md").write_text("\n".join(table) + "\n", encoding="utf-8")
        files = {
            str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in stage.rglob("*")
            if p.is_file()
        }
        _write(
            stage / "manifest.json", {"schema_version": "coverage-campaign-files-1", "files": files}
        )
        if destination.exists():
            raise ValueError("output appeared during evaluation")
        stage.rename(destination)
    return summary
