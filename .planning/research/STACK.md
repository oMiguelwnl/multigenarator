# Technology Stack Research: Classical Latin v2.0 MVP

**Project:** Multilang Anki Card Generator — v2.0 Classical Latin MVP  
**Researched:** 2026-06-01  
**Scope:** New Latin-only stack/resource additions for a 50-card MVP; do not replace the validated Python/uv/Pydantic/Azure/genanki pipeline.  
**Overall confidence:** MEDIUM-HIGH for frequency/morphology/sentence resources; MEDIUM for TTS quality because Classical Latin commercial neural support remains weak/unverified.

## Bottom-line Recommendation

Do **not** add a separate Latin platform. Keep the existing Python 3.12 + uv CLI pipeline and add a thin Latin resource layer with frozen assets, deterministic validators, and human review gates.

For the MVP:

1. **Frequency-by-lemma:** Use **Dickinson College Commentaries Latin Core Vocabulary** as the primary MVP ordering source, not a freshly computed corpus frequency list. It is already lemma/headword based, has ranks, has Portuguese UI pages, and was created from LASLA/TLG-derived frequency data. Freeze the 50 selected lemmas in project assets with rank/provenance.
2. **Lemmatization/morphology:** Use **CLTK 1.5.0** as the Python-native adapter only if the project remains on Python 3.12. Do **not** upgrade to CLTK 2.x unless the whole project moves to Python 3.13. For actual card acceptance, cross-check with **Collatinus 11.2 CLI/data** or manually curated morphology fixtures because Latin token analysis is ambiguous.
3. **Sentence source selection:** Use **DCC/Perseus public-domain classical texts** for source discovery, but store only vetted excerpts with citation/provenance in frozen project fixtures. For the first 50 cards, prefer short prose or didactic lines over raw poetic frequency examples.
4. **Portuguese translation and grammar notes:** Keep the existing PydanticAI/LiteLLM-style structured generation pattern, but treat PT translation/grammar as **review-required generated fields**. Validate against Latin morphology and target-form-in-sentence checks; do not allow LLM-only grammar to approve cards.
5. **Latin audio/TTS:** Make **eSpeak NG 1.52+ (`-v la`)** the primary MVP Latin audio provider because it explicitly supports Latin and runs locally. Keep Azure as an experiment/fallback only through multilingual voices, because Azure and Google official voice lists do **not** list Classical Latin/`la` as a supported TTS locale. Audio quality must be marked `experimental` until human playback approval.

## Recommended Additions

### Core additions

| Capability | Recommended addition | Version / status | Purpose | Why | Confidence |
|---|---|---:|---|---|---|
| Latin NLP adapter | `cltk==1.5.0` | PyPI release 2025-05-04; Python `>=3.9,<3.13` | Tokenization, normalization, candidate lemmatization hooks | Last CLTK line compatible with current Python 3.12 project. CLTK 2.5.1 requires Python >=3.13, so it is not a drop-in addition. | HIGH |
| Latin frequency seed | DCC Latin Core Vocabulary | ~1000 ranked headwords | MVP frequency-by-lemma ordering | Already ranked by lemma/headword, pedagogical, peer-reviewed DCC ecosystem, PT-localized page exists. Faster and safer than building a 50-card corpus frequency system first. | HIGH |
| Morphology cross-check | Collatinus | 11.2 source line; GPL-3.0 | Lemma + morphology validation, quantities/scansion signal | Strong Latin-specific lemmatizer/analyzer; recognizes >500k forms from ~11k lemmas. Use as CLI/tool boundary or data reference, not as linked library, to contain GPL risk. | MEDIUM-HIGH |
| Gold morphology fixtures | UD Latin Perseus / Perseus LDT samples | UD 2.18 page; CC BY-NC-SA 2.5 | Test cases for POS/features/case labels | Manual/semi-manual annotation with lemmas, morphology, dependency relations; useful for validators and grammar-note examples. NC license means test/reference only unless project accepts share-alike/noncommercial obligations. | MEDIUM |
| Latin source texts | PerseusDL `canonical-latinLit` + DCC texts | Perseus repo latest release seen 2026-04-22; CC BY-SA 4.0 unless otherwise indicated | Traceable sentence candidates and citations | Canonical XML resources and Scaife integration; DCC provides educational commentary context. Must preserve attribution/license metadata. | MEDIUM-HIGH |
| Local Latin TTS | eSpeak NG | 1.52 latest release Dec 2024; development docs list `la` Latin | Word/sentence audio synthesis | Only verified option found with explicit Latin support, local execution, and automatable CLI. Voice is formant/synthetic, so quality review is mandatory. | HIGH for availability; MEDIUM for learner quality |

### Keep from existing stack

| Existing component | Latin integration point |
|---|---|
| Python 3.12 + uv | Add Latin optional dependencies/assets under the current project; do not fork runtime. |
| Pydantic v2/domain models | Add `LatinCard`, `LatinMorphology`, `LatinSourceCitation`, `LatinAudioMetadata`, and strict enums for cases/functions. |
| Typer CLI | Add `latin import-frequency`, `latin select-sentences`, `latin generate-50`, `latin synthesize-audio`, `latin export` commands or subcommands. |
| Provider adapter pattern | Add `LatinMorphologyProvider`, `LatinFrequencyProvider`, `LatinSentenceSourceProvider`, `LatinTtsProvider`. |
| Existing audio cache/export | Store provider `espeak-ng`, voice `la`, command/version, text hash, pronunciation profile, and human playback status. |
| genanki/APKG export | Add a dedicated Latin note type and fields; do not overload normal modern-language note schema. |

## Prescriptive Stack by Feature

### 1) Frequency-by-lemma

**Primary:** DCC Latin Core Vocabulary, frozen into project CSV/JSON.

Recommended asset fields:

```csv
frequency_rank,lemma,headword_display,pos,semantic_group,short_gloss_en,short_gloss_pt,source_url,source_license,selected_for_mvp
```

**Why:** The MVP is 50 cards, not a full Latin corpus project. DCC states the Latin core vocabulary is about 1000 lemmas and that core lemmas generate about 75% of words in a typical text. Its public list exposes `Frequency Rank`, POS/declension/conjugation categories, semantic groups, and Portuguese localization. This is exactly the needed MVP ordering signal.

**Fallback:** If DCC scraping/import is too brittle, create a manually curated `latin_mvp_50_lemmas.csv` using DCC rank/source URLs plus a few Rafael Falcon progression overrides. The file should remain auditable and sorted by `frequency_rank` plus `didactic_order`.

**Do not add yet:** A full LASLA/TLG corpus-frequency pipeline. DCC already used LASLA/TLG-derived frequency work; recreating it is overkill for 50 cards and brings licensing/access complexity.

### 2) Lemmatization and morphology

**Primary integration:** `cltk==1.5.0` for Python 3.12-compatible Latin NLP plumbing.

Important version constraint:

- CLTK **2.5.1** is current on PyPI, but requires **Python >=3.13**.
- This project is Python **3.12**, so use **CLTK 1.5.0** (`>=3.9,<3.13`) or defer CLTK 2.x until a separate Python upgrade phase.

**Validation/fallback:** Collatinus 11.2 as a subprocess or manually exported reference table for ambiguous forms. Because Collatinus is GPL-3.0, keep it behind a process/tool boundary and record whether generated artifacts include Collatinus-derived data. If the project later distributes Collatinus code/data with the app, legal review is needed.

**Manual-review rule:** No automatic analyzer should be treated as definitive for the `Gramatica` field. Latin forms are frequently ambiguous (`Romae`, `arma`, `cum`, enclitics like `-que`). Accepted cards need `review_status=approved` after human or curated fixture review.

Recommended Pydantic fields:

```python
class LatinMorphology(BaseModel):
    target_form: str
    lemma: str
    pos: Literal["subst", "adj", "pron", "v", "prep", "conj", "adv", "part", "num", "interj"]
    gender: Literal["masc", "fem", "neut"] | None
    case: Literal["Nominativus", "Vocativus", "Accusativus", "Genitivus", "Dativus", "Ablativus", "Locativus"] | None
    number: Literal["singularis", "pluralis"] | None
    tense: str | None
    mood: str | None
    voice: str | None
    syntactic_function: Literal["Suj", "OD", "OI", "CN", "Adj Adv", "verbo principal", "prep", "conj"] | str
    analyzer_candidates: list[str]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    review_status: Literal["needs_review", "approved", "rejected"]
```

### 3) Source sentence selection

**Primary:** curated frozen Latin sentence fixtures sourced from DCC/Perseus texts, not live scraping at generation time.

Recommended sentence asset fields:

```csv
sentence_id,latin_sentence,normalized_sentence,target_form,lemma,author,work,passage,source_url,source_license,is_original,is_adapted,complexity_score,notes
```

**Selection rules for MVP:**

- Prefer 4-12 token sentences or sentence fragments that remain grammatically coherent.
- Prefer target-form clarity over famous-line value.
- Avoid first-batch poetic inversions unless Rafael Falcon progression explicitly wants them.
- If using adapted didactic sentences, mark `is_adapted=true` and cite the adaptation source/rule. Do not represent adapted text as classical quotation.
- Always store source line/passage, URL, license, and retrieval date.

**Good starting sources:**

- DCC texts/commentaries for pedagogically curated passages and reference notes.
- PerseusDL `canonical-latinLit` / Scaife for canonical XML text and stable classical citations.
- UD Latin Perseus only for morphology/dependency examples; its CC BY-NC-SA 2.5 license is too restrictive for casual content reuse in shipped decks unless explicitly accepted.

### 4) Portuguese translation and grammar notes

**Primary:** existing structured LLM generation workflow, constrained by Latin fixtures and validated morphology.

Use the LLM to draft:

- `short_translation_pt`
- `sentence_translation_pt`
- `grammar` in the short deck style

Do **not** let the LLM choose the lemma/case/function from scratch. Feed it the selected sentence, target form, lemma, candidate morphology, source citation, and allowed labels.

Validation gates:

- `target_form` must appear in the Latin sentence after normalization/enclitic handling.
- `lemma` must match the frequency asset.
- `grammar` must start with `target_form:` and use approved case spelling (`Genitivus`, not `Genetivus`).
- If morphology confidence is LOW or multiple plausible analyses remain, card stays `needs_review`.
- Portuguese translation must be contextual, not just dictionary gloss.

**Fallback:** Human-authored PT translations for the 50-card MVP are preferable to adding DeepL Latin support assumptions. DeepL supports Portuguese as a target language, but Latin is not a standard source language in the verified project stack; use LLM/human review, not DeepL, for Latin → Portuguese.

### 5) Latin TTS/audio

**Primary for MVP:** eSpeak NG CLI with voice `la`.

Example integration:

```bash
espeak-ng -v la -s 135 -w output.wav "Arma virumque cano."
```

Then convert/normalize to the project’s expected media format if necessary.

Why this is the recommendation:

- eSpeak NG official docs list BCP-47 identifier `la`, family `Italic`, language `Latin`.
- It is local, deterministic, scriptable, and can produce WAV files.
- The project already has audio hashing/cache/export gates; eSpeak can fit the same provider adapter shape.

Quality limitations:

- eSpeak NG uses formant synthesis; its own README says speech is clear and compact but not as natural or smooth as larger systems based on human recordings.
- Classical pronunciation quality must be manually tested. Store `pronunciation_profile="classical_approx"` unless a reviewed profile is chosen.

**Azure status:** Keep Azure as an experimental secondary adapter only. Microsoft’s official 2026 TTS voice table contains multilingual voices but no Latin/`la` locale; search hits for “Latin” refer to scripts/regions like Azerbaijani Latin, not Classical Latin. Do not promise Azure Latin audio unless a manual sample audition passes and metadata says it is a multilingual fallback, not native Latin.

**Google status:** Google Cloud TTS official voice list similarly has no Classical Latin/`la` support found in the supported voices page. Do not add Google Cloud TTS for this milestone.

**Best fallback if eSpeak quality fails:** Human-recorded audio for the 50-card MVP. This is operationally feasible at 100 clips (word + sentence) and likely higher quality than pretending a modern-language neural voice supports Latin.

Recommended audio metadata additions:

```json
{
  "provider": "espeak-ng",
  "provider_version": "1.52",
  "voice": "la",
  "pronunciation_profile": "classical_approx",
  "input_text": "Arma virumque cano.",
  "input_hash": "...",
  "audio_kind": "sentence",
  "quality_status": "needs_playback_review"
}
```

## Alternatives Considered

| Category | Recommended | Alternative | Why not / when to revisit | Confidence |
|---|---|---|---|---|
| Frequency | DCC Latin Core Vocabulary | Build corpus frequency from Perseus texts | Too much for 50 cards; lemmatization ambiguity and corpus composition will dominate roadmap. Revisit for 300/1000-card Latin scaling. | HIGH |
| Frequency | DCC + curated `didactic_order` | Pure Rafael Falcon grammar progression | User wants frequency organization; use Falcon progression as tie-breaker/filter, not replacement. | MEDIUM |
| NLP Python dependency | CLTK 1.5.0 | CLTK 2.5.1 | CLTK 2.5.1 requires Python >=3.13; project baseline is 3.12. | HIGH |
| Morphology | CLTK + Collatinus cross-check + review | LEMLAT 3.0 | LEMLAT is strong but type-only/no context disambiguation per README, C build/integration overhead, and CC BY-NC-SA license. Use as research/reference, not MVP dependency. | MEDIUM-HIGH |
| Morphology | Tool-assisted curated fixtures | LLM-only grammar analysis | Too hallucination-prone; Latin ambiguity makes silent grammar errors likely. | HIGH |
| Sentences | Curated DCC/Perseus fixtures | Tatoeba or generated Latin sentences | Known project concern with Tatoeba quality; generated Latin needs strict marking as adapted and review. | HIGH |
| TTS | eSpeak NG `la` | Azure native Latin voice | Official Azure TTS list does not include Classical Latin/`la`. Multilingual voices may pronounce Latin-ish text but are not verified native Latin support. | HIGH |
| TTS | eSpeak NG `la` | Google Cloud TTS | Official Google voice list does not show Classical Latin/`la`; adding provider increases complexity without verified support. | HIGH |
| TTS fallback | Human recording for 50-card MVP | ElevenLabs/other commercial TTS | Could be tested manually later, but no authoritative verified Classical Latin voice support was established here. Avoid adding a new paid provider without audition evidence. | MEDIUM |

## Installation / Dependency Plan

Keep Python 3.12. Add only Python-compatible packages and treat native tools as optional external binaries.

```bash
# Python-native Latin NLP for current Python 3.12 runtime
uv add "cltk==1.5.0"

# Optional if using CLTK's Stanza-backed paths after compatibility tests
uv add "stanza>=1.8,<2"

# Native TTS tool: install outside uv; detect with subprocess in CLI
# Windows: install eSpeak NG 1.52+ and ensure espeak-ng.exe is on PATH
# Linux CI/container: apt/binary package or pinned release artifact
espeak-ng --voices
espeak-ng -v la -w sample.wav "Arma virumque cano."
```

Do not run `uv add cltk` without a version pin: it may resolve to CLTK 2.x, which requires Python 3.13 and can force an unintended runtime upgrade.

## Integration Architecture

Recommended package shape:

```text
multilang/
  latin/
    assets/
      latin_core_vocabulary_mvp.csv
      latin_mvp_sentences.csv
      morphology_gold_fixtures.json
    frequency.py          # DCC/frozen rank loader
    morphology.py         # CLTK/Collatinus adapters + normalization
    sentence_selection.py # fixture-backed selector + complexity scoring
    grammar_notes.py      # structured PT generation + validators
    tts.py                # eSpeak adapter implementing existing audio interface
    schema.py             # LatinCard, LatinMorphology, LatinCitation
    validators.py         # target form, case labels, source/audio/review gates
```

Pipeline:

```text
DCC ranked lemmas
  -> frozen 50-lemma MVP list
  -> curated source sentence candidates
  -> morphology analysis candidates (CLTK + Collatinus/reference)
  -> LLM drafts PT translation + short grammar note
  -> deterministic validators
  -> human review status
  -> eSpeak word/sentence audio
  -> Latin APKG/CSV/TSV export
```

## Licensing and Quality Risks

| Resource | License / risk | Recommendation |
|---|---|---|
| DCC Core Vocabulary/texts | DCC terms say free educational use under CC BY-SA; About page says CC BY-SA 4.0 for commentaries/resources. | Store attribution/source URL/license in every imported asset. Share-alike obligations may apply to redistributed deck content. |
| PerseusDL canonical-latinLit | CC BY-SA 4.0 unless otherwise indicated; repository warns individual materials can vary. | Use with attribution and source metadata. Verify individual text status before broad redistribution. |
| UD Latin Perseus / Perseus treebank | CC BY-NC-SA 2.5. | Use for tests/reference only unless noncommercial/share-alike constraints are acceptable for shipped decks. |
| Collatinus | GPL-3.0. | Use as external CLI or reference during generation; avoid bundling/linking without legal review. |
| LEMLAT 3.0 | CC BY-NC-SA 4.0; type analyzer only, no context disambiguation. | Do not add to MVP runtime. Useful for offline comparison/research. |
| CLTK | MIT. | Safe as Python dependency, but version must be pinned to 1.5.0 for Python 3.12. |
| eSpeak NG | GPL-3.0 plus additional licenses. | Use as installed external binary and record version. Avoid bundling in app distribution until license packaging is reviewed. Generated audio licensing should be reviewed before commercial redistribution. |

## What NOT to Add in v2.0 MVP

- **Do not upgrade the whole project to Python 3.13 only to use CLTK 2.x.** That is a platform migration, not a Latin MVP need.
- **Do not build a full Latin corpus-frequency engine** for 50 cards. Freeze DCC-ranked lemmas now; revisit corpus frequency for 300/1000 cards.
- **Do not use LLM-only morphology or grammar.** Every accepted grammar note must be grounded in analyzer output or curated fixtures and review status.
- **Do not add Google Cloud TTS.** No verified Classical Latin voice support was found in official docs.
- **Do not claim Azure supports Latin TTS.** At most, test Azure multilingual voices as a non-native fallback and label outputs accordingly.
- **Do not use Tatoeba as primary Latin sentence source.** It conflicts with existing project quality decisions and lacks the traceable classical citation style needed here.
- **Do not display a separate `Classe` field** on the card. Keep POS/class internally and express it inside `Gramatica` as specified.

## Open Questions for Phase Planning

1. Does the project/deck distribution model accept CC BY-SA content in generated deck assets? If not, source selection must prioritize public-domain texts and project-authored notes.
2. Is eSpeak NG audio acceptable after human playback review, or should the MVP switch to human-recorded audio for the 50-card launch?
3. Should `Locativus` be allowed as a case label in internal schema while the seed requires the six core cases? Recommendation: yes internally, but keep deck examples conservative.
4. Should CLTK be a runtime dependency or only a dev/import dependency? Recommendation: start as optional/runtime-extra until tests prove installation stability on Windows.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Frequency source | HIGH | DCC list is directly aligned with lemma-rank MVP needs. |
| CLTK version recommendation | HIGH | PyPI confirms CLTK 2.5.1 requires Python >=3.13 and 1.5.0 supports Python 3.12. |
| Morphology architecture | MEDIUM-HIGH | Tool options are clear; ambiguity/review burden remains real. |
| Sentence sources | MEDIUM-HIGH | DCC/Perseus are authoritative; licensing/redistribution must be checked per content. |
| Portuguese translation/grammar generation | MEDIUM | Feasible with existing structured AI pipeline, but human review is essential. |
| Latin TTS | MEDIUM | eSpeak availability is verified; quality for daily learner use is uncertain. |

## Sources

- CLTK GitHub README — Python NLP for pre-modern languages; installation and optional backends — https://github.com/cltk/cltk — HIGH
- CLTK PyPI 2.5.1 — current release, requires Python >=3.13 — https://pypi.org/project/cltk/ — HIGH
- CLTK PyPI 1.5.0 — Python >=3.9,<3.13, compatible with Python 3.12 — https://pypi.org/project/cltk/1.5.0/ — HIGH
- CLTK `pyproject.toml` — version 2.5.1 and Python/dependency metadata — https://github.com/cltk/cltk/blob/master/pyproject.toml — HIGH
- DCC Latin Core Vocabulary — ranked Latin headwords with POS/semantic group/frequency rank and Portuguese page links — https://dcc.dickinson.edu/latin-core-list1 — HIGH
- DCC About — core vocabulary created from LASLA/TLG-derived data; Latin core about 1000 lemmas; CC BY-SA 4.0 statement — https://dcc.dickinson.edu/about-dcc — HIGH
- DCC Terms of Use — free educational use and CC BY-SA terms — https://dcc.dickinson.edu/terms-use — HIGH
- Collatinus GitHub — Latin lemmatizer/morphological analyzer/scansion, 11.2 line, GPL-3.0, >500k forms from ~11k lemmas — https://github.com/biblissima/collatinus — HIGH
- LEMLAT 3.0 GitHub — Latin analyzer/lemmatizer; type-only, no context disambiguation; CC BY-NC-SA 4.0 — https://github.com/CIRCSE/LEMLAT3 — HIGH
- UD Latin Perseus — UD 2.18, Latin treebank stats/features, CC BY-NC-SA 2.5, Morpheus-assisted annotation — https://universaldependencies.org/treebanks/la_perseus/index.html — HIGH
- PerseusDL canonical Latin Literature — canonical XML Latin literature repo, CC BY-SA 4.0 unless otherwise indicated, active releases — https://github.com/PerseusDL/canonical-latinLit — MEDIUM-HIGH
- Scaife Viewer library — Perseus library access/search surface — https://scaife.perseus.org/library/ — MEDIUM
- eSpeak NG README — local TTS, formant synthesis, WAV output, not as natural as larger human-recording-based systems; 1.52 release visible — https://github.com/espeak-ng/espeak-ng — HIGH
- eSpeak NG languages docs — development version lists BCP-47 `la`, Italic, Latin — https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md — HIGH
- Azure Speech language/voice support — no Classical Latin/`la` TTS locale found; multilingual voice caveat — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts — HIGH
- Google Cloud TTS supported voices — no Classical Latin/`la` voice found in official list — https://cloud.google.com/text-to-speech/docs/voices — HIGH
