# Linguistic qualification and importance calibration

Approved directly by the user on 2026-09-13: implement the preceding proposal,
write a detailed step-by-step plan, and execute it. This extends commit `1f949e4`
on `feature/roadmap-4-0-native-architecture`.

## Product outcome

The operator can prepare a small, real vocabulary pilot; inspect source-backed
importance measurements; review lexical entries, forms and annotation cases in
a local browser; import those decisions; calibrate candidate selection criteria
on calibration data; and evaluate frozen criteria on separate evaluation data.
The same workflow supports all 22 modern languages, starting with 100 headword
candidates each in Portuguese and English, then exercising Turkish, Korean,
Japanese and Chinese before preparing the remaining languages.

The output distinguishes a machine proposal, an unsigned human submission, an
authenticated review, a calibrated rule and a production-qualified policy. None
of these stages may silently substitute for another. Software tests, UD labels
and a second LLM are not independent human linguistic approval.

## Preserved contracts

- Keep exact existing Anki field names/order/templates. Linguistic metadata stays
  in the database and manifests; important forms display their studied form.
- Core has 3000 identities, three levels of 1000, plus every approved important
  form. Pilots are expressly staging material, not shortened production Core.
- Preserve NFC, case and accents. Never invent lemma/sense identities or substring
  offsets. Missing evidence remains visible and cannot authorize promotion.
- No GSDD workflow/runtime, no deploy, no push/merge, no migration of real data.
- Preserve preexisting user files and staged changes. Downloaded texts/models and
  raw review data stay under ignored `.multilang`, not redistributed in commits.
- No paid provider calls without a concrete workload and authorized budget.
  Existing content/audio services are reused; no duplicate generator or TTS stack.
- No fabricated expert identities, license decisions, signed approvals or Anki
  client results. A declared expert identity alone is not a verified credential.

## Analysis improvements

Accept Stanza multiword expansions only when vendor-provided integer child spans
partition the exact parent surface and each slice equals the child's text.
For unalignable expansions, keep the complete source span and its constituent
evidence in an explicit blocker while retaining exact surrounding tokens.
The matcher remains closed whenever full analysis/sense coverage is incomplete.
Japanese punctuation can use its exact surface as punctuation lemma when both
Unicode category and native tagging establish punctuation. Unknown lexical tokens
must never receive invented lemmas. Preserve native annotation inventories and
report incomparable UD/Kiwi/UniDic metrics as unavailable with reasons.

Unknown Wiktextract POS needs a category report. Character, syllable, root,
romanization, redirect and affix records are not silently converted to nouns.
Corrections require source-bound review; blanket adnominal/conjunction mappings
are not justified by a shared label alone.

## Evidence and importance

Compute observed count, distinct document count, frequency per million, dispersion
and a declared empirical normalization from deduplicated, source-bound occurrences.
Preserve language, source, register, document IDs and split. Do not turn each
sentence into a new document if the source lost document boundaries. A corpus
sample's measurements are not automatically representative general frequency.

Irregularity, unpredictability, ambiguity, pronunciation, prerequisite value and
learning difficulty are optional measured/reviewed signals. Explicit dictionary
tags can yield a declared proposal; missing linguistic/pedagogical evidence is
unknown, not a fabricated numerical score. Keep individual signal provenance,
methods and missing reasons. Candidate lemma/POS counts cannot be distributed to
multiple senses without a reviewed occurrence-to-sense mapping.

Split unapproved scoring criteria from approved ImportantFormPolicy without
changing existing policy payloads/hashes. Calibration evaluates bounded candidate
criteria on reviewed calibration labels, with false-positive/false-negative
counts and reproducible tie-breaking. Evaluation uses separate source-bound
items and never selects the winning criteria using evaluation outcomes.
Human-reviewed, authenticated inputs are required for a trusted result; synthetic
tests remain explicitly test evidence. Calibration alone never grants production
approval or invents an approval receipt.

## Local review

Export an immutable, bounded ReviewPacket plus a self-contained HTML page. The
page works without a server, external assets, network or secrets. It shows source
excerpts, lexical proposals, exact analyses, importance measurements and reasons.
The reviewer can accept, correct, reject or leave inconclusive, save a JSON
submission and load it again. Evaluation proposals start hidden to reduce bias.

Decisions refer to original item IDs/hashes; they cannot change packet language,
split, evidence or source. Corrections have explicit typed fields and reasons.
Python revalidates every downloaded decision. Authenticated import verifies the
receipt purpose and signer identity, rather than treating a typed reviewer name
as authentication. Unsigned imports remain useful drafts without promotion.

## Pilots and qualification material

Prepare reproducible 100-headword pilot selections, preserving all associated
source senses and eligible observed form candidates. Produce separate review
packets for lexical/form calibration and 200 diagnostic annotation cases per
language, subject to available source count. Cases with source labels are
annotation proposals until independently reviewed. Never label the existing UD
test sample an independent golden dataset merely because it has annotations.

Use limited, checksummed corpus samples for Portuguese/English across distinct
registers where accessible; retain rights and sampling limitations per document.
Exercise new analysis and measurement code on actual local data for the six early
languages, then prepare coverage/review artifacts for all 22. Record missing
coverage explicitly; do not drop important forms to fit a card or cost cap.

Existing draft-content, complete-content-draft, review, audio and export commands
remain the path for a complete pilot package once grounding/reviews and provider
budget exist. Implement a concrete workload/preflight report so paid generation
and client acceptance can proceed from inspectable inputs.

## Acceptance

Tests must demonstrate exact-span preservation, unchanged policy hashes, no
training/evaluation leakage, deterministic measures/calibration, authentic review
binding, inert HTML, bounded inputs, replay safety and unchanged Anki fields.
Actual reports must name source/model/version hashes, measurements and blockers.
Finish with focused regressions, affected integration, scoped Ruff, distribution
and strict docs checks; use the diagnosed non-sandbox test environment where
AnyIO TestClient otherwise deadlocks. External human/budget/client requirements
remain explicitly distinguishable from completed software work.
