---
mode: quick
task: 036-gerar-deck-dummy-alemao
plan: 036
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 1
requirements: []
files_modified:
  - german_frequency_template_dummy.apkg
files_verified:
  - path: src/multilang/templates/normal_card.md
    mode: read-only-live-input
  - path: src/multilang/services/export_anki_package.py
    mode: read-only-service
reduced_assurance: true
reduced_assurance_reasons:
  - ".planning/templates/roles/planner.md is absent; this plan applies the quick-task contract directly."
  - "Per the user's request for speed, verification is deliberately limited to APKG/SQLite structure and template/ID checks; no test suite or formal visual verification is planned."
non_goals:
  - "Do not modify product code, templates, tests, or create a permanent generator script."
  - "Do not call providers or the network, add audio/image media, run test suites, capture screenshots, or perform formal Anki UI proof."
  - "Do not update ROADMAP.md, SPEC.md, STATE.md, LOG.md, or create/stage/commit changes."
hard_boundaries:
  - "Execution writes only german_frequency_template_dummy.apkg at the repository root; the executor creates 036-SUMMARY.md separately as the required lifecycle artifact."
  - "The dirty Quick 035 version of src/multilang/templates/normal_card.md is a read-only live input and must not be restored, rewritten, or replaced with HEAD content."
anti_regression_targets:
  - "All existing product and test files, including the intentional uncommitted Quick 035 template change, remain untouched."
closure_claim_limit: "Claim only that the generated package is structurally inspectable, contains seven representative notes, embeds the live height rule, and uses preview-only IDs; native Anki appearance is intentionally unverified."
no_ui_proof_rationale: "Artefato para inspeção manual; o usuário dispensou prova visual formal."
must_haves:
  truths:
    - "The user receives one root APKG containing seven representative German frequency cards, including one long-content card."
    - "Every card has a German word, IPA, English definition, German sentence, English translation, and blank audio/Image fields."
    - "The APKG embeds the live normal German template with min-height: min(760px, calc(100vh - 80px))."
    - "The APKG uses clearly named Dummy/Preview model and deck identities that differ from production IDs."
    - "Generation and inspection stay local, do not modify product/tests, and leave no permanent generator script."
  artifacts:
    - path: german_frequency_template_dummy.apkg
      provides: "Offline German normal-frequency template preview importable into Anki"
  key_links:
    - from: src/multilang/templates/normal_card.md
      to: german_frequency_template_dummy.apkg
      via: "build_multilang_model(source_type='frequency', language=SupportedLanguage.DE), followed by a preview-ID model clone"
    - from: "seven ExportCardRow values"
      to: german_frequency_template_dummy.apkg
      via: "build_multilang_note with the cloned preview model and genanki.Package"
---

# Quick Task 036 Plan: Gerar deck dummy alemão

<objective>
Generate one offline German frequency dummy APKG from the current dirty-worktree normal template so the user can promptly open it in Anki and inspect the recently changed vertical layout.

Output: `german_frequency_template_dummy.apkg` only, plus executor-owned `.planning/quick/036-gerar-deck-dummy-alemao/036-SUMMARY.md` after execution.
</objective>

## Locked Decisions

- **D-01 — Read-only product:** do not modify any product or test file; create only the requested root APKG during the task.
- **D-02 — Live template:** load the current Quick 035 `normal_card.md` through the existing German frequency model service, not from Git/HEAD or copied CSS.
- **D-03 — Isolated identities:** clone the loaded model to fixed preview-only IDs `1995036001`/`1995036002` and names containing both `Dummy` and `Preview`; never package production IDs.
- **D-04 — Offline sample:** package exactly seven representative German cards, including one long-content card, with blank audio and Image fields and no provider/network call.
- **D-05 — Ephemeral generation:** use one inline Python execution with installed `uv`/`genanki`; do not create a permanent script.
- **D-06 — Reduced verification:** check only non-empty ZIP/APKG, `collection.anki2`, seven notes, the exact live min-height rule, representative field completeness/blank media, and preview-only IDs. Do not run pytest, UI proof, screenshots, or visual verifier.
- **D-07 — Workflow boundaries:** do not update ROADMAP/SPEC/STATE/LOG and do not branch, stage, or commit; create `036-SUMMARY.md` after the task.

<checks>
<plan_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: "One task has executable generation and verification commands, covers all supplied decisions, and limits assurance exactly as requested."
</plan_check>
</checks>

<tasks>

<task id="036-01" type="auto">
  <name>Generate and minimally inspect the German dummy APKG</name>
  <files>
    - CREATE/REPLACE: german_frequency_template_dummy.apkg
  </files>
  <action>
    Per D-01/D-02/D-03/D-04/D-05, run the following command from the repository root. It must load the live German frequency model first, clone its fields/templates/CSS under dedicated preview identities, build seven notes through `build_multilang_note`, and replace only the requested APKG. Do not call `export_anki_package`, because that service intentionally applies the production deck ID and media contract.

```bash
PYTHONPATH=src uv run python - <<'PY'
from pathlib import Path

import genanki

from multilang.domain.exporting import ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
from multilang.services.export_anki_package import (
    DECK_ID as PRODUCTION_DECK_ID,
    MODEL_ID as PRODUCTION_MODEL_ID,
    build_multilang_model,
    build_multilang_note,
)

OUTPUT = Path("german_frequency_template_dummy.apkg")
PREVIEW_MODEL_ID = 1_995_036_001
PREVIEW_DECK_ID = 1_995_036_002
HEIGHT_RULE = "min-height: min(760px, calc(100vh - 80px));"

assert PREVIEW_MODEL_ID != PRODUCTION_MODEL_ID
assert PREVIEW_DECK_ID != PRODUCTION_DECK_ID

live_model = build_multilang_model(
    source_type="frequency",
    language=SupportedLanguage.DE,
)
assert HEIGHT_RULE in live_model.css

preview_model = genanki.Model(
    PREVIEW_MODEL_ID,
    "Multilang::German Frequency Dummy Preview",
    fields=[dict(field) for field in live_model.fields],
    templates=[dict(template) for template in live_model.templates],
    css=live_model.css,
)
deck = genanki.Deck(
    PREVIEW_DECK_ID,
    "Multilang::German Frequency Template Dummy Preview",
)

cards = [
    ("der Alltag", "/deːɐ̯ ˈʔaltaːk/", "everyday life; the ordinary activities and routines of a normal day", "Im Alltag fahre ich meistens mit dem Fahrrad zur Arbeit.", "In everyday life, I usually ride my bicycle to work."),
    ("zuverlässig", "/ˈt͡suːfɛɐ̯ˌlɛsɪç/", "reliable; able to be trusted to work well or behave consistently", "Unsere Nachbarin ist sehr zuverlässig und hilft immer pünktlich.", "Our neighbor is very reliable and always helps on time."),
    ("trotzdem", "/ˈtʁɔt͡sdeːm/", "nevertheless; despite the situation just mentioned", "Es regnete stark, trotzdem gingen wir im Park spazieren.", "It was raining heavily; nevertheless, we went for a walk in the park."),
    ("die Herausforderung", "/diː hɛʁˈaʊ̯sˌfɔʁdəʁʊŋ/", "a demanding task or situation that requires sustained effort, careful thought, and the willingness to adapt before a satisfactory result can be reached", "Obwohl die Herausforderung zunächst größer wirkte als erwartet, teilte das Team sie in klare Schritte auf und fand schließlich eine ruhige, zuverlässige Lösung.", "Although the challenge initially seemed larger than expected, the team divided it into clear steps and eventually found a calm, reliable solution."),
    ("sich entscheiden", "/zɪç ʔɛntˈʃaɪ̯dn̩/", "to decide; to make a choice after considering alternatives", "Nach einem langen Gespräch entschied sie sich für den früheren Zug.", "After a long conversation, she decided on the earlier train."),
    ("gemütlich", "/ɡəˈmyːtlɪç/", "cozy, comfortable, and pleasantly relaxed", "Das kleine Café ist am Abend besonders gemütlich.", "The small café is especially cozy in the evening."),
    ("wahrscheinlich", "/vaːɐ̯ˈʃaɪ̯nlɪç/", "probably; in a way that is likely to happen or be true", "Der Brief kommt wahrscheinlich schon morgen an.", "The letter will probably arrive tomorrow."),
]

for rank, (word, ipa, definition, sentence, translation) in enumerate(cards, start=1):
    row = ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.DE,
            source_type="frequency",
            job_id="quick-036-german-dummy-preview",
            item_key=f"dummy-level-1-rank-{rank:04d}",
            lemma_key=f"de-dummy-{rank:04d}",
            sort_index=rank,
        ),
        word=word,
        front_of_card=word,
        ipa=ipa,
        definitions=definition,
        example_sentence=sentence,
        translation=translation,
        word_audio="",
        sentence_audio="",
        image="",
    )
    deck.add_note(build_multilang_note(row, model=preview_model))

OUTPUT.unlink(missing_ok=True)
package = genanki.Package(deck)
package.media_files = []
package.write_to_file(str(OUTPUT))
assert OUTPUT.is_file() and OUTPUT.stat().st_size > 0
print(f"created {OUTPUT} with {len(cards)} notes")
PY
```

    Per D-07, do not stage or commit the artifact and do not update planning state/log files. After verification succeeds, create `036-SUMMARY.md` recording the fixed preview IDs, seven-note count, exact commands/results, no network/providers, no product/test changes, no formal visual proof, and both reduced-assurance reasons from this plan.
  </action>
  <verify>
    <automated>PYTHONPATH=src uv run python -c 'exec("""from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile
import json
import sqlite3

from multilang.services.export_anki_package import DECK_ID, MODEL_ID

path = Path("german_frequency_template_dummy.apkg")
preview_model_id = 1_995_036_001
preview_deck_id = 1_995_036_002
expected_notes = 7
height_rule = "min-height: min(760px, calc(100vh - 80px));"

assert path.is_file() and path.stat().st_size > 0
assert is_zipfile(path)
with ZipFile(path) as archive, TemporaryDirectory() as temp_dir:
    assert "collection.anki2" in archive.namelist()
    database = Path(temp_dir) / "collection.anki2"
    database.write_bytes(archive.read("collection.anki2"))
    with sqlite3.connect(database) as connection:
        note_count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        model_ids = {row[0] for row in connection.execute("SELECT DISTINCT mid FROM notes")}
        deck_ids = {row[0] for row in connection.execute("SELECT DISTINCT did FROM cards")}
        fields = [row[0].split("\\x1f") for row in connection.execute("SELECT flds FROM notes")]
        models_raw, decks_raw = connection.execute("SELECT models, decks FROM col").fetchone()

models = json.loads(models_raw)
decks = json.loads(decks_raw)
model = models[str(preview_model_id)]
deck = decks[str(preview_deck_id)]

assert note_count == expected_notes
assert model_ids == {preview_model_id} and MODEL_ID not in model_ids
assert deck_ids == {preview_deck_id} and DECK_ID not in deck_ids
assert all(token in model["name"] for token in ("Dummy", "Preview"))
assert all(token in deck["name"] for token in ("Dummy", "Preview"))
assert height_rule in json.dumps(model, ensure_ascii=False)
assert all(len(parts) == 9 for parts in fields)
assert all(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] for parts in fields)
assert all(parts[6] == parts[7] == parts[8] == "" for parts in fields)
assert any(len(parts[3]) > 100 and len(parts[4]) > 120 for parts in fields)
print("APKG OK: 7 notes, live height rule, blank media/Image, preview-only model/deck IDs")
""")'</automated>
  </verify>
  <done>`german_frequency_template_dummy.apkg` is a non-empty readable APKG with `collection.anki2`, exactly seven complete representative notes (including long content), the live Quick 035 height rule, blank media/Image fields, and only the dedicated Dummy/Preview model/deck IDs; no other root artifact, permanent script, provider/network call, product/test edit, planning-state update, or Git action occurs.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Live local template/data -> APKG | Read-only project content is packaged into a user-imported archive under new identities. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q036-01 | Tampering | Anki model/deck identity | mitigate | Use fixed preview-only IDs/names and inspect `notes.mid`, `cards.did`, and collection JSON against production constants before claiming success. |
| T-Q036-02 | Information disclosure / SSRF | Inline generator | mitigate | Use only fixed fictitious card text and local services; make no network/provider calls and package no media or user data. |
| T-Q036-03 | Tampering | APKG inspection | mitigate | Read only the known `collection.anki2` member into a temporary directory and remove it automatically after parameterized SQLite reads. |
</threat_model>

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Quickly deliver a German frequency dummy deck for manual Anki inspection | Task 036-01 generation command |
| REQ | Quick mode has no ROADMAP requirement IDs | N/A (`requirements: []`) |
| RESEARCH | Existing Python/uv/genanki model/note/template services and APKG SQLite shape | Task 036-01 uses and inspects those established patterns |
| CONTEXT | D-01 through D-07: read-only product, live template, preview IDs, seven offline cards, inline generation, minimal checks, no planning/Git updates | Task 036-01 action, verify, done, and boundaries |

Excluded without gap: product/test changes, permanent scripts, real frequency/provider data, audio/images, network calls, broad tests, UI proof, screenshots, formal visual verification, planning-state/log updates, and Git actions.

## Success Criteria

- Exactly one task produces the one requested root APKG and includes runnable generation and verification commands.
- The package satisfies every D-01 through D-07 condition and the minimal verifier prints the declared success line.
- The executor creates `.planning/quick/036-gerar-deck-dummy-alemao/036-SUMMARY.md`; no verifier/UI-proof artifact is required by this plan.
