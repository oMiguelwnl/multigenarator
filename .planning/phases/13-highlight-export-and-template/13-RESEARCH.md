# Phase 13 Research: Highlight Export and Template

**Status:** Complete  
**Discovery level:** Level 1 quick verification  
**Scope:** Existing `genanki` packaging, Anki text import headers, and current project export contracts.

## Findings

### genanki model/template/media behavior

Verified via Context7 (`/kerrickstaley/genanki`) that `genanki.Model` accepts:

- stable model id and note type name
- ordered `fields=[{"name": ...}]`
- one or more card templates with `qfmt` and `afmt`
- optional `css`

The docs show the expected back template pattern:

```python
"afmt": "{{FrontSide}}<hr id=\"answer\">{{Answer}}"
```

Media references belong in fields as `[sound:filename.mp3]` or image HTML and the package must include files through `genanki.Package(...).media_files`.

### Anki text import headers

Verified against the Anki Manual text import docs that Anki 2.1.54+ supports top-of-file headers:

- `#separator:Comma` / `#separator:Tab`
- `#html:true`
- `#notetype:<name>`
- `#deck:<name>`
- `#columns:<field list>`

The manual confirms `[sound:filename.mp3]` is the text import syntax for audio. HTML mode is required for HTML formatting/newline replacement.

## Applied constraints for planning

- No new external dependencies are needed.
- Keep the existing `genanki` package path and media validation pattern.
- Highlight APKG must use the dedicated `Multilang::Highlight Card` model and fields already defined in source profiles/exporting.
- Highlight CSV/TSV must keep strict Anki headers and exact highlight columns with no `Translation`.
- Template validation should detect dangling `{{Field}}` references before writing packages.

## Sources

- Context7 docs: `/kerrickstaley/genanki`, query `Model fields templates css Package media_files Note guid`
- Anki Manual: https://docs.ankiweb.net/importing/text-files.html
