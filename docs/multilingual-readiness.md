# Resultado da preparação das 22 línguas

Observação local em 12/09/2026. Foram instalados os 22 analisadores e preparados
24 lotes de fontes reais: **260.439 candidatos lexicais**, **71.940 registros de
possíveis flexões** e **4.400 frases de diagnóstico**, 200 por língua. São entradas
para revisão; nenhuma identidade Core recebeu nova aprovação nesta preparação.
Os fields Anki mantêm os nomes e a ordem existentes.

O [relatório JSON](multilingual-readiness.json) contém contagens, hashes dos
manifests, modelos, fontes e observações. As contagens foram reconciliadas lendo
os arquivos reais e verificando seus hashes. A deduplicação entre lotes usa o ID
do candidato; nenhum candidato duplicado entre lotes foi encontrado.

## Cobertura observada

Um candidato lexical representa uma possibilidade de sentido, não necessariamente
uma palavra distinta. Uma flexão de dicionário ainda não é uma forma importante
aprovada em contexto. Portanto, essas colunas não contam cartões prontos.

| Língua | Candidatos lexicais | Possíveis flexões | Completas / 200 | Divergentes |
|---|---:|---:|---:|---:|
| `pt` | 11320 | 4501 | 53 | 23 |
| `es` | 11157 | 5026 | 113 | 62 |
| `en` | 62053 | 2919 | 164 | 89 |
| `fr` | 10461 | 3715 | 106 | 63 |
| `de` | 10863 | 7277 | 149 | 107 |
| `it` | 11081 | 5029 | 71 | 26 |
| `pl` | 10203 | 4658 | 171 | 101 |
| `tr` | 6501 | 1658 | 173 | 107 |
| `ro` | 5363 | 1948 | 200 | 97 |
| `ru` | 5647 | 5150 | 200 | 157 |
| `nl` | 9172 | 5187 | 196 | 140 |
| `ko` | 27765 | 680 | 11 | 11 |
| `da` | 6783 | 2555 | 198 | 117 |
| `nb` | 5941 | 3702 | 198 | 150 |
| `sv` | 7917 | 3781 | 200 | 110 |
| `fi` | 7184 | 4789 | 199 | 131 |
| `hu` | 6734 | 2741 | 200 | 168 |
| `cs` | 3942 | 2499 | 188 | 103 |
| `hr` | 5476 | 0 | 196 | 143 |
| `el` | 4934 | 3956 | 118 | 81 |
| `ja` | 17296 | 165 | 54 | 53 |
| `zh` | 12646 | 4 | 187 | 142 |

“Completas” significa que o analisador produziu uma estrutura válida com spans
exatos. Não significa que todos os lemas, classes ou traços estejam corretos.
“Divergentes” conta as frases estruturalmente completas com pelo menos uma
divergência de segmentação, lema, classe ou traço anotado em relação ao corpus UD.
O JSON conserva denominadores, métricas e casos inconclusivos. Divergência não
mede aceitação indevida de sentidos: essa taxa ainda não foi avaliada.

## O que foi executado

- Dicionário Wiktextract completo adquirido uma vez, verificado por SHA-256 e
  separado por código exato de língua. A seleção inicial preserva maiúsculas,
  acentos e todos os sentidos dos lemas selecionados.
- Croata preparado a partir de Croatian Wordnet com glosses dos synsets exatos
  de Princeton WordNet 3.0. Registros de `sh` não foram reclassificados como `hr`.
- Seleção de 6000 candidatos de frequência por língua, exceto o lote coreano,
  com 29.978 itens de seleção. A seleção não é o ranking final do Core.
- Finlandês e chinês divididos em dois lotes de 3000 itens de seleção após
  atingirem o limite de saída de 128 MiB. As tentativas recusadas não publicaram
  resultados parciais e os dois lotes preservam a seleção original.
- Stanza 1.14.0/PyTorch CPU com recursos fixados em 1.10.0 para 20 línguas,
  Kiwi 0.23.2 para coreano e Fugashi 1.5.2/UniDic-lite 1.0.8 para japonês.
  A verificação final releu os bytes dos modelos; nenhuma disponibilidade foi
  convertida automaticamente em qualificação.
- Corpora UD r2.16 adquiridos para todas as línguas. Cada amostra usa os 200
  menores hashes de frase vinculados à fonte, distribuídos pelo arquivo de teste.
  Corpus de teste permanece fora do ranking e da preparação de frequência.
- Diagnósticos recalculados com avaliador versão 2, que também conta erros de
  traços nas divergências. O japonês foi novamente analisado após a inclusão dos
  arquivos de configuração do dicionário no fingerprint. Resultados antigos
  permanecem locais, mas não entram duas vezes nas contagens atuais.

Os dados e modelos ficam em `.multilang/sources`, `.multilang/models` e
`.multilang/verification/real-languages`. Não foram incluídos nos commits como
assets lexicais redistribuíveis. O repositório recebe código, catálogo e relatórios
agregados. O [catálogo de pesquisa](multilingual-source-research.md) documenta
fontes, atribuições, restrições e alternativas ainda não incorporadas.

## Limites encontrados nos dados reais

As contrações representadas por múltiplas palavras no UD podem não oferecer
spans exatos para cada análise. O adaptador Stanza recusa a frase inteira nesse
caso, o que reduz especialmente a cobertura em português, espanhol, francês,
italiano e grego. Essa recusa evita aceitar uma correspondência inventada;
recuperar cobertura exige um alinhamento comprovado.

Kiwi e UniDic usam unidades e classes diferentes das anotações dos corpora UD
coreano e japonês selecionados. As métricas são diagnósticos dessa combinação,
não porcentagens gerais de qualidade dessas línguas. Ainda são necessários
goldens independentes compatíveis, revisão de mapeamentos e avaliação de sentidos
e strict-i+1. A sobreposição entre dados UD e o pré-treinamento dos modelos não
foi estabelecida; a divisão chamada `test` não prova avaliação independente.

POS não reconhecido permanece `X` e pendente; não é escolhido por palpite. O
material croata filtrado contém 1603 lemas distintos e não prova cobertura das
3000 identidades exigidas. O chinês também tem menos de 3000 lemas distintos
nesse recorte. Sentidos múltiplos podem aumentar identidades, mas não resolvem
automaticamente cobertura, atualidade ou equilíbrio do vocabulário.

O dicionário identifica possibilidades lexicais; UD oferece contexto anotado.
Nenhum dos dois fornece sozinho os corpora equilibrados, dispersão e pesos
aprovados necessários para o ranking de produção. O pipeline mantém essa
distinção no manifest, em vez de transformar ordem de arquivo em frequência.

## Compatibilidade Anki e banco local

O núcleo oficial Anki 26.8.1 importou o pacote de inspeção com 11 notas e cinco
modelos de campos, renderizou perguntas/respostas e registrou uma revisão.
A reimportação do mesmo pacote preservou IDs, ordinais, agendamento e histórico.
O pacote é sintético, sem áudio de produção; isso verifica estrutura e reimportação,
sem aprovar conteúdo nem representar os quatro aplicativos exigidos pelo plano.

O ensaio PostgreSQL 17.11 passou em duas bases descartáveis locais, com backup,
restauração, migração, conservação do legado e rollback. Nenhuma base existente
do usuário foi migrada. Os resultados de testes e commits ficam no relatório
`ROADMAP_4_NATIVE_IMPLEMENTATION.md`, na raiz do projeto.

## Pendência que permanece

O software prepara as fontes, analisa frases, recebe decisões revisadas, verifica
suas evidências e importa sentidos e formas. O [guia de uso](vocabulary-preparation.md)
descreve também a geração de rascunhos e sua conclusão após revisão contextual.

Para liberar os decks finais ainda faltam decisões reais de revisão linguística
e de distribuição, corpus de frequência adequado, qualificação por capacidade,
conteúdo/áudio aprovados e aceitação nos clientes. Geração paga exige orçamento
definido; nenhuma chamada paga foi realizada neste complemento. Essas entradas
não podem ser substituídas por receipts sintéticos nem por instalar uma biblioteca.
Deploy está fora do escopo por decisão do usuário.
