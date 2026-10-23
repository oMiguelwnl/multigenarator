# Offline vocabulary consolidation

`scripts/finalize_vocabulary.py` composes explicitly pinned reviewed inventories
into a new preparation version. It does not call providers, load `.env`, import
native reviews, generate card text or audio, or authorize production.

## Input and command

The input JSON is a list with one object per language:

```json
[{"language":"de","path":"/absolute/path/reviewed-proposals.jsonl","sha256":"<64 hex digits>"}]
```

Both reviewed-proposals and selection-snapshot rows are accepted. An optional
`source_manifest` object with `path` and `sha256` preserves snapshot language
metadata and its hash-checked attachments. This identifies the metadata origin;
a deliberately derived input inventory may have a different content hash.

```bash
env MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 \
  .venv/bin/python scripts/finalize_vocabulary.py \
  --inputs /absolute/path/inputs.json --inputs-sha256 HASH \
  --output /absolute/path/output/reports/vocabulary-finalization/version
```

The output directory must not exist. Inputs must be regular, non-symlink files
with the supplied hashes. The root completion manifest is written last. A
directory without that manifest is incomplete and must not be consumed.

## Outputs and meaning

- `snapshot/` preserves review decisions, original source groups, imported
  reviews and derived corrections, with the existing selection-snapshot schema.
- `languages/<code>/identities.jsonl` joins only fragments of the same exact
  source entry, lemma and POS. Explicit derived homonyms remain distinct. Sense
  identifiers, their own readings and reviewed form-parent links are preserved.
- `pending-review.jsonl` includes unresolved units and partially unresolved
  included units. `preparation-findings.jsonl` explains adapter findings such as
  missing POS. These findings do not rewrite historical review decisions.
- `pending-frequency.json` lists identities without qualified final frequency.
- `summary.json` counts review units, preparation identities and associations.
  None of these numbers is a final card count.

The Nordic adapter preserves its original resolution and reads historical split
and form structures without guessing POS or merging homonyms. Forms retained as
lexical evidence are not automatically selected for generation. The scoped alias
consumer additionally requires exact raw-record hashes and selected target sense
boundaries; an alias never inherits all senses of its spelling variant.

## Frequency and coverage boundaries

`source_order_preview` accepts explicitly bound published lexical frequency
ranks. It organizes the first 3,000 ranked identities into three initial bands
and subsequent identities into an expansion. Additional senses/forms stay with
their parent identity. Source ordinals and surface bootstrap priorities are
rejected as lexical frequency. Preview flags remain unapproved on every row.

The consolidator does not perform cross-dictionary deduplication, qualify a
frequency corpus, reconcile incompatible morphological annotations, or certify
90% coverage. Run the existing coverage campaign against the new snapshot and
pinned independent corpora. Report spoken and written evidence separately;
previously inspected diagnostic corpora cannot become untouched holdouts.
Existing Korean ranking and licensing gates remain in effect.
