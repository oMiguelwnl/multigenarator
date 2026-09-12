# Multilang

Multilang gera cards Anki multilíngues com identidade lexical, definições,
exemplos, traduções e áudio. O campo `Image` permanece vazio para preenchimento
manual. O pacote continua usando Python, Typer, Pydantic, SQLAlchemy, Alembic e
genanki, com os serviços existentes de texto, tradução e síntese de voz.

A arquitetura nativa do Roadmap 4 acrescenta perfis linguísticos versionados,
ranking por corpus, conteúdo canônico, filas duráveis e uma API FastAPI. A
ativação é gradual: `MULTILANG_ROADMAP_4_ENABLED=false` por padrão. O pipeline e
os GUIDs legados continuam disponíveis. As capacidades dos 22 idiomas modernos
e do caminho isolado de Latim exigem qualificação explícita antes da produção.

## Instalação e uso

Requer Python 3.12+ e uv. No checkout:

```bash
uv sync --locked --extra dev
uv run multilang --help
uv run multilang native --help
uv run multilang native status
```

Use [.env.example](.env.example) como referência. `Settings` lê variáveis com
prefixo `MULTILANG_`. Não use credenciais de produção nos testes.

Depois de seguir o [procedimento de migração](docs/migration.md), registrar
perfis qualificados e configurar credenciais, as interfaces nativas são:

```bash
uv run multilang native serve
uv run multilang native worker --loop
uv run multilang native search run --language en
```

Os comandos `import-dataset`, `rank`, `generate-content`, `generate-audio` e
`export-anki` recebem um arquivo JSON validado. A API envia operações pesadas à
mesma fila, sem permitir caminhos de arquivos ou endpoints fornecidos pelo
cliente. Chamadas pagas também exigem
`MULTILANG_NATIVE_PROVIDER_CALLS_ENABLED=true`; habilitar a arquitetura não
habilita automaticamente providers.

## Verificação

```bash
env -u MULTILANG_DATABASE_URL MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 \
  uv run --no-sync pytest -n 4 --dist=loadfile --timeout=120 --tb=short -q
uv run --no-sync python -m build --no-isolation
uv run --no-sync mkdocs build --strict
```

Os testes de carga usam dados sintéticos. Eles não certificam precisão
linguística, licença de redistribuição ou comportamento real de scheduling no
Anki. O relatório de implementação registra os resultados efetivamente obtidos.

## Documentação

- [Relatório de implementação e pendências](ROADMAP_4_NATIVE_IMPLEMENTATION.md)
- [Arquitetura](docs/architecture.md), [domínio](docs/domain-model.md) e [banco](docs/database.md)
- [API, permissões e jobs](docs/api.md)
- [Migração, backup e recuperação](docs/migration.md)
- [Contratos de conteúdo, áudio e Anki](docs/native-content-audio-anki-contracts.md)
- [Decisões arquiteturais](docs/adr/0001-native-architecture.md)

O runtime não executa GSDD nem lê `.planning` como fonte operacional. Os
documentos históricos de planejamento foram preservados; as evidências coreanas
necessárias ao runtime têm cópia verificada em `data/korean_foundations/evidence`.
