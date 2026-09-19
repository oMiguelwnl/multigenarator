"""Small multilingual review batches from immutable, published local pilots.

Selection is a diagnostic sample, never a frequency rank. IPA is copied from a
hash-bound candidate; syntax admission is not a pronunciation judgment. Upstream
raw-record hashes are retained, not reauthenticated against a remote dictionary.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, model_validator

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import Identifier, LanguageProfile, NativeContract, Sha256
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine import (
    MachineActor,
    MachineReviewRequest,
    build_machine_request,
)
from multilang.services.qualification_machine_evidence import _lexical
from multilang.services.qualification_machine_runner import (
    _locked,
    _write_once,
    export_machine_request,
    json_bytes,
    persist_artifact,
    read_json,
)
from multilang.services.qualification_pipeline import ArtifactReference
from multilang.services.qualification_review import (
    LexicalReviewItem,
    ReviewPacket,
    ReviewSource,
    _json,
)
from multilang.services.vocabulary_preparation import source_catalog
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_sources import LexicalSenseCandidate

_MAX_FILE_BYTES = 128 * 1024**2
_MAX_INPUT_BYTES = 2 * 1024**3
_MAX_RECORDS = 100000
_HASH = re.compile(r"[a-f0-9]{64}")
_LEXICAL_POS = frozenset(
    "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN SCONJ VERB".split()
)
_SINOLOGICAL_TONE_TAGS = frozenset({"Mandarin", "Standard-Chinese", "Sinological-IPA"})


def _allows_sinological_tones(language: SupportedLanguage, tags: tuple | list) -> bool:
    return language is SupportedLanguage.ZH and _SINOLOGICAL_TONE_TAGS.issubset(tags)


def _is_source_ipa(value: object, *, allow_sinological_tones: bool = False) -> bool:
    """Admit bounded IPA-like source notation, without judging pronunciation.

    This gate only selects dictionary IPA candidates for review. Orthographic
    readings, markup and controls cannot substitute for delimited phonetic data;
    Japanese, Korean and Chinese reading fields retain their separate contracts.
    The opt-in tone notation is only enabled by a Chinese candidate's explicit
    Mandarin/Standard-Chinese/Sinological-IPA source tags. Source text is retained.
    """
    if not isinstance(value, str) or not 3 <= len(value) <= 512:
        return False
    if any(unicodedata.category(character).startswith("C") for character in value):
        return False
    notation = value.strip()
    if len(notation) < 3 or (notation[0], notation[-1]) not in {("/", "/"), ("[", "]")}:
        return False
    segments = False
    for character in unicodedata.normalize("NFD", notation[1:-1]):
        codepoint = ord(character)
        segment = (
            "a" <= character <= "z"
            or 0x0250 <= codepoint <= 0x02AF
            or 0x1D00 <= codepoint <= 0x1D7F
            or character in "æçðøħŋœǀǁǂǃβθχφϕ"
        )
        if segment:
            segments = True
        elif not (
            0x02B0 <= codepoint <= 0x02FF
            or 0x0300 <= codepoint <= 0x036F
            or 0x1D80 <= codepoint <= 0x1DBF
            or character in " .|‖‿↗↘"
            or (allow_sinological_tones is True and character in "¹²³⁴⁵⁰⁻")
        ):
            return False
    return segments


class LanguageExpansionInput(NativeContract):
    language: SupportedLanguage
    pilot_directory: Path
    pilot_manifest_sha256: Sha256
    profile: ArtifactReference
    variant: Identifier | None = None
    pronunciation_tags: tuple[Identifier, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def explicit_modern_variant(self):
        if self.language is SupportedLanguage.LA:
            raise ValueError("Latin requires the separate source pipeline")
        if self.variant is not None and not self.pronunciation_tags:
            raise ValueError("a pronunciation variant requires explicit source tags")
        if len(set(self.pronunciation_tags)) != len(self.pronunciation_tags):
            raise ValueError("duplicate pronunciation tags")
        return self


class LanguageExpansionRequest(NativeContract):
    inputs: tuple[LanguageExpansionInput, ...] = Field(min_length=1, max_length=22)
    actor: MachineActor
    item_limit: int = Field(default=10, ge=1, le=10, strict=True)
    model_inventory: ArtifactReference | None = None

    @model_validator(mode="after")
    def unique_languages(self):
        if len({row.language for row in self.inputs}) != len(self.inputs):
            raise ValueError("duplicate expansion language")
        return self


class SourcePronunciationCandidate(NativeContract):
    candidate_sha256: Sha256
    source_record_sha256: Sha256
    sound_index: int = Field(ge=0)
    sound_sha256: Sha256
    ipa: str = Field(min_length=3, max_length=512)
    tags: tuple[str, ...] = Field(max_length=128)
    variant: Identifier | None = None
    pronunciation_reviewed: Literal[False] = False
    raw_dictionary_reauthenticated: Literal[False] = False


class LanguageLexicalSelection(NativeContract):
    candidate: LexicalSenseCandidate
    item: LexicalReviewItem
    parent_item_sha256: Sha256
    parent_packet_sha256: Sha256
    pronunciation: SourcePronunciationCandidate

    @model_validator(mode="after")
    def pronunciation_binds_candidate(self):
        proof, candidate = self.pronunciation, self.candidate
        if (
            candidate.kind != "lexeme"
            or candidate.form_of
            or proof.candidate_sha256 != canonical_sha256(candidate.model_dump(mode="json"))
            or proof.candidate_sha256 != self.item.candidate_sha256
            or candidate.candidate_id != self.item.candidate_id
            or candidate.source_record_sha256 != proof.source_record_sha256
            or proof.sound_index >= len(candidate.sounds)
        ):
            raise ValueError("pronunciation candidate binding mismatch")
        sound = candidate.sounds[proof.sound_index]
        if (
            canonical_sha256(sound) != proof.sound_sha256
            or sound.get("ipa") != proof.ipa
            or tuple(sound.get("tags", [])) != proof.tags
            or not _is_source_ipa(
                proof.ipa,
                allow_sinological_tones=_allows_sinological_tones(candidate.language, proof.tags),
            )
        ):
            raise ValueError("pronunciation source sound mismatch")
        return self


class MachineLanguageBatch(NativeContract):
    language: SupportedLanguage
    status: Literal["prepared", "blocked", "missing_input", "separate_pipeline"]
    variant: Identifier | None = None
    pronunciation_tags: tuple[Identifier, ...] = ()
    pilot_manifest_file_sha256: Sha256 | None = None
    profile_sha256: Sha256 | None = None
    source_catalog_sha256: Sha256 | None = None
    dictionary_sha256s: tuple[Sha256, ...] = ()
    preparation_manifest_sha256s: tuple[Sha256, ...] = ()
    model_snapshot: dict = Field(default_factory=dict)
    model_runtime_revalidated: Literal[False] = False
    lexical_candidate_count: int = Field(default=0, ge=0)
    eligible_ipa_count: int = Field(default=0, ge=0)
    audio_reference_candidate_count: int = Field(default=0, ge=0)
    evaluation_case_count: int = Field(default=0, ge=0)
    measured_form_count: int = Field(default=0, ge=0)
    calibration_context_sha256: Sha256 | None = None
    exclusion_counts: dict[Identifier, int] = Field(default_factory=dict)
    blockers: tuple[Identifier, ...] = ()
    selected: tuple[LanguageLexicalSelection, ...] = Field(default=(), max_length=10)
    request: MachineReviewRequest | None = None
    qualified: Literal[False] = False
    redistribution_approved: Literal[False] = False
    production_eligible: Literal[False] = False

    @model_validator(mode="after")
    def exact_request(self):
        if (self.status == "prepared") != bool(self.selected):
            raise ValueError("prepared language requires selected candidates")
        if (self.request is not None) != bool(self.selected):
            raise ValueError("language request and selection mismatch")
        if self.language is SupportedLanguage.LA and self.status != "separate_pipeline":
            raise ValueError("Latin cannot inherit a modern-language request")
        if self.request is not None and (
            self.request.packet.items != tuple(row.item for row in self.selected)
            or self.request.packet.language != self.language
            or self.request.packet.profile_sha256 != self.profile_sha256
            or len({row.candidate.lemma for row in self.selected}) != len(self.selected)
            or any(row.candidate.language != self.language for row in self.selected)
            or any(
                not set(self.pronunciation_tags).issubset(row.pronunciation.tags)
                or row.pronunciation.variant != self.variant
                for row in self.selected
            )
        ):
            raise ValueError("language request source/profile/variant mismatch")
        return self


class MachineLanguageExpansion(NativeContract):
    schema_version: Literal[1] = 1
    configuration: LanguageExpansionRequest
    languages: tuple[MachineLanguageBatch, ...] = Field(min_length=23, max_length=23)
    selection_policy: Literal["published-candidate-id-order-distinct-lemma-ipa-v1"] = (
        "published-candidate-id-order-distinct-lemma-ipa-v1"
    )
    selection_is_frequency_rank: Literal[False] = False
    evaluation_used_for_calibration: Literal[False] = False
    qualified: Literal[False] = False
    redistribution_approved: Literal[False] = False
    production_eligible: Literal[False] = False
    provider_calls_executed: Literal[0] = 0

    @model_validator(mode="after")
    def catalog_coverage(self):
        if {row.language for row in self.languages} != set(SupportedLanguage):
            raise ValueError("expansion must inventory all supported languages exactly once")
        if any(len(row.selected) > self.configuration.item_limit for row in self.languages):
            raise ValueError("expansion selection exceeds configured limit")
        return self

    @computed_field
    @property
    def expansion_sha256(self) -> str:
        return canonical_sha256(self.model_dump(mode="json", exclude_computed_fields=True))


def _relative(name):
    if (
        not isinstance(name, str)
        or not name
        or "\\" in name
        or Path(name).is_absolute()
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or not re.fullmatch(r"[A-Za-z0-9._/-]+", name)
    ):
        raise ValueError("invalid pilot artifact path")
    return name


def _pilot(input_, budget):
    root = _plain_path(input_.pilot_directory)
    manifest = _json(
        _read_bytes(root / "manifest.json", input_.pilot_manifest_sha256, limit=4 * 1024**2)
    )
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or manifest.get("production_eligible") is not False
        or manifest.get("language") != input_.language.value
        or manifest.get("pilot_sha256")
        != canonical_sha256(
            {key: value for key, value in manifest.items() if key != "pilot_sha256"}
        )
    ):
        raise ValueError("pilot manifest language, authority or checksum mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not 1 <= len(files) <= 500 or "candidates.jsonl" not in files:
        raise ValueError("pilot file inventory is incomplete or outside bounds")
    data = {}
    for name, digest in sorted(files.items()):
        _relative(name)
        content = _read_bytes(root / name, digest, limit=_MAX_FILE_BYTES)
        budget[0] += len(content)
        if budget[0] > _MAX_INPUT_BYTES:
            raise ValueError("language expansion aggregate input byte limit exceeded")
        if name == "candidates.jsonl" or name.endswith("/packet.json"):
            data[name] = content
    profile = LanguageProfile.model_validate(read_json(input_.profile.path, input_.profile.sha256))
    if (
        profile.language != input_.language
        or canonical_sha256(profile.model_dump(mode="json")) != manifest["profile_sha256"]
    ):
        raise ValueError("pilot language profile binding mismatch")
    candidates = {}
    lines = data["candidates.jsonl"].splitlines()
    if len(lines) > _MAX_RECORDS:
        raise ValueError("language candidate record limit exceeded")
    for line in lines:
        if not line.strip():
            continue
        if len(line) > 2 * 1024**2:
            raise ValueError("language candidate line limit exceeded")
        candidate = LexicalSenseCandidate.model_validate(_json(line))
        if candidate.language != input_.language:
            raise ValueError("candidate language differs from pilot")
        if (
            not _HASH.fullmatch(candidate.source_record_sha256)
            or candidate.candidate_id in candidates
        ):
            raise ValueError("candidate source hash or duplicate identity")
        candidates[candidate.candidate_id] = candidate
    packets = manifest.get("packets", [])
    if not isinstance(packets, list) or len(packets) > 500:
        raise ValueError("pilot packet inventory outside bounds")
    lexical, observed_counts, seen_paths = {}, Counter(), set()
    dictionaries = {item["dictionary_sha256"] for item in manifest["prepared_inputs"]}
    for row in packets:
        name = _relative(row["path"]) + "/packet.json"
        if name in seen_paths or name not in data or files[name] != row["packet_file_sha256"]:
            raise ValueError("pilot packet inventory binding mismatch")
        seen_paths.add(name)
        packet = ReviewPacket.model_validate(_json(data[name]))
        packet_sha = packet.packet_sha256
        if (
            packet.language != input_.language
            or packet.profile_sha256 != manifest["profile_sha256"]
            or packet.rubric_sha256 != manifest["rubric_sha256"]
            or packet_sha != row["packet_sha256"]
            or packet.split != row["split"]
            or len(packet.items) != row["item_count"]
        ):
            raise ValueError("pilot packet source/profile/scope mismatch")
        observed_counts[row["kind"]] += len(packet.items)
        if row["kind"] != "lexical":
            continue
        if packet.split != "calibration":
            raise ValueError("lexical expansion cannot consume evaluation cases")
        for item in packet.items:
            if not isinstance(item, LexicalReviewItem) or item.candidate_id in lexical:
                raise ValueError("duplicate or nonlexical pilot item")
            candidate = candidates.get(item.candidate_id)
            if (
                candidate is None
                or item.candidate_sha256 != canonical_sha256(candidate.model_dump(mode="json"))
                or item.lemma != candidate.lemma
                or not any(
                    source.record_id == candidate.candidate_id
                    and source.source_sha256 in dictionaries
                    for source in item.sources
                )
            ):
                raise ValueError("lexical candidate checksum or dictionary binding mismatch")
            lexical[item.candidate_id] = (item, packet_sha)
    if {name for name in data if name.endswith("/packet.json")} != seen_paths:
        raise ValueError("pilot contains an unlisted review packet")
    for kind, field in (
        ("lexical", "lexical_candidate_count"),
        ("case", "evaluation_case_count"),
        ("measured-forms", "measurement_count"),
    ):
        if observed_counts[kind] != manifest[field]:
            raise ValueError("pilot packet count mismatch")
    _read_bytes(root / "manifest.json", input_.pilot_manifest_sha256, limit=4 * 1024**2)
    return manifest, candidates, lexical


def _pronunciation(candidate, input_):
    for index, sound in enumerate(candidate.sounds):
        tags = sound.get("tags", [])
        if (
            not isinstance(tags, (list, tuple))
            or not all(isinstance(tag, str) for tag in tags)
            or len(tags) > 128
            or not _is_source_ipa(
                sound.get("ipa"),
                allow_sinological_tones=_allows_sinological_tones(candidate.language, tags),
            )
            or not set(input_.pronunciation_tags).issubset(tags)
        ):
            continue
        return SourcePronunciationCandidate(
            candidate_sha256=canonical_sha256(candidate.model_dump(mode="json")),
            source_record_sha256=candidate.source_record_sha256,
            sound_index=index,
            sound_sha256=canonical_sha256(sound),
            ipa=sound["ipa"],
            tags=tuple(tags),
            variant=input_.variant,
        )
    return None


def _model_snapshots(reference):
    if reference is None:
        return {}
    rows = read_json(reference.path, reference.sha256)
    if not isinstance(rows, list) or len(rows) > 23:
        raise ValueError("model inventory must be a bounded language list")
    snapshots = {}
    allowed = {
        "language",
        "backend",
        "available",
        "package_version",
        "manifest_sha256",
        "model_package",
        "model_package_version",
        "model_artifact_sha256",
        "qualified",
    }
    for row in rows:
        if not isinstance(row, dict) or set(row) - allowed:
            raise ValueError("unsupported model inventory fields")
        language = SupportedLanguage(row["language"])
        if language in snapshots or row.get("qualified") is not False:
            raise ValueError("duplicate model language or unsupported qualification claim")
        snapshots[language] = row
    return snapshots


def build_machine_language_expansion(
    configuration: LanguageExpansionRequest,
) -> MachineLanguageExpansion:
    """Verify published pilot evidence and create at most ten lexical requests per language."""
    configuration = LanguageExpansionRequest.model_validate(configuration.model_dump(mode="json"))
    inputs = {item.language: item for item in configuration.inputs}
    models, budget, rows = _model_snapshots(configuration.model_inventory), [0], []
    for language in SupportedLanguage:
        if language is SupportedLanguage.LA:
            rows.append(
                MachineLanguageBatch(
                    language=language,
                    status="separate_pipeline",
                    blockers=("latin_isolated_source_pipeline",),
                )
            )
            continue
        input_ = inputs.get(language)
        if input_ is None:
            rows.append(
                MachineLanguageBatch(
                    language=language, status="missing_input", blockers=("missing_published_pilot",)
                )
            )
            continue
        manifest, candidates, lexical = _pilot(input_, budget)
        selected, excluded, seen, eligible, audio = [], Counter(), set(), 0, 0
        for candidate_id, (item, parent_hash) in sorted(lexical.items()):
            candidate = candidates[candidate_id]
            audio += any(
                sound.get("audio") or sound.get("mp3_url") or sound.get("ogg_url")
                for sound in candidate.sounds
            )
            if candidate.kind != "lexeme" or candidate.form_of or item.pos not in _LEXICAL_POS:
                excluded["unresolved_lexical_identity"] += 1
                continue
            pronunciation = _pronunciation(candidate, input_)
            if pronunciation is None:
                excluded["missing_matching_ipa"] += 1
                continue
            eligible += 1
            if candidate.lemma in seen:
                excluded["duplicate_lemma_in_sample"] += 1
                continue
            if len(selected) >= configuration.item_limit:
                excluded["sample_limit"] += 1
                continue
            enriched, proof = _lexical(item, candidate, (parent_hash,))
            sound_excerpt = json.dumps(
                {
                    "candidate_id": candidate_id,
                    "source_record_sha256": candidate.source_record_sha256,
                    "sound_index": pronunciation.sound_index,
                    "sound": candidate.sounds[pronunciation.sound_index],
                    "scope": "source pronunciation candidate; accuracy and locale require review",
                },
                ensure_ascii=True,
                sort_keys=True,
            )
            if (
                len(sound_excerpt) > 64000
                or len(enriched.sources) >= 128
                or proof.coverage == "unavailable"
            ):
                excluded["pronunciation_evidence_limit"] += 1
                continue
            source = next(source for source in item.sources if source.record_id == candidate_id)
            enriched = LexicalReviewItem.model_validate(
                enriched.model_copy(
                    update={
                        "sources": (
                            *enriched.sources,
                            ReviewSource(
                                source_id="prepared-pronunciation",
                                source_sha256=source.source_sha256,
                                record_id=candidate.source_record_sha256,
                                excerpt=sound_excerpt,
                            ),
                        )
                    }
                ).model_dump(mode="json")
            )
            selected.append(
                LanguageLexicalSelection(
                    candidate=candidate,
                    item=enriched,
                    parent_item_sha256=item.item_sha256,
                    parent_packet_sha256=parent_hash,
                    pronunciation=pronunciation,
                )
            )
            seen.add(candidate.lemma)
        blockers = [
            "linguistic_review_pending",
            "pronunciation_review_pending",
            "source_redistribution_review",
            "reviewed_content_and_audio",
            "importance_policy_unqualified",
        ]
        if not manifest.get("measurement_context_sha256"):
            blockers.append("missing_calibration_corpus")
        if not selected:
            blockers.append("no_source_bound_ipa")
        machine_request = None
        if selected:
            binding = canonical_sha256(
                [input_.model_dump(mode="json"), [row.item.item_sha256 for row in selected]]
            )
            packet = ReviewPacket(
                packet_id="language-sample:" + binding,
                language=language,
                split="calibration",
                profile_sha256=manifest["profile_sha256"],
                rubric_sha256=manifest["rubric_sha256"],
                items=tuple(row.item for row in selected),
            )
            actor = configuration.actor.model_copy(
                update={
                    "context_id": "context:"
                    + canonical_sha256([configuration.actor.context_id, binding])
                }
            )
            machine_request = build_machine_request(
                packet, actor=actor, run_id="proposal:" + binding
            )
        rows.append(
            MachineLanguageBatch(
                language=language,
                status="prepared" if selected else "blocked",
                variant=input_.variant,
                pronunciation_tags=input_.pronunciation_tags,
                pilot_manifest_file_sha256=input_.pilot_manifest_sha256,
                profile_sha256=manifest["profile_sha256"],
                source_catalog_sha256=canonical_sha256(source_catalog(language.value)),
                dictionary_sha256s=tuple(
                    sorted({item["dictionary_sha256"] for item in manifest["prepared_inputs"]})
                ),
                preparation_manifest_sha256s=tuple(
                    sorted({item["manifest_file_sha256"] for item in manifest["prepared_inputs"]})
                ),
                model_snapshot=models.get(language, {}),
                lexical_candidate_count=len(lexical),
                eligible_ipa_count=eligible,
                audio_reference_candidate_count=audio,
                evaluation_case_count=manifest["evaluation_case_count"],
                measured_form_count=manifest["measurement_count"],
                calibration_context_sha256=manifest.get("measurement_context_sha256"),
                exclusion_counts=dict(sorted(excluded.items())),
                blockers=tuple(blockers),
                selected=tuple(selected),
                request=machine_request,
            )
        )
    return MachineLanguageExpansion(configuration=configuration, languages=tuple(rows))


def render_machine_language_expansion(expansion: MachineLanguageExpansion) -> str:
    lines = [
        "<!doctype html><html lang='pt'><meta charset='utf-8'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; base-uri 'none'; form-action 'none'\">",
        "<title>Lotes linguísticos de revisão</title><h1>Lotes linguísticos de revisão</h1>",
        "<p>Amostras de origem máquina, sem ranking, qualificação ou autorização de redistribuição. IPA é evidência candidata. Casos de avaliação permanecem reservados. Nenhum provedor foi chamado.</p>",
        "<table><thead><tr><th>Idioma</th><th>Estado</th><th>Variante/tags</th><th>Selecionados</th><th>IPA elegível</th><th>Casos reservados</th><th>Formas medidas</th><th>Impedimentos</th></tr></thead><tbody>",
    ]
    for row in expansion.languages:
        cells = (
            row.language.value,
            row.status,
            row.variant or ", ".join(row.pronunciation_tags) or "source-declared",
            str(len(row.selected)),
            str(row.eligible_ipa_count),
            str(row.evaluation_case_count),
            str(row.measured_form_count),
            ", ".join(row.blockers),
        )
        lines.append(
            "<tr>" + "".join("<td>" + html.escape(cell) + "</td>" for cell in cells) + "</tr>"
        )
    return "\n".join([*lines, "</tbody></table></html>"])


def export_machine_language_expansion(expansion: MachineLanguageExpansion, output: Path) -> dict:
    """Write source-bound requests idempotently; modified children fail on resume."""
    expansion = MachineLanguageExpansion.model_validate(expansion.model_dump(mode="json"))
    if build_machine_language_expansion(expansion.configuration) != expansion:
        raise ValueError("language expansion source or selection drift")
    config = {"expansion_sha256": expansion.expansion_sha256, "schema_version": 1}
    requests = []
    with _locked(output) as root:
        if root.exists():
            if read_json(root / "configuration.json") != config:
                raise ValueError("language expansion configuration drift")
        else:
            root.mkdir(mode=0o700)
            _write_once(root / "configuration.json", config)
        for row in expansion.languages:
            persist_artifact(
                root / ("language-" + row.language.value),
                kind="machine-language-batch",
                binding=canonical_sha256(row.model_dump(mode="json")),
                files={"batch.json": json_bytes(row)},
            )
            if row.request is None:
                continue
            path = "request-" + row.language.value
            manifest = export_machine_request(row.request, root / path)
            requests.append(
                {
                    "language": row.language.value,
                    "path": path,
                    "item_count": len(row.selected),
                    "request_sha256": row.request.request_sha256,
                    "request_file_sha256": manifest["files"]["request.json"],
                }
            )
        persist_artifact(
            root / "inventory",
            kind="machine-language-expansion",
            binding=expansion.expansion_sha256,
            files={
                "inventory.json": json_bytes(expansion),
                "matrix.html": render_machine_language_expansion(expansion).encode(),
            },
        )
        index = {
            **config,
            "requests": requests,
            "request_count": len(requests),
            "prepared_languages": len(requests),
            "item_count": sum(row["item_count"] for row in requests),
            "inventoried_languages": len(expansion.languages),
            "provider_calls_executed": 0,
            "qualified": False,
            "production_eligible": False,
            "redistribution_approved": False,
        }
        if (root / "index.json").exists():
            if read_json(root / "index.json") != index:
                raise ValueError("language expansion output inventory drift")
        else:
            _write_once(root / "index.json", index)
        return index
