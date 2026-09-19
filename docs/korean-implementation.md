# Coreano: implementação direta

Este trabalho usa os requisitos existentes sem executar workflows GSD. O mapa
`korean-implementation.json` aponta código e testes para os 32 requisitos; essa
relação não é uma declaração de que o conteúdo de produção foi aprovado.

## Operação local

Os comandos abaixo usam o banco configurado em `MULTILANG_DATABASE_URL`.
`multilang korean --help` apenas mostra a interface; não abre o banco nem chama
provedores. O nome antigo `phase33` continua como alias de `korean`.

```console
multilang korean import-custom --input-file palavras.txt
multilang korean bind-provider-policy --job-id JOB_ID --provider-policy-file provedores.json
multilang korean status --job-id JOB_ID
multilang korean process --job-id JOB_ID --source custom --mode start --max-items 10
multilang korean process --job-id JOB_ID --source custom --mode resume --max-items 10
```

A importação preserva ordem, duplicatas e palavras ainda sem identidade lexical
resolvida. Resolver local e evidências de pré-requisitos determinam quais itens
podem prosseguir. `--prerequisites-file` admite evidência por posição da lista;
lacunas exigem uma decisão explícita de ponte ou adiamento por
`korean decide-prerequisites`. Um item pendente não é contado como aceito.

Para highlights, `multilang korean import-highlights --input-file highlights.txt`
faz apenas a importação local. Em seguida, vincule a política ao job e use
`korean process --source highlight`. A geração direta usa o alvo lexical e não
envia o trecho privado do livro como contexto. Os relatórios
operacionais usam identificadores opacos, inclusive para chaves antigas que
continham a palavra original. A disponibilização de contexto privado a um
provedor continua dependendo do protocolo de autorização próprio.

## Revisão por campo

```console
multilang korean review list --job-id JOB_ID --actor-id local \
  --request-id list-001 --field sentence --status needs_review
multilang korean review edit --job-id JOB_ID --item-id ITEM_ID \
  --field sentence --value-file frase.txt --actor-id local \
  --request-id edit-001 --expected-pointer-version VERSION
multilang korean review validate --job-id JOB_ID --item-id ITEM_ID
```

`review approve` e `review reject` recebem a revisão e a versão exatas mostradas
na listagem. Edições preservam os outros valores e deixam as dependências
afetadas pendentes de nova revisão. O histórico de valores anteriores e novos
fica no banco local; não é anexado a solicitações a provedores.
Um campo aprovado precisa ser rejeitado explicitamente antes de ser substituído.
Rejeitar texto também bloqueia sua aceitação nos fluxos de status e exportação.
Validar ou aprovar manualmente um campo não fabrica uma revisão linguística AI.

`review regenerate` gera somente `definition`, `sentence` ou `translation`,
usando a política vinculada ao job. A identidade da solicitação permite repetir
um comando concluído sem uma segunda chamada paga. Um resultado incerto exige
recuperação explícita.

Após editar e validar o texto, prepare o snapshot para revisão e importe a
evidência de três passes AI em contextos novos e separados:

```console
multilang korean review prepare-text-evidence --job-id JOB_ID --item-id ITEM_ID --output snapshot.json
multilang korean review apply-text-evidence --job-id JOB_ID --item-id ITEM_ID \
  --evidence-file revisao-ai.json --actor-id local --request-id review-001
```

Esses comandos não executam a revisão AI nem chamam provedores. A aplicação exige
consenso, validação determinística e vínculos atuais de conteúdo, identidade,
política e revisões. Mudanças nesses dados invalidam a evidência. O contrato
`PersonalTextReviewEvidence` está em
`src/multilang/services/korean_personal_text_review.py`.

Para áudio, os comandos `review regenerate-audio`, `apply-audio-review`,
`reject-audio` e `recover-audio` usam autorização específica para a fonte.
O procedimento está em [korean-personal-audio.md](korean-personal-audio.md).
A síntese permanece pendente até a aplicação da evidência acústica exata.

## Gramática e pré-requisitos

```console
multilang korean import-grammar --bundle gramatica.json
multilang korean export-grammar --job-id JOB_ID --media-dir audio \
  --bootstrap-cards vocabulario-revisado.json --output-dir exportacao --format apkg
```

O destino deve estar vazio. Os formatos disponíveis são `apkg`, `csv` e `tsv`;
os formatos tabulares incluem `collection.media`. A exportação confere o
snapshot ativo das fundações, a ordem curricular, as revisões e os bytes dos
áudios antes de produzir cartões. Os áudios devem ser MP3 decodificáveis,
compatíveis com o perfil Azure coreano. O campo Image continua vazio.

Quando o bundle contém `lexical_bootstrap`, `--bootstrap-cards` deve fornecer
exatamente esses cartões em uma lista JSON de `KoreanGrammarBootstrapCard`.
O esquema está em `src/multilang/domain/korean_grammar_bootstrap.py`. Cada item
contém definição, exemplo, tradução, IPA opcional e vínculos de revisão e mídia.
A revisão do bootstrap vincula o candidato exato, a fonte, o bundle curricular e
ambos os áudios. A revisão das construções gramaticais usa
`grammar_candidate_sha256` e `grammar_review_curriculum_sha256`: o segundo
vincula a raiz e o grafo curricular, sem incluir as próprias revisões, evitando
um hash circular. Metadados lexicais sem conteúdo revisado não substituem esses cartões.

Os cartões de pré-requisitos precedem os de gramática no mesmo baralho. O status
só informa que estão prontos depois de uma exportação válida e enquanto os
arquivos e as evidências continuarem atuais. Uma alteração nos áudios, no bundle
ou no snapshot ativo invalida essa indicação.

## Frequência, áudio e retomada

A síntese real de frequência usa `synthesize-korean-frequency-audio`, com
catálogo, perfil, política e hashes de autoridade explícitos. Consulte o `--help`
desse comando para os arquivos e vínculos exigidos. `--max-items` limita palavras
e `--missing-only` reaproveita os áudios compatíveis já persistidos. Síntese
bem-sucedida fica pendente de revisão acústica; não aprova o cartão.

O perfil de frequência não autoriza automaticamente síntese para outras fontes.
Configure `MULTILANG_KOREAN_AZURE_TTS_USD_PER_MILLION_CHARACTERS` e
`MULTILANG_KOREAN_AZURE_TTS_PRICING_VOICE_ID` com a tarifa e a voz contratadas.
A regeneração via DeepL exige `MULTILANG_DEEPL_COST_PER_CHARACTER_USD`; zero
só deve ser informado quando essa for a tarifa aplicável ao seu plano.
Nenhum preço Azure é embutido no código. O preflight de orçamento usa a tarifa
configurada para a voz exata; uso e custo não retornados pelo provedor permanecem
desconhecidos nos registros, sem tokens ou valores fictícios.

Geração compartilhada aceita concorrência 1. PostgreSQL permite jobs distintos
em processos separados; SQLite serializa a geração no banco. Interrupções após
o início de uma tentativa preservam uma reserva para impedir repetição paga
silenciosa. Consulte `generation-lease-status` e `recover-generation-lease`,
descritos em [generation-operations.md](generation-operations.md).

As famílias de gramática, listas e highlights coreanos têm modelos Anki
específicos com fontes para Hangul. Frequência usa três subbaralhos reais e
preserva a fórmula dos GUIDs dos cartões existentes.
Exports coreanos revalidam os dados atuais mesmo quando há snapshots salvos.
CSV/TSV incluem os arquivos referenciados em `collection.media`.

## Evidência e trabalho de produção

Os resultados automatizados desta execução ficam em
`.multilang/verification/korean-direct/`. Os testes usam provedores falsos,
arquivos locais e bancos descartáveis. Eles verificam estrutura e comportamento;
não medem qualidade linguística ou acústica de um deck real.

Ainda precisam de execução de produção: gerar e revisar os 3.000 cartões de
frequência e suas traduções, sintetizar e revisar 6.000 áudios, produzir o
currículo gramatical revisado e validar os artefatos finais no Anki Desktop e
mobile. Nenhuma aprovação de conteúdo, publicação ou chamada paga foi simulada
para declarar essas etapas concluídas.
