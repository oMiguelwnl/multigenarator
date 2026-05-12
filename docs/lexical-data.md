# Lexical Data Preparation

`multilang generate` reads lexical grounding data from a local JSON cache. The runtime does not build this cache from a provider-specific archive.

Card definitions are not sourced from this cache. The cache may provide lookup, display form, lemma, part of speech, and IPA, but `definitions_html` and `provenance.definition` are produced by the configured text-generation provider.

## Cache Location

Create one cache file per language at:

```text
$MULTILANG_LEXICON_DATA_DIR/<language>/lexical-index.json
```

If `MULTILANG_LEXICON_DATA_DIR` is unset, the default path is:

```text
.multilang/lexicon/<language>/lexical-index.json
```

## Cache Format

The file is a JSON object keyed by normalized term. Each value must match the runtime lexical record shape:

```json
{
  "hello": {
    "term": "hello",
    "display_form": "hello",
    "lemma": "hello",
    "definitions": [],
    "part_of_speech": "interjection",
    "grammar_tags": [],
    "ipa": "/həˈloʊ/",
    "source": "manual"
  }
}
```

`definitions` is retained only for compatibility with existing cache files. New card definitions are generated through the LLM definition flow.

## Running Generation

After the cache exists, run `multilang generate` normally:

```text
uv run python -m multilang.cli generate --language en --source frequency
```

Or for a custom word list:

```text
uv run python -m multilang.cli generate --language en --source word-list --input-file words.txt
```

## Local Smoke Assets

To create a minimal local English `words.txt` plus matching cached lexical index for smoke generation and Azure audio synthesis, run:

```text
uv run python -m multilang.cli prepare-local-smoke
```

By default this writes `.multilang/live-smoke-azure/words.txt` and `.multilang/live-smoke-azure/lexicon/en/lexical-index.json`.

## Missing Data Behavior

If the cache is missing, `multilang generate` exits before lexical ingestion starts and prints the expected cache path instead of producing hollow output.
