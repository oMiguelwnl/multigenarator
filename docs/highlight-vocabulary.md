# Cards a partir de palavras e expressões

Há duas entradas para esse fluxo: uma lista `.txt` e destaques do Kindle.
Ambas usam o template `highlight_card`, com `SortIndex`, `Word`, `IPA`,
`Example Sentence`, `sentence_audio`, `Definition` e `Image` vazio.
Cada entrada precisa de correspondência no cache lexical configurado.
A definição é gerada com as evidências disponíveis, e o exemplo precisa
corresponder ao sentido escolhido e passar pelas validações de texto.

## Lista `.txt`

Prefira uma palavra ou expressão por linha:

```text
take off
in spite of
a
```

```bash
uv run multilang generate --language en --source word-list --input-file words.txt
```

Entradas repetidas são deduplicadas. Apóstrofos internos são preservados.
Se a expressão contém um separador como vírgula, coloque-a entre aspas:
`"hello, world"`. Listas densas e separadores continuam sendo aceitos;
uma entrada por linha evita ambiguidades.

## Palavras destacadas no Kindle

Use `--highlight-input vocabulary` quando cada destaque já for uma palavra
ou expressão que você escolheu estudar. Um destaque inteiro vira uma entrada;
ele não é dividido em palavras. Entradas repetidas, inclusive com diferenças
de maiúsculas ou espaços, contam uma vez.

Confira a prévia, que mostra apenas contagens:

```bash
uv run multilang preview-kindle-highlights --language en \
  --input-file "My Clippings.txt" --highlight-input vocabulary
```

Depois gere os cards:

```bash
uv run multilang generate --language en --source highlights \
  --input-file "My Clippings.txt" --highlight-input vocabulary
```

Também são aceitos exports HTML com `noteText`. Títulos e metadados do arquivo
de clippings não entram no vocabulário. No modo de vocabulário, o destaque
identifica a entrada; ele não é enviado como contexto de leitura para a frase.
A tradução de frase é dispensada nesse perfil de highlights, pois não faz
parte do card nem da sua validação. O áudio continua sendo o da frase.

A opção funciona também com `generate --webdav-remote-path` e
`fetch-webdav-highlights`. Informe o mesmo `--highlight-input vocabulary`
ao retomar um job com `--resume`. Trocar o modo de uma execução existente
é recusado; inicie outro job para mudar a interpretação da entrada.

O padrão `--highlight-input text` mantém a extração de palavras de trechos
de leitura. O caminho especializado de coreano continua usando esse modo.

## Expressões e revisão

O exemplo deve conter a expressão completa. Flexões contíguas podem ser
confirmadas por um modelo morfológico local disponível. Sem essa confirmação,
uma correspondência parcial não aprova a frase. Expressões separáveis podem
precisar de uma nova frase com a expressão contígua.

Os testes automatizados usam dados sintéticos e adaptadores controlados.
Uma amostra gerada com seus providers ainda deve ser revisada para avaliar
naturalidade das definições, frases, IPA e áudio.
