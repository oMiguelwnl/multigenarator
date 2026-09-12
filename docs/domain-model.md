# Modelo de domínio

Os imports públicos estão em `multilang.domain.contracts`: `LanguageProfileContract`,
`LexicalIdentityContract`, `RankingContract`, `AudioContract`, `ContentContract`,
`MigrationContract` e `ValidationContract`.

| Entidade | Invariante |
|---|---|
| LanguageProfile | Versão, locale, explicação, fontes e políticas/capacidades explícitas; desconhecido/desabilitado falha fechado |
| LexicalIdentity | Idioma + lema NFC + POS + sentido + namespace semântico; rank/provider/job não definem ID |
| MorphologicalAnalysis / SurfaceForm | Forma exata, pai, análise e proveniência; atualização preserva histórico |
| ImportantFormPolicy | Score/evidência, deduplicação e ordem determinísticos; nenhuma forma aprovada sofre cap posterior |
| MultiWordExpression | Segmentação e unidade lexical explícitas; sem heurística de espaço |
| CorpusManifest / CorpusObservation | Corpus checksummed, pesos, spans e alocações; soma das shares exatamente 1 |
| RankingResult | Fórmula e precisão versionadas; desempate estável; quarentena e quality score auditáveis |
| DatasetManifest | Versão imutável, namespace, fonte, aprovação e memberships com revisões fixadas |
| ContentVersion | Saída fechada da IA, target matching e revisão; não altera Core |
| PronunciationSignature / AudioVersion | Texto e contexto exatos, análise, locale, voz, SSML, provider/modelo, formato e integridade |
| SemanticCard | Papel, pai, destino herdado, pré-requisito e identidade semântica separados do note GUID |
| DeckEdition | Versões explícitas de conteúdo/word audio/sentence audio para cada card, política de forma e aprovação |
| LearnerState / HistoryImport | Namespace privado, histórico minimizado e revogável; nenhuma transferência de scheduling |
| DomainEvent / AuditLog | Mudança, responsável, horário, revisão, motivo e hashes anterior/novo na mesma transação |

## Core, formas e destinos

Cada Core de produção exige exatamente 3000 identidades com ranks 1–3000 e
1000 headwords por nível real. A contagem total é
`3000 + formas importantes aprovadas + papéis opcionais habilitados`.
Formas herdam rank, nível e deck ID do pai. Expansão contém de 0 a 3000 outras
identidades; não serve para esconder formas obrigatórias. Reverse, listening e
cloze são papéis opcionais desligados por padrão.

As identidades estáveis não resolvem automaticamente aliases dos decks antigos:
o exporter legado inclui job/ordem em alguns GUIDs. Migração ambígua, merge ou
split exige decisão explícita; não se escolhe a primeira acepção nem se move
histórico silenciosamente.

## Ranking e avaliação

RANK-01 agrega `peso * ln(1 + frequência por milhão) * dispersão`, com Decimal,
precisão intermediária, arredondamento e desempate versionados. MWE alocada
consome seu span antes de tokens sobrepostos no mesmo canal; canais sobrepostos
precisam de autorização própria. Corpus privado não pode alterar Core público.

EVAL-01 representa datasets, estratos, dimensões, taxas, baseline, tolerância a
regressão e revisão independente. São necessárias evidências por idioma; não
há aprovação global por passar um teste unitário ou por julgamento de LLM.

## Política linguística

Os 22 códigos modernos já existentes são reutilizados. O Latim permanece em
foundation isolada. Na arquitetura nativa, explicações são em inglês, exceto
inglês e Latim, que usam português. Coreano nativo usa `ko`/`ko-KR` e explicação
em inglês; os decks coreanos legados mantêm seus contratos existentes.
