# Lexical Data Preparation

`multilang generate` needs a local Kaikki `.jsonl.gz` archive the first time you run lexical grounding for a language.

## First Run

Pass `--lexicon-source-file` with the local archive for the requested language:

```text
uv run python -m multilang.cli generate --language en --source frequency --lexicon-source-file /path/to/kaikki-en.jsonl.gz
```

Or for a custom word list:

```text
uv run python -m multilang.cli generate --language en --source word-list --input-file words.txt --lexicon-source-file /path/to/kaikki-en.jsonl.gz
```

The command builds a reusable cache at `$MULTILANG_LEXICON_DATA_DIR/<language>/kaikki-index.json`.
If `MULTILANG_LEXICON_DATA_DIR` is unset, the default path is `.multilang/lexicon/<language>/kaikki-index.json`.

## Later Runs

After the cache exists, run `multilang generate` again without `--lexicon-source-file` and the shipped runtime will reuse the cached index.

## Local Smoke Assets

To create a minimal local English Kaikki archive plus matching `words.txt` and cached index for smoke generation and Azure audio synthesis, run:

```text
uv run python -m multilang.cli prepare-local-smoke
```

By default this writes `.multilang/live-smoke-azure/kaikki-en.jsonl.gz`, `.multilang/live-smoke-azure/words.txt`, and `.multilang/live-smoke-azure/lexicon/en/kaikki-index.json`.

## Missing Data Behavior

If the cache is missing and no `--lexicon-source-file` was provided, `multilang generate` exits before lexical ingestion starts and prints a prerequisite message instead of producing hollow output.
