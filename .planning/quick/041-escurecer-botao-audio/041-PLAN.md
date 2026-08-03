# Quick Task Plan: Escurecer Botao de Audio

## Objective

Remover o fundo branco herdado ou explicito pelo botao de audio nos templates escuros de Japones, Kana, Latim e Highlight.

## Task 1: Criar regressao de CSS

<files>
- `tests/services/test_card_template_loader.py`
</files>

<action>
- Adicionar teste que exige `.replay-button` sem fundo branco nos templates afetados.
</action>

<verify>
- Rodar o teste focado e observar falha antes da implementacao.
</verify>

## Task 2: Ajustar templates e preview

<files>
- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
- `src/multilang/templates/highlight_card.md`
- `templates_preview.html`
</files>

<action>
- Estilizar o proprio `.replay-button`, nao apenas o SVG interno.
- Regenerar o preview consolidado.
</action>

<verify>
- Rodar testes focados de template/deck e validacao estatica do preview.
</verify>
