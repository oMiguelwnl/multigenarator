# Saídas do Multilang

Esta é a pasta única para arquivos gerados de cards e decks. O
[índice visual](index.html) reúne as entregas locais disponíveis.

```text
output/
  previews/                 HTML e capturas de tela
    mandarin/               Frente, verso, pinyin e cores por tom
    frequency/              Template de frequência e demonstrações
    output-deck/            Protótipo do deck de produção de frases
    legacy/                 Prévias históricas preservadas
  examples/                 Amostras, pilotos e testes de exportação
    mandarin/               Piloto de revisão de pronúncia e sentidos
    japanese/               Kana e validação de frequência
    pt/                     Pilotos em português
    quality/                Amostras de qualidade
    legacy/                 Pacotes demonstrativos antigos
  decks/                    Exportações APKG, CSV e TSV
  reports/                  Revisões, auditorias e verificações
```

## Abrir os cards

- Vocabulário: [preparação dos 22 idiomas modernos e latim](reports/vocabulary-preparation/README.md), com geração de conteúdo e decks adiada.
- Mandarim: [frente](previews/mandarin/front.html), [verso](previews/mandarin/back.html), [imagem no celular](previews/mandarin/back-390.png).
- Revisão de mandarim: [36 contextos revisados por IA](examples/mandarin/review-pilot/index.html), [relatório](reports/mandarin/linguistic-review-20260920/review.md).
- Frequência: [prévia interativa](previews/frequency/index.html), [proposta anterior](previews/frequency/proposal.html), [deck demonstrativo](previews/frequency/artifacts/multilang-frequency-minimal-dark-demo.apkg).
- Produção de frases: [protótipo](previews/output-deck/prototype.html), [prévia do card](previews/output-deck/card.html).
- Português: [piloto](examples/pt/pilot/pilot.apkg).
- Japonês: [kana](examples/japanese/kana/japanese-kana.apkg), [amostra de frequência](examples/japanese/validation/japanese-dynamic-frequency-smoke.apkg).
- Coreano: [Hangul](decks/korean-foundations/hangul.apkg), [pronúncia](decks/korean-foundations/pronunciation-i-plus-1.apkg), [gramática](decks/korean-grammar/v1/coreano-gramatica-v1.apkg).

As saídas locais não acompanham necessariamente um checkout novo. Os geradores
recriam os arquivos nos destinos documentados. A pasta de um deck indica seu
destino de exportação; seus relatórios continuam determinando a qualificação.

## Gerar novos arquivos

Execute a partir da raiz do projeto:

```bash
uv run python scripts/preview_mandarin_card.py
uv run multilang prepare-local-smoke
uv run multilang export --job-id SEU_JOB --format apkg
```

Use `Settings().preview_output_dir`, `example_output_dir`, `export_output_dir` e
`report_output_dir` em scripts novos. A raiz padrão é `output/`; a variável
`MULTILANG_OUTPUT_DIR` permite alterá-la. O override existente
`MULTILANG_EXPORT_OUTPUT_DIR` e destinos explícitos dos comandos são preservados.
O comando `korean-foundations inspect-exports` inspeciona o conjunto fixo em
`output/decks/korean-foundations/`.

Organize por idioma ou finalidade dentro destas pastas e mantenha cada exemplo
com suas mídias e arquivos de apoio. Não crie novas pastas de saída na raiz,
em `docs/`, `work/`, `exports/` ou `.multilang/verification/`.

Templates continuam em `src/multilang/templates/`; geradores reutilizáveis,
em `scripts/`. Bancos, modelos e caches operacionais continuam em `.multilang/`.

## Arquivos anteriores

A organização de 20/09/2026 moveu as entregas existentes preservando seu conteúdo.
Os caminhos antigos em `.multilang/` têm links de compatibilidade para os arquivos
aqui, preservando acessos de scripts, registros e relatórios anteriores. Eles não
são cópias nem destinos para novas entregas. O registro da migração, com hashes,
fica em `reports/output-organization/migration.json`.

Relatórios históricos de testes e cópias de trabalho fora das entregas migradas
continuam em `.multilang/verification/` como histórico técnico.
