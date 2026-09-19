# Revisão linguística, importância e calibração

O fluxo prepara dados reais para revisão e mede o que pode ser medido. Os campos
dos cards Anki continuam iguais: uma forma importante, como `went`, aparece no
campo da palavra estudada; a ligação com `go`, o sentido, os traços e as fontes
ficam nos registros internos. O Core permanece com três níveis de 1000 identidades,
mais todas as formas importantes aprovadas. Um piloto de 100 verbetes é preparação,
não um Core reduzido.

O [plano detalhado de implementação](superpowers/plans/2026-09-13-linguistic-qualification.md)
descreve arquivos, interfaces, testes e a sequência aprovada. A
[especificação](superpowers/specs/2026-09-13-linguistic-qualification.md) registra
os contratos e os critérios de conclusão.

Os [resultados locais](linguistic-qualification-results.md) registram os pilotos
efetivamente preparados e os limites das fontes usadas. O índice para abrir os
formulários está em `.multilang/verification/qualification/review-index.html`.

## Passo a passo de uso

1. **Congelar as fontes.** Guardar texto, revisão, origem, licença e SHA-256.
   A aquisição Wikimedia mantém a identidade da página e a resposta original.
   O texto medido é a prosa extraída dos parágrafos: tabelas, código, matemática
   e navegação são excluídos. Frases não viram documentos independentes.
   Limites e indisponibilidades aparecem no manifest.
2. **Selecionar o piloto.** Usar a ordem declarada de candidatos de frequência
   para escolher 100 grafias com entrada lexical disponível. Preservar todos os
   sentidos e formas relacionados; não escolher automaticamente o primeiro sentido.
   A lista de sementes deve estar em NFC. Quando a fonte usa outra representação
   Unicode, guardar o original e registrar a normalização antes de enviar a lista.
   Isso não autoriza modificar frases que já tenham posições anotadas.
3. **Analisar ocorrências.** Os modelos locais produzem lema, classe, traços e
   posições comprovadas no texto. Contrações sem alinhamento, palavras desconhecidas
   e análises divergentes ficam visíveis para revisão.
4. **Medir importância observável.** Contar ocorrências distintas e documentos,
   calcular frequência e dispersão na amostra e registrar critérios ainda não medidos.
5. **Revisar no navegador.** Abrir `review.html`, examinar as fontes, registrar
   decisões e baixar o JSON. O arquivo pode ser reaberto na mesma página para
   retomar o trabalho. Não é necessário servidor, deploy ou conexão na página.
6. **Autenticar a revisão.** Importar o JSON ligado ao pacote original. Uma revisão
   sem assinatura continua sendo um rascunho válido. A autenticação verifica tanto
   a assinatura quanto a identidade esperada do revisor; uma declaração de
   experiência no formulário não verifica credenciais profissionais.
7. **Calibrar critérios.** Comparar uma lista explícita de pesos/limiares com as
   decisões de inclusão e exclusão do conjunto de calibração. Registrar erros e
   casos sem evidência suficiente. Não ajustar pesos usando o conjunto de avaliação.
8. **Avaliar a regra congelada.** Aplicar a regra escolhida em material separado,
   verificando sobreposição de documentos/ocorrências, idioma, perfil e rubrica.
9. **Preparar geração e áudio.** Gerar entradas para o importador já existente,
   conferir a seleção completa, cache e estimativa de custo. Usar os serviços
   nativos de conteúdo, áudio e exportação depois das revisões e da autorização
   de orçamento. A preparação local não realiza chamadas pagas.

## O que entra na política de importância

`ImportantFormCriteria` contém uma proposta de pontuação. `ImportantFormPolicy`
mantém o contrato anterior e exige a aprovação separada. Seu JSON e seu hash
continuam compatíveis. A calibração não cria essa aprovação.

| Sinal | Cálculo ou evidência |
| --- | --- |
| Contagem | Ocorrências físicas distintas, ligadas à fonte, documento, frase e posição |
| Frequência por milhão | `ocorrências × 1.000.000 / tokens declarados da amostra` |
| Dispersão | `documentos com a forma / documentos distintos da amostra` |
| Nota de frequência | Percentil empírico de posto médio: `(grupos com contagem menor + grupos empatados / 2) / total de grupos` |
| Irregularidade e imprevisibilidade | Evidência lexical explícita e/ou julgamento revisado; ausência não vira nota inventada |
| Ambiguidade e pronúncia inesperada | Análise contextual/pronúncia e revisão vinculadas à fonte |
| Pré-requisito e dificuldade | Avaliação pedagógica explícita, registrada com a rubrica |

O percentil depende da população medida; o relatório guarda o hash dessa
população e o método `sample-midrank-cdf-1`. Um único grupo tem percentil `0,5`,
não evidência automática de alta importância. Esses valores não são probabilidades
do modelo. Documentos copiados são contados uma vez. Sem limites documentais
conhecidos, a dispersão é `null` e seu motivo é registrado.

Sem uma associação revisada ao sentido, a contagem pertence ao grupo
lema/classe/forma/análise. Ela não é replicada em todos os sentidos daquele lema.
A confiança na análise informada na revisão é uma avaliação humana explícita;
não é apresentada como confiança estatística fornecida pelo modelo.

A calibração usa no máximo 256 critérios por execução. O objetivo é minimizar
`falsos positivos × custo_FP + falsos negativos × custo_FN`, com custos fornecidos
explicitamente. Empates são resolvidos pelo hash dos critérios. O resultado
mostra precisão, revocação, contagens, formas selecionadas e exclusões. Casos sem
rótulo definido, sentido, classe, contagem ou confiança revisada não são escondidos
no denominador. Exige exemplos avaliáveis positivos e negativos.

Não existe corte por quantidade ou orçamento que descarte formas aprovadas.
Depois da seleção, o orçamento informa o trabalho necessário para a seleção inteira.

A avaliação reexecuta a calibração com o pacote, as decisões autenticadas, a grade
e os custos originais. Alterar apenas o hash ou a lista de fontes do relatório não
remove a verificação de sobreposição. Cada grupo medido também registra a origem
de todas as ocorrências contadas, além dos exemplos exibidos no formulário.
As contas da calibração usam precisão decimal e arredondamento fixados.

## Comandos e arquivos

```bash
uv run --no-sync multilang native vocabulary qualification --help
```

Nos exemplos abaixo, nomes em maiúsculas são valores a substituir pelos caminhos
e hashes dos arquivos. Todos os diretórios/arquivos de saída devem ser novos.
SHA de arquivo significa hash dos bytes; `packet.packet_sha256` é o hash canônico
usado dentro da submissão. O manifest de exportação informa os dois valores.

A descoberta pode selecionar um prefixo alfabético ou páginas recém-criadas.
Ambas são amostras limitadas, sem garantia de representatividade. A aquisição
recebe IDs explícitos e pode verificar a seleção congelada pelo hash:

```bash
uv run --no-sync multilang native vocabulary qualification discover-corpus \
  pt wikipedia NEW_SELECTION_JSON --strategy recent-new-pages --limit 25

uv run --no-sync multilang native vocabulary qualification acquire-corpus \
  pt wikipedia NEW_CORPUS_DIR --page-id PAGE_ID_1 --page-id PAGE_ID_2 \
  --selection SELECTION_JSON --selection-sha256 SELECTION_FILE_SHA256
```

Os IDs devem corresponder à seleção fornecida. Sem `--selection`, registra-se a
política de IDs explícitos; não se presume como eles foram escolhidos.
Limitações remotas e pedidos de espera são registrados, sem repetição ilimitada.

```bash
uv run --no-sync multilang native vocabulary qualification prepare-pilot \
  REQUEST_JSON REQUEST_FILE_SHA256 NEW_PILOT_DIR

uv run --no-sync multilang native vocabulary qualification measure \
  MEASUREMENT_REQUEST_JSON REQUEST_FILE_SHA256 NEW_REPORT_JSON

uv run --no-sync multilang native vocabulary qualification export-review \
  PACKET_JSON PACKET_FILE_SHA256 NEW_REVIEW_DIR

uv run --no-sync multilang native vocabulary qualification import-review \
  PACKET_JSON PACKET_FILE_SHA256 SUBMISSION_JSON SUBMISSION_FILE_SHA256 \
  EXPECTED_REVIEWER NEW_VALIDATED_JSON

uv run --no-sync multilang native vocabulary qualification review-payload \
  PACKET_JSON PACKET_FILE_SHA256 SUBMISSION_JSON SUBMISSION_FILE_SHA256 NEW_PAYLOAD_JSON
```

O pedido de medição contém `context` e `occurrences`, validados pelos contratos
`CorpusEvidenceContext` e `EvidenceOccurrence`. O pedido do piloto contém
`language`, `prepared_inputs` (diretório e hash do manifest), `seed_words`
(lista ordenada), hashes do perfil/rubrica e, quando disponíveis, `evaluation_input`,
`evidence_context` e `occurrences`. Fontes de teste não podem entrar na medição de
calibração. Os pacotes de revisão são divididos em arquivos limitados sem descartar
os registros originais.

O pacote de assinatura usa o propósito `qualification-review`. A chave permanece
no ambiente local (`MULTILANG_NATIVE_EVIDENCE_SIGNING_KEY`); nunca vai para o HTML.
Receipts ficam em `MULTILANG_NATIVE_EVIDENCE_DIR`. A página não assina decisões,
não envia dados à rede e não grava automaticamente no navegador.

```bash
uv run --no-sync multilang native vocabulary qualification calibrate \
  CALIBRATION_PACKET PACKET_FILE_SHA256 SUBMISSION SUBMISSION_FILE_SHA256 \
  CRITERIA_GRID_JSON GRID_FILE_SHA256 EXPECTED_REVIEWER NEW_CALIBRATION_JSON \
  COST_FALSE_POSITIVE COST_FALSE_NEGATIVE

uv run --no-sync multilang native vocabulary qualification evaluate \
  CALIBRATION_JSON CALIBRATION_FILE_SHA256 EVALUATION_PACKET PACKET_FILE_SHA256 \
  SUBMISSION SUBMISSION_FILE_SHA256 EXPECTED_REVIEWER NEW_EVALUATION_JSON

uv run --no-sync multilang native vocabulary qualification workload \
  WORKLOAD_REQUEST_JSON REQUEST_FILE_SHA256 NEW_WORKLOAD_JSON
```

O pedido de carga pode informar `headwords`, `observed_forms`, `selected_forms`,
cards opcionais e quantidades verificadas no cache. Sem seleção final,
`expected_card_count` fica indefinido. Sem preços explícitos e sua origem,
`expected_cost` fica `null`, nunca zero. Preços por requisição são estimativas
fornecidas pelo operador; tarifas por token/caractere precisam dos textos reais.
O tamanho exato do `.apkg` depende dos áudios concluídos.

Na carga final, `headwords` conta as identidades lexicais selecionadas para cards,
não simplesmente grafias distintas do piloto: dois sentidos aprovados podem
produzir duas identidades. `content_units` separa essas notas dos cards opcionais
de reversão/escuta, que compartilham texto e áudio. O cache e as requisições são
contados sobre as unidades de conteúdo.

Para observar um corpus adquirido, use `observe-corpus`. Para o corpus UD de treino,
`observe-training` exige também o recibo e seu hash; não aceita renomear um arquivo
de teste como treino. O denominador dessas observações contém apenas tokens
lexicais alinhados pelo modelo, com cobertura e trechos bloqueados separados.
Esses dois comandos produzem observações para calibração. Por padrão, analisam
até 1000 parágrafos (`observe-corpus`) ou 200 frases (`observe-training`), conforme
`--max-units`. `--model-root` aponta para os modelos locais já preparados.
Unidades longas demais ficam registradas como ignoradas; arquivos acima do limite
são recusados. O relatório não implica que todo o corpus foi analisado.

```bash
uv run --no-sync multilang native vocabulary qualification observe-corpus \
  DOCUMENTS_JSONL DOCUMENTS_SHA256 NEW_OBSERVATIONS_JSON

uv run --no-sync multilang native vocabulary qualification observe-training \
  CORPUS_CONLLU CORPUS_SHA256 LANGUAGE ACQUISITION_RECEIPT RECEIPT_SHA256 \
  NEW_OBSERVATIONS_JSON

uv run --no-sync multilang native vocabulary qualification vocabulary-input \
  PREPARATION_DIR PACKET PACKET_FILE_SHA256 SUBMISSION SUBMISSION_FILE_SHA256 \
  EXPECTED_REVIEWER PROFILE_JSON PROFILE_FILE_SHA256 SOURCE_ID SOURCE_VERSION NEW_BRIDGE_JSON
```

`vocabulary-input` produz o `VocabularyReview` e os payloads individuais ainda
sem assinatura. Uma decisão sobre forma sem o vínculo contextual nativo completo
continua pendente, com o motivo explícito. Correções de lema/classe podem ser
aplicadas por `derive-corrections`, que usa os mesmos argumentos e recebe um
diretório novo na saída. Ele preserva a fonte original, produz candidatos derivados
com novos IDs e registra a correção autenticada. A nova preparação contém revisão
pendente; o compilador existente continua exigindo suas aprovações próprias.

## Fontes e diferenças entre idiomas

O caminho moderno atende `pt es en fr de it pl tr ro ru nl ko da nb sv fi hu cs hr
el ja zh`. Os modelos, normalização, evidências e decisões continuam específicos
de cada língua. O caminho de Latim permanece separado.

Wikipedia fornece prosa enciclopédica e Wikinews pode fornecer notícias.
Wikibooks é uma alternativa instrucional pesquisada. Uma amostra pequena desses
projetos não demonstra frequência geral equilibrada. `nb → no` identifica o
projeto Wikimedia; não comprova que o texto é Bokmål. `zh` também não comprova
que cada documento está em escrita simplificada.

Na execução local, `wordfreq` 3.1.1 usou `sh` como aproximação para a semente
solicitada como `hr`. Essa semente não comprova frequência especificamente croata.
O piloto permanece ligado às fontes e revisões do seu idioma; a limitação foi
registrada em `.multilang/verification/qualification/seed-provenance/hr.json`.

A aquisição preserva revisão, primeira publicação, atribuição e licença
declarada. Licenças históricas do Wikinews inglês variam por data, e as condições
de uma página podem exigir análise adicional. Nenhuma aquisição aprova
redistribuição automaticamente. Consulte as fontes primárias:
[licenciamento Wikimedia](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content),
[Wikinews](https://en.wikinews.org/wiki/Wikinews:Copyright),
[revisões da API](https://www.mediawiki.org/wiki/API:Revisions) e
[etiqueta da API](https://www.mediawiki.org/wiki/API:Etiquette).

UD permanece diagnóstico gramatical. UD train pode apoiar um piloto explicitamente
gramatical; UD test fica separado da calibração. As anotações UD coreanas e os
atributos nativos de UniDic/Kiwi não são comparados como se usassem sempre o mesmo
inventário. Métricas incompatíveis aparecem como `null` com explicação. Isso não
é aprovação linguística do modelo.

## O que uma revisão humana ainda precisa resolver

A ferramenta organiza o trabalho de quem conhece a língua: confirmar sentidos,
classes, análises ambíguas, naturalidade, pronúncia e utilidade pedagógica. A pessoa
responsável pode revisar lotes pequenos, registrar motivos e discordâncias e
deixar casos inconclusivos. Para avaliação independente, deve revisar material que
não tenha sido usado para escolher a regra.

Testes automáticos verificam os contratos, contagens, hashes e segurança do fluxo.
Eles não substituem um especialista nem verificam credenciais. Pilotos de máquina
não são chamados de conjuntos de referência aprovados. Conteúdo, tradução, áudio,
licenciamento e os clientes Anki também têm sua verificação própria antes de uma
edição de produção.

## Verificação desta implementação

Em 2026-09-13, passaram **451 casos distintos de teste**: contratos e serviços
novos, CLI e regressão nativa, incluindo a geração e exportação a partir da
revisão autenticada. A regressão foi executada em uma cópia da base com os arquivos
desta entrega, pois outra refatoração estava alterando o workspace simultaneamente.
Os dois percursos de geração/exportação também passaram no workspace compartilhado.

A revisão foi exercitada no Chromium 151 com dados sintéticos e pacotes reais de
500 itens em português e coreano, em tamanhos de desktop e celular. Busca, filtros,
paginação e fontes funcionaram sem erros JavaScript nem requisições externas.
As interações com dados reais não criaram decisões ou aprovações.

O backend oficial do Anki 26.8.1 importou as duas notas sintéticas produzidas pelo
fluxo de qualificação, conferiu os campos, renderizou os cards e preservou IDs,
agendamento e histórico na reimportação. Esse ensaio não verificou a reprodução
do áudio sintético nem os aplicativos gráficos ou móveis.

Ruff, distribuição wheel/sdist e construção estrita da documentação também foram
verificados. O resumo e os relatórios completos ficam em
`.multilang/verification/qualification/verification-summary.json`; resultados de
software e preparação de dados permanecem distintos da qualificação linguística.

## Revisão por IA

O [fluxo de qualificação por IA](ai-linguistic-qualification.md) conecta os pacotes deste guia a propostas, julgamento em contexto separado, rascunhos de vocabulário e calibração com rótulos de máquina. Inclui modo por arquivos, execução limitada por API e retomada verificável.
