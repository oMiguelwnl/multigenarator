# Piloto completo e revisão dirigida

Esta entrega acrescenta revisão dirigida de decisões, correções por ocorrência, geração de conteúdo com julgamento separado, importação de áudio verificado e exportação de um piloto Anki. Os campos dos cards permanecem iguais: nove no piloto PT, com `Image` vazio. Os contratos existentes de japonês e mandarim continuam separados.

## Resultados do português

Os dois registros de **beber** passaram por uma nova revisão conjunta e agora compartilham a mesma identidade e glosa. A distinção entre construção transitiva e intransitiva permanece nas fontes. O rascunho resultante contém **128 mapeamentos lexicais, sem conflito de identidade, e 11 mapeamentos de formas**.

A campanha conserva 139 acordos, duas rejeições e três dúvidas nos registros antigos. As dúvidas são o registro genérico de **trabalho**, a agregação dos contextos de **grandes** e a interpretação da forma **veja**. Uma decisão inconclusiva não é convertida em aprovação apenas para encerrar a fila.

Em separado, proposta e julgamento concordaram sobre **seis projeções por ocorrência**:

| Ocorrência | Projeção |
|---|---|
| aberto, CF41-4 | Adjetivo, lema `aberto`, conservando a análise original `abrir/VERB` no histórico |
| boa, CF22-1 e CF31-2 | Sentido quantitativo e avaliação de compra separados |
| grandes, CF7-1 e CF24-3 | Escala institucional e magnitude do dano separados |
| veja, CF35-5 | Interpretação funcional imperativa explicitamente editorial; a fonte UD e o modelo original registram `Mood=Sub` |

As seis projeções têm texto e posições originais, origem máquina e nova medição. Não substituem o corpus nem se apresentam como uma nova saída do Stanza. O denominador permanece **2918 tokens**. A leitura de `newdoc_id` recuperou **48 documentos na amostra**, reutilizando exatamente as 200 análises congeladas, sem executar o modelo novamente.

## Importância: resultado e limites

A rubrica integral ainda não dispõe das **66 notas justificadas**: seis critérios para cada uma das onze formas com acordo. Falta preparar evidência adequada de regras/paradigmas, currículo, relações de pré-requisito, pronúncia e resultados de aprendizes. Ausência permanece desconhecida; não recebe nota zero nem é preenchida com alunos simulados.

Foi executada uma política exploratória que usa somente frequência medida. A grade e os custos de erro foram congelados antes da avaliação: pesos `frequency=1`, limiares `0, 0.4, 0.5, 0.75, 0.9, 1`, custo de falso positivo 2 e falso negativo 1, mínimo de uma ocorrência e diagnóstico de análise pelo menos 0,9.

| Conjunto | Revisão aproveitável | Resultado da política escolhida |
|---|---:|---|
| Calibração | 11 formas: 2 positivas, 9 negativas | Limiar 1; nenhuma seleção; 2 falsos negativos, 9 verdadeiros negativos |
| Avaliação separada | 14 acordos positivos entre 29 formas; 15 abstenções | Nenhuma seleção; 14 falsos negativos |

Essas métricas medem concordância com avaliações de máquina, não acurácia linguística comprovada. A avaliação não tem negativos consensuais e não constitui uma amostra equilibrada. Os resultados não autorizam promover essa política a produção. O corpus de teste não foi usado para escolher candidatos de frequência ou ajustar os limiares; possíveis interseções de pré-treinamento dos modelos continuam desconhecidas.

## Piloto de conteúdo e áudio

O lote contém **casa, tempo, dia, vida, mundo, água, livro, cidade, amigo e comer**. Definições e traduções estão em inglês, como determina o perfil PT existente; exemplos e áudio estão em português brasileiro. A IPA foi copiada dos candidatos da variante `Brazil` e não foi produzida pelo modelo.

Os dez conteúdos passaram por julgamento separado e análise morfológica local com cobertura completa do exemplo. Quatro frases foram simplificadas porque o analisador não conseguia alinhar todas as contrações; as primeiras respostas permanecem arquivadas. A revisão não certifica todos os conceitos da frase nem strict-i+1.

O usuário autorizou um lote de até vinte sínteses e quinhentos caracteres no Azure, sem repetição automática. A execução concluiu **20 sínteses, 384 caracteres**, usando `pt-BR-FranciscaNeural`. A voz é listada na [documentação oficial de idiomas do Azure](https://learn.microsoft.com/pt-br/azure/ai-services/speech-service/language-support?tabs=tts). A tarifa da conta e o custo faturado não foram consultados. O modelo interno do serviço permanece identificado como não informado; a versão instalada do SDK consta nas assinaturas.

Conteúdo e áudio têm estado nativo `pending`; o pacote é uma edição local de protótipo do inventário Expansion, sem rank Core. Não foram criados recibos humanos, licenças ou qualificações fictícias.

O APKG foi exportado e a repetição da exportação reutilizou o mesmo manifesto. A verificação confirmou ZIP válido, SQLite íntegro, **10 notas, 10 cards, 10 GUIDs distintos, 20 áudios referenciados e decodificáveis com sinal não silencioso, e 10 campos `Image` vazios**. O SHA-256 do pacote é `bda47ffe8a7f1d9e6606c70c5167349ae4688ad94566689b021229993b93bcaf`. A abertura nos clientes Anki desktop e móvel ainda não foi verificada; integridade de mídia não certifica a pronúncia pelo ouvido.

### Correções após avaliação do piloto

O primeiro pacote não aplicava a regra existente de classe gramatical em `Definitions`. A exportação agora usa a classe do mapeamento lexical e a mesma política de definições do produto: por exemplo, `noun: House; a building where people live.` e `verb: To eat; to consume food.`. Rótulos existentes incompatíveis são rejeitados. Propostas e julgamentos anteriores permanecem intactos; a apresentação derivada é identificada no relatório e no binding da exportação.

O pacote corrigido está em `.multilang/verification/pilot-feedback/export-definitions/pilot.apkg`, com SHA-256 `ae7a60781aa1c0ff9207d2175f1087f3b77f4fa927649e9dc699e8d88dc29236`. A comparação com o anterior confirmou que somente `Definitions` mudou: os nove campos, os dez GUIDs e os vinte arquivos de áudio foram preservados.

Para a nova leitura de palavras, o plano usa SSML `prosody` com `rate="-15%"` e `volume="+20%"`, sem alterar pitch. Esse controle é suportado pelo [SSML do Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice#adjust-prosody). A assinatura de cada palavra muda para evitar reaproveitamento do áudio antigo; as assinaturas das frases permanecem iguais. O adaptador foi corrigido para preservar a prosódia do SSML completo até o SDK, validando voz, locale e marcação permitida.

Essa nova síntese ainda não foi executada. O preflight em `.multilang/verification/pilot-feedback/word-audio-preflight.json` contém dez chamadas, 46 caracteres de texto, sem repetição automática, e reutilização dos dez áudios de frases. O orçamento anterior foi consumido; a execução exige nova autorização para esse lote. A contagem de texto não é uma apuração dos caracteres faturáveis nem do preço da conta. A duração e a nitidez percebidas devem ser conferidas na nova gravação.

A regressão desta correção passou em **66 casos distintos** no checkout isolado, incluindo a borda do SDK Azure, a exportação APKG e a CLI do piloto. Ruff e formatação também passaram.

## Comandos adicionados

Os comandos ficam em `multilang vocabulary qualification ai`:

| Comando | Função |
|---|---|
| `prepare-revision` | Selecionar decisões pendentes, conflitos completos ou notas a revisar, vinculando o estado atual e os suplementos |
| `consolidate` | Aceitar rodadas anteriores e planos dirigidos; rejeitar decisões ultrapassadas e cobertura incompleta |
| `prepare-observation-revision` | Preparar revisão dos tokens de ocorrências exatas |
| `apply-observation-revision` | Aplicar somente acordos, conservar o original e recalcular as medidas |
| `pilot-prepare` | Selecionar mapeamentos sem conflito e IPA da variante exata |
| `pilot-request` / `pilot-import` | Preparar e importar conteúdo de proposta/julgamento com metadados do executor |
| `pilot-complete` | Vincular os dois pareceres e a análise real de cada exemplo |
| `pilot-audio-plan` | Preparar assinaturas de palavra e frase com texto, voz, locale e versão declarados |
| `pilot-export` | Exigir duas mídias verificadas por card e produzir o APKG modelo B de protótipo |
| `prepare-languages` | Verificar fontes/perfis publicados e preparar até dez lemas distintos por idioma |

`prepare-revision` recebe `CAMPAIGN SHA CONFIG SHA OUTPUT`. Os outros comandos novos recebem `INPUT_JSON SHA OUTPUT`. Os schemas dos arquivos de configuração estão em `qualification_revision_cli.py`, `qualification_pilot_cli.py` e `qualification_languages_cli.py`. Referências externas são `{ "path": "...", "sha256": "..." }`; o SHA fornecido na CLI é dos bytes do arquivo.

O piloto não chama provedores durante preparação/importação/exportação. A síntese real desta execução utiliza `NativeAudioService` e o adaptador Azure existente, com um registro persistente de tentativas, limite de consumo e ausência de repetição automática. A autorização desse lote não vale para novos lotes ou outros idiomas.

Campanhas antigas continuam no schema 1. Campanhas com revisão dirigida usam schema 2. Planos dirigidos conservam a seleção, o estado anterior e as fontes adicionais; a consolidação relê os suplementos pelos hashes declarados. Esses arquivos precisam permanecer disponíveis no caminho informado para reproduzir a consolidação. As observações originais, análises, contagens e resultados anteriores não são sobrescritos.

## Expansão por idioma

O inventário cobre os **22 idiomas modernos e o caminho separado de Latim**. Cada lote contém os candidatos, trechos, pronúncias declaradas na fonte, hashes e pedido de revisão. Os modelos são inventariados a partir do snapshot existente; sua mera presença não é revalidada como qualificação de idioma.

Foram preparados dez candidatos por idioma em **21 idiomas, totalizando 210 itens**: PT, ES, EN, FR, DE, EL, IT, PL, TR, RO, RU, NL, DA, NB, SV, FI, HU, CS, JA, ZH e KO. Croata (`hr`) permanece bloqueado por falta de IPA admitida nas fontes disponíveis. Latim (`la`) conserva o pipeline próprio.

PT exige a variante brasileira. ZH exige as marcações de mandarim e chinês padrão; a notação tonal sobrescrita só é admitida quando a fonte também declara `Sinological-IPA`. O texto fonético é preservado, sem conversão silenciosa para outra notação. Isso prepara a revisão, não atesta a pronúncia.

Ausência de fonte, incompatibilidade da variante ou ausência de IPA admitida bloqueiam o lote. Ter um lote preparado não significa que seus dez itens foram revisados, nem que existem três mil cards prontos naquela língua. As capacidades de produção e a permissão de redistribuição permanecem desligadas.

## Verificação e trabalho restante

As verificações isoladas cobrem **179 casos distintos**, usando a execução mais recente de cada caso nas suítes de regressão. Foram verificados revisão dirigida, proveniência, projeção por ocorrência, importação de conteúdo, mídia, exportação e preparação multilíngue, inclusive a rejeição de mudanças no catálogo entre preparação e exportação. Ruff e formatação passaram, assim como o build de wheel/sdist e a documentação em modo estrito. A revisão independente também conferiu o APKG e as evidências reais do português. Esses testes não representam a suíte completa das alterações concorrentes do repositório.

Para avançar da preparação à qualificação:

1. Vincular evidências reais às 66 avaliações ausentes da rubrica de importância e repetir calibração/avaliação com amostras adequadas. Dados de aprendizes continuam necessários para critérios que dependem deles.
2. Resolver as três dúvidas PT com fontes que distingam os sentidos e as funções relevantes, conservando os resultados inconclusivos anteriores.
3. Executar proposta e julgamento dos novos lotes por idioma; obter uma fonte de IPA para croata e conservar o caminho próprio de Latim.
4. Gerar e revisar conteúdo/áudio dos lotes aceitos com orçamento próprio; conferir os pacotes nos clientes Anki e cumprir os critérios existentes de produção e redistribuição.

## Artefatos locais

As evidências desta execução estão em `.multilang/verification/ai-completion/`:

- `pt-campaign/`, `pt-draft/`: histórico consolidado e rascunho sem o conflito de `beber`.
- `pt-observation-derived/`: originais, seis decisões, projeções e novas medidas.
- `pt-importance-calibration/` e `pt-importance-evaluation/`: política, rótulos, métricas e abstenções reproduzíveis.
- `pt-pilot/content/`, `pt-pilot/audio-plan/` e `pt-pilot/azure/`: conteúdo, vinte assinaturas, áudio real e registro de tentativas.
- `pt-pilot/export/`: pacote completo, cards e manifesto de exportação; `pt-pilot/package-verification.json` registra a conferência estrutural e das mídias.
- `languages-v2/`: inventário e pedidos por idioma; revisões posteriores usam novas saídas.
- `before.json`, `owned-paths.json` e XMLs: estado inicial, isolamento de alterações e resultados dos testes.

Os dados de fontes e os áudios permanecem locais. Os commits desta entrega contêm código, testes e documentação; não publicam o corpus nem habilitam deploy.
