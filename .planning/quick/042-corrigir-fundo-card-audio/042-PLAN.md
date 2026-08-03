# Quick Task Plan: Corrigir Fundo do Card e Audio

## Objective

Corrigir o fundo branco remanescente nos cards escuros e no botao/icone de audio dos templates Anki.

## Task 1: Fortalecer regressao CSS

<files>
- `tests/services/test_card_template_loader.py`
</files>

<action>
- Verificar que Latim e Japones definem fundo escuro para o canvas do Anki (`body`, `body.card`, `body.nightMode`, `.card`).
- Verificar que os botoes de audio tem override forte contra fundo branco padrao do Anki.
</action>

<verify>
- Rodar o teste focado de CSS e confirmar falha antes do ajuste.
</verify>

## Task 2: Corrigir templates e preview

<files>
- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
- `src/multilang/templates/highlight_card.md`
- `templates_preview.html`
</files>

<action>
- Aplicar fundo escuro ao canvas do card.
- Aplicar overrides `!important` no botao/icone de audio quando necessario.
- Regenerar o preview consolidado.
</action>

<verify>
- Rodar testes focados de template/deck/export.
- Validar estaticamente o preview.
</verify>
