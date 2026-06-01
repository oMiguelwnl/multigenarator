# Phase 23 Discovery: Latin source pack licensing and sequencing

Discovery level: 2 — source licensing and Latin sentence provenance affect implementation constraints.

## Findings

- Dickinson College Commentaries (DCC) publishes a Latin Core Vocabulary with lemma/headword entries, definitions, part of speech, semantic group, and frequency rank. The DCC site states the core lists define the most common Latin lemmas and are licensed CC BY-SA.
- DCC Terms of Use allow free educational use and reproduction with attribution and share-alike terms. Any committed DCC-derived metadata must carry explicit attribution and license notes.
- The Latin Library exposes public Classical Latin texts by work and book/page URLs. It is usable as a source locator for original Classical Latin citations, but each source-pack row must still store a license note and must not imply modern commentary licensing unless derived from DCC.
- Phase 23 should avoid Tatoeba and untraceable generated sentences. Adapted didactic Latin may be project-authored only when marked as adapted didactic, not as an original Classical citation.

## Implementation constraints for PLAN.md

- Use a frozen JSON source pack as the source of truth for the first 50 Latin MVP rows.
- Store DCC Core Vocabulary as the frequency source for lemma rank metadata with CC BY-SA attribution.
- Store sentence provenance per row: `source_type`, `citation`, `work_reference`, `source_url_or_id`, `license_note`, and a license-gate status.
- Validate exact target-form presence or accepted orthographic/enclitic normalization before the asset is accepted.
- Keep Phase 23 focused on source/frequency/sentence ordering. Grammar analysis, Portuguese translation, audio generation, and export remain later phases.
