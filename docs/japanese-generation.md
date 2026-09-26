# Operação dos decks de japonês

O japonês tem três caminhos: frequência, kana e highlights. A frequência parte de um núcleo de 3.000 entradas em três níveis. **Esse número não limita o total de cartões de nenhuma língua**: vocabulário adicional, sentidos distintos e formas importantes podem ampliar o deck quando úteis e revisados. O plano e os critérios estão em [japanese-generation-plan.md](japanese-generation-plan.md).

Conte entradas lexicais e cartões separadamente. Cartões úteis de uma entrada existente ficam no nível dessa entrada, que pode ultrapassar 1.000 cartões. Novas entradas além do núcleo entram em expansões de frequência. Um sentido lexical distinto recebe identidade própria; ele não é cadastrado como simples flexão para alterar as contagens. Os comandos de congelamento abaixo continuam preparando o núcleo inicial.

## Fontes implementadas

| Uso | Fonte | Papel |
| --- | --- | --- |
| Ordenação proposta | TUBELEX-JA, tabela UniDic 3.1.0 base | Contagem agregada de palavras, vídeos e canais; comparação com wordfreq. |
| Evidência lexical | JMdict_e, EDRDG | Escritas, leituras, classes gramaticais, sentidos e restrições de combinação. |
| Análise local | Fugashi + UniDic explicitamente escolhido | Lema, forma flexionada, leitura, POS e posição exata no trecho. |
| Traços de kana | KanjiVG | SVGs verificados e recompostos, com ordem dos traços e atribuição. |
| Áudio | Azure Speech, ja-JP | Áudio real de palavras, frases e kana; cache por conteúdo, voz, localidade e formato. |

TUBELEX é a nova fonte candidata recomendada para frequência. O arquivo antigo `assets/frequency/ja/curated-v1.csv` continua sendo a versão ativa até a revisão e ativação de uma nova edição. Frequência de uma escrita não é frequência de um sentido: o programa não divide contagens entre leituras ou significados automaticamente.

JMdict usa CC BY-SA 4.0 e o procedimento de atualização/atribuição da EDRDG. KanjiVG usa CC BY-SA 3.0. A licença do software TUBELEX não é tratada como aprovação automática para redistribuir seus dados. Os arquivos baixados e os relatórios ficam separados do código e preservam seus hashes.

Fontes primárias: [TUBELEX](https://github.com/naist-nlp/tubelex), [avaliação publicada](https://aclanthology.org/2025.coling-main.641/), [JMdict](https://www.edrdg.org/wiki/JMdict-EDICT_Dictionary_Project.html), [termos EDRDG](https://www.edrdg.org/edrdg/licence.html), [Fugashi](https://github.com/polm/fugashi), [KanjiVG](https://github.com/KanjiVG/kanjivg), [Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts).

## 1. Adquirir e comparar frequência e dicionário

Execute na raiz do projeto, com as dependências do lockfile instaladas:

```bash
.venv/bin/python -m multilang.cli native vocabulary acquire ja lexical-supplement --root .multilang/japanese/sources
.venv/bin/python -m multilang.cli native vocabulary acquire ja frequency --root .multilang/japanese/sources
```

Cada comando informa o nome do arquivo, SHA-256, URL e recibo. `frequency --index 0` seleciona base; `--index 1` seleciona lemma. Mantenha essas variantes separadas. Nas instruções seguintes, os nomes em maiúsculas representam arquivos e hashes retornados pelos comandos, não valores para copiar literalmente.

```bash
.venv/bin/python -m multilang.cli native vocabulary prepare-japanese \
  JMDICT_XML_GZ JMDICT_SHA256 TUBELEX_TSV_XZ TUBELEX_SHA256 \
  .multilang/japanese/prepared --candidate-limit 6000
```

Para um piloto, use `--candidate-limit 100` e outro diretório de saída. A preparação exige um diretório novo. Para a variante lemma, acrescente `--frequency-variant unidic310-lemma`.

Arquivos principais:

- `candidates.jsonl`: candidatos de escrita/leitura/POS/sentido com proveniência; ainda sem identidade semântica aprovada.
- `frequency-comparison.json`: contagem, dispersão, ranking antigo e candidatos lexicais por palavra. Decisões começam pendentes.
- `source-diagnostics.json`: sentidos em quarentena por restrições incompatíveis no JMdict. Eles não recebem leituras inventadas.
- `manifest.json`: checksums, cobertura, limitações e quantidade de revisão necessária.

XML externo, entidades expansivas, caminhos simbólicos, arquivos alterados e limites excedidos são rejeitados. O TSV trata aspas como tokens literais. Prioridades `ichi/news/nf` do JMdict permanecem etiquetas; não viram contagens.

## 2. Revisar, congelar e conectar ao gerador

Use a revisão de vocabulário já existente:

```bash
.venv/bin/python -m multilang.cli native vocabulary review-template \
  .multilang/japanese/prepared jmdict-english SNAPSHOT_ID .multilang/japanese/review.json
```

Selecione sentidos, leituras e POS; atribua identidades semânticas estáveis; registre o revisor e os recibos verificáveis. Um ordinal de sentido do XML identifica evidência naquele snapshot, não uma identidade eterna. O perfil japonês de revisão deve declarar a fonte `jmdict-english`, normalização `nfc-preserve-1` e o analisador/versionamento efetivamente usado. Os comandos `review-payloads` e `compile-review` verificam os recibos pelo mecanismo de evidências do projeto; esta implementação não os assina automaticamente.

```bash
.venv/bin/python -m multilang.cli native vocabulary review-payloads REVIEW_JSON REVIEW_SHA256 PROFILE_JSON
.venv/bin/python -m multilang.cli native vocabulary compile-review \
  PREPARATION_DIR REVIEW_JSON REVIEW_SHA256 PROFILE_JSON COMPILED_DIR
.venv/bin/python -m multilang.cli native vocabulary export-japanese-cache \
  COMPILED_BUNDLE_JSON BUNDLE_FILE_SHA256 PROFILE_JSON NEW_CACHE_DIR
```

O cache resultante fica em `NEW_CACHE_DIR/lexicon/ja/lexical-index.json`. Configure `MULTILANG_LEXICON_DATA_DIR=NEW_CACHE_DIR/lexicon`. Ele guarda leituras, sentidos, aliases, hash do dicionário e atribuição. Homógrafos com evidência insuficiente continuam exigindo revisão.

Para uma nova edição de frequência, crie um JSON com **exatamente 3.000** escolhas distintas:

```json
[
  {"candidate_id": "ID_REVISADO_NO_JMDICT", "frequency_word": "学校"}
]
```

O exemplo mostra o formato de uma linha. Cada escolha deve corresponder a um candidato revisado e à palavra contada no TUBELEX. Não repita escritas ou contagens para multiplicar sentidos. A ordenação final é por contagem, dispersão em canais e escrita, sem preenchimento automático por palavras não revisadas.

```bash
.venv/bin/python -m multilang.cli native vocabulary japanese-frequency-review-payload \
  BUNDLE_JSON BUNDLE_FILE_SHA256 PROFILE_JSON SELECTION_JSON SELECTION_SHA256 TUBELEX_SHA256
.venv/bin/python -m multilang.cli native vocabulary freeze-japanese \
  BUNDLE_JSON BUNDLE_FILE_SHA256 PROFILE_JSON SELECTION_JSON SELECTION_SHA256 \
  TUBELEX_TSV_XZ TUBELEX_SHA256 SOURCE_RECEIPT_ID NEW_RELEASE_DIR
```

O recibo de finalidade `japanese-frequency-source` vincula a seleção e os dois snapshots à decisão de redistribuição. `freeze-japanese` gera o cache lexical, `curated-tubelex-jmdict-v1.csv`, o manifesto e a atribuição; valida os três níveis pelo leitor comum do produto. A aprovação das fontes não aprova automaticamente as frases e os áudios gerados.

Ative a edição pelas configurações do processo:

```bash
export MULTILANG_FREQUENCY_ASSETS_DIR=NEW_RELEASE_DIR/frequency
export MULTILANG_FREQUENCY_LIST_VERSION=tubelex-jmdict-v1
export MULTILANG_LEXICON_DATA_DIR=NEW_RELEASE_DIR/lexicon
.venv/bin/python -m multilang.cli generate --language ja --source frequency --level 1
```

Repita para os níveis 2 e 3. Use primeiro `--test-mode`. O fluxo comum continua responsável por definições, geração de exemplos, tradução, revisão, síntese e persistência. O comando `export-japanese` é a coleção demonstrativa antiga de 12 exemplos; ele não substitui esse fluxo de 3.000 entradas.

## 3. Kana

O padrão agora é **218 cartões**: 208 da base original e 10 lições de leitura. Há 109 por escrita. Os IDs dos 208 cartões foram preservados, inclusive após corrigir `dji/dzu` para `ji/zu`. As lições cobrem kana pequenos, duração, partículas e confusões visuais. O áudio de ん/ン usa o exemplo contextual “an”, indicado no cartão.

```bash
.venv/bin/python -m multilang.cli native vocabulary acquire ja kana-strokes --root .multilang/japanese/sources
.venv/bin/python -m multilang.cli export-kana \
  --stroke-dir KANJIVG_SNAPSHOT_DIR --stroke-manifest-sha256 MANIFEST_SHA256 \
  --output-path .multilang/japanese/kana.apkg
```

O download fixa um commit do KanjiVG, verifica os SVGs e informa cobertura. O exportador recompõe apenas geometria local segura, sem scripts ou recursos externos. `Strokes` contém a arte; `Gif` fica vazio nesta implementação estática. `Picture` permanece vazio para preenchimento manual.

Use `--prototype` para uma prévia explicitamente sem áudio e sem chamadas Azure. Use `--base-only` para omitir as dez lições. `--from DECK.apkg` mantém a importação de um pacote fornecido pelo usuário e não combina com as opções do gerador.

Produção exige credenciais Azure configuradas e MP3s decodificáveis. Uma falha impede a criação de um novo pacote incompleto. O cache válido é reutilizado ao retomar. O arquivo `.manifest.json` registra quantidade de cartões, áudio, voz, cobertura, atribuição e hash do APKG.

## 4. Highlights

```bash
.venv/bin/python -m multilang.cli generate --language ja --source highlights \
  --input-file HIGHLIGHTS_FILE --highlight-input text
.venv/bin/python -m multilang.cli generate --language ja --source highlights \
  --input-file HIGHLIGHTS_FILE --highlight-input vocabulary
```

`text` analisa palavras em contexto, resolve formas flexionadas para a base e mantém leitura, POS e posições de origem. `vocabulary` preserva expressões intencionais como 気を付ける e normaliza um verbo isolado flexionado quando a análise permite. Tokens desconhecidos e seleção lexical ambígua são relatados para revisão. Trechos privados não entram nos arquivos públicos de frequência.

O modelo de highlights japonês usa 11 campos, incluindo leitura, romaji e áudios de palavra e frase. A frequência conserva seus 12 campos. O modelo de highlights tem ID próprio: pacotes antigos com sete campos precisam de migração explícita de tipo de nota no Anki. O programa não altera automaticamente o tipo das notas antigas. `Image` continua manual e vazio.

```bash
.venv/bin/python -m multilang.cli export --job-id JOB_ID --format apkg
.venv/bin/python -m multilang.cli export --job-id JOB_ID --format tsv
```

## 5. Analisador e validação

O padrão local explícito é `unidic-lite`. Para uma instalação completa já adquirida, use `MULTILANG_JAPANESE_DICTIONARY=unidic` ou `MULTILANG_JAPANESE_DICTIONARY_PATH=/caminho/absoluto/do/dicionario`. Não há download ou troca silenciosa de modelo. O fingerprint inclui os arquivos reais do dicionário. A avaliação da variante TUBELEX UniDic 3.1.0 deve registrar qualquer diferença em relação ao analisador local.

Presença do alvo respeita fronteiras lexicais: `日` não é aceito apenas por estar em `日本`, e `生` não é aceito em `学生`. Leituras revisadas são usadas no furigana, romaji e SSML da palavra; a validação também verifica compatibilidade com o exemplo. Isso identifica incompatibilidades morfológicas, sem alegar comprovação automática do sentido.

O piloto local e os resultados automatizados ficam em `.multilang/verification/japanese-implementation/`. A versão de 3.000 cartões só deve ser publicada depois da seleção lexical, da decisão sobre fontes, da revisão de conteúdo/áudio e da conferência no cliente Anki.
