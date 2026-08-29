# Phase 33: Grammar and Personal Sources - Pattern Map

**Mapped:** 2026-08-28
**Requirements:** KGRAM-01, KGRAM-02, KPERS-01, KPERS-02, GJOB-01, GREV-01
**Files/artifact groups classified:** 34 inferred new or modified surfaces
**Primary analog families:** 5
**Exact end-to-end analogs for novel Phase 33 behavior:** 0

## Scope Truth

- `33-APPROACH.md` is the authoritative Phase 33 input. There is no Phase 33 `CONTEXT.md` or `RESEARCH.md` yet.
- Grammar imports the exact active, approved Phase 31 foundation snapshot once and adds a grammar-owned learner-visible lexical bootstrap. It does not mutate Phase 31, require Frequency Level 1, or operate as a standalone curriculum.
- Custom input retains every nonblank row and its immutable position. The first exact normalized occurrence is card-bearing; later exact duplicates remain visible `duplicate_of` outcomes. Distinct submitted forms remain distinct items even when they resolve to one lemma/POS/sense.
- Personal-source prerequisite decisions are explicit `bridge`, `defer`, or `needs_review`. No bridge is inserted automatically, and there is no adaptive queue.
- Exact highlight excerpts, derived provider context, and generated microexamples are three different typed artifacts. Exact excerpts stay private. A remote provider receives no highlight context without exact per-run private-processing authority.
- Reviewable values are immutable revisions. Append-only events reference before/after revision IDs and hashes but do not duplicate private values. Approved revisions are never updated in place.
- `processed`, `accepted`, `review_required`, and `failed` are distinct persisted facts. Only accepted required work advances item completion.
- Phase 33 is CLI-first. Do not add FastAPI, a dashboard, authentication, remote callbacks, publication commands, provider-selection switches, or private-content remote management.
- Production provider calls, private uploads, source/media acquisition, production DB mutation, asset commit, publication, and distribution remain unauthorized. Automated tests use synthetic offline fixtures.
- Final APKG/CSV/TSV closure and observed Anki behavior remain Phase 34. Phase 33 preserves existing layouts, field order, note identities, GUID formulas, and blank `Image`.

## File Classification

Exact module/table names are technical discretion under `33-APPROACH.md:284-295`. The paths below are recommended ownership boundaries so plans do not scatter one contract across unrelated modules.

| New/Modified File or Artifact Group | Role | Data Flow | Closest Live Analog | Match Quality |
|---|---|---|---|---|
| `src/multilang/domain/korean_grammar.py` **(create; recommended)** | model | transform | `domain/korean.py`; `services/korean_curriculum.py` | role + schema match |
| `src/multilang/services/korean_grammar.py` **(create; recommended)** | service/model | file-I/O, transform, batch | `services/korean_curriculum.py`; `korean_foundation_snapshot.py` | composite role + flow |
| `data/korean_grammar/<bundle-sha256>/...` **(gated, do not create production content without authority)** | config/data | immutable file-I/O, batch | Phase 31 hash-named foundation snapshots/bundles | publication shape only |
| `src/multilang/domain/personal_sources.py` **(create; recommended)** | model | transform | `domain/highlights.py`; `domain/korean.py` | role match |
| `src/multilang/services/word_list_parser.py` | utility | file-I/O, transform | current parser in the same file | exact self-extension, current duplicate behavior is an anti-pattern |
| `src/multilang/services/input_fingerprint.py` | utility | transform | current fingerprint builder | exact self-extension, current sorting is an anti-pattern |
| `src/multilang/services/korean_personal_sources.py` **(create; recommended)** | service | transform, batch, CRUD | `highlight_candidate_extraction.py`; `korean_curriculum.py` | composite; no exact bridge/defer analog |
| `src/multilang/domain/highlights.py` | model | transform | current private/safe highlight contracts | exact self-extension |
| `src/multilang/services/highlight_candidate_extraction.py` | service | transform, batch | current Korean-first branch | exact self-extension |
| `src/multilang/repositories/highlight_import_repository.py` | repository | CRUD | current private record/safe manifest split | exact self-extension |
| `src/multilang/services/korean_private_context.py` **(create; recommended)** | service/middleware | request-response, transform | `korean_checkpoint_authority.py`; `text_generation.py`; `security/redaction.py` | role match; no exact scoped-context receipt analog |
| `src/multilang/services/text_generation.py` | service/provider boundary | request-response | current typed request/cache/retry/telemetry path | exact self-extension, current automatic context path must be guarded |
| `src/multilang/domain/revisions.py` **(create; recommended)** | model | CRUD, event-driven | frozen Korean models; text/audio domain records | no single exact analog |
| `src/multilang/repositories/revision_repository.py` **(create; recommended)** | repository | CRUD, event-driven | text/audio repositories; provider-call append path | no single exact analog |
| `src/multilang/services/field_review.py` **(create; recommended)** | service | request-response, event-driven, CRUD | foundation review gates; text review reports | no single exact analog |
| `src/multilang/domain/jobs.py` | model | event-driven, batch | current stage/status/progress contracts | exact self-extension |
| `src/multilang/repositories/job_repository.py` | repository | CRUD, event-driven | current item success/failure/resume methods | exact self-extension, current one-status-per-item model is insufficient |
| `src/multilang/db/models.py` | model | CRUD | current SQLAlchemy models and constraints | exact self-extension |
| `alembic/versions/<next>_phase33_grammar_personal_review.py` **(create only after live head is settled)** | migration | CRUD | `20260821_18_frequency_text_audio_evidence.py` | exact migration style |
| `src/multilang/domain/exporting.py` | model/guard | transform | `ExportCardRow`, normal/highlight field contracts | exact self-extension |
| `src/multilang/services/assemble_export_cards.py` | service | transform, CRUD | current accepted lexical/text/audio projection | exact self-extension |
| `src/multilang/repositories/text_repository.py`, `audio_repository.py` | repository/compatibility | CRUD | current explicit mappings | role match; in-place upsert is not revision history |
| `src/multilang/cli.py` | controller/route | request-response | injected Typer app and Korean foundation command group | exact self-extension |
| `tests/domain/test_korean_grammar.py`, `test_personal_sources.py`, `test_revisions.py` **(create)** | test | transform | Korean frozen-contract tests | role match |
| `tests/services/test_korean_grammar.py` **(create)** | test | file-I/O, transform | `test_korean_curriculum.py`; `test_korean_foundation_snapshot.py` | role + flow match |
| `tests/services/test_word_list_parser.py`, `test_korean_personal_sources.py` | test | file-I/O, transform, batch | current parser and Korean grounding tests | exact + role match |
| `tests/services/test_highlight_candidate_extraction.py`, `test_korean_private_context.py` | test | transform, request-response | current Korean extraction, checkpoint-authority, and text-generation tests | exact + role match |
| `tests/repositories/test_revision_repository.py` **(create)** | test | CRUD, event-driven | text/audio/highlight repository round-trip tests | role match |
| `tests/services/test_field_review.py` **(create)** | test | request-response, event-driven | foundation review and text review tests | role match |
| `tests/repositories/test_job_repository.py` | test | CRUD, event-driven | current duplicate/resume/authority tests | exact self-extension |
| `tests/test_migration_schema_parity.py` | test | CRUD | current sole-head and upgrade/downgrade/re-upgrade tests | exact self-extension |
| `tests/cli/test_korean_review_commands.py` **(create; recommended)** | test | request-response | `test_korean_foundation_commands.py`; checkpoint-authority CLI tests | role + flow match |
| `tests/integration/test_korean_grammar_personal_sources_flow.py` **(create)** | test | batch, CRUD, transform, request-response | Korean modern flow; custom-list E2E; local Kindle flow | composite role match |
| Existing custom-list/highlight/normal-layout regressions | test | batch, CRUD, file-I/O | files named in the test matrix below | exact regression homes |

## Pattern Assignments

### `domain/korean_grammar.py`, `services/korean_grammar.py`, grammar bundle, and grammar tests

**Primary analogs:** `src/multilang/services/korean_curriculum.py`, `src/multilang/domain/korean.py`, and `src/multilang/services/korean_foundation_snapshot.py`.

**Imports and graph tooling** (`korean_curriculum.py:3-32`):

```python
from enum import Enum
from graphlib import CycleError, TopologicalSorter
from hashlib import sha256
import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from multilang.domain.korean import (
    KoreanConcept,
    KoreanCurriculumEvidence,
)
```

Keep reusable Phase 30 concepts in `domain/korean.py`; import them into the new Phase 33 module. Do not enlarge or rewrite the Phase 31 registry.

**Frozen bounded model pattern** (`korean_curriculum.py:347-369`):

```python
class _FrozenManifest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

def korean_canonical_json_sha256(value: object) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
```

Apply this to the root bundle, member declarations, registry overlay, bootstrap entries, grammar entries, review bindings, media bindings, and recomputed evidence. Use tuples for ordered immutable collections, bounded fields, lowercase SHA-256 validators, and `extra="forbid"`.

**Concept and evidence shape** (`domain/korean.py:366-446`):

```python
class KoreanConcept(_FrozenContract):
    id: str
    domain: Literal["orthography", "phonology", "grammar", "lexicon"]
    prerequisite_ids: tuple[str, ...] = ()
    sequence: int

class KoreanCurriculumEvidence(_FrozenContract):
    target_concept_id: str
    prerequisite_concept_ids: tuple[str, ...] = ()
    observed_concept_ids: tuple[str, ...]
    unknown_concept_ids: tuple[str, ...]
    policy: Literal["strict", "adaptive", "contextual"]
```

The existing domains already support the overlay. Add stable Phase 33 `lexicon` and `grammar` concepts and validate collision freedom against imported Phase 31 IDs.

**Closed deterministic graph** (`korean_curriculum.py:642-711`):

```python
concept_by_id = {concept.id: concept for concept in self.concepts}
graph = {
    concept.id: set(concept.prerequisite_ids) for concept in self.concepts
}
try:
    tuple(TopologicalSorter(graph).static_order())
except CycleError as exc:
    raise ValueError("concept registry contains a cycle") from exc

if any(
    concept_by_id[predecessor].sequence >= concept.sequence
    for concept in self.concepts
    for predecessor in concept.prerequisite_ids
):
    raise ValueError("concept registry contains a forward dependency")
```

Copy the uniqueness, existence, cycle, forward-dependency, and transitive-closure checks. Expand permitted dependency domains additively: imported foundation concepts precede grammar-owned lexicon, and both may precede grammar. Never alter imported concept objects.

**Strict recomputation loop** (`korean_curriculum.py:1591-1666`):

```python
for entry in pack.entries:
    evidence = entry.evidence
    target_id = evidence.target_concept_id
    if evidence.policy != "strict":
        _raise(KoreanCurriculumReasonCode.STRICT_POLICY_REQUIRED)
    if target_id not in evidence.observed_concept_ids:
        _raise(KoreanCurriculumReasonCode.TARGET_NOT_OBSERVED)
    if target_id in known:
        _raise(KoreanCurriculumReasonCode.REPEATED_TARGET)
    if not set(evidence.prerequisite_concept_ids) <= known:
        _raise(KoreanCurriculumReasonCode.UNKNOWN_PREREQUISITE)
    recomputed_unknown = tuple(
        concept_id for concept_id in evidence.observed_concept_ids
        if concept_id not in known
    )
    if recomputed_unknown != (target_id,):
        _raise(KoreanCurriculumReasonCode.RECOMPUTED_UNKNOWN_MISMATCH)
    known.add(target_id)
```

For Phase 33, initialize `known` from the exact imported Phase 31 concepts, then admit the ordered learner-visible bootstrap, then G0-G13 targets. Every strict grammar card must have exactly one recomputed unknown construction. Review cannot override a graph failure.

**Exact Phase 31 join** (`korean_foundation_snapshot.py:1107-1154`):

```python
def resolve_active_korean_foundation_snapshot() -> ResolvedKoreanFoundationSnapshot:
    pointer_path = _PROJECT_ROOT / ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH
    pointer = _parse_pointer(_read_pointer_once(pointer_path))
    ...
    manifest, _manifest_raw, members = _verify_snapshot_tree(
        snapshot_root,
        expected_bundle_sha256=pointer.bundle_sha256,
        expected_manifest_sha256=pointer.snapshot_manifest_sha256,
    )
    ...
    return _resolved_snapshot(
        pointer=pointer,
        snapshot_root=snapshot_root,
        manifest=manifest,
        members=members,
    )
```

Call this resolver once per grammar operation. Bind `bundle_sha256`, `receipt_sha256`, `snapshot_manifest_sha256`, `snapshot_root_sha256`, and the imported concept-registry member hash into the Phase 33 root and downstream evidence. Reject missing v2 provenance, candidate/history/test/request-only input, pointer drift, or a second mutable-pointer read.

**Testing assignment:** copy mutation-table tests from `test_korean_curriculum.py`; add collision, missing ID, cycle, forward edge, incomplete closure, broad/repeated target, non-strict policy, hidden lexical/morphological/register prerequisite, mixed speech level, source hash drift, and exactly-one-unknown cases. Poison provider/network/asset writers in all offline schema tests. Production grammar data remains absent or `needs_review` until real source/review/media authority exists.

---

### `domain/exporting.py`, `assemble_export_cards.py`, and grammar normal-card projection

**Primary analog:** existing normal-card row construction. Do not add a grammar note type.

**Frozen normal field order** (`domain/exporting.py:17-27`):

```python
FREQUENCY_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "word",
    "IPA",
    "Definitions",
    "Example Sentence",
    "Translation",
    "word_audio",
    "sentence_audio",
    "Image",
)
```

**Stable identity and blank image guard** (`domain/exporting.py:95-117,147-156`):

```python
class ExportCardIdentity(BaseModel):
    language: SupportedLanguage
    source_type: str
    job_id: str
    item_key: str
    lemma_key: str
    sort_index: int

def build_export_note_guid(identity: ExportCardIdentity) -> str:
    return sha256(identity.stable_guid_input().encode("utf-8")).hexdigest()[:32]

if self.image != "":
    raise ValueError("Image must default to an empty string for export rows")
```

Do not change `stable_guid_input()` or existing source-mode routing. Phase 33 adds order/evidence records, not a GUID migration.

**Projection construction** (`assemble_export_cards.py:115-150`):

```python
row = ExportCardRow(
    identity=ExportCardIdentity(
        language=deck_language,
        source_type=source_type,
        job_id=job_id,
        item_key=text_record.item_key,
        lemma_key=lexical_candidate.lemma_key,
        sort_index=sort_index,
    ),
    word=escape(lexical_candidate.lemma),
    front_of_card=escape(lexical_candidate.display_form),
    definitions=self._render_definitions(lexical_candidate, deck_language=deck_language),
    example_sentence=escape(text_record.example_sentence or ""),
    translation=escape(text_record.translation_text or ""),
    word_audio=self._to_sound_tag(word_audio) if word_audio is not None else "",
    sentence_audio=self._to_sound_tag(sentence_audio),
)
```

Adapt the input side, not the row contract: grammar `word` is the reviewed construction form; `IPA` is reviewed pronunciation/display policy; `Definitions` deterministically combines function + attachment/allomorph rule + register; sentence/translation/audio come only from current approved revisions. The combined definition must be reversible to its exact structured source revision. Keep `Image=""`.

Final Phase 33 readiness must additionally verify current approved definition/sentence/translation/audio revisions and exact dependency hashes. Do not let current `list_accepted_records()` alone imply field approval.

---

### `personal_sources.py`, `word_list_parser.py`, `input_fingerprint.py`, `korean_personal_sources.py`, and tests

**Primary analogs:** current word-list parsing, Korean lexical identity, and strict graph evidence. The parser's duplicate dropping and fingerprint sorting are explicit anti-patterns for this phase.

**Current ordered parse seam** (`word_list_parser.py:163-181`):

```python
for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
    submitted_forms = split_loose_word_list_line(raw_line)
    ...
    for submitted_form in submitted_forms:
        display_form = unicodedata.normalize("NFC", submitted_form.strip())
        item_key = normalize_word_list_key(display_form)
```

Retain source iteration order and exact bounded `submitted_form`, but introduce a monotonically increasing `input_position` for every nonblank parsed item, including multiple entries from one line.

**Do not copy duplicate dropping** (`word_list_parser.py:182-203`):

```python
if item_key in first_line_by_key:
    warnings.append(...)
    continue
```

Replace this with a persisted row outcome carrying `duplicate_of=<first row identity>`. Only the first exact-normalized row is card-bearing. A duplicate is processed and visible, not silently omitted. Distinct submitted surfaces must not deduplicate merely because source resolution returns the same lexical identity.

**Current fingerprint anti-pattern** (`input_fingerprint.py:12-20,36-38`):

```python
normalized = {
    unicodedata.normalize("NFC", item).strip().lower()
    for item in requested_item_keys
    if item and item.strip()
}
return sorted(normalized)
```

Phase 33 needs an ordered source fingerprint over framed canonical entries, including duplicate positions, so reordering changes the source fingerprint. Keep stable per-row/item identity separate from the run fingerprint and preserve current GUID behavior.

**Source-backed identity** (`domain/korean.py:767-828`):

```python
class KoreanLexicalIdentity(_FrozenContract):
    submitted_form: str | None
    canonical_nfc: str
    lemma: str
    part_of_speech: str
    sense_id: str
    usage_register: str = Field(alias="register", serialization_alias="register")
    morpheme_signature: tuple[KoreanSignatureItem, ...]
    analyzer_fingerprint: KoreanAnalyzerFingerprint
    status: Literal["resolved"]
```

Preserve submitted form separately from canonical NFC and source-backed identity. Ambiguous/OOV/unavailable/fingerprint-drift/missing-sense outcomes stay `needs_review`; do not use top-1, suffix, substring, whitespace, provider, or generic fallback.

The personal-source service should persist a versioned adaptive prerequisite assessment and one explicit decision state: `bridge`, `defer`, or `needs_review`. A bridge proposal names exact prerequisite concept IDs; it never inserts a card. Repository/report ordering is `input_position`, with explicitly approved bridge rows immediately before their dependent item while preserving relative user-row order.

**Tests to copy:** `test_word_list_parser.py:18-45,131-150` proves submitted-form and NFC evidence. Change the duplicate expectation from omission to two persisted ordered outcomes. Add reordered-run fingerprints, same identity/different submitted form, compound predicate, inflected form, ambiguity, bridge/defer idempotency, and no-auto-insertion tests. `test_custom_word_list_e2e_export_flow.py:77-143` is the end-to-end shell, but replace live-style generated acceptance with synthetic approved revision fixtures.

---

### Highlight contracts, local morphology, private context authority, and provider boundary

**Primary analogs:** `domain/highlights.py`, `highlight_candidate_extraction.py`, `highlight_import_repository.py`, `korean_morphology.py`, `text_generation.py`, and `korean_checkpoint_authority.py`.

**Private/safe split** (`highlight_import_repository.py:41-57,68-83`):

```python
payload = {
    "job_id": job_id,
    "import_content_hash": import_content_hash,
    "highlight_id": highlight.highlight_id,
    "source_content_hash": highlight.provenance.content_hash,
    "source_index": highlight.provenance.source_index,
    "normalized_text": highlight.text,
}
...
payload = {
    "job_id": job_id,
    "import_content_hash": manifest.import_content_hash,
    "candidate_keys": list(manifest.candidate_keys),
    "counts": dict(manifest.counts),
}
```

Strengthen this boundary with immutable private excerpt revisions. Ordinary candidates/manifests retain only safe identity, hashes, indexes, and counts. Do not add excerpt text, path, book/location metadata, or private context to the safe manifest.

**Korean-first extraction** (`highlight_candidate_extraction.py:146-223`):

```python
for highlight in sorted(highlights, key=lambda item: item.provenance.source_index):
    ...
    raw_lexemes = tuple(resolver.resolve_korean_highlight_text(highlight.text))
    ...
    for _word_position, identity in sorted(resolved_lexemes, key=lambda item: item[0]):
        duplicate_count += _record_korean_candidate(
            candidates_by_key,
            highlight=highlight,
            identity=identity,
        )
```

Keep this branch before generic token length/stopword filtering. `KiwiKoreanMorphologyService` projects lexical signatures from all lexical morphemes (`korean_morphology.py:400-423`), which preserves one-syllable lexemes, attached `J*`/`E*` evidence, and compound predicates. Deduplicate only by complete source-backed identity within one exact excerpt hash; different excerpt hashes remain distinct private records.

**Current sanitizer is not authorization** (`text_generation.py:55-98,548-572`):

```python
if (
    data.get("target_language") == SupportedLanguage.KO.value
    and data.get("source_type") == "kindle-highlights"
    and isinstance(context, str)
):
    data["highlight_context"] = _sanitize_korean_highlight_context(...)

tokens = _CONTEXT_TOKEN_RE.findall(sanitized)
...
return " ".join(tokens[start:end])
```

Reuse the deterministic redaction and maximum 24-token target-centered window, but do not treat sanitization as permission. The new private-context service must return `None` unless an exact, current authority receipt matches job/run, source hashes, task, provider/model route, purpose, redaction policy, cap, item/attempt ceiling, budget, authorizer, and expiry. Re-sanitize at typed request and adapter boundaries.

**Least-power authority model** (`korean_checkpoint_authority.py:35-79,137-149`):

```python
class _AuthorityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

class KoreanAuthorityBinding(_AuthorityModel):
    path: str
    sha256: str
    byte_count: int

@model_validator(mode="after")
def authority_must_match_fixed_registry(self) -> Self:
    if self.expected_kind != self.kind:
        raise ValueError("authority expected kind mismatch")
    if self.powers != _POWER_REGISTRY[self.kind]:
        raise ValueError("authority powers do not match fixed registry")
```

Adapt this shape to a private-processing receipt with fixed powers; do not widen the Phase 32 registry implicitly. `validate_korean_checkpoint_authority()` (`:190-214`) demonstrates exact bytes, typed validation, hash-drift rejection, and a hash-only return value.

Provider telemetry follows `provider_call_log_repository.py:41-65`: store operation, controlled identifiers, hashes, attempts, status, and redacted errors. For private context add authority ID, context hash, redaction-policy version, and bounded metrics only—never the context value, prompt, completion, excerpt, path, or payload.

**Testing assignment:** preserve `test_highlight_candidate_extraction.py:256-417` for one-syllable/particle/compound identity, homographs, NFC, and content-free failures. Copy checkpoint-authority mutation tests (`test_korean_checkpoint_authority.py:48-121`) and safe CLI-output tests (`:124-165`). Add absent/expired/wrong-route/wrong-source/over-budget/policy-drift authority cases proving the adapter is never called and context is `None`. Keep the exact excerpt out of export `Example Sentence`; only an approved generated microexample revision is eligible.

---

### `domain/revisions.py`, `revision_repository.py`, `field_review.py`, and revision tests

**No single exact analog exists.** Compose frozen domain contracts, explicit repository mapping, append-only provider-log behavior, and one atomic SQLAlchemy transition. Do not extend mutable text/audio upserts into a fake audit log.

**Repository mapping style to copy** (`text_repository.py:30-55`):

```python
payload = {
    "job_id": record.job_id,
    "item_key": record.item_key,
    "example_sentence": record.example_sentence,
    "translation_text": record.translation_text,
    "review_status": record.review_status.value,
    "sentence_provenance": record.sentence_provenance.model_dump(mode="json"),
    "translation_provenance": record.translation_provenance.model_dump(mode="json"),
}
```

Use explicit domain-to-ORM and ORM-to-domain mappings. Do **not** copy the existing update loop (`text_repository.py:57-64`; `audio_repository.py:59-80`) for approved values.

Recommended relational decomposition:

1. `field_revisions`: immutable private value or media reference; `(job_id, item_key, field_name, revision_number)` unique; canonical content hash; provenance; validation/review state; creator; policy IDs; dependency bindings; timestamps.
2. `current_field_revisions`: one row per `(job_id, item_key, field_name)` pointing separately to selected and current-approved revisions; include an integer optimistic version or exact expected-current revision for compare-and-swap.
3. `field_review_events`: append-only action with before/after revision IDs and hashes, actor type/ID, controlled reason, policy/validation snapshot identity, timestamp. It contains no field value, media bytes, prompt, path, private context, or reviewer note.

Dependencies may be strict typed JSON on the immutable revision or normalized rows. Either way they must bind exact revision IDs and hashes and be queryable for invalidation. A changed sentence marks bound translation and sentence-audio pointers stale/review-required while retaining all old revisions. A definition invalidates a sentence only when the sentence revision declares that grounding dependency.

The application service owns one short transaction for candidate insertion, compare-and-swap pointer transition, dependent staleness, and event insertion. Perform provider calls and validation before opening that transaction. A stale expected base produces a deterministic conflict and no partial rows. Repository APIs expose insert/list/get/transition methods; they expose no update/delete for revision/event rows.

Review semantics:

- `list` is read-only and privacy-safe by default; exact private values require explicit local display.
- `edit` and `regenerate` create one new `needs_review` candidate for only the selected field.
- `reject` records an event and leaves the last approved revision selected/current; with no approved revision the field remains blocking.
- `approve` moves the approved pointer only after validation and expected-base checks; history remains addressable.
- Repeating the exact successful command returns/reuses current state or a duplicate-safe observation; it does not create a second revision/event/provider call.

**Tests:** assert frozen domain models, no ORM update/delete of revisions/events, full reconstruction through before/after references, private values absent from events and public output, exact retry idempotency, two-session stale-base conflict, rollback on event/dependency failure, field-local regeneration, rejected candidate preserving prior approval, sentence approval staling only declared dependents, and no orphaned referenced media.

---

### `domain/jobs.py`, `job_repository.py`, per-item/per-stage outcomes, and resume tests

**Primary analog:** current resumable repository, but extend its data model rather than adding more mutable counters.

**Current item identity and idempotent success seam** (`job_repository.py:125-185`):

```python
def list_completed_item_keys(self, run_key: str) -> set[str]:
    rows = self.session.scalars(
        select(GenerationItem.item_key).where(
            GenerationItem.run_key == run_key,
            GenerationItem.status == JobStatus.COMPLETED.value,
        )
    )
    return set(rows)

if item and item.status == JobStatus.COMPLETED.value:
    ...
    if previous_stage == completed_stage:
        job.skipped_duplicates += 1
```

Retain stable run/item lookup and duplicate-safe transitions, but replace “one status plus last completed stage” as authority with persisted outcomes for each relevant task/stage: ingest, lexical resolution, definition, sentence, translation, review, word audio, sentence audio, and prepared-export readiness.

Each outcome stores at least `pending|processing|accepted|review_required|failed`, `processed_at`, attempt count, controlled reason code, exact input/output/authority/policy hashes, and timestamps. Only `accepted` required outcomes count as stage success. Automatic validation acceptance is distinct from explicit field approval.

**Resume diagnostic shape** (`job_repository.py:285-328`):

```python
completed_items = [item for item in items if item.status == JobStatus.COMPLETED.value]
failed_items = [item for item in items if item.status == JobStatus.FAILED.value]
...
if not mismatches:
    return None
return ResumeDiagnostic(
    job_id=job.id,
    reason="persisted resume state is inconsistent",
    details={"mismatches": mismatches},
)
```

Recompute job aggregates from persisted outcome truth; counters are projections, never independent authority. Default resume skips current accepted work, retries pending and explicitly retryable failures idempotently, and leaves review-required fields for explicit review/regeneration. Do not mark review-required or failed audio as complete.

At each item/task boundary, catch provider/parser/validation/persistence/media exceptions, roll back only that item's short transaction, persist a controlled redacted failure, then continue. A global authority/budget/policy circuit breaker may stop the bounded batch but must persist truthful denominators.

**Tests:** extend `test_job_repository.py:66-154` and `:186-247` for duplicate-safe retries and exact authority drift. Add mixed accepted/review/failed stages, processed-but-incomplete audio, aggregate reconstruction after deliberate counter corruption, remaining-item continuation after one exception, retry taxonomy, exact input-policy idempotency, and resume refusing stale revision/authority hashes.

---

### ORM, Alembic, indexes, and schema-parity tests

**Primary analogs:** `db/models.py` and `20260821_18_frequency_text_audio_evidence.py`.

**SQLAlchemy shape** (`db/models.py:193-220`):

```python
class GenerationItem(Base):
    __tablename__ = "generation_items"
    __table_args__ = (
        UniqueConstraint("run_key", "item_key", name="uq_generation_items_run_key_item_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
```

Use explicit primary keys, named unique constraints, indexed foreign keys, timezone-aware timestamps, and bounded string columns. Add composite indexes matching real list/resume queries, with equality columns first—for example `(job_id, item_key, stage/task)` and `(job_id, outcome, input_position)`—rather than many unrelated single-column indexes.

Historical rows must remain valid. Add new nullable columns or new tables; do not reinterpret old mutable text/audio rows as revision history. Use check constraints for bounded outcome/field/action vocabularies where migration portability permits, and matching Pydantic/ORM validation regardless.

**Additive migration style** (`20260821_18_frequency_text_audio_evidence.py:9-30,68-118`):

```python
revision = "20260821_18"
down_revision = "20260804_17"

def upgrade() -> None:
    op.add_column(
        "generation_items",
        sa.Column("stage_evidence", sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("generation_items", "stage_evidence")
```

Do not copy the literal revision pair. `20260821_18` is currently untracked Phase 32 work. Determine the unique live Alembic head only after Phase 32 coordination, then create one linear Phase 33 migration. Migration plans must update ORM, repositories, and real upgrade/downgrade/re-upgrade parity in one lane.

**Database safety:** avoid SELECT-then-INSERT races for unique transitions; use the database constraint plus atomic insert/conflict handling. Keep transactions short and never hold a lock while calling a provider or reading remote data. Every foreign key used by joins/cascades needs an index.

---

### `cli.py` and Phase 33 CLI tests

**Primary analog:** injected Typer app plus fixed Korean foundation commands.

**Composition and subcommand pattern** (`cli.py:684-700`):

```python
def create_app(... ) -> typer.Typer:
    """Build the CLI application with injectable collaborators for tests."""
    cli = typer.Typer(help="Multilang operator CLI.")
    korean_foundations = typer.Typer(
        help="Operate the fixed Korean foundation evidence and export workflow."
    )
    cli.add_typer(korean_foundations, name="korean-foundations")
```

Add one coherent Phase 33 review/decision group rather than many unrelated root commands. Inject services through `create_app` only if the signature change is coordinated with the exact signature-lock test.

**Typed options, controlled error, safe output** (`cli.py:767-786`):

```python
@korean_foundations.command("validate-and-write-receipt")
def validate_and_write_korean_foundation_receipt(
    confirmed_index_sha256: Annotated[
        str,
        typer.Option("--confirmed-index-sha256", callback=_validate_foundation_sha256),
    ],
) -> None:
    try:
        receipt = validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=confirmed_index_sha256
        )
    except ValueError as exc:
        _fail_korean_foundation_operation(exc)
    typer.echo(f"receipt_sha256={_foundation_receipt_sha256(receipt)}")
```

Every mutating Phase 33 command requires exact job, item, field, candidate revision, and expected current/base identity plus controlled actor/reason inputs. Use enums and SHA validators. Do not add `--force`, `--allow-unapproved`, arbitrary provider/module/template/URL/publication options, or a private-path bypass.

Default output contains IDs, hashes, states, counts, and controlled codes. Exact excerpt/revision values require an explicit local-display option and must never appear in aggregate JSON, diagnostics, logs, or telemetry. A provider invocation, parsed response, synthesis success, or DB write is not approval.

**CLI tests:** copy exact command/option allowlist assertions from `test_korean_foundation_commands.py:177-200`, malformed-input service poisoning from `:203-268`, and controlled-vs-unexpected exception behavior from `:644-678`. Add exact revision targeting, stale-base conflict, private display opt-in, no private output on failure, and no hidden network/provider construction tests.

## Exact Upstream Dependency Joins

### Phase 31

**Source:** `ResolvedKoreanFoundationSnapshot` (`korean_foundation_snapshot.py:526-547`) and `resolve_active_korean_foundation_snapshot()` (`:1107-1154`).

Bind and revalidate:

- active pointer provenance, not `current-candidate`;
- `bundle_sha256`;
- `receipt_sha256`;
- `snapshot_manifest_sha256`;
- `snapshot_root_sha256`;
- exact imported concept-registry member hash and IDs.

Resolve once. Candidate, v1 history, synthetic fixture, request-only evidence, stale pointer, or inactive prepared snapshot cannot establish production known state.

### Phase 32

The live Phase 32 surfaces are dirty/untracked and therefore contracts to join only after they land:

- `KoreanFrequencyTextAudioEvidence` (`domain/korean.py:985-1012`) for exact Phase 31/frequency/provider hash tuples;
- `KoreanFrequencyJobAuthority` (`domain/korean.py:1014-1094`) for staged provider authority;
- `KoreanFrequencyEntry` (`domain/korean.py:1097-1161`) for exact source-backed lexical identity;
- `KoreanFrequencyBundleManifest` (`domain/korean.py:1164-1252`) and `korean_frequency.py` validation for bundle/source hashes;
- Phase 32 audio columns (`db/models.py:353-362`) for voice/profile/catalog/request/artifact/review bindings;
- provider route/budget/cache/schema hashes (`db/models.py:131-134`).

Grammar bootstrap/custom/highlight code persists exact consumed bundle/source/version/entry hashes and the selected identity. Frequency membership never means “known.” Provider/text/audio code may run only against exact approved route, budget, voice/profile, and review bindings. Merely finding a Phase 32 file does not activate it.

## Shared Patterns

### Authentication and Authorization

There is no HTTP authentication layer in Phase 33. The effective guards are local CLI scope, fixed commands, exact job/item/revision identifiers, immutable hash-bound upstream artifacts, qualified actor identity, and least-power authority receipts. Do not add web auth or interpret local filesystem access as provider/private-processing authority.

### Frozen, Bounded, and Content-Free Models

Use `ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)`, bounded strings/collections, enums/Literals, tuple order, lowercase SHA-256, NFC Korean, and controlled reason codes. Errors must not echo Korean excerpts, submitted private values, local paths, prompts, provider payloads, raw analyzer output, reviewer notes, credentials, or tracebacks.

### Canonical Identity and Hashing

- Store/tag `ko`; use `ko-KR` only for provider locale.
- NFC-normalize before identity and content hashes; reject Compatibility/halfwidth Hangul rather than hiding it through NFKC.
- Structured evidence hashes use canonical UTF-8 JSON with sorted keys, compact separators, `ensure_ascii=False`, and `allow_nan=False`.
- Artifact/excerpt/media hashes use exact bytes.
- Distinguish locator, content, canonical-object, and raw-byte hashes in field names.

### Privacy and LLM Security

- Treat highlight text as untrusted data, never instructions.
- Full excerpts are local-only. Derived provider context is separately typed, redacted, target-centered, <=24 tokens, hash-bound, and authority-gated.
- Provider output can propose learner content; it cannot set identity, graph truth, route, approval, authority, or policy.
- Re-sanitize parser input, typed requests, adapter payloads, persistence projections, CLI output, reports, and exceptions.
- Telemetry is hashes/codes/counts only.

### Transactions and Error Handling

- Validate and make external calls before a short DB transition transaction.
- Atomically insert candidate revision, compare-and-swap pointer, stale dependents, and event.
- A stale base, malformed authority, dependency drift, or uniqueness conflict fails without partial writes.
- Catch heterogeneous operational exceptions only at item/task boundaries, map them to controlled redacted failures, and continue the bounded batch. Unexpected programmer errors at CLI boundaries remain unhandled, matching `test_korean_foundation_commands.py:644-678`.

### Existing-Mode Isolation

Keep normal/highlight field order, source profiles, templates, blank `Image`, note IDs, and GUID formulas unchanged. Do not migrate frozen Latin/foundation history into Phase 33 revisions automatically. Existing Japanese, Mandarin, Latin, frequency, phoneme, custom-list, and highlight tests remain regression gates.

## Test Pattern Matrix

| Phase 33 Area | Existing Test Pattern | Required New Assertion |
|---|---|---|
| Grammar bundle/overlay | `test_korean_curriculum.py`; `test_korean_foundation_snapshot.py` | exact active snapshot bound once; immutable overlay; collision/cycle/closure/drift refusal |
| Strict G0-G13 evidence | strict recomputation tests in `test_korean_curriculum.py` | exactly one construction unknown after imported foundation + ordered bootstrap |
| Normal projection | `test_assemble_export_cards.py`; `test_v13_normal_template_export_contract.py` | deterministic reversible Definitions projection; approved revisions only; blank Image/GUID unchanged |
| Ordered custom ledger | `test_word_list_parser.py`; `test_custom_word_list_e2e_export_flow.py` | every nonblank row persists; duplicates visible; reordered fingerprint differs; submitted order survives reload |
| Morphology/bridge decisions | Korean grounding/morphology tests | inflection/compound resolution; ambiguity needs review; explicit bridge/defer; no automatic card |
| Highlight privacy | `test_highlight_candidate_extraction.py`; `test_highlight_import_repository.py` | exact excerpt private; public hash/index only; microexample distinct; source excerpt never exported |
| Context authority | `test_korean_checkpoint_authority.py`; `test_text_generation.py` | no authority => `None` and zero provider calls; exact scope/expiry/budget/route/policy enforcement |
| Field revisions/events | text/audio repository round trips | immutable values; append-only hash/reference events; reconstructable history; no copied private values |
| Dependency invalidation | audio integrity + review tests | changed sentence stales bound translation/sentence audio only; old revisions retained |
| Item/stage outcomes | `test_job_repository.py`; text/audio job flows | processed != accepted; one item failure does not abort rest; aggregates derive from persisted truth |
| Migration | `test_migration_schema_parity.py` | unique linear head after Phase 32; nullable compatibility; upgrade/downgrade/re-upgrade; ORM parity/indexes |
| CLI | `test_korean_foundation_commands.py` | exact command/options; exact revision targeting; stale conflict; private display opt-in; safe output |
| Offline integration | Korean modern, custom-list, and Kindle local flows | no network/provider/asset publication; synthetic fixtures cannot satisfy production readiness |

## No Single Exact Analog Found

| File/Area | Why | Planner Direction |
|---|---|---|
| Phase 33 grammar bundle and registry overlay | Phase 31 owns complete orthography/phonology snapshots but no additive imported-root grammar overlay. | Compose snapshot single-resolution, frozen manifests, and curriculum graph recomputation. Never mutate Phase 31. |
| Custom bridge/defer decision ledger | Current custom lists drop exact duplicates and have no prerequisite decision model. | Create ordered row/outcome records and explicit decision transitions; never auto-insert bridges. |
| Immutable field revisions/current pointers/append-only events | Current text/audio repositories update rows in place. | Build new revision/pointer/event tables and one atomic optimistic service; do not retrofit mutable rows as history. |
| Per-item/per-stage truthful outcomes | Current `GenerationItem` stores one status and a last stage, with mutable aggregate counters. | Add task/stage outcomes and derive completion/aggregates from accepted required facts. |
| Private provider-context authority | Current text request sanitizes supplied context but does not establish exact disclosure authority. | Compose least-power receipt validation and sanitizer; absent or drifted authority means no provider context. |

## Dirty and Contended Surfaces

The worktree was already dirty before this map. Do not reset, rebase, overwrite, stage, or “clean up” these changes from Phase 33 plans.

**Dirty shared production/test files:**

- `src/multilang/cli.py`
- `src/multilang/db/models.py`
- `src/multilang/domain/audio.py`
- `src/multilang/domain/korean.py`
- `src/multilang/domain/lexicon.py`
- `src/multilang/domain/text_quality.py`
- `src/multilang/repositories/audio_repository.py`
- `src/multilang/repositories/job_repository.py`
- `src/multilang/repositories/lexical_repository.py`
- `src/multilang/repositories/text_repository.py`
- `scripts/build_frequency_assets.py`
- `tests/repositories/test_job_repository.py`
- `tests/repositories/test_lexical_repository.py`
- `tests/test_migration_schema_parity.py`

**Untracked Phase 32 contracts that Phase 33 may consume but must not silently adopt as settled:**

- `alembic/versions/20260821_18_frequency_text_audio_evidence.py`
- `src/multilang/services/authority_locator.py`
- `src/multilang/services/korean_checkpoint_authority.py`
- `src/multilang/services/korean_frequency.py`
- `src/multilang/services/korean_source_review.py`
- `tests/repositories/test_phase32_text_audio_evidence.py`
- their CLI/service/repository/integration tests and Phase 32 evidence inbox

**Planning-state changes are also pre-existing:** `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/.state-fingerprint.json`, and Phase 32 plan/summary/evidence files.

**Sibling worktrees:** `/tmp/multilang-phase31-ai` and `/tmp/multilang-phase31-media` contain dirty Phase 31 activity. Treat foundation authority, data, and shared CLI/runtime surfaces as coordinator-owned joins.

## Disjoint Write Lanes for the Planner

| Lane | Safe Initial Ownership | Deferred Coordinator Join |
|---|---|---|
| A — grammar contracts | new `domain/korean_grammar.py`, `services/korean_grammar.py`, synthetic fixtures, focused tests | `domain/korean.py`, real grammar data, active Phase 31/32 hash join, export readiness |
| B — personal sources/privacy | new `domain/personal_sources.py`, `korean_personal_sources.py`, private-context service, focused tests | parser/fingerprint changes, highlight/text-generation wiring, CLI |
| C — revision/review | new `domain/revisions.py`, `revision_repository.py`, `field_review.py`, focused tests | ORM tables, Alembic, text/audio compatibility, CLI |
| D — job outcomes | new outcome contracts and focused service tests where possible | dirty `job_repository.py`, `db/models.py`, migration, aggregate/report wiring |
| E — integration join | no early shared-file edits | after Phase 32 head/contracts settle: migration, models, CLI, exporting/assembly, full regressions |

Do not let parallel lanes independently edit `cli.py`, `db/models.py`, the Alembic head, `domain/korean.py`, `job_repository.py`, or `test_migration_schema_parity.py`. Assign those files to one integration owner after upstream reconciliation.

## Planner Guardrails

1. Begin with failing offline contracts for exact joins, ordered rows, graph truth, privacy refusal, immutable revisions, and truthful outcomes.
2. Build grammar bundle/graph validation before content review/media joins.
3. Build revision contracts before mutating review CLI commands.
4. Build item/stage truth before resume/report aggregation.
5. Refactor “no authority means no context” before any provider path can receive highlight context.
6. Do not create production grammar/bootstrap assets from synthetic fixtures or model output.
7. Do not create the Phase 33 migration until the unique post-Phase-32 Alembic head is known.
8. Do not change GUID semantics, source modes, layouts, or field order.
9. Keep provider/network tests offline and injected; planning does not authorize credentials or spend.
10. Missing Phase 31/32/review/media/private-processing authority yields complete offline machinery plus blocked/review-required records, not fabricated learner-ready output.

## Metadata

**Analog search scope:** `.planning/SPEC.md`, `.planning/ROADMAP.md`, Phase 31/32 approach/pattern artifacts, `src/multilang/domain`, `services`, `repositories`, `security`, `db`, Alembic migrations, CLI, and focused domain/service/repository/CLI/integration tests.

**Primary analog set:** Korean curriculum graph; active foundation snapshot; ordered word-list/highlight ingestion; job repository/resume; explicit text/audio persistence; least-power Korean authority; normal-card projection; Typer command group.

**Pattern extraction date:** 2026-08-28.

**Worktree policy:** This mapping writes only `33-PATTERNS.md`. All source and other planning changes are pre-existing and remain untouched.
