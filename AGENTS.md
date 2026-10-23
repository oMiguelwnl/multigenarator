<!-- GSD:project-start source:PROJECT.md -->
## Project

**Multilang Anki Card Generator**

Multilang is a multilingual Anki card generator focused on the most frequent words in a target language. It creates high-quality study decks for modern-language frequency, user-provided word lists, and reading highlights, with language-specific foundation paths where needed. v3.0 plans complete Korean support alongside the existing language and Classical Latin paths.

The product generates structured Anki-ready cards with word data, phonetics, definitions, example sentences, translations, audio, and an empty image field that the user can fill manually later. AI-assisted generation is part of the intended approach, but the exact provider and supporting services still need research and validation.

**Core Value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.

### Constraints

- **Languages**: v1 supports Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch; v3.0 adds modern standard Korean with canonical code `ko` and provider locale `ko-KR`.
- **Deck Size — all languages**: 3,000 is an initial frequency reference, not a maximum number of cards per language. A language may have more than 3,000 cards when useful vocabulary, distinct senses or pedagogically important forms justify them. Preserve quality, lexical identity, provenance and deduplication; do not discard valid content or generate redundant conjugations merely to meet a number. The existing three levels of 1,000 core entries are the initial organization, not a ceiling on total cards. Foundation, custom-list and highlight decks follow their own content needs.
- **Frequency organization**: Count lexical identities separately from cards. Keep useful cards for an existing identity with its parent frequency level, even when that level exceeds 1,000 cards. Put additional lexical identities beyond the initial core in frequency expansions, retaining their source/rank metadata. Prefer a small deck hierarchy and tags for detailed classification; frequency bands are not proficiency certificates.
- **Vocabulary coverage — all languages**: The user's target is at least 90% lexical occurrence coverage in representative general-use material, expanding the vocabulary when needed rather than stopping at 3,000 cards. Measure the finalized inventory against independent, versioned evaluation corpora with language-appropriate normalization/morphology; report spoken and written coverage separately, the counting unit and exclusions. Card count and literature estimates do not prove achieved coverage or comprehension. This is a target until the exact inventory has been evaluated.
- **Current preparation scope**: The user requested vocabulary files and reports for every language now, with deck generation deferred until a later explicit instruction. Notify the user before resuming card text, translation, audio or deck generation. Offline preparation and tests may proceed; do not interpret completed preparation as authorization to run generation.
- **Korean Decks**: Korean includes Hangul foundations, strict-i+1 pronunciation, three frequency levels, strict-i+1 Particles & Endings, custom lists, and privacy-safe highlights.
- **Korean Linguistics**: Korean content must use NFC normalization, morphology-aware lemma/POS/sense identity, and fail-closed target matching rather than whitespace or suffix heuristics.
- **Korean Licensing**: A redistributed 3000-entry Korean frequency asset requires an approved source, attribution, and redistribution decision before it is committed.
- **Output Quality**: Example sentences and translations must be high quality — prior low-quality outputs from Tatoeba are a known concern.
- **Audio Provider**: Audio should use Azure TTS if the required voices are available — this is the user's preferred TTS direction.
- **Card Schema**: The generated deck must preserve the requested field set and formatting — Anki export usefulness depends on consistent structure.
- **Engineering Quality**: The codebase must follow architecture and good practices, with tests and fallbacks — reliability is a stated requirement, not a nice-to-have.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:docs/development-stack-reference.md -->
## Technology Stack

- Python 3.12 and uv; FastAPI + Typer + Pydantic v2; SQLAlchemy 2 + Alembic; PostgreSQL 17 target with an 18-compatible schema.
- PydanticAI typed generation and LiteLLM provider fallback; generic/manual lexical grounding and IPA cache. Generate definitions and grounded examples through the configured LLM; validate target inclusion with spaCy/Stanza.
- Use wordfreq only for bootstrap candidates; curate, deduplicate, freeze and version production lexical assets with provenance.
- DeepL for sentence translation, with LLM QA/repair as fallback; Azure Speech for separate, cached, idempotent word/sentence audio; genanki for stable-schema Anki exports.
- Keep pytest, mocked provider/API checks, lexical validation and golden export regressions. Preserve field order, HTML, media references and stable GUIDs.
- Do not use Tatoeba as the default sentence source, LLM-only dictionary/IPA, SQLite as the production source of truth, or live provider responses as permanent truth.
- Before architecture, dependency, provider, persistence, generation, validation or export changes, read the relevant sections of [the full stack reference](docs/development-stack-reference.md). It preserves the original version recommendations, storage model, alternatives, rationale and source links. Check installed versions and existing code before treating historical recommendations as current facts.

## Working Practices

- Implement the user's requested scope and follow existing codebase conventions.
- Verify changes before claiming completion.
- Research unfamiliar domains from real documentation and code.
- Existing `.planning/` documents remain available as project history and context.
- Put generated card previews, examples, decks and delivery reports under the single `output/` root: `previews/`, `examples/`, `decks/` and `reports/`. Use the output directory properties in `Settings`; respect an explicit user-supplied destination.
- Keep each example's HTML, images, audio and supporting files together. Do not create new deliverables in the repository root, `docs/`, `work/`, `exports/` or `.multilang/verification/`. See `output/README.md` for the directory convention.
- Templates belong in `src/multilang/templates/`, reusable generators in `scripts/`, and runtime databases/caches in `.multilang/`. Historical compatibility links are not new output destinations.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

## Gitflow and worktrees

- Follow [the Gitflow + worktree workflow](docs/gitflow-worktrees.md) for branch creation, integration, releases and cleanup. Use native Git; the `git-flow` extension is not required.
- `main` holds stable releases; `develop` is the integration branch. Start `feature/<slug>` and `fix/<slug>` from `develop`, `release/<version>` from `develop`, and `hotfix/<slug>` from `main`. Merge features/fixes into `develop`; merge releases/hotfixes into `main` and back into `develop`, tagging the resulting release commit on `main`.
- Use one dedicated worktree per task under the ignored `.worktrees/` directory. Inspect `git status`, `git branch -a` and `git worktree list` before creating one. Never check out the same branch in two worktrees or use `--force` to bypass Git protections.
- Preserve existing dirty worktrees and unrelated changes. A new worktree contains committed files only; do not silently stash, copy secrets, move unfinished work, reset branches or include another task's files in a commit.
- During migration, do not infer a stable baseline from the current feature branch or from the legacy `Monarch` name. Establish a reviewed baseline before creating `main`/`develop`; until then, explicitly identify the existing integration branch used as the task base.
- Keep each worktree's virtual environment, runtime state, output and test database isolated. Run the relevant offline checks before integration; worktree creation does not authorize provider calls or deck generation.
- Prefer reviewed PRs and merge commits (`--no-ff` for local integration). Do not force-push shared branches. Remove a worktree only after checking tracked, untracked and ignored files for useful data, and delete its branch only after confirming integration. Never use forced cleanup by default.

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

Project skills are stored in `.agents/skills/`. Use relevant skills when they help fulfill the user's request.
<!-- GSD:skills-end -->

## Conventional Commits

- The user authorizes local staging and commits for the requested work without repeated confirmation. Review the diff, validate the change, stage only task-owned paths, then commit using Conventional Commits. This does not authorize unrelated changes, history rewrites, pushes or merges beyond the requested scope.
- Execute `git add` and `git commit` directly with the tool's working directory set to the intended checkout. Do not wrap routine Git writes in Python, shell loops, substitutions or custom commit scripts: those wrappers do not match Git approval rules.
- For existing worktrees without project-local Codex rules, use `git -C /absolute/path/to/checkout add ...` and `git -C /absolute/path/to/checkout commit ...`; this machine has scoped allow rules for the current Multilang checkouts. Preserve hooks and branch protections.

- All new commits across this project must follow Conventional Commits 1.0.0 and the project policy in CONTRIBUTING.md. Preserve historical commits.
- Use lowercase types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert. Optional scopes use lowercase letters, digits, dots, underscores, slashes or hyphens. Provide a concrete description in Portuguese or English.
- Use `feat` for features, `fix` for bug fixes; mark breaking changes with `!` or a `BREAKING CHANGE:` footer. Separate body/footer from the subject with a blank line.
- Merge messages and PR titles must also follow the format; use `chore(merge): ...`, not `merge: ...` or Git's default merge title. Reverts use `revert: ...`.
- The local commit-msg hook is shared across worktrees through core.hooksPath. Do not bypass it with --no-verify. Check existing hooks before configuring another clone.

## Current branch organization

- `main` is the GitHub default branch, initialized from local `Monarch`; `develop` integrates completed work. Both require PRs and the Conventional Commits check; force-push and deletion are blocked.
- Preserve `Monarch`. `feature/roadmap-4-0-native-architecture` remains in progress, with its root checkout retained. Changes are committed here only when authorized; integration into `develop`/`main` requires a later explicit request.
- Full workflow and hook installation details are in CONTRIBUTING.md and docs/gitflow-worktrees.md. Existing historical commits are not rewritten.
