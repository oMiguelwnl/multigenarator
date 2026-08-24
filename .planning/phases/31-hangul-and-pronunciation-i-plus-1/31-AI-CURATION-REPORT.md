# Phase 31 AI-Assisted Curation Report

**Generated**: 2026-08-24
**Scope**: Noncanonical Korean Hangul and pronunciation draft curation for Phase 31.
**Authority**: `draft_only`; this report does not approve, promote, select, publish, or provide evidence for learner-ready content.

## Claim Limits

- The artifacts below are AI-assisted draft curation artifacts only.
- All records remain `review_status=needs_review` and `promotion_authority=false`.
- No qualified Korean phonetics, Portuguese, rights, media, playback, production-readiness, export-readiness, or Anki acceptance claim is made.
- No provider, network, LLM, TTS, Azure, database, or external source call occurred during these draft curation steps.
- No canonical Korean foundation source pack, evidence inbox, active snapshot, export artifact, media file, or learner-ready deck was modified.

## Complete Draft Set

| Artifact | Content Hash | Records | Proposals | Uncertainties | Disagreements |
|---|---|---:|---:|---:|---:|
| `hangul-v2-draft` | `71e1d3c402acf964247c9551cc63f27dff6c18ad3d5bddc1322cf48cd80e254f` | 92 | 249 | 27 | 0 |
| `pronunciation-i-plus-1-v2-draft` | `aff724efda01ebfe67e28dd446470f544d68e54b181219611e6ed529e4cdace5` | 47 | 312 | 111 | 0 |
| `draft-manifest` | `8f053a815b4b18c9e8004d295849f562989410f05f4a1cc8725bc37f8c7f26b5` | 139 | 561 | 138 | 0 |

## Batch Bindings

| Batch | Content Hash | Records | Stages | Proposals | Uncertainties | Disagreements |
|---|---|---:|---|---:|---:|---:|
| `hangul-h0-h3` | `a14590a950ad9cde3bef63d58e47c0dee102ebd41e309b074d2d2f8f113a87a3` | 25 | H0-H3 | 68 | 7 | 0 |
| `hangul-h4-h7` | `f641410fe46c5b218a7adfd419bd77a1f6704525b2a9ac56ed494382dfc3de33` | 32 | H4-H7 | 95 | 1 | 0 |
| `hangul-h8-h10` | `ac2039edbe79ced986f1ec2bbe6abab8eae2393a83ccdbb1e0da407228e59376` | 35 | H8-H10 | 86 | 19 | 0 |
| `pronunciation-p0-p4` | `29781e441080af0b8c2504adae8f65982ab014864ad52490992a2a2f92af9c0c` | 24 | P0-P4 | 176 | 40 | 0 |
| `pronunciation-p5-p9` | `b7b42cd50630abdbb0ffbeb2c26eff897ff2f40e8f1ef8ca15d209edba4332e2` | 13 | P5-P9 | 104 | 13 | 0 |
| `pronunciation-p10-p13` | `1374893a8038b790189c0682c3132b4ec4a8f99a4562329bdd7eab55ea5b5a0f` | 10 | P10-P13 | 32 | 58 | 0 |

## Coverage Results

- Hangul stages covered exactly once: H0, H1, H2, H3, H4, H5, H6, H7, H8, H9, H10.
- Pronunciation stages covered exactly once: P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13.
- Total source-bound records: 139.
- Total batch bindings: 6.
- Total family bindings: 2.
- Total disagreements: 0.

## Uncertainty Results

- Hangul uncertainties remain draft review items, not approved orthographic or mnemonic content.
- Pronunciation IPA remains unresolved wherever no qualified phonetics evidence is available.
- P2 sentence fields that would introduce later connected-speech rules remain uncertain.
- P11-P13 specialist-sensitive reduction, auditory, focus, boundary, rate-conditioned, and rule-ordering claims remain explicitly uncertain pending qualified review.

## Safety Results

- Drafts use only allowlisted learner-copy fields or explicit uncertainty fields.
- No authority-bearing reviewer, approval, rights, redistribution, media hash, playback, production voice, prerequisite, active-rule, target-concept, structure-hash, provider, URL, path, force, repair, promote, or export fields were added to curation drafts.
- Drafts preserve exact immutable source-entry hash bindings through batch, family, and manifest assembly.
- The report is prose-only and cannot authorize promotion or export.

## Verification Commands

```bash
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch pronunciation-p0-p4
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch pronunciation-p5-p9
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch pronunciation-p10-p13
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py assemble-family pronunciation
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py assemble
UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-drafts
```

## Next Gate

Plan 31-20 may review exact draft hashes and prepare machine-readable handoffs. It must not promote, approve, export, or claim evidence without the later qualified review, rights, media, playback, receipt, snapshot, and activation gates.
