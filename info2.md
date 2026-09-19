 MISSÃO: IMPLEMENTAÇÃO COMPLETA DO ROADMAP 4.0 DO MULTIGENERATOR

Você é um engenheiro de software sênior responsável pela evolução arquitetural completa do projeto:



Sua missão é implementar TODAS as mudanças definidas no Roadmap 4.0 do projeto.

O Roadmap 4.0 foi organizado utilizando GSDD como metodologia de planejamento, porém a implementação NÃO deve utilizar GSDD como arquitetura, framework ou mecanismo operacional.

Você deve extrair apenas os requisitos técnicos e arquiteturais do Roadmap 4.0 e implementar uma arquitetura própria, seguindo os padrões já existentes no Multigenarator.


====================================================
REGRA PRINCIPAL: RESPEITAR O PROJETO EXISTENTE
====================================================

Antes de modificar qualquer código:

Analise completamente o projeto atual.

Você deve respeitar:

- arquitetura existente;
- organização das pastas;
- nomenclaturas;
- padrões de código;
- estilo de programação;
- bibliotecas utilizadas;
- banco de dados atual;
- migrations existentes;
- padrões de testes;
- padrões de documentação.


Não crie um projeto paralelo.

Não substitua tecnologias existentes sem necessidade.

Não recrie funcionalidades já existentes.

A implementação deve parecer uma evolução oficial do Multigenarator.


Sempre que precisar criar algo novo:

1. Verifique se já existe algo semelhante.
2. Reutilize quando possível.
3. Refatore apenas quando necessário.
4. Documente decisões importantes.


====================================================
FASE 1 — CRIAR BRANCH
====================================================

Antes de qualquer alteração:


Criar branch:

feature/roadmap-4-0-native-architecture


Todas as alterações devem ocorrer exclusivamente nessa branch.


====================================================
FASE 2 — ANÁLISE COMPLETA DO REPOSITÓRIO
====================================================

Não implemente nada inicialmente.

Primeiro faça uma análise completa:

- arquitetura atual;
- módulos;
- entidades;
- banco;
- migrations;
- serviços;
- pipelines;
- geração lexical;
- sistema multilíngue;
- IA;
- áudio;
- Anki;
- testes.


Produza um relatório contendo:

1. Arquitetura atual.
2. Pontos impactados pelo Roadmap 4.0.
3. Arquivos afetados.
4. Riscos.
5. Estratégia de migração.


Somente após essa análise comece a implementação.


====================================================
FASE 3 — REMOVER DEPENDÊNCIA OPERACIONAL DO GSDD
====================================================

O projeto não deve depender do GSDD para funcionar.


Não utilizar como mecanismo:

- .planning;
- comandos GSDD;
- skills GSDD;
- workflows GSDD;
- agentes GSDD.


Criar arquitetura própria usando:

- domínio;
- serviços;
- contratos;
- eventos;
- pipelines;
- validações;
- jobs.


====================================================
FASE 4 — CONFIGURAR INFRAESTRUTURA NECESSÁRIA
====================================================

Antes de adicionar qualquer tecnologia:

Verifique se já existe solução equivalente no projeto.


Adicionar somente se necessário:


1. Redis + RQ

Para:

- geração de áudio;
- ranking;
- importações;
- exportação Anki;
- tarefas pesadas.


Criar:

jobs/

- audio_jobs
- ranking_jobs
- import_jobs
- anki_jobs


--------------------------------


2. Meilisearch

Para:

Lexical Search Service


Indexar:

- lemma;
- formas;
- idioma;
- sentido;
- frequência.


--------------------------------


3. OpenTelemetry

Para:

- tracing;
- métricas;
- logs estruturados.


--------------------------------


4. MkDocs

Para documentação técnica:

- arquitetura;
- domínio;
- API;
- migração;
- ADR.


--------------------------------


5. GitHub Actions

Criar pipeline:

- instalação;
- testes;
- lint;
- validação migrations;
- build.


--------------------------------


6. Dependabot

Configurar atualização automática de dependências.


====================================================
FASE 5 — NOVA ARQUITETURA DE DOMÍNIO
====================================================
[12/09/2026 08:44] Miguel 💻: Criar arquitetura baseada em:

- Domain Driven Design;
- módulos desacoplados;
- contratos;
- serviços.


Criar:

Contracts:

- LanguageProfileContract
- LexicalIdentityContract
- RankingContract
- AudioContract
- ContentContract
- MigrationContract
- ValidationContract


====================================================
FASE 6 — DOMAIN EVENTS
====================================================

Criar sistema de eventos:


Eventos:

- LexicalIdentityCreated
- LexicalIdentityUpdated
- DatasetImported
- RankingCalculated
- AudioGenerated
- MigrationCompleted


Objetivos:

- desacoplamento;
- auditoria;
- automações futuras.


====================================================
FASE 7 — AUDIT TRAIL
====================================================

Criar histórico de alterações.


Registrar:

- alteração;
- origem;
- data;
- usuário/processo;
- versão anterior;
- versão nova.


====================================================
FASE 8 — LANGUAGE PROFILE SYSTEM
====================================================

Implementar:


LanguageProfile


Cada idioma deve possuir:

- regras;
- locale;
- fontes;
- configuração;
- políticas;
- áudio;
- conteúdo.


Idioma deixa de ser apenas string.


====================================================
FASE 9 — LEXICAL IDENTITY SYSTEM
====================================================

Criar:


LexicalIdentity


Identidade:

Language

+

Normalized Lemma

+

Part Of Speech

+

Sense


Adicionar:

- GUID estável;
- versionamento;
- histórico.


====================================================
FASE 10 — MORPHOLOGY SYSTEM
====================================================

Criar:


- SurfaceForm
- MorphologicalAnalysis
- ImportantFormPolicy


Exemplo:

run

↓

running

ran

runs


Cada forma deve ter:

- análise;
- frequência;
- importância;
- áudio;
- contexto.


====================================================
FASE 11 — MULTI WORD EXPRESSIONS
====================================================

Criar:


MultiWordExpression


Exemplo:

take care


Possuir:

- identidade;
- ranking;
- frequência;
- cards próprios.


====================================================
FASE 12 — CORE DATA / GENERATED DATA / USER DATA
====================================================

Separar completamente:


CORE:

- identidade;
- ranking;
- datasets.


GENERATED:

- IA;
- exemplos;
- explicações.


USER:

- progresso;
- preferências.


Nenhuma camada pode sobrescrever outra.


====================================================
FASE 13 — DATASET VERSIONING
====================================================

Versionar:

- lexical dataset;
- ranking dataset;
- audio dataset;
- content dataset.


Permitir:

- rollback;
- comparação;
- atualização.


====================================================
FASE 14 — LEXICAL PIPELINE
====================================================

Criar:


Sources

↓

Normalizer

↓

Analyzer

↓

Ranking Engine

↓

Validation

↓

Production Dataset


====================================================
FASE 15 — RANKING ENGINE
====================================================

Implementar ranking baseado em:

- frequência;
- dispersão;
- pesos;
- corpora;
- MWE.


Deve ser:

- determinístico;
- reproduzível;
- auditável.


====================================================
FASE 16 — EVIDENCE SYSTEM
====================================================

Cada item lexical deve armazenar:


- fonte;
- corpus;
- frequência;
- confiança;
- evidências.


====================================================
FASE 17 — QUALITY SCORE
====================================================

Criar:

Lexical Quality Score


Base:

- frequência;
- confiança;
- cobertura;
- validação.


====================================================
FASE 18 — IA COMO ENRIQUECIMENTO
====================================================

IA nunca altera:


- identidade lexical;
- GUID;
- ranking;
- Core Data.


IA somente cria:

- exemplos;
- explicações;
- exercícios.
[12/09/2026 08:44] Miguel 💻: ====================================================
FASE 19 — AUDIO VERSIONING SYSTEM
====================================================

Criar:


AudioVersion


Guardar:

- provider;
- voz;
- versão;
- texto;
- contexto;
- pronunciation_signature.


====================================================
FASE 20 — NOVO SISTEMA ANKI
====================================================

Migrar para:


Lexical Identity

├── Headword Card

├── Frequency Form Card

└── Optional Cards


Manter:

- GUID;
- compatibilidade;
- histórico.


====================================================
FASE 21 — SEARCH SYSTEM
====================================================

Criar:


Lexical Search Service


Permitir:

- busca por palavra;
- lemma;
- idioma;
- sentido;
- frequência.


====================================================
FASE 22 — IMPORT FRAMEWORK
====================================================

Criar suporte:


- Corpus Importer;
- Dictionary Importer;
- CSV Importer;
- External API Importer.


====================================================
FASE 23 — JOB SYSTEM
====================================================

Criar processamento assíncrono:


Jobs:

- AudioGenerationJob
- RankingUpdateJob
- ContentGenerationJob
- AnkiExportJob


Com:

- fila;
- retry;
- status;
- logs.


====================================================
FASE 24 — VALIDADORES
====================================================

Criar:


- LexicalValidator
- DatasetValidator
- MigrationValidator
- ContentValidator


====================================================
FASE 25 — API VERSIONING
====================================================

Criar APIs versionadas:


/api/v1

/api/v2


Evitar quebra futura.


====================================================
FASE 26 — PLUGIN ARCHITECTURE
====================================================

Permitir expansão:

- novos idiomas;
- novos providers;
- novos módulos.


====================================================
FASE 27 — SECURITY
====================================================

Adicionar:

- validação;
- permissões;
- secrets;
- rate limit.


====================================================
FASE 28 — BACKUP E RECOVERY
====================================================

Antes de migrações:


- criar snapshot;
- validar backup;
- permitir rollback.


====================================================
FASE 29 — MIGRAÇÃO PROGRESSIVA
====================================================

Nunca substituir tudo diretamente.


Implementar:


Legacy

↓

Adapter

↓

New Core


Preservar:

- usuários;
- progresso;
- histórico.


====================================================
FASE 30 — TESTES
====================================================

Criar:


Unit Tests

Integration Tests

Contract Tests

Migration Tests

Performance Tests

End-to-End Tests


Testar com dados reais quando possível.


====================================================
FASE 31 — BANCO DE DADOS
====================================================

Toda alteração deve usar migrations.


Nunca alterar banco manualmente.


Criar:

- migrations versionadas;
- rollback;
- validação.


====================================================
FASE 32 — DOCUMENTAÇÃO
====================================================

Criar:


docs/


architecture.md

domain-model.md

migration.md

api.md

adr/


Criar ADRs:

- decisões arquiteturais;
- modelos;
- migração.


====================================================
FASE 33 — VALIDAÇÃO FINAL
====================================================

Executar:


- testes;
- migrations;
- build;
- lint;
- validações.


Garantir:

- nenhuma funcionalidade existente quebrada;
- compatibilidade preservada.


====================================================
FASE 34 — COMMITS
====================================================

Organizar commits:


feat(core): native architecture

feat(language): language profile

feat(lexical): lexical identity

feat(ranking): ranking engine

feat(audio): audio versioning

feat(anki): new anki architecture
[12/09/2026 08:44] Miguel 💻: feat(migration): roadmap migration

test: add coverage

docs: update documentation


====================================================
ENTREGA FINAL
====================================================

Entregar relatório final contendo:


- arquitetura antiga;
- arquitetura nova;
- arquivos alterados;
- novas entidades;
- migrations criadas;
- serviços adicionados;
- decisões técnicas;
- riscos;
- próximos passos.


Resultado esperado:


Multigenarator v4


Uma evolução completa do projeto atual.

Sem GSDD como dependência.

Seguindo todos os padrões existentes.

Com arquitetura escalável, testada e documentada.
