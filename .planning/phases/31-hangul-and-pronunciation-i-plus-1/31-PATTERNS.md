# Phase 31: Hangul and Pronunciation i+1 - Pattern Map

**Mapped:** 2026-08-24
**Planning scope:** Replanned execution sequence 31-11 through 31-28
**Coverage:** Every new or modified artifact named by those plans is classified below; related artifacts are grouped where they share one contract and analog.

## Scope Truth

- `31-APPROACH.md` and `31-RESEARCH.md` both exist and govern this map.
- Plans 31-01 through 31-10 already established the domain, curriculum, review, media, evidence, snapshot, export, CLI, and test patterns. Plans 31-11 through 31-28 must extend those patterns rather than create a parallel architecture.
- Assisted curation is `draft_only`: it may propose bounded learner-copy patches and report uncertainty, but it cannot approve linguistic content, Portuguese, rights, playback, evidence, activation, release, or Anki acceptance.
- All coordination and production operations use fixed repository roots and exact lowercase SHA-256 values. Arbitrary input paths, URLs, archives, provider hooks, and import surfaces remain forbidden.
- The four v2 candidate members live in one immutable hash-named bundle exposed through one atomic `current-candidate.json` pointer. v1 remains immutable historical data; ordinary candidate defaults move coherently to that complete v2 bundle only after promotion.
- Review and media manifests remain `candidate_only` with pending gates after promotion. Selection is promotion authority only; it is not review authority.
- Evidence validation precedes receipt writing; preparation precedes activation; read-only verification precedes exact activation authorization; export resolves only the active immutable snapshot.
- Phase 31 may prove structurally and media-valid local exports. Observed Anki Desktop/mobile import, rendering, and playback acceptance remains Phase 34.

## File Classification

| New/Modified File or Artifact Group | Role | Data Flow | Closest Existing Analog | Match Quality |
|---|---|---|---|---|
| `src/multilang/services/korean_foundation_ai_curation.py` | service | transform, batch, file-I/O | `src/multilang/services/korean_curriculum.py`; `korean_foundation_review.py` | role + flow match |
| `scripts/build_korean_foundation_candidates.py` | utility/CLI | batch, transform, file-I/O | `scripts/build_frequency_assets.py`; fixed command surface in `src/multilang/cli.py` | role match |
| `tests/services/test_korean_foundation_ai_curation.py` | test | batch, transform, file-I/O | `tests/services/test_korean_curriculum.py`; evidence/export failure tests | role + flow match |
| Six compact projections under `curation-drafts/inputs/`: H0-H3, H4-H7, H8-H10, P0-P4, P5-P9, P10-P13 | config/data | bounded batch input | v1 source-pack entries plus frozen curriculum models | schema match |
| Six matching batch drafts under `curation-drafts/` | config/data | batch, transform | compact projections plus frozen patch contracts | schema match |
| Two family drafts: `hangul-v2-draft.json`, `pronunciation-i-plus-1-v2-draft.json` | config/data | batch, transform | `data/korean_foundations/hangul-v1.json`; `pronunciation-i-plus-1-v1.json` | exact shape, new version |
| `curation-drafts/draft-manifest.json` | config/data | batch, transform | hash-bound curation/media manifests | role + flow match |
| `31-AI-CURATION-REPORT.md` | config/audit report | batch, transform | existing Phase 31 request contracts and summaries | partial match |
| `scripts/phase31_handoff.py` | utility/CLI | request-response, file-I/O | fixed evidence APIs and atomic receipt writer | composite role match |
| `tests/services/test_phase31_handoff.py` | test | request-response, file-I/O | `tests/services/test_korean_foundation_evidence.py`; CLI surface tests | role + flow match |
| `execution-handoffs/curation-selection.json`, `evidence-confirmation.json`, `activation.json` | config/audit record | event-driven, file-I/O | validation receipt and active pointer contracts | role match |
| `data/korean_foundations/candidate-bundles/<bundle-sha256>/` manifest plus four exact v2 members | config/data | batch, transform, immutable publication | v1 schemas plus hash-named snapshot staging | composite exact match |
| `data/korean_foundations/current-candidate.json` | config/candidate pointer | event-driven, file-I/O | atomic active-foundations pointer | exact publication pattern, non-production authority |
| `31-CURRICULUM-REVIEW.md`, `31-AUDIO-PLAYBACK-REVIEW.md` | config/request contract | request-response, transform | the same v1 request contracts | exact self-extension |
| `korean_curriculum.py`, `korean_foundation_review.py`, `korean_foundation_media.py` | service | file-I/O, transform | their current v1 fixed-default loaders and gates | exact self-extension |
| Their three service tests | test | file-I/O, transform | existing fixed-loader, pending-gate, and drift tests in the same files | exact self-extension |
| `korean_foundation_evidence.py`, `korean_foundation_snapshot.py`, `korean_foundation_export.py` | service | request-response, file-I/O | their current fixed v1 workflow | exact self-extension |
| Their three service tests | test | request-response, file-I/O | existing atomicity, write-poison, drift, and export tests in the same files | exact self-extension |
| `scripts/verify_phase31_runtime_isolation.py` | utility | batch, process/file-I/O | temporary-root and state-digest mechanics in Phase 31 tests | partial; no standalone analog |
| `tests/services/test_phase31_runtime_isolation.py` | test | batch, process/file-I/O | snapshot write-poison tests and integration canonical-state digests | role + safety match |
| `tests/cli/test_korean_foundation_commands.py` | test | request-response | existing exact command/option allowlist in the same file | exact self-extension |
| `tests/integration/test_korean_foundations_flow.py` | test | request-response, file-I/O | existing private full evidence-to-six-export flow | exact self-extension |
| Exact fixed members under `evidence-inbox/` | config/evidence data | batch, file-I/O | `KoreanFoundationEvidenceIndex` and fixed inbox validator | exact contract |
| `evidence-inbox/validation-receipt.json` | config/audit record | request-response, file-I/O | `KoreanFoundationValidationReceipt` | exact contract |
| `data/korean_foundations/snapshots/<bundle-sha256>/` | model/immutable snapshot | batch, file-I/O | current hash-named staged snapshot implementation | exact contract |
| `data/korean_foundations/active-foundations.json` | config/active pointer | event-driven, file-I/O | `KoreanFoundationActivePointer` and atomic activation | exact contract |
| Six outputs under `.multilang/exports/korean-foundations/` | export artifacts | batch, file-I/O | current APKG/CSV/TSV staged writers and deep inspectors | exact contract |

## Pattern Assignments

### `korean_foundation_ai_curation.py`, candidate script, draft JSON, and curation tests

**Primary analogs:**

- `src/multilang/services/korean_curriculum.py`
- `src/multilang/services/korean_foundation_review.py`
- `scripts/build_frequency_assets.py`

**Imports and ownership pattern** — keep schemas/validation in the service and leave argument parsing/orchestration in the script (`scripts/build_frequency_assets.py:3-18`):

```python
from __future__ import annotations

import argparse
from pathlib import Path

from multilang.domain.jobs import SupportedLanguage
from multilang.services.frequency_decks import (
    CURATED_COLUMNS,
    load_curated_frequency_entries,
)
```

For Phase 31, import the frozen Korean curriculum/review contracts in the service; the script should call service functions rather than duplicate model or hash logic.

**Frozen fail-closed models** — copy directly from `korean_curriculum.py:330-337`:

```python
class _FrozenManifest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )
```

Apply this to batch proposals, family drafts, manifest entries, uncertainty/disagreement records, and promotion inputs. Bound string lengths and collection counts with `Field`; use tuple fields for deterministic order. Unknown fields and authority-bearing fields must fail closed.

**Canonical hash pattern** — reuse, do not redefine incompatibly (`korean_curriculum.py:340-352`):

```python
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

Every draft record must bind the exact base source-pack version, item key/sequence, base content hash, and allowed learner-copy patch. The family and global manifests must hash deterministic ordered child bindings.

**CLI/parser pattern** — use a fixed command vocabulary and enum/choice validation, adapting the standalone script pattern at `scripts/build_frequency_assets.py:212-232`:

```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=DEFAULT_SUPPORTED_LANGUAGES)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_assets(...)
    else:
        build_assets(...)

if __name__ == "__main__":
    main()
```

For the new script, commands and batch/family names are fixed choices: `validate-batch`, `assemble-family`, `assemble`, `validate-drafts`, `check-selection`, `promote`, `verify-promoted`, and `regenerate-requests` only when introduced by the corresponding plan. Do not expose arbitrary draft, data, manifest, or handoff paths.

**Authority boundary** — promoted candidate manifests still fail readiness (`korean_foundation_review.py:806-826`):

```python
manifest = snapshot.curation_manifest
validate_korean_foundation_curation(...)
if manifest.candidate_only:
    _raise(KoreanFoundationReviewReasonCode.CANDIDATE_MANIFEST_NOT_ACTIVE)
summary = summarize_korean_foundation_review(manifest)
if summary.learner_ready_records == summary.total_records:
    return
_raise(KoreanFoundationReviewReasonCode.REVIEW_NOT_READY, ...)
```

Draft generation may change only plan-approved learner-copy fields. It must preserve identity, order, structure, prerequisite graph, media-slot identity, and all pending review state. Uncertain records stay explicit; never silently convert uncertainty into approval.

**Testing pattern:**

- Assert model immutability, `extra="forbid"`, bounded sizes, lowercase hashes, stale-base rejection, NFC-safe learner copy, and no structural/authority fields.
- Validate each batch independently, then require exact nonoverlapping family coverage and exact 92 + 47 global coverage.
- Hash repeated assembly outputs and require byte/content determinism, following the repeated-export comparison style in `tests/services/test_korean_foundation_export.py:973-1016`.
- Poison promotion writers for every validation-failure test and compare complete pre/post trees.

---

### Batch drafts, family drafts, `draft-manifest.json`, and `31-AI-CURATION-REPORT.md`

**Asset analogs:** the immutable v1 source packs and request contracts.

The family draft must retain the source-pack envelope. Existing files begin with the exact identity pair (`hangul-v1.json:3-4`, `pronunciation-i-plus-1-v1.json:3-4`):

```json
{
  "family": "hangul",
  "source_pack_version": "hangul-v1"
}
```

```json
{
  "family": "pronunciation",
  "source_pack_version": "pronunciation-i-plus-1-v1"
}
```

Adapt versions to v2 only in assembled/promoted v2 artifacts. Batch drafts are noncanonical proposal envelopes and must preserve explicit base-v1 bindings.

**Manifest pattern** — mirror the typed, hash-bound envelope at `korean_foundation_review.py:407-429`:

```python
class KoreanFoundationCurationManifest(_FrozenReviewModel):
    schema_version: Literal[1] = 1
    manifest_version: Literal["korean-foundations-v1-curation"]
    candidate_only: bool
    registry_version: str = Field(...)
    registry_content_sha256: str = Field(min_length=64, max_length=64)
    hangul_source_pack_sha256: str = Field(min_length=64, max_length=64)
    pronunciation_source_pack_sha256: str = Field(min_length=64, max_length=64)
    records: tuple[KoreanFoundationCurationRecord, ...] = Field(...)
    content_hash: str = Field(min_length=64, max_length=64)
```

`draft-manifest.json` should bind both complete family drafts, every batch hash, deterministic coverage, and aggregate uncertainty/disagreement counts. It grants no approval.

**Report pattern:** preserve the explicit non-evidence wording used by `31-CURRICULUM-REVIEW.md:1-7` and `31-AUDIO-PLAYBACK-REVIEW.md:1-7`: request/report artifacts supply no human, legal, rights, or playback evidence, and status remains `needs_review`. Report exact hashes/counts and named blockers; do not use prose as a later machine authority source.

---

### `scripts/phase31_handoff.py`, handoff tests, and `execution-handoffs/*.json`

**Primary analog:** `src/multilang/services/korean_foundation_evidence.py`.

**Fixed roots** — define constants, not caller-selected paths (`korean_foundation_evidence.py:44-52`):

```python
PHASE31_EVIDENCE_INBOX: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox"
)
PHASE31_EVIDENCE_INDEX: Final = PHASE31_EVIDENCE_INBOX / "evidence-index.json"
PHASE31_VALIDATION_RECEIPT: Final = (
    PHASE31_EVIDENCE_INBOX / "validation-receipt.json"
)
```

The handoff utility should similarly own one fixed `execution-handoffs/` root and exact filenames per kind. Its public arguments are operation names plus lowercase hashes only.

**Typed hash contract** — copy strict model and digest validation from `korean_foundation_evidence.py:217-232`:

```python
class _FrozenEvidenceModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

def _sha256_text(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _LOWERCASE_HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value
```

Each handoff needs a typed kind/version, the exact relevant current-artifact bindings, and a canonical self-hash. Selection binds the current draft manifest; evidence confirmation binds the current evidence index; activation binds the current receipt/prepared tuple.

**Validation-before-write and idempotency** — copy operation order from `korean_foundation_evidence.py:2252-2301`:

```python
with _korean_foundation_state_lock(paths.project_dir):
    validated = _validate_fixed_evidence(...)
    _assert_state_unchanged(paths, validated)
    receipt = _derive_receipt(validated)
    receipt_raw = _json_file_bytes(receipt)
    _assert_state_unchanged(paths, validated)
    if _receipt_exists(paths):
        if existing == receipt_raw:
            return receipt
        _raise(KoreanFoundationEvidenceReasonCode.STALE_RECEIPT)
    _assert_state_unchanged(paths, validated)
    _atomic_write_receipt(paths, receipt_raw)
```

An identical retry returns the existing binding without rewriting. A nonidentical existing handoff is a hard refusal, not replacement.

**Atomic write and cleanup** — adapt `korean_foundation_evidence.py:2201-2243`:

```python
descriptor, temporary_name = tempfile.mkstemp(
    prefix=".validation-receipt.", suffix=".tmp", dir=paths.inbox
)
with os.fdopen(descriptor, "wb", closefd=True) as handle:
    handle.write(raw)
    handle.flush()
    os.fsync(handle.fileno())
os.replace(temporary_name, paths.receipt)
_fsync_parent_directory(paths.inbox)
```

Retain secure temp permissions where available, `lstat`/symlink/reparse rejection, parent `fsync`, failure cleanup, content-free errors, and no arbitrary path surface.

**Surface tests** — copy exact allowlist/signature assertions from `tests/cli/test_korean_foundation_commands.py:30-43,167-190`. For the handoff script, lock the exact operations and parameters and prove there is no filesystem option. Evidence tests show the public pathless pattern at `tests/services/test_korean_foundation_evidence.py:978-1020`.

---

### One immutable four-member v2 bundle and regenerated review requests

**Primary analogs:** the four v1 assets, their model classes, hash-named snapshot staging, and one-pointer publication.

**Direct file pairing:**

| Exact member inside `candidate-bundles/<bundle-sha256>/` | Copy schema/order from |
|---|---|
| `hangul-v2.json` | `hangul-v1.json` |
| `pronunciation-i-plus-1-v2.json` | `pronunciation-i-plus-1-v1.json` |
| `korean-foundations-v2-curation.json` | `korean-foundations-v1-curation.json` |
| `korean-foundations-v2-media.json` | `korean-foundations-v1-media.json` |

The current curation and media manifests explicitly encode `candidate_only` (`korean_foundation_review.py:407-429`; `korean_foundation_media.py:653-675`). Keep that field true and every gate/status pending in the v2 candidates.

**All-or-nothing staged publication** — adapt the directory staging pattern from `korean_foundation_snapshot.py:1686-1720`:

```python
stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=paths.snapshot_root))
for member in state.authority.copy_members:
    _copy_member_to_stage(stage, member)
_write_manifest_to_stage(stage, state.manifest_raw)
_fsync_stage_directories(stage)
_validate_staged_snapshot(state, stage)
_rename_snapshot_stage(stage, state.target)
_fsync_directory(paths.snapshot_root)
```

Stage one canonical bundle manifest plus all four exact members, fully validate selected-manifest identity, immutable v1 prestate, allowed-field-only diffs, bundle/member prestates, and staged bytes, then rename the immutable hash-named directory and atomically replace only `current-candidate.json`. Concurrent readers observe no/old or complete new bundle. A pre-existing exact unreferenced bundle is retryable only when every byte matches; nonidentical bundle/pointer state is refusal. Clean only the operation's own temporary state.

**Request regeneration:** keep `request_status="needs_review"`, `evidence_supplied=false`, exact selector coverage, fixed future evidence filenames, and the request-only disclaimer. Replace all v1 candidate bindings/projection digests with coherent v2 bindings. Never preserve a stale v1 hash beside a v2 label.

---

### v2 defaults with explicit v1 history

**Files:** curriculum, review, media, evidence, snapshot, export services and their tests.

**Current default pattern to migrate** — `korean_curriculum.py:32-40`:

```python
KOREAN_FOUNDATION_DATA_ROOT: Final = Path("data") / "korean_foundations"
DEFAULT_KOREAN_HANGUL_SOURCE_PACK_PATH: Path = (
    KOREAN_FOUNDATION_DATA_ROOT / "hangul-v1.json"
)
DEFAULT_KOREAN_PRONUNCIATION_SOURCE_PACK_PATH: Path = (
    KOREAN_FOUNDATION_DATA_ROOT / "pronunciation-i-plus-1-v1.json"
)
```

Change ordinary candidate defaults coherently across all six services by resolving `current-candidate.json` once and validating the complete declared bundle. Preserve v1 only through an explicit historical path/version branch; do not add candidate fallback, root-level v2 lookup, or mixed v1/v2 auto-detection.

**Versioned compatibility pattern** — copy the complete-discriminator rule from `korean_foundation_snapshot.py:303-359`:

```python
schema_version: Literal[1, 2] = 1
...
if self.schema_version == 1:
    if any(value is not None for value in provenance):
        raise ValueError("legacy pointer cannot contain activation provenance")
    return self
if any(value is None for value in provenance):
    raise ValueError("active pointer provenance must be complete")
```

Likewise, v1 and v2 asset tuples must each be internally complete. Reject mixed source pack, curation, media, request, evidence, snapshot, and export identities. For v2, revalidate every provenance tuple as snapshot resolution does at `korean_foundation_snapshot.py:1120-1141`.

**Test surface:** preserve fixed/pathless production loaders. The current test at `tests/services/test_korean_curriculum.py:417-463` locks no-argument fixed loaders and forbids path/root/URL/archive/APKG parameters. Add explicit historical loading without weakening the production no-path contract, and test:

- defaults resolve the exact promoted v2 tuple;
- explicit v1 history still loads and validates;
- mixed v1/v2 tuples fail before evidence, snapshot, pointer, or export writes;
- missing v2 never falls back to v1;
- v1 bytes and hashes remain unchanged.

---

### `verify_phase31_runtime_isolation.py` and runtime-isolation tests

**Closest analogs:** no standalone repository script exists. Compose the helper from fixed-root rules, canonical tree-digest helpers in `tests/integration/test_korean_foundations_flow.py`, and the completed Plan 31-10 isolated command contract.

Required fixed behavior:

- operations are exactly `prepare` and `hash-venv`;
- isolated environment is exactly current-user mode-0700 `/tmp/multilang-phase31-py312`, directly beneath root-owned sticky `/tmp`, after containment/identity checks;
- repository `.venv` is read-only input to `hash-venv` and is never removed, synchronized, or modified;
- reject symlink/reparse roots and unsafe pre-existing filesystem types using `lstat` before cleanup/preparation;
- hash deterministic relative paths, file bytes, type, and relevant mode metadata; do not use mtimes as identity;
- `prepare` removes/recreates only that fixed direct child after proving `/tmp` sticky ownership/mode plus child containment, ownership, mode, and type safety; it never traverses `/tmp/opencode`;
- no shell interpolation, provider calls, network setup, arbitrary root, or environment-selected destination.

**Write-poison test pattern** — reuse `tests/services/test_korean_foundation_snapshot.py:269-334`:

```python
def forbidden(*_args: object, **_kwargs: object) -> Any:
    raise AssertionError("strictly read-only verification attempted a write")

write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
...
if flags & write_flags:
    return forbidden(...)
```

Add containment, symlink/reparse, wrong-type, exact-root, deterministic-hash, and shared-`.venv` invariance tests. High-level CLI/integration fixtures should bind v2 but otherwise retain their existing fixed command seams.

---

### Genuine evidence intake, validation receipt, and inactive snapshot

**Primary analogs:** `korean_foundation_evidence.py` and `korean_foundation_snapshot.py`.

**Evidence intake:** place only the exact fixed member set under the fixed inbox. There is no importer. `inspect_fixed_korean_foundation_evidence_inbox()` is read-only (`korean_foundation_evidence.py:2246-2249`), while the only receipt writer takes the independently confirmed index hash (`2252-2269`).

**Filesystem safety:** preserve recursive `lstat`, symlink/reparse rejection, archive/path rejection, bounded member sizes, exact member-set checking, and content-free errors. The adversarial test pattern is concrete at `tests/services/test_korean_foundation_evidence.py:1146-1184`: mutate a required member into a symlink/reparse point, require `unsafe_filesystem_component`, no receipt/temp file, an identical tree, and no leaked path in the exception.

**Validation receipt:** derive it only after complete fresh semantic validation and a post-validation prestate recheck. Publish atomically and allow byte-identical retry only. `tests/services/test_korean_foundation_evidence.py:1187-1218` demonstrates asserting that the receipt is the sole changed path and its payload self-hash is canonical.

**Inactive snapshot:** use fixed paths (`korean_foundation_snapshot.py:41-57`):

```python
ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH = (
    Path("data") / "korean_foundations" / "active-foundations.json"
)
KOREAN_FOUNDATION_SNAPSHOT_ROOT = (
    Path("data") / "korean_foundations" / "snapshots"
)
```

Preparation validates under the shared lock before recovery and staging (`korean_foundation_snapshot.py:1723-1747`). It creates one exact hash-named immutable tree but does not create or modify the active pointer.

**Strictly read-only verification** — copy `korean_foundation_snapshot.py:1750-1818`: read receipt authority, reconstruct expected manifest/member bytes, verify the tree, re-read receipt/prestate, verify the tree again, and return a report without lock, repair, recovery, cleanup, or writes. The proof pattern is `tests/services/test_korean_foundation_snapshot.py:989-1029`, which poisons all write primitives and compares the complete tree before/after.

---

### Activation and six local exports

**Primary analogs:** snapshot atomic pointer activation, fixed CLI command group, and export staged writers.

**Authority pattern:** this is not application authentication. Authority is one exact reviewed authorization SHA-256 bound to the current receipt, bundle, snapshot-manifest, root, and active-prestate tuple. CLI hash validation and content-free errors follow `src/multilang/cli.py:125-155`:

```python
def _validate_foundation_sha256(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise typer.BadParameter("lowercase SHA-256")
    return value

def _fail_korean_foundation_operation(exc: ValueError) -> None:
    typer.echo(f"korean_foundations_error={_foundation_failure_reason(exc)}")
    raise typer.Exit(code=1) from exc
```

**Atomic pointer pattern** — `korean_foundation_snapshot.py:1944-2003`:

```python
descriptor, temporary_name = tempfile.mkstemp(
    prefix=".active-foundations.", suffix=".tmp", dir=paths.candidate_dir
)
_write_all(descriptor, raw)
_fsync_descriptor(descriptor)
...
os.replace(temporary_path, paths.active_pointer)
_fsync_directory(paths.candidate_dir)
```

Activation revalidates everything under the shared lock before this one swap (`korean_foundation_snapshot.py:2022-2046`). An exact already-active retry is no-write success; any tuple or prestate drift requires a new preparation/review cycle.

**Fixed local destinations** — copy the existing allowlist at `src/multilang/cli.py:94-103`:

```python
_KOREAN_FOUNDATION_EXPORT_ROOT = Path(".multilang/exports/korean-foundations")
_KOREAN_FOUNDATION_EXPORT_NAMES = (
    "hangul.apkg", "hangul-csv", "hangul-tsv",
    "pronunciation-i-plus-1.apkg",
    "pronunciation-i-plus-1-csv",
    "pronunciation-i-plus-1-tsv",
)
```

The export command may retain its fixed local `--output` contract, but final execution writes exactly these six names.

**Safe destination checks** — retain `lstat`, link/reparse rejection, suffix/type checks, and snapshot exclusion from `korean_foundation_export.py:916-963`.

**Stage, inspect, then replace** — copy `korean_foundation_export.py:1349-1408`:

```python
with tempfile.TemporaryDirectory(prefix=".korean-foundation-", dir=parent) as temporary:
    ...
    _canonicalize_apkg(raw_path, staged_path)
    _inspect_staged_apkg(staged_path, bundle=bundle)
    os.replace(staged_path, output_destination)

with tempfile.TemporaryDirectory(prefix=".korean-foundation-", dir=parent) as temporary:
    ...
    _inspect_staged_tabular_bundle(staged_bundle, ...)
    os.replace(staged_bundle, output_destination)
```

Each export resolves one active snapshot (`korean_foundation_export.py:1450-1464`). Do not export from candidates, drafts, inbox members, or an inactive prepared snapshot.

**Testing:**

- Parameterize both families and all three formats, as in `tests/services/test_korean_foundation_export.py:1019-1041`.
- Require deterministic bytes/tree content (`973-1016`).
- Inject staged-inspector failure and require no destination or temp workspace (`1044-1073`).
- Independently deep-inspect every artifact against one bundle and record hashes, following `tests/integration/test_korean_foundations_flow.py:558-594`.
- Do not claim observed Anki acceptance from static archive/table/media inspection.

## Shared Patterns

### Fixed Paths and Narrow Public Surfaces

**Sources:** `korean_foundation_evidence.py:44-52`, `korean_foundation_snapshot.py:41-57`, `src/multilang/cli.py:729-926`, `tests/cli/test_korean_foundation_commands.py:167-190`.

Apply to candidate commands, handoffs, evidence, snapshots, activation, and final exports. Public surfaces accept enums and exact hashes; only the already-established export command accepts an output path. Never add arbitrary path/root/source/import/provider options to production commands.

### Frozen, Bounded, Content-Free Validation

**Sources:** `_FrozenManifest`, `_FrozenReviewModel`, `_FrozenMediaModel`, `_FrozenEvidenceModel`, `_FrozenSnapshotModel`.

All machine-readable coordination/data models use Pydantic `extra="forbid"`, `frozen=True`, bounded fields/collections, lowercase hashes, and hidden input in validation errors. Service errors expose stable reason codes, not candidate text, filesystem paths, evidence payloads, or reviewer content.

### Canonical Identity

**Source:** `korean_curriculum.py:340-352`.

Use UTF-8, `ensure_ascii=False`, `allow_nan=False`, sorted keys, compact separators, and aliases. Distinguish canonical object hashes from exact file-byte hashes; never label one as the other. Handoff/receipt files use their contract's exact newline convention.

### Validate Before Any Write

**Sources:** `korean_foundation_evidence.py:2252-2301`, `korean_foundation_snapshot.py:1723-1747`, `korean_foundation_export.py:1417-1464`.

Validate schema, authority, exact hashes, immutable base/prestate, filesystem type, and complete semantic relationships before creating a canonical destination. Recheck bound state immediately before the atomic publication step.

### Link-Safe Atomic Publication

**Sources:** evidence receipt, snapshot staging/activation, and export writers above.

Use `lstat` and link/reparse rejection, same-parent secure staging, flush/`fsync`, staged revalidation, `os.replace` or one directory rename, parent-directory `fsync`, and own-temp cleanup. Do not delete or repair unrelated stale state on a read-only or prevalidation failure.

### Read-Only Means Write-Poisonable

**Sources:** `korean_foundation_snapshot.py:1750-1818`; `tests/services/test_korean_foundation_snapshot.py:269-334,989-1029`.

Selection review, draft validation, inbox inspection, receipt continuity, prepared verification, active verification, and runtime hashing must pass with all reachable write/recovery/lock-creation primitives poisoned and complete trees byte-identical.

### Authority Separation

Selection authorizes only exact candidate promotion. Reviewer/rights/playback evidence authorizes receipt creation only after complete validation. Receipt existence does not authorize activation. Activation requires a separately reviewed exact authorization hash. None of these authorize publication, distribution, provider calls, or observed Anki acceptance.

### Pending Gates Remain Pending

**Sources:** `korean_foundation_review.py:806-826`; `korean_foundation_media.py:1237-1255`.

Both review and media readiness reject `candidate_only`. Promotion and request regeneration must not manufacture approvals, timestamps, reviewer identities, rights dispositions, media bytes, or heard-playback claims.

### v1 History, v2 Production Default

Production defaults must become one coherent v2 tuple. Explicit historical v1 reads remain available only through a deliberately named/versioned route. Never mutate v1, silently fall back from missing v2 to v1, or resolve a mixed tuple.

### Existing Modes and Runtime Stay Isolated

Retain existing phoneme, Kana, Russian, Latin, generic export, and template behavior. Phase 31 full-suite verification runs from the fixed isolated Python 3.12 environment, leaves the shared `.venv` hash unchanged, and performs no provider, network, import, upload, publication, or release action.

## Test Pattern Matrix

| Planned Area | Existing Test Pattern to Copy | Required New Assertion |
|---|---|---|
| Curation contracts | `test_korean_curriculum.py` fixed/frozen/hash validation | bounded patch-only drafts; no structural or authority fields |
| Draft assembly | deterministic export comparison at `test_korean_foundation_export.py:973-1016` | repeated batch/family/global assembly is byte/hash identical |
| Promotion | hash-named snapshot staging plus one atomic pointer and concurrent-reader tests | one immutable four-member v2 bundle becomes visible through one pointer or not at all |
| Handoffs | `test_korean_foundation_evidence.py:978-1020,1146-1218` | fixed operations, hash-only args, link refusal, identical retry, nonidentical refusal |
| v2 migration | curriculum fixed-loader test and snapshot v1/v2 discriminator | v2 default, explicit v1 history, mixed-tuple refusal, no fallback |
| Runtime isolation | snapshot write poisoning and integration state digests | only fixed temp root changes; `.venv` hash identical |
| Evidence/receipt | existing 37-case evidence suite | genuine v2 bindings and independently confirmed current index |
| Snapshot/verification | `test_korean_foundation_snapshot.py:989-1029` | inactive immutable v2 tree; verifier cannot write or repair |
| Activation | existing drift/idempotence/concurrency tests | exact handoff authorization and v2 provenance only |
| Six exports | `test_korean_foundation_export.py:1019-1073`; integration deep inspection | both families × APKG/CSV/TSV, fixed names, no partial replacement |

## No Single Exact Analog

| File/Area | Reason | Planner Direction |
|---|---|---|
| `korean_foundation_ai_curation.py` | No existing bounded assisted-curation patch compiler exists. | Compose frozen curriculum models, canonical hashes, pending review gates, and existing deterministic batch utilities. Do not add an LLM/provider runtime dependency. |
| `scripts/phase31_handoff.py` | No existing multi-kind checkpoint handoff utility exists. | Compose fixed paths, strict evidence models, validation-before-atomic-write, and exact command allowlist tests. |
| `verify_phase31_runtime_isolation.py` | No standalone runtime-isolation helper exists. | Implement only the exact plan-defined fixed root/operations and copy link safety plus deterministic tree-hash/write-poison test patterns. |
| `31-AI-CURATION-REPORT.md` | Existing documents are request contracts or execution summaries, not this bounded draft report. | Reuse explicit non-evidence/authority-limit wording and report exact machine hashes/counts without creating authority. |

## Planner Guardrails

1. Plans 31-11 through 31-19 create and assemble only bounded noncanonical drafts; no v2 candidate may appear.
2. Plan 31-20 records one exact selection and implements bundle/pointer promotion primitives without promotion.
3. Plan 31-21 is the sole v2 promotion step: one immutable hash-named four-member bundle becomes visible through one atomic pointer, never four sibling replaces.
4. Plan 31-22 separately implements and runs exact pending request regeneration.
5. Plans 31-23 and 31-24 migrate bounded service groups to v2 while preserving explicit immutable v1 history and blocked production.
6. Plan 31-25 completes all named cross-mode pre-evidence regressions and adds only the fixed isolated-runtime helper; no canonical state change.
7. Plan 31-26 accepts only genuine direct-placement evidence and records independent exact index confirmation; no receipt/snapshot/pointer/export write.
8. Plan 31-27 creates the canonical receipt and one inactive immutable snapshot; it does not activate or export.
9. Plan 31-28 verifies read-only, obtains exact separate authorization, atomically activates, writes and deep-inspects six fixed local outputs, and runs isolated Python 3.12 closure.
10. Any stale hash, structural diff, mixed version, partial destination, link/reparse component, malformed authority, or prestate drift fails closed without repair.
11. Phase 34 owns observed Anki Desktop/mobile import, rendering, and playback acceptance.

## Metadata

**Analog search scope:** `src/multilang/`, `scripts/`, `tests/`, `data/korean_foundations/`, and Phase 31 plans/request contracts/summaries.

**Primary analog set:** curriculum, review, media, evidence, snapshot, export, fixed CLI, standalone asset builder, and their focused tests.

**Pattern extraction date:** 2026-08-23
