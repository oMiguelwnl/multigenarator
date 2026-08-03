# Quick Task Plan: Preview Todos os Templates

## Objective

Gerar um preview HTML local e navegavel de todos os templates Anki do projeto para revisao visual rapida.

## Task 1: Consolidar preview HTML

<files>
- `templates_preview.html`
</files>

<action>
- Ler os templates em `src/multilang/templates/`.
- Renderizar frente e verso com dados de exemplo.
- Isolar cada preview em `iframe` para evitar conflito de CSS entre templates.
- Incluir todos os templates encontrados: normal, highlight, Latin MVP, phoneme, Mandarin, Japanese frequency e Japanese Kana.
</action>

<verify>
- `python - <<'PY' ... PY` para validar que o HTML existe e contem os 7 nomes de templates esperados.
</verify>

## Task 2: Registrar conclusao

<files>
- `.planning/quick/039-preview-todos-templates/039-SUMMARY.md`
- `.planning/quick/039-preview-todos-templates/039-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>

<action>
- Registrar o resultado da quick task e o caminho do arquivo de preview.
</action>

<verify>
- Confirmar existencia dos arquivos de summary/verification e entrada no log.
</verify>

## UI Proof

No UI proof formal: o artefato solicitado e um HTML local de preview estatico. A aceitacao visual final depende da revisao humana abrindo `templates_preview.html` no navegador.
