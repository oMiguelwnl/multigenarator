# Roadmap 4 — implementação nativa

Branch: `feature/roadmap-4-0-native-architecture`. Baseline: `c13d603`.
Solicitações: `info1.md` e `info2.md`. Contrato detalhado:
[plano mestre v4](docs/multilingual-lexical-adaptive-plan-v4.md).

Complemento de 2026-09-12: [preparação linguística e fluxo de revisão](docs/vocabulary-preparation.md)
e [resultados reais por língua](docs/multilingual-readiness.md). Este complemento
preserva exatamente os fields Anki, acrescenta fontes/modelos locais, importação
de sentidos e formas revisados e rascunhos de conteúdo retomáveis. O ensaio em
PostgreSQL 17.11 foi executado e passou; a seção histórica abaixo descreve a
validação da entrega inicial até `6149619`.

Esta entrega implementa mecanismos nativos dentro do Multilang: domínio,
persistência, serviços, importação, ranking, geração, áudio, Anki, histórico,
adaptação, API, jobs, migração e infraestrutura de verificação. **Isso não
certifica um rollout completo dos 22 idiomas.** Produção permanece desligada:
faltam aprovação das fontes/licenças e avaliações linguísticas independentes por idioma,
conteúdo real aprovado e comparação Anki nos quatro clientes. Não foram
fabricados receipts, 66 mil verbetes aprovados nem resultados de clientes reais.

## Arquitetura antiga e nova

Antes: aplicação Python/Typer com serviços de geração, jobs e itens legados,
SQLAlchemy/Alembic, providers existentes, caches de texto/áudio e exporters
genanki. Identidade e GUID em alguns caminhos dependem de job/ordem; policies
linguísticas e fontes ficam distribuídas. O relatório anterior à implementação
está em [análise](docs/roadmap-4-analysis.md).

Agora: os mesmos diretórios `domain`, `services`, `repositories` e `db` recebem
contratos versionados, identidades semânticas, revisões imutáveis e edições.
`native_runtime.NativeFacade` compõe os serviços; Typer, FastAPI e workers
consomem essa composição. A fila e a busca usam o banco existente. O caminho
legado continua disponível e a revisão nativa não é aplicada no startup.

| Fronteira | Dados e responsabilidade |
|---|---|
| Core | Perfis, identidades, formas, ranking, manifests e edições |
| Generated | Conteúdo e áudio versionados, com revisão independente |
| User | Conhecimento explícito, histórico minimizado, preferências e prioridade |
| Aplicação | Transações, ownership, autorização, providers e entrega de jobs |
| Infraestrutura | Banco, arquivos, observabilidade, backup e interfaces |

GSDD não foi utilizado na execução. O runtime não lê `.planning` nem executa
seus planos. As alterações locais anteriores do usuário foram preservadas.
As evidências coreanas operacionais foram copiadas byte a byte para
`data/korean_foundations/evidence`: 385 arquivos, 23.921.894 bytes, manifest
`8c88c563aeed9a6b9956a94801d58f1307acd8f7ee1ed8509fdb76d316c25c80`.
Isso preserva provas existentes; não constitui nova aprovação linguística.

## Rastreabilidade das solicitações

| info1 | info2 | Implementação / evidência principal |
|---|---|---|
| 1 | 1 | Branch solicitada; commits somente dos arquivos desta tarefa |
| 2 | 2 | `docs/roadmap-4-analysis.md`: estrutura, limitações, impacto e estratégia |
| 3 | 3 | Contratos/serviços nativos; evidências runtime fora de `.planning` |
| 4 | 5 | `domain/contracts.py`: os sete contratos públicos solicitados |
| 5 | 6 | `domain/events.py`, `services/domain_events.py`: eventos e outbox |
| 6 | 7 | `AuditLog`: responsável, motivo, revisão, data e hashes anterior/novo |
| 7 | 8 | `LanguageProfile`, registry de capacidades/políticas e locales |
| 8 | 9 | `LexicalIdentity`, ID semântico, revisão, histórico e aliases provados |
| 9 | 10 | `SurfaceForm`, `MorphologicalAnalysis`, `ImportantFormPolicy` |
| 10 | 11 | `MultiWordExpression`, alocação de spans, deduplicação de frequência |
| 11 | 12 | Tabelas e namespaces Core/Generated/User separados |
| 12 | 13 | Datasets imutáveis, revisões fixadas, heads, comparação e rollback |
| 13 | 14 | Sources → Normalizer → Analyzer → Ranking → Validation → staging/aprovação |
| 14 | 15 | `RankingEngine`: RANK-01, pesos, dispersão, MWE, Decimal e hashes |
| 15 | 16 | Proveniência lexical, manifests de corpus, confiança e quarentena |
| 16 | 17 | Quality score versionado de frequência/confiança/cobertura/validação |
| 17 | 18 | Conteúdo tipado, limites, target matching e review; IA não escreve Core |
| 18 | 19 | `AudioVersion`, assinatura contextual completa, integridade e cache |
| 19 | 20 | Projeção semântica, protótipos A/B, subdecks reais, versões fixadas |
| 20 | 21 | Busca SQL parametrizada por lema, forma, idioma, sentido, significado/rank |
| 21 | — | Cache limitado por TTL/versão/namespace; verificação de bytes de áudio |
| 22 | 22 | CSV, Dictionary, Corpus e ExternalAPI importers com limites/checksums |
| 23 | 23 | Fila SQLAlchemy, jobs reais, retry, lease/heartbeat/fencing e status |
| 24 | 24 | Lexical/Dataset/Migration/Content validators e contratos EVAL-01 |
| 25 | 25 | `/api/v1` e `/api/v2`, adapters de compatibilidade e ownership |
| 26 | 26 | Registro explícito de plugins confiáveis por categoria/nome/versão |
| 27–28 | 27 | Papéis Admin/Linguist/ContentCreator/User/Worker, secrets e rate limit |
| 29 | 28 | Snapshot, verificação, restore isolado, ensaio e rollback confirmado |
| 30 | 30 | Testes unitários, contratos, integração, migrations e carga sintética |
| 31 | 4 | Instrumentação OpenTelemetry, logs sem conteúdo, métricas e health |
| 32–33 | 4 | Settings, `.env.example`, flag nativo e providers desligados por padrão |
| 34 | 29/31 | Migration 20 aditiva, adaptação do legado, aliases e histórico preservado |
| 35 | 4/33 | CI de testes/lint/build/migrations/docs, artefatos e Dependabot |
| 36 | 32 | README, arquitetura, domínio, banco, API, migração e três ADRs |
| 37 | 34 | Commits por domínio; arquivos preexistentes excluídos dos commits |

Redis/RQ e Meilisearch eram sugestões condicionais à ausência de equivalente.
Não foram adicionados: fila persistida e busca SQL atendem ao escopo atual.
FastAPI, OpenTelemetry, MkDocs e dependências de verificação foram acrescentados
e fixados em `uv.lock`. CI entrega artefatos; **deploy em um ambiente externo
foi adiado por decisão expressa do usuário e não foi configurado/executado**.

## Contratos do plano mestre

| Contratos | Mecanismo implementado | Condição que permanece externa |
|---|---|---|
| CARD-01, FORM-01/02/03, SENSE-01, MWE-01 | IDs, análise, evidência, seleção integral e ambiguidade fail-closed | Fontes e análises aprovadas para cada idioma |
| ROUTE-01, LOAD-01, DEPEND-01 | Destino/rank herdado, contagens reconciliadas, pré-requisitos e módulos | Aceitação pedagógica e comportamento real no Anki |
| DEF-01, DISPLAY-01 | Conteúdo meaning-first, contexto da forma e resposta estruturada | Revisão especialista de exemplos/definições |
| GUID-01 | Identidade semântica independente de rank/job/provider; aliases explícitos | Decisões de merge/split e provas de migração de GUIDs reais |
| ANKI-01 | Dois protótipos; B preserva os fields existentes; A é experimental e bloqueado para produção | Aceitação real nos clientes; A não atende à restrição posterior de fields |
| RANK-01 | Pesos/shares, ln/ppm/dispersão, spans, precisão e manifests reproduzíveis | Corpora redistribuíveis, pesos/rubricas aprovados |
| FORM-04 | Score/política/thresholds, deduplicação, previsão integral sem truncamento | Evidência linguística dos critérios por idioma |
| AUDIO-01/02 | Texto/contexto/SSML/voz/provider/modelo exatos; cache e hashes | Licença, custo autorizado e revisão de pronúncia |
| AISEC-01 | Dados/controles separados, schemas fechados, limites e conteúdo ativo rejeitado | Budgets e controles operacionais do deployment |
| CONTENT-01 | Edição canônica com bindings imutáveis de conteúdo e dos dois áudios | Bundle real revisto e assinado |
| EVAL-01 | Datasets/estratos/métricas/thresholds/baselines e bloqueios de regressão | Goldens e avaliação independente por idioma |

Os 22 perfis modernos e Latim são representados, mas começam desabilitados.
O complemento instalou modelos e preparou fontes reais para os 22 idiomas
modernos. Os 200 casos UD por língua são diagnóstico, sem qualificação automática:
não substituem os mínimos de goldens independentes exigidos pelo contrato.
Não foram produzidos os 66.000 itens Core aprovados exigidos para o rollout.
Os testes sintéticos comprovam invariantes de software e escala, apenas.

## Migração realizada

Foi criada a revisão Alembic `20260912_20`, filha de `20260828_19`, com 18
tabelas adicionais. Os nomes, entidades e transações estão em
[banco](docs/database.md). Foram implementados e testados snapshot, clone,
upgrade/downgrade, conservação do legado, detecção de drift, replay do journal,
rollback sem perda silenciosa e adoção do SQLite legado sem stamp.

O ensaio também foi executado usando a wheel extraída fora do código-fonte:
CLI e recursos Alembic empacotados produziram upgrade para 20, downgrade para 19
e preservação dos registros legados. A revisão 20 tem SHA-256
`f468f5390824846fa9ded0e39739ce62f7b53520a6bcc00fd151a059831e9694`.
Upgrade e downgrade nativos diretos exigem autorização vinculada à prévia.

Nenhuma base real foi atualizada e nenhum histórico Anki foi reescrito. O
processo de aplicação exige evidência e confirmação vinculada à prévia.
[Migração](docs/migration.md) documenta os comandos e as limitações.

## Revisão e validação da entrega inicial até `6149619`

A revisão independente reproduziu dois bugs e orientou regressões permanentes:
replay de uma importação antiga podia restaurar a fonte anterior como atual;
uma edição podia aceitar conteúdo grounded em outra revisão de fonte. A
importação agora retorna versões já registradas antes de alterar projeções,
e a edição compara o grounding com sua revisão fixada. Aprovar uma versão de
dataset também preserva suas formas e identidades originais.
Os clozes exigem offsets de ocorrência fornecidos pelo matcher e conferidos
contra o texto; não usam a primeira substring encontrada. Aliases de identidade
e de histórico mantêm provas independentes, inclusive em atualizações concorrentes.

Os testes de integração exercem os serviços reais com providers e receipts
claramente sintéticos: importação → persistência → geração → revisão → áudio
→ edição → APKG. Casos negativos cobrem origem alterada, conteúdo ativo,
SSML indevido, áudio corrompido, namespaces privados e confirmações inválidas.
Os logs e relatórios locais estão em `.multilang/verification/` (ignorados pelo
Git). Os checks de distribuição verificaram os 196 arquivos de código/recursos
contra a wheel, além das migrations; wheel e sdist excluem `.planning`, `.env`,
os documentos de entrada e bytecode. Build Python, lint Ruff e build estrito
MkDocs passaram.

**Resultado histórico: 2.307 testes aprovados e 1 ignorado, entre 2.308
nodeids daquela entrega; nenhum caso ficou sem resultado.** A verificação foi feita em
lotes, não em uma única execução verde. A primeira execução paralela foi
interrompida após 2.230 aprovações e 41 falhas: incluía módulos carregados antes
das últimas correções, fixtures antigas e timeouts sob contenção/sandbox.
Os 74 casos atuais falhos ou pendentes foram repetidos sequencialmente fora do
sandbox: **73 aprovados e 1 ignorado em 697,19 segundos**. As quatro regressões
novas do scanner também passaram, dentro de seu arquivo com 14 testes.
O cruzamento nominal dos três XMLs com a coleta final está em
`verification-consolidated.json` e `verification-by-nodeid.json`, nessa pasta.

| Verificação | Resultado observado |
|---|---|
| Cobertura nominal da coleta inicial | 2.307 aprovados, 1 ignorado, 0 pendentes |
| Contratos de idioma/ranking/conteúdo/áudio/Anki | 78 aprovados no lote focado |
| Scanner de IDs, cache e invalidação | 14 aprovados; edição com mesmo tamanho/mtime e mudança de registro continuam detectadas |
| Migração/backup/restore | Paridade de schema, autorização, ensaio, rollback e proteção de dados aprovados; também exercitados pela CLI e wheel |
| Escala sintética | 66.000 identidades/66.000 formas em 22 idiomas; protótipos A/B com 6.000 cards cada, sem truncamento |
| Distribuição | Wheel e sdist gerados; 196 arquivos do pacote e migrations conferidos contra a árvore final |
| Qualidade estática/documentação | Ruff, `git diff --check`, lockfile e MkDocs estrito aprovados |

A varredura de IDs Anki foi otimizada com cache limitado a 512 análises limpas.
Cada chamada relê e calcula o hash do texto; a chave inclui caminho, regra de
isenção e registro, e o cache armazena apenas fatos de análise. A medição local
final, nos mesmos 364 arquivos, foi **8,12 s na primeira leitura e 0,33 s na
repetição**. A CI separa migrações, regressões e integração/escala, evita trabalho
duplicado e preserva os relatórios mesmo quando uma etapa falha.

Na entrega inicial, o teste PostgreSQL foi ignorado por ausência das duas URLs
de bancos descartáveis. No complemento, foi executado com PostgreSQL 17.11,
`pg_dump`, `pg_restore` e dois bancos locais isolados, e passou. O ensaio também
revelou uma diferença real na representação de CHECKs, corrigida com normalização
restrita e testes de equivalência e rejeição. A execução do job CI no GitHub
continua sem observação; a prova aqui é local.

## Validação do complemento linguístico de 12/09/2026

O complemento preserva os nomes e a ordem exata dos fields por modelo existente.
`word` contém a forma estudada; lema, sentido, análise e vínculo entre formas
ficam no banco e no manifest. O Modelo B reutiliza os templates atuais, inclusive
leituras japonesas e chinesas. O Modelo A permanece experimental e bloqueado
para produção por não atender à restrição posterior de fields.

Foram implementados aquisição e leitura limitada de fontes, manifests imutáveis,
gestão de modelos locais, análise contextual, preparação de candidatos, avaliação,
entrada de revisão e importação de sentidos/formas com evidências assinadas.
O dataset preserva somente as formas de seu bundle; o bundle inteiro é guardado
para revalidação. A geração agora pode salvar um rascunho original, aguardar os
vínculos contextuais revisados e concluir sem repetir a chamada ao provedor.

Os resultados reais são 22 modelos disponíveis, 24 lotes, 260.439 candidatos
lexicais, 71.940 registros de possíveis flexões e 4.400 frases de diagnóstico.
Não equivalem a cards aprovados. O [relatório por língua](docs/multilingual-readiness.md)
expõe as recusas de alinhamento, divergências, limitações das fontes, hashes e
entradas de revisão ainda necessárias.

| Verificação do complemento | Resultado observado |
|---|---|
| Integração e regressões nativas/linguísticas | 299 aprovados, 0 falhas e 0 ignorados, em 151,24 s |
| Serviço de migração completo | 33 aprovados em 307,19 s; segunda revisão independente também passou os 33 |
| PostgreSQL real | 1 aprovado em 32,41 s, PostgreSQL 17.11 e duas bases descartáveis |
| Escala sintética | 3 aprovados em 245,64 s; 66.000 identidades e exportações A/B de 6000 cards |
| Núcleo Anki 26.8.1 | 11 notas, cinco modelos de fields; importação, renderização, revisão e reimportação preservaram IDs, agendamento e histórico |
| Distribuição | Wheel e sdist gerados; 209 arquivos de código/recursos iguais à árvore, nenhuma inclusão proibida; CLI da wheel verificada fora do checkout |
| Qualidade estática | Escopo de Ruff da CI aprovado; `git diff --check` e `uv lock --check --offline` aprovados |
| Documentação | `mkdocs build --strict` aprovado |

Esses lotes são separados: não se somam testes focados repetidos às contagens
da suíte de 299. A varredura Ruff do repositório inteiro ainda encontra problemas
preexistentes fora do escopo da CI; não foi declarada limpa. O GitHub Actions
não foi executado remotamente nesta entrega.

A primeira execução conjunta ficou bloqueada na sandbox. A investigação
reproduziu o problema em um portal AnyIO mínimo, sem Multilang; os mesmos cinco
testes HTTP passaram fora da sandbox. A execução bloqueada foi encerrada e a
suíte completa de 299 foi repetida fora dela, com timeouts, sem rede nem chamadas
a provedores. Nenhuma correção de produção foi feita para mascarar esse problema.

Evidências locais principais: `.multilang/verification/native-completion-tests.xml`,
`native-completion-scale.xml`, `postgresql/run/native-postgresql.xml`,
`anki-backend/report.json`, `wheel-completion-report.json` e
`real-languages/`. O [guia linguístico](docs/vocabulary-preparation.md)
documenta os comandos e a distinção entre biblioteca instalada, material preparado
e conteúdo efetivamente aprovado. Nenhuma chamada paga ou deploy foi executado.

## Commits do complemento por domínio

| Commit | Domínio |
|---|---|
| `82f1a2a` | Fingerprint PostgreSQL e regressões de restauração |
| `810dfd5` | Fields existentes, formas semânticas e testes Anki |
| `20d76f8` | Fontes/modelos de 22 línguas, revisão, rascunhos, runtime e testes |

Este relatório, o guia, o inventário e os resultados agregados compõem o commit
de documentação do complemento. São 52 arquivos novos ou modificados nesta
etapa. Os arquivos preexistentes do usuário e sua alteração staged foram
conferidos por hash e preservados. Nenhum push, merge ou deploy foi executado.

## Commits da entrega inicial por domínio

| Commit | Domínio |
|---|---|
| `c02f489` | Perfis de idioma e identidades lexicais |
| `ae59036` | Pipeline, ranking e qualidade |
| `3f1cc10` | Conteúdo e áudio versionados |
| `f5a8f03` | Anki semântico e adaptação |
| `c9974cc` | Desempenho e invalidação segura do scanner |
| `781c954` | Persistência, eventos, revisão e estado privado |
| `199acd0` | Migração e recuperação |
| `a37ce89` | CLI, API e jobs |
| `12fd1ce` | Evidências operacionais fora de `.planning` |
| `497dce4` | Fixtures de compatibilidade |
| `9073d1e` | Dependências, CI e empacotamento |

Este relatório, o inventário e os demais documentos compõem o commit final de
documentação. A entrega contém 509 arquivos novos ou modificados, incluindo os
386 arquivos da cópia de evidências com seu manifest. Nenhum push, merge ou
deploy foi executado.

## Riscos e próximos passos obrigatórios

1. Qualificar individualmente os analyzers, corpora, fontes/licenças e goldens;
   assinar baselines e policies antes de habilitar cada capacidade.
2. Executar a matriz ANKI-01 nos quatro clientes. O Modelo B preserva os fields
   e usa notas separadas; não promete burying nativo de siblings. O Modelo A
   permanece experimental e incompatível com a restrição de fields. A prova
   local com o núcleo Anki não representa aprovação dos quatro aplicativos.
3. Congelar Core e expansão revisados, com todas as formas obrigatórias e
   conteúdo/áudio aprovados; não transformar os fixtures em dados de produção.
4. Definir orçamento, providers/vozes e distribuição de mídia para geração real.
   Se houver uma publicação futura, configurar também TLS, egress, segredos,
   telemetria e rate limit compartilhado. Deploy não faz parte da entrega atual,
   conforme a decisão posterior do usuário.
5. Ensaiar backup/restore na instalação PostgreSQL de destino, revisar aliases
   reais e só então aplicar a prévia confirmada. Teste local SQLite não substitui
   a prova operacional no banco de destino, mesmo após o ensaio PostgreSQL local.

Entrega de jobs é pelo menos uma vez: crash após efeito externo pode causar
retry. Use os caches/idempotência e mantenha budgets. SQLite deve usar um worker
por causa de write locks/heartbeats. Busca SQL com substring e cache local
precisam de novas medições antes de aumentar a carga e o número de réplicas.

## Arquivos alterados

O [inventário da entrega](docs/roadmap-4-file-inventory.md) lista código, testes,
configuração e o manifest integral dos assets copiados. Os arquivos `.planning`
que já estavam modificados/staged, os planos e
evidências locais anteriores, `tests/planning` preexistente e `info1.md`/`info2.md`
não pertencem aos commits da implementação.
