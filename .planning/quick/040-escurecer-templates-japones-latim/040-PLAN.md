# Quick Task Plan: Escurecer Templates de Japones e Latim

## Objective

Fazer os decks de Japones, Kana e Latim renderizarem em tema escuro por padrao, sem depender de `nightMode`.

## Task 1: Atualizar CSS dos templates

<files>
- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
</files>

<action>
- Trocar variaveis de fundo/texto default para os valores escuros ja usados em night mode.
- Ajustar cores de headers, divisores, palavras, botoes e midia para manter contraste no modo escuro.
</action>

<verify>
- Checar que os templates nao mantem fundo branco como padrao.

## Task 2: Atualizar preview e validar

<files>
- `templates_preview.html`
- `.planning/quick/040-escurecer-templates-japones-latim/040-SUMMARY.md`
- `.planning/quick/040-escurecer-templates-japones-latim/040-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>

<action>
- Regenerar `templates_preview.html` com as novas cores.
- Registrar o resultado da quick task.
</action>

<verify>
- Validar que o preview contem os 7 templates e 14 iframes.
- Rodar testes focados de template se disponiveis.
</verify>
