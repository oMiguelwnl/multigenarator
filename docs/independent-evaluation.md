# Avaliação documental e expansão lexical

Esta entrega adiciona um caminho nativo para avaliar a seleção de formas com
documentos separados, referências lexicais verificáveis e revisão por dois
contextos de IA. O contrato é optativo e não habilita produção automaticamente.
Os nove campos dos cards e o áudio do piloto aprovado permanecem preservados.

## Implementação

`document-partition-evaluation-1` reconstrói as partições a partir do CoNLL-U
original, vinculado por SHA-256. Cada partição conserva os frames originais,
documentos, frases, tokens, anotações e motivos de exclusão. As medições usam
todos os tokens elegíveis dos documentos selecionados, inclusive ocorrências de
formas que não foram escolhidas para revisão.

O denominador é explícito: tokens lexicais UD com lema e superfície alinhável.
Pontuação, anotações ausentes e componentes de contrações sem alinhamento
comprovável não entram nessa população. As contagens desses descartes ficam no
artefato. As anotações UD não são tratadas como análises linguísticas já aprovadas.

A comparação rejeita documentos ou frases de texto idêntico, mesmo sob outros
IDs ou arquivos. Ela não é um detector de paráfrases. Um mesmo arquivo de corpus
pode fornecer documentos diferentes, desde que as duas partições sejam
reconstruídas e verificadas. A proteção histórica por `evidence_source_keys`
continua intacta nos contratos anteriores.

`dictionary-reference-registry-1` permite compartilhar apenas uma projeção
reproduzível da fonte lexical: lema, classe, formas, glosas e qualificadores de
uso. Exemplos, observações e rótulos de revisão ficam fora da projeção. Alterar a
projeção ou o arquivo original invalida sua verificação. Esse vínculo demonstra
proveniência local, não autentica o editor do dicionário nem certifica sua exatidão.

O experimento congela os dois pacotes, o registro compartilhado, a grade de
políticas e os custos de erro. Calibração e avaliação exigem o pacote exato e
reproduzem as verificações antes de calcular métricas. Os horários declarados das
revisões devem ser posteriores ao congelamento; isso é uma conferência de
metadados, não uma prova criptográfica de revisão cega. A aritmética decimal usa
precisão fixa, independentemente da configuração do processo chamador.

## CLI

Os seis comandos pertencem ao grupo
`multilang native vocabulary qualification ai evaluation`:

| Comando | Entrada | Artefato principal |
|---|---|---|
| `prepare-partition` | fonte, idioma, split e IDs de documentos | `partition.json` |
| `prepare-references` | dicionário e pares exatos lema/classe | `references.json` |
| `prepare-review` | partição, referências, grupos e perfil/rubrica | `bundle.json`, `packet.json` |
| `freeze` | dois bundles, grade, custos e horário | `experiment.json` |
| `calibrate` | experimento e qualificação da calibração | `result.json` |
| `evaluate` | experimento, calibração e qualificação da avaliação | `result.json` |

Cada comando recebe `INPUT INPUT_SHA256 OUTPUT`. As referências dentro dos inputs
seguem `{ "path": "...", "sha256": "..." }`. A saída usa o manifesto imutável
existente; nomes, limites, hashes e inventários são verificados. Nenhum desses
comandos chama um provedor de IA ou áudio.

Exemplo de entrada para preparar uma partição:

```json
{
  "source": {"path": "corpus.conllu", "sha256": "SHA256_DO_ARQUIVO"},
  "language": "pt",
  "split": "evaluation",
  "document_ids": ["ID_REAL_DO_DOCUMENTO"]
}
```

Os identificadores devem existir na fonte. Uma seleção vazia, repetida, inventada
ou sem limites documentais explícitos falha. Para descobrir os demais contratos,
consulte `qualification_evaluation_cli.py` e os modelos dos serviços associados.

## Execução real e revisão

As evidências desta rodada ficam em
`.multilang/verification/evaluation-expansion/`. O protocolo de seleção foi
registrado antes dos novos rótulos: 11 grupos de desenvolvimento já estudados e
20 grupos de avaliação ordenados por hash, sem usar pontuações ou decisões para
escolher os itens. A grade conserva as seis políticas e os custos anteriores.

| Partição PT | Documentos | Frases | Tokens sintáticos | Tokens elegíveis |
|---|---:|---:|---:|---:|
| Calibração | 49 | 208 | 4.055 | 2.969 |
| Avaliação | 20 | 90 | 2.481 | 1.769 |

O replay confirmou separação documental e textual. Os 20 documentos vieram da
reserva anterior, vinculada ao seu manifesto original. Não se afirma que o
treinamento prévio dos modelos nunca tenha incluído esse corpus público.

As propostas de importância foram escritas após o congelamento. A proposta e o
julgamento separados produziram nove acordos em 11 grupos de calibração e 16 em
20 grupos de avaliação. Permanecem seis abstenções: `trabalho`, `dia`, `paulistas`,
`ascendem`, `grades` e `vizinhas`, por sentidos concorrentes ou escopo de uso
insuficiente. Critérios que exigem currículo, áudio ou erros observados de
aprendizes foram omitidos. Os escores fornecidos são julgamentos ordinais de IA.

A primeira importação do julgamento usou 22 caracteres do identificador da fonte,
enquanto a proposta usava 24. O sistema bloqueou esses 25 acordos por divergência
de identidade. A versão `*-result-v2` corrige somente essa representação do mesmo
registro/índice de sentido; rótulos, notas, razões e citações ficaram iguais. A
versão anterior e os horários de revisão e reimportação foram preservados. A
primeira tentativa de calibração foi interrompida antes de produzir métricas.

Os comandos públicos `calibrate` e `evaluate` terminaram com exit 0 e artefatos
íntegros, usando a mesma cópia de código verificada nos testes:

| Conjunto | Itens avaliados | Abstenções | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Calibração | 9 de 11 | 2 | 2 | 7 | 0 | 0 |
| Avaliação | 16 de 20 | 4 | 1 | 15 | 0 | 0 |

TP/TN contam inclusões/exclusões corretas em relação aos rótulos de máquina;
FP/FN contam divergências nesses dois sentidos. A avaliação cobre 80% da amostra.
Precisão e recall são 1 entre os casos avaliáveis, mas existe apenas um positivo
na avaliação. Esses números não medem acurácia contra especialistas humanos nem
aprendizagem e não certificam desempenho geral em outras línguas.

A calibração escolheu `pt-supported-linguistic-morphology` v1: frequência com peso
0,25, irregularidade com peso 0,75 e limiar 0,25. A política seleciona `vista` e
`viu` na calibração e `veio` na avaliação. A grade inteira, seus custos de erro e
a seleção dos itens já estavam congelados; não houve ajuste usando o resultado
da avaliação. A elegibilidade é comum à grade e exige também evidência de
ambiguidade, embora a política vencedora não lhe atribua peso.

Os resultados estão em `experiment/calibration-metrics/` e
`experiment/evaluation-metrics/`, vinculados aos inputs e recibos da CLI. O hash
do experimento é `5c4b0350ffb727a2e0c1bb0db7e10405feeeb038b18d043f2fd5afdf26b63fe7`;
o da política é `82e3f43c74e94465b6b3d42af34febac92e88c11536440ffe43d9291898fae3d`.

## Revisão lexical consolidada

Os 44 itens antes inconclusivos receberam fontes recuperadas, novas propostas e
julgamentos separados. A rotação usa os contextos reais existentes: nenhum
contexto foi renomeado para aparentar independência. O contrato de campanha
conferiu que os dois contextos da nova rodada não participaram da rodada anterior
daquela língua. A exposição a resultados agregados anteriores permanece declarada.

| Resultado | Antes, entre 210 itens | Depois, entre os mesmos 210 itens |
|---|---:|---:|
| Concordância entre IAs | 152 | 183 |
| Rejeição | 14 | 18 |
| Incerteza ou desacordo | 44 | 9 |

A rodada resolveu 31 itens por concordância e rejeitou outros quatro. Todos os
166 itens fora da seleção conservaram sua decisão, incluindo as 14 rejeições
anteriores. As nove incertezas restantes continuam explícitas; não viraram
aprovações por ausência de resposta.

Os novos resultados foram consolidados em campanhas nativas e reimportados. O
relatório dos 44 itens usa requests que correspondem exatamente aos pacotes
revisados; não reutiliza os requests antigos com fontes diferentes. Evidências:
`effective-language-reviews/report.json`, `revised-language-reviews/report.json`
e `lexical-pending/*/campaign-final/` sob a raiz desta rodada.

`replacement-candidates.json` identifica uma alternativa lexical documentada
para cada uma das 18 rejeições, mais a evidência flexional francesa `a → avoir`.
Cada alternativa conserva ID, hash, linha/acepção original, referência de licença,
motivo e perguntas de revisão. São candidatos para uma próxima rodada; não
substituíram automaticamente as entradas rejeitadas.

## Expansão das fontes

O preparo anterior usava as primeiras 6.000 grafias de uma lista de candidatos.
Os dicionários locais já continham um recorte de 30.000; esse conjunto foi
processado para recuperar lemas e paradigmas que o corte menor omitira. A operação
produziu 224.774 candidatos nativos nos oito idiomas, preservando acepções,
qualificadores e vínculos com as fontes.

| Idioma | Lemas distintos antes → depois | Sementes legadas cobertas antes → depois |
|---|---:|---:|
| Grego | 2.438 → 6.997 | 2.414 → 2.751 |
| Polonês | 2.297 → 8.255 | 2.592 → 2.831 |
| Romeno | 2.923 → 10.440 | 2.679 → 2.780 |
| Russo | 2.333 → 8.425 | 2.646 → 2.890 |
| Finlandês | 2.703 → 9.179 | 2.804 → 2.900 |
| Tcheco | 2.571 → 8.782 | 2.672 → 2.822 |
| Croata | 1.603 → 5.327 | 849 → 864 |
| Chinês (`zh`; variedade ainda por filtrar) | 2.661 → 10.728 | 1.398 → 1.426 |

Cada idioma tem 3.000 sementes legadas nessa comparação. Cobertura significa
lema direto ou ligação documentada entre a grafia e um lema; não significa 3.000
cards distintos, sentidos resolvidos ou frequência agregada por lema.

O inventário bruto `zh` ainda inclui outras variedades, como cantonês. A exigência
de tags `Mandarin` e `Standard-Chinese` é aplicada à contagem separada de IPA no
escopo pretendido; ela não qualifica automaticamente todos os lemas como mandarim.

No russo, os dois lados da comparação usam a mesma regra adicional de links
literais da fonte entre grafias exibidas com acento e títulos. Foram reproduzidos
77.153 links; nenhum acento foi removido por heurística. Sem esse suplemento, a
correspondência literal estrita passa de 1.557 para 1.567 sementes.

No croata, os números de lemas se referem ao preparo OMW. O ganho de cobertura de
849 para 864 inclui o suplemento separado com 311 sentidos explicitamente
marcados como croatas; 286 têm IPA no registro. Há 33 sementes ligadas a candidatos
de IPA com esse escopo. O código original `sh` foi preservado e não virou alias
global de `hr`. A prioridade `wordfreq:sh` continua sendo exploratória, sem se
apresentar como ranking croata aprovado.

O manifesto de cobertura vincula 112 arquivos. Fontes, atribuição e licenças
declaradas permanecem nos artefatos locais. Nenhum corpus de teste foi usado para
ordenar candidatos. Os novos dados não certificam IPA: a contagem de pronúncias
qualificadas desta expansão é zero. A cobertura detalhada, inclusive variantes,
polissemia e lacunas por rank, está em `coverage/README.md` e seus manifestos.

## Verificação

- 185 testes passaram no checkout isolado da base `7e12f493`, acrescido apenas
  dos arquivos desta implementação. Incluem os novos contratos, a CLI pública,
  adulteração de medições/fontes, população omitida, sobreposição de textos,
  persistência imutável e regressões de calibração/revisão.
- Ruff e a conferência de formatação passaram nos nove arquivos Python próprios.
- Build de sdist e wheel passou; o wheel contém os cinco novos módulos públicos.
- A documentação compilou com `mkdocs build --strict`.
- Duas revisões de código independentes não encontraram pendências materiais no
  escopo examinado. Limites das garantias continuam documentados acima.
- O SHA-256 do piloto aprovado continua
  `594980b9b000384c3507df7f1bf5ad37993749ad9259fbe6a1be71560def14f1`.

Um primeiro teste isolado da CLI excedeu 60 segundos durante a importação sob
carga concorrente; a execução final com limite de 300 segundos passou. As falhas
vermelhas iniciais de TDD e essa tentativa permanecem nos logs. O relatório não
as omite nem as conta como testes aprovados. Os helpers locais também preservam
seus logs de correções de serialização, separados dos testes do produto.

## Limites de entrega

Uma identidade candidata, uma ocorrência de corpus, uma concordância entre IAs e
um card final são artefatos diferentes. Concordância de IA continua sendo uma
avaliação de máquina, sujeita a erros correlacionados. Não substitui evidência
ausente de IPA, adequação do sentido, licença ou qualidade do conteúdo.

Os decks completos exigem 3.000 identidades qualificadas por idioma, ranking
congelado, conteúdo validado e áudio correspondente. Formas flexionadas adicionais
dependem de sua política de importância e de evidência de sentido. Esta rodada
não altera o esquema do card para acomodá-las.
