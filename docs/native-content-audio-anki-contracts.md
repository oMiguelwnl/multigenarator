# Native content, pronunciation, export and learning contracts

The v4 services extend the existing provider adapters, `AudioSynthesisService`,
`genanki` exporter dependency and `AnkiIdRegistry`. The legacy generation and
export entry points retain their contracts. Persistence and authorization belong
to the native application facade and repository; these services return immutable
domain records and do not choose another user's namespace.

## Content editions

`NativeContentService.generate(ContentRequest) -> ContentVersion` accepts an
already selected lexical identity, sense, morphological analysis, semantic card
ID and deck edition. Generated output has a closed plain-text schema. The
qualified matcher must confirm those same identifiers; strict i+1 requires the
observed unknown concept set to contain exactly the target. Incidental concepts
are recorded in contextual mode rather than silently added to the known set.

Core requests may use canonical known concepts but cannot contain personal known
concepts or private context. Private context requires an explicit authorization
flag and a `user:` namespace. Request bytes, characters and a conservative token
upper bound are checked before calling a provider. Structured output receives
size, schema and active-markup checks before persistence or rendering.

`NativeProviderContentAdapter` uses the existing provider transport and config
helpers, with fixed system instructions and request data in the user message. It
can use the existing translation port. `ExistingTextContentAdapter` also bridges
the legacy sentence, definition and translation ports; legacy Korean requests
retain their Portuguese contract and are deliberately excluded from this bridge.

`ContentContract` aliases `ContentVersion`. Its `version_id` hashes the complete
record, including review evidence. Approval appends a version rather than mutating
the pending record. `CanonicalContentEdition` requires approved Core versions
from one edition and exposes a stable bundle hash and card-level version diff.
Model properties such as `version_id` are recomputed after `model_validate`; the
repository stores the ordinary `model_dump(mode="json")` payload separately from
the indexed identifier.

## Exact pronunciation and reusable media

`NativeAudioService.generate(signature, job_id=..., item_key=..., namespace=...,
cached_version=...) -> AudioVersion` wraps the existing synthesis service. The
signature includes language/profile, displayed and NFC text, contextual reading,
context, sense, analysis, locale, voice, complete SSML, pronunciation policy,
provider/model version, format and word/sentence kind.

SSML must enclose all spoken text in one explicit voice under a `speak` element
with the exact locale. Only bounded pronunciation/prosody markup is accepted;
external audio, entities, declarations, substitution aliases, arbitrary attributes
and unapproved namespaces fail before provider access. The literal spoken text
must equal the signature's normalized display. Phoneme controls are part of the
immutable signature and remain subject to pronunciation review.

Reuse requires the complete signature and namespace to match, plus a nonsymlink
artifact with the recorded size and SHA-256. New synthesis uses a temporary file
and checks returned provider, voice, locale, format, status and bytes before
publishing under the namespace and signature/content hashes. Provider fallback
cannot silently satisfy a signature for another provider.

`AudioContract` aliases `AudioVersion`. Audio version IDs include review state,
review receipt and license receipt, while artifact paths remain content-addressed.
Approval creates a new record referencing the same bytes. Production semantic
cards require exact content, word audio and sentence audio bindings; selecting
versions merely by matching text is insufficient.

## Semantic projection and Anki topology

`project_cards` consumes lexical identities and approved important-form selections.
Every parent receives one headword card and all selected forms; required forms
are never truncated to a deck size. Forms inherit the parent's inventory,
frequency destination and prerequisite. Distinct analyses of the same spelling
have distinct semantic IDs and visible context. Reverse, listening and gap-cloze
roles are optional and counted separately. Gap-cloze uses a regular template with
one exact target replaced by a gap; it is not Anki's built-in cloze note type.

`validate_semantic_cards` checks identity uniqueness and parent relationships.
Production Core validation requires exactly 3,000 parents with ranks 1–3,000 per
language. `summarize_cards` reports parents, headwords, forms, optional roles and
totals by inventory, language and Core level. Actual deck IDs come only from
`AnkiIdRegistry`; existing allocations are unchanged and native allocations are
reserved separately.

`export_semantic_anki(..., model="A"|"B", prototype=True)` produces real APKG
files and semantic JSON/CSV/TSV manifests. Model A groups a lexical family in one
note; Model B uses a separate note for each semantic card. The exporter verifies
the resulting SQLite `(note GUID, template ordinal, deck ID)` tuples against the
manifest before publication. Text is escaped and CSV/TSV cells neutralize formula
prefixes. Prototype fields explicitly identify missing unapproved content.

**Neither prototype is approved for production.** Model A currently assigns form
ordinals by sorted semantic ID; inserting a form can shift existing ordinals.
Its grouped notes demonstrate native sibling structure but do not establish safe
dynamic migration. Model B has no native sibling relationship and needs a proven
alternative for nonconcurrent exposure. These limitations are evidence targets,
not claims that scheduling has been solved.

Production export requires a `TopologyDecision` containing both models' positive
and negative results for every required scenario on current/previous Anki Desktop,
current AnkiDroid and current AnkiMobile. The matrix must bind one semantic fixture
and pass an independently supplied evidence verifier. No accepted client matrix
or chosen production topology is shipped. Unit tests and generated package
inspection do not substitute for real-client acceptance.

## Read-only history and adaptive preparation

`read_anki_history(path, aliases=..., namespace=..., limits=...) -> HistoryImport`
supports bounded `.apkg` archives containing `collection.anki2`. Other collection
formats and live collection files fail closed. Archive size/member/ratio limits,
safe names, bounded extraction, SQLite read-only mode, schema checks, unique
scheduling keys and operation/time limits protect parsing. Only a disposable
database copy is opened; the input package is hash-checked and never modified.

Mapping requires an explicit verified one-to-one alias for note GUID, template
ordinal and model ID. Unknown or duplicate semantic mappings are quarantined.
The returned record retains only mapped scheduling aggregates and hashes, without
note fields, raw package bytes or paths. Its namespace is private. The facade must
resolve alias evidence from an authorized, verified manifest before calling it.

`build_adaptive_queue` is deterministic over its source snapshot, policy and
learner state. It exposes score components, deferred reasons, queue hashes and
50–200-card modules. It changes preparation priority only; it does not change
editorial rank, canonical content or Anki scheduling. Imported review counts do
not imply mastery. Important forms require an explicit known parent, foreign
private cards remain excluded and Expansion requires opt-in. `override_priority`,
`reset_adaptation` and `revoke_history` return new learner states. Reset clears
preferences; history revocation separately removes imported derived state.

`NativeLearningService(NativeRepository(session), evidence_store=...)` connects
these operations to the existing `user_state` table. `get_state(owner_id=...)`
returns revision zero when no state exists. Every mutation accepts
`expected_revision`; creation, replacement and deletion use a database comparison
to reject concurrent stale writers. State changes, privacy-safe audit hashes and
outbox events share the caller's transaction. The service flushes without committing.
`set_known`, `set_reading`, `set_expansion`, `override`, `reset`, `revoke_history`
and `delete` affect only the authenticated owner's `native-learning` record.
`queue(owner_id=..., cards=..., policy=...)` prepares the supplied pinned semantic
cards from that durable state and does not persist a stale derivative queue.

History import resolves stored `LegacyIdentityAlias` records. Identity-only
aliases do not prove card template/model relationships and are skipped.
`register_aliases` requires signed local evidence with purpose
`anki-history-alias`, binding the complete alias list (excluding its receipt field)
and reviewer. It preserves an existing `identity_alias` payload while adding
`history_aliases` only when GUID, parent identity and evidence receipt agree.
Conflicting mappings fail closed. Imported summaries are idempotent, bounded and
revocable; original package bytes and note fields never enter `user_state`.

The synthetic scale check exports 3,000 headwords plus 3,000 mandatory forms as
6,000 actual cards with 2,000 cards in each frequency level. In the initial local
run, package generation took 15.045 seconds for Model A (1,466,586 bytes) and
21.313 seconds for Model B (1,929,434 bytes). These measurements use synthetic
unapproved content under concurrent tests; they establish a packaging baseline,
not real-client acceptance or linguistic quality.

## Korean evidence independent of planning files

Runtime Korean authority defaults to `data/korean_foundations/evidence`.
`MULTILANG_KOREAN_EVIDENCE_ROOT` may select a safe project-relative native path;
absolute paths, traversal and `.planning` roots are rejected. Snapshot, evidence,
AI curation and approved fallback readers all use this location.

`import_legacy_evidence` is an explicit migration helper: callers provide the
legacy source and an exact relative-path/SHA-256 map. It validates all sources
before staged copying and never searches planning state during normal operation.
The imported bundle contains 385 existing tracked authority files, including all
325 declared media artifacts, preserved byte-for-byte. Its
`native-import-manifest.json` records hashes, byte totals and import manifest hash
`8c88c563aeed9a6b9956a94801d58f1307acd8f7ee1ed8509fdb76d316c25c80`.
Historical locator strings inside evidence remain provenance text; they are not
runtime fallback paths. Original planning files, active pointers and immutable
snapshot bytes are unchanged.

An empty `failed-attempts` directory is optional because Git cannot track empty
directories. The validator still rejects undeclared files and unexpected
directories. Tests verify the native inventory and approved snapshot provenance
while denying every attempted `.planning` file read.
