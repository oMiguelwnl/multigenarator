Você é um engenheiro de software sênior responsável pela evolução arquitetural completa do projeto:


Sua missão é implementar TODAS as mudanças definidas no Roadmap 4.0 do Multigenarator.

IMPORTANTE:

O Roadmap 4.0 foi planejado utilizando GSDD como metodologia de organização, porém a implementação final NÃO deve utilizar GSDD.

Você deve extrair os requisitos técnicos, funcionais e arquiteturais do Roadmap 4.0 e implementar uma arquitetura própria, independente, profissional e escalável.


==================================================
REGRA FUNDAMENTAL — RESPEITAR A ARQUITETURA EXISTENTE
==================================================

Antes de implementar qualquer mudança:

Analise profundamente a estrutura atual do projeto.

Você deve seguir os padrões existentes:

- arquitetura atual;
- organização de diretórios;
- nomenclatura de arquivos;
- padrões de código;
- estilo de programação;
- padrões de banco de dados;
- convenções de API;
- padrões de testes;
- padrões de documentação;
- bibliotecas já utilizadas;
- decisões arquiteturais existentes.


NÃO criar uma arquitetura paralela desconectada do projeto.


A nova implementação deve parecer uma evolução natural do Multigenarator.


Antes de criar novos módulos:

Verifique se já existe uma implementação equivalente.

Reutilize, adapte ou refatore componentes existentes quando possível.


Evite:

- duplicação de código;
- criação de serviços redundantes;
- quebra dos padrões existentes;
- substituir tecnologias sem necessidade.


==================================================
FASE 1 — CRIAR NOVA BRANCH
==================================================

Criar:

feature/roadmap-4-0-native-architecture


Todas as alterações devem acontecer somente nessa branch.


==================================================
FASE 2 — ANÁLISE COMPLETA
==================================================

Mapear:

- arquitetura atual;
- módulos existentes;
- banco;
- entidades;
- APIs;
- serviços;
- pipelines;
- geração lexical;
- IA;
- áudio;
- Anki;
- multilíngue.


Criar mapa:

ESTRUTURA ATUAL

↓

LIMITAÇÕES

↓

REQUISITO ROADMAP 4.0

↓

NOVA IMPLEMENTAÇÃO


==================================================
FASE 3 — REMOVER DEPENDÊNCIA GSDD
==================================================

O GSDD não deve ser usado como motor da aplicação.


Não utilizar:

- comandos GSDD;
- skills GSDD;
- agentes GSDD;
- workflows GSDD;
- planejamento GSDD executável.


Criar mecanismos próprios:

- contratos;
- serviços;
- pipelines;
- validações;
- jobs;
- migração.


==================================================
FASE 4 — CONTRACT FIRST ARCHITECTURE
==================================================

Criar contratos internos:

- LanguageProfileContract
- LexicalIdentityContract
- RankingContract
- AudioContract
- ContentContract
- MigrationContract
- ValidationContract


Módulos devem se comunicar através desses contratos.


==================================================
FASE 5 — DOMAIN EVENTS
==================================================

Implementar eventos internos:

- LexicalIdentityCreated
- LexicalIdentityUpdated
- DatasetImported
- RankingCalculated
- AudioGenerated
- MigrationCompleted


Permitir:

- desacoplamento;
- auditoria;
- automações futuras.


==================================================
FASE 6 — AUDIT TRAIL
==================================================

Criar histórico completo:

AuditLog


Registrar:

- alteração;
- usuário/processo responsável;
- data;
- versão anterior;
- versão nova;
- motivo.


==================================================
FASE 7 — LANGUAGE PROFILE
==================================================

Criar:

LanguageProfile


Cada idioma possui:

- regras;
- identidade;
- fontes;
- configuração;
- áudio;
- conteúdo;
- locale.


==================================================
FASE 8 — IDENTIDADE LEXICAL
==================================================

Criar:

LexicalIdentity


Base:

Language

+

Normalized Lemma

+

POS

+

Sense


[12/09/2026 08:20] Miguel 💻: - GUID estável;
- versionamento;
- histórico.


==================================================
FASE 9 — MORFOLOGIA
==================================================

Criar:

- SurfaceForm
- MorphologicalAnalysis
- ImportantFormPolicy


Suporte:

running
ran
runs


==================================================
FASE 10 — MWE
==================================================

Criar:

MultiWordExpression


Exemplo:

take care


Com:

- identidade;
- frequência;
- ranking;
- cards.


==================================================
FASE 11 — CORE / GENERATED / USER DATA
==================================================

Separar:


CORE:

- identidade;
- ranking;
- datasets.


GENERATED:

- exemplos;
- explicações;
- IA.


USER:

- progresso;
- preferências.


==================================================
FASE 12 — DATASET VERSIONING
==================================================

Versionar:

- lexical dataset;
- ranking dataset;
- áudio;
- conteúdo.


Permitir:

- rollback;
- comparação;
- atualização.


==================================================
FASE 13 — PIPELINE LINGUÍSTICO
==================================================

Criar:

Sources

↓

Normalizer

↓

Analyzer

↓

Ranking

↓

Validation

↓

Production Dataset


==================================================
FASE 14 — RANKING ENGINE
==================================================

Implementar:

- frequência;
- dispersão;
- pesos;
- corpora;
- MWE.


Resultado:

Ranking reproduzível e auditável.


==================================================
FASE 15 — EVIDENCE SYSTEM
==================================================

Cada item lexical deve possuir:

- fonte;
- corpus;
- frequência;
- confiança.


==================================================
FASE 16 — QUALITY SCORE
==================================================

Criar:

Lexical Quality Score


==================================================
FASE 17 — IA COMO ENRIQUECIMENTO
==================================================

IA nunca altera:

- Core;
- GUID;
- ranking.


IA somente gera:

- exemplos;
- explicações;
- exercícios.


==================================================
FASE 18 — AUDIO SYSTEM
==================================================

Criar:

Audio Versioning


Guardar:

- provider;
- voz;
- versão;
- texto;
- contexto;
- pronunciation_signature.


==================================================
FASE 19 — ANKI ARCHITECTURE
==================================================

Novo modelo:


Lexical Identity

├── Headword Card

├── Frequency Form Card

└── Optional Cards


==================================================
FASE 20 — SEARCH ENGINE
==================================================

Criar:

Lexical Search Service


Busca por:

- palavra;
- lemma;
- idioma;
- significado;
- frequência.


==================================================
FASE 21 — CACHE
==================================================

Criar camada de cache para:

- idioma;
- lexical identity;
- ranking;
- áudio.


==================================================
FASE 22 — IMPORT FRAMEWORK
==================================================

Criar suporte:

- Corpus Importer;
- Dictionary Importer;
- CSV Importer;
- External API Importer.


==================================================
FASE 23 — JOB SYSTEM
==================================================

Criar jobs:

- AudioGenerationJob;
- RankingUpdateJob;
- ContentGenerationJob;
- AnkiExportJob.


Com:

- fila;
- retry;
- status.


==================================================
FASE 24 — VALIDATORS
==================================================

Criar:

- LexicalValidator;
- DatasetValidator;
- MigrationValidator;
- ContentValidator.


==================================================
FASE 25 — API VERSIONING
==================================================

Implementar APIs versionadas:

v1
v2


Evitar quebra de clientes.


==================================================
FASE 26 — PLUGIN ARCHITECTURE
==================================================

Permitir expansão:
[12/09/2026 08:20] Miguel 💻: novos idiomas;

novos providers;

novos módulos.


==================================================
FASE 27 — SECURITY
==================================================

Adicionar:

- validação;
- permissões;
- rate limit;
- secrets management.


==================================================
FASE 28 — PERMISSIONS
==================================================

Criar papéis:

- Admin;
- Linguist;
- Content Creator;
- User;
- Worker.


==================================================
FASE 29 — BACKUP E RECOVERY
==================================================

Antes da migração:

- criar snapshot;
- validar backup;
- permitir rollback.


==================================================
FASE 30 — PERFORMANCE
==================================================

Criar testes:

- grandes datasets;
- múltiplos idiomas;
- exportações grandes.


==================================================
FASE 31 — OBSERVABILIDADE
==================================================

Adicionar:

- logs estruturados;
- métricas;
- health checks.


==================================================
FASE 32 — CONFIG MANAGEMENT
==================================================

Separar:

código

de

configurações.


==================================================
FASE 33 — FEATURE FLAGS
==================================================

Criar:

ROADMAP_4_ENABLED


Permitir ativação gradual.


==================================================
FASE 34 — MIGRAÇÃO PROGRESSIVA
==================================================

Não substituir tudo de uma vez.


Usar:

Legacy

↓

Adapter

↓

Novo Core


Preservar:

- usuários;
- progresso;
- histórico.


==================================================
FASE 35 — CI/CD
==================================================

Criar pipeline:

- testes;
- lint;
- build;
- migration check;
- deploy.


==================================================
FASE 36 — DOCUMENTAÇÃO
==================================================

Atualizar:

README

Arquitetura

API

Banco

Migração


Criar:

ROADMAP_4_NATIVE_IMPLEMENTATION.md


==================================================
FASE 37 — COMMITS
==================================================

Organizar commits por domínio.


==================================================
RESULTADO FINAL
==================================================

Entregar:

Branch:

feature/roadmap-4-0-native-architecture


Resultado:

- todas as mudanças Roadmap 4.0 implementadas;
- sem GSDD;
- seguindo padrões existentes;
- arquitetura escalável;
- testes passando;
- documentação completa.


No relatório final incluir:

- arquivos alterados;
- arquitetura nova;
- decisões técnicas;
- migração realizada;
- riscos;
- próximos passos.


IMPORTANTE:

A implementação deve parecer uma evolução oficial do Multigenarator.

Não criar um projeto novo.

Não ignorar padrões existentes.

Não substituir tecnologias sem necessidade.

Respeitar a identidade técnica atual do projeto enquanto implementa toda a visão do Roadmap 4.0.
