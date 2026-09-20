# Mandarim: template e fontes

Solicitado em 2026-09-20. Execução direta, sem GSD. `manda.png` é referência para
os recursos de leitura. Preferência posterior do usuário: manter o layout antigo.

## Objetivo e contrato

Preservar o layout original de mandarim: palavra, pinyin e tradicional no topo;
definição e imagem opcional no meio; exemplo e tradução abaixo. A frase em
tradicional fica em uma seção própria mais abaixo, com divisória e título.
A tradução fica imediatamente após a frase. Não exibir a linha de pinyin completo
abaixo da tradução; o campo continua salvo para produzir o pinyin sobre os caracteres.
Manter os áudios ao lado da palavra e da frase, a tipografia, as dimensões
e o fundo da base `normal_card` tanto para frequência quanto para listas pessoais.
A frase recebe pinyin sobre cada caractere e cores por tom. Os rótulos e a política
padrão de novos conteúdos usam português; a tradução continua sendo revelada no
verso.

Preservar os 12 nomes/ordem dos campos, os IDs do modelo, GUIDs, snapshots e a
estrutura de três níveis de 1.000. `Pinyin` continua sendo a leitura da palavra;
`Sentence Pinyin`, a da frase. Leituras armazenadas com acentos ou números são
aceitas; a anotação visual usa acentos. A exportação usa a leitura salva, sem
consultar provedores nem recalcular a pronúncia. Anotação incompatível com a
frase deve impedir a exportação, em vez de deslocar sílabas silenciosamente.

## Plano de execução

- [x] Comparar fontes com o contrato Multilang: ranking separado de identidade
  lexical, sentidos, leituras e revisão; registrar recomendação e limites.
- [x] Cobrir com testes a frase da imagem, cinco tons, polifonia, pontuação,
  escaping, leituras incompatíveis e exportações legada/nativa/APKG/CSV/TSV.
- [x] Implementar renderização estática segura com `pypinyin` existente,
  `<ruby>/<rt>` e CSS; preservar leituras congeladas e cloze sem revelar pinyin.
- [x] Manter os recursos de leitura da referência, restaurar o layout antigo
  conforme a preferência posterior e usar a política padrão de mandarim em PT.
- [x] Atualizar os fixtures de integração para o contrato atual de revisão de
  definições/traduções, mantendo as verificações de produção.
- [x] Executar regressões pertinentes, gerar uma prévia local reproduzível e
  inspecionar a apresentação em desktop e tela estreita.

## Fontes: decisão

`wordfreq:zh` é uma base compatível para candidatos e ordenação inicial. Não há
evidência de que seja a melhor fonte única para o Core Multilang. Seus dados são
um retrato até aproximadamente 2021 e a normalização chinesa junta grafias
simplificadas/tradicionais. Isso não fornece identidades lema/POS/sentido/leitura.
O asset atual tem 3.000 linhas (1.000 por nível), todas com POS `unknown` e
`definition_seed` igual à palavra: são candidatos, não 3.000 identidades aprovadas.

Recomendação para este projeto:

| Papel | Fonte | Limite |
| --- | --- | --- |
| Ranking inicial multilíngue | wordfreq, versão congelada | Não inferir POS, sentido nem pronúncia do rank. |
| Evidência lexical | Wiktionary via Wiktextract/Kaikki, já previsto no catálogo | Usar JSONL bruto da edição inglesa; os downloads pós-processados estão depreciados. Admitir apenas registros explicitamente de mandarim, com POS/sentido e proveniência. |
| Complemento de grafia/leitura | CC-CEDICT | Tem simplificado, tradicional, pinyin e glosas; não oferece POS uniforme nem IDs estáveis de sentido. Não substituir o ranking pela ordem do dicionário. |
| Comparação de frequência em diálogo | SUBTLEX-CH | Corpus de legendas; avaliar cobertura e viés antes de substituir ou combinar rankings. |

Manter o ranking existente nesta implementação. A substituição de uma lista exige
comparação mensurada de cobertura, homógrafos, sentidos e utilidade pedagógica.
O trabalho de template não aprova nem redistribui automaticamente novos dumps,
nem equivale à geração/revisão dos 3.000 cartões finais.

Fontes primárias consultadas:

- [wordfreq: fontes e normalização chinesa](https://github.com/rspeer/wordfreq)
- [wordfreq: data snapshot e manutenção](https://github.com/rspeer/wordfreq/blob/master/SUNSET.md)
- [Kaikki: sentidos, POS e recomendação de dados brutos](https://kaikki.org/dictionary/Chinese/)
- [CC-CEDICT: conteúdo e licença CC BY-SA 4.0](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)
- [SUBTLEX-CH: estudo dos autores](https://biblio.ugent.be/publication/1045459)
- [pypinyin: estilos e dicionários de frases](https://github.com/mozillazg/python-pinyin)
- [OpenCC Python: conversão s2t](https://github.com/yichen0831/opencc-python)
- [pinyin-pro: alternativa JavaScript com ruby](https://pinyin-pro.cn/en/use/html.html)

## Evidência de execução

### Bibliotecas e apresentação

| Requisito | Implementação |
| --- | --- |
| Campo Pinyin | `pypinyin==0.55.0`, já instalado, com dicionário de frases. |
| Leitura sobre a frase e cores | HTML `<ruby>/<rt>` + CSS dos cinco tons; conversão de tons pelo mesmo `pypinyin`. Não é necessária uma biblioteca JavaScript adicional. |
| Palavra e frase tradicionais | `opencc-python-reimplemented==0.1.7`, configuração `s2t`, já instalada. |
| Layout antigo restaurado | Palavra/pinyin/tradicional, definição, imagem opcional e bloco do exemplo; áudios laterais e tradução no verso. O visual deriva de `normal_card`, com acréscimo apenas do suporte de leitura. |
| Exportadores | APKG e CSV/TSV legados e notas semânticas nativas compartilham a mesma renderização de mandarim. |
| Cloze | O trecho oculto inclui seus caracteres e suas leituras; o pinyin do alvo não aparece na pergunta. |

A anotação preserva a leitura salva, aceita tons marcados ou numéricos, escapa o
texto e interrompe a exportação quando a leitura não se alinha à frase. Números
literais após sílabas neutras são preservados (`看了2次` / `kàn le2 cì`).
Bibliotecas automáticas não substituem a revisão de leituras polifônicas e
conversões tradicionais dependentes do contexto.

### Legibilidade e significado das cores

A hierarquia geral do layout antigo permanece. O bloco do exemplo contém
`Example Sentence` e, imediatamente abaixo, `Translation`, revelada no verso.
`Traditional Sentence` aparece em outra seção, com divisória e título “Tradicional”.
O pinyin completo da frase deixa de aparecer como linha adicional; seu valor
continua em `Sentence Pinyin` para gerar as anotações sobre os caracteres.
A frase usa 26 px, com pinyin de aproximadamente 15,6 px acima dos caracteres.
A tradução foi ampliada de 16 para 18 px. Essas mudanças mantêm os 12 campos e
a geração existentes.

O exportador lê `Sentence Pinyin`, alinha uma sílaba a cada Han e aplica a cor do
tom: 1 vermelho, 2 amarelo, 3 verde, 4 azul e neutro cinza. O caractere e sua
leitura recebem a mesma cor. Não há classificação de palavras/POS por cor.
Na referência atual, `他下载了很多电影。` corresponde aos tons
`1, 4, 4, 5, 3, 1, 4, 3`.

Essa verificação comprova o mapeamento de tons e o alinhamento; não constitui
revisão linguística independente de toda leitura. `tonal_pinyin` usa
`tone_sandhi=False`: o projeto não aplica uma política completa de mudanças de
tom na fala. Há leituras contextuais já presentes no dicionário de frases, como
`yí gè rén` e `bú shì`, enquanto `你好` sai como `nǐ hǎo`. A biblioteca documenta
[correções por dicionários e a opção de sandhi](https://pypinyin.readthedocs.io/zh-cn/master/usage.html).

Cartões antigos com pinyin salvo continuam compatíveis com a geração e o esquema.
Para anotar notas já importadas no Anki, é necessário reexportar/atualizar o
conteúdo de `Example Sentence`; trocar apenas o CSS não insere o HTML de ruby.

Foram atualizados apenas os fixtures de revisão dos testes: pares explícitos de
frase/tradução/definição e MP3 silencioso decodificável. As exigências de revisão
de produção permanecem. O áudio da prévia é apenas ilustrativo.

Durante a validação, uma alteração paralela do registro de IDs para japonês
passou a bloquear qualquer exportação pelo scanner de chaves dinâmicas. A busca
foi ajustada para percorrer somente registros prealocados, como os outros
resolvedores existentes; os valores e contratos dos IDs foram preservados.

### Reprodução e auditoria

Gerar a prévia com:

```sh
.venv/bin/python scripts/preview_mandarin_card.py
```

Artefatos em `output/previews/mandarin/`:

- `front.html` e `back.html`: frente e verso usando o template real;
- `front-1280.png`, `back-1280.png`, `front-390.png`, `back-390.png`,
  `front-320.png` e `back-320.png`: imagens da inspeção visual;
- `browser-check.json`: alinhamento dos oito caracteres/leituras, cores,
  ausência de transbordamento e tradução oculta/revelada;
- `cloze.html`, `cloze.png` e `cloze-check.json`: pergunta gerada pelo modelo
  semântico real, com caractere em tamanho zero, leitura oculta e marcador visível;
- `source-audit.json`: contagem por nível, proveniência, POS e versões instaladas;
- `regression.xml`: resultado da rodada inicial de regressão;
- `layout-restored-tests.xml`: resultado da verificação após restaurar o layout antigo;
- `readability-tests.xml`: 71 testes aprovados após os ajustes de legibilidade,
  incluindo ortografia, cores/alinhamento, templates e modelos Anki.

A mudança da tradução para imediatamente abaixo da frase passou nos mesmos
71 testes; o resultado está em `output/reports/mandarin/translation-order-tests.xml`.
As prévias foram regeneradas, e o Chromium verificou a ordem dos elementos e
suas posições em 1280, 390 e 320 px, com tradução oculta na frente e visível no verso.

O ajuste posterior separou a frase tradicional em sua própria seção, removeu a
linha visível de `Sentence Pinyin` e ampliou a tradução para 18 px. Os 71 testes
passaram em `output/reports/mandarin/traditional-section-tests.xml`; a checagem
visual também confirma a seção separada, o tamanho da tradução e a ausência da
linha repetida, preservando o pinyin sobre os caracteres.

O asset `assets/frequency/zh/curated-v1.csv` foi mantido: SHA-256
`2f7eb1f2402fbc8bc52566bc5d09ee22b5022808fc226e5a1c69ab4e0fdaba2d`.
As 3.000 linhas têm `source_provenance=wordfreq:zh`, POS `unknown` e
`definition_seed=display_form`. A recomendação lexical está alinhada ao contrato
descrito em `docs/multilingual-completion-design.md` e
`docs/multilingual-source-research.md`; esta entrega não importa novos dumps.

Após restaurar o layout antigo, **60 testes passaram** em
`layout-restored-tests.xml`: carregamento dos templates, renderização de mandarim
e contrato dos modelos Anki de frequência/listas pessoais. `ruff check` e
`git diff --check` também passaram. As prévias foram regeneradas com o layout
restaurado.

Antes da preferência pelo layout antigo, **92 testes passaram** na rodada registrada em `regression.xml`
(391 segundos): integração de mandarim, renderização, exportação tabular,
registro de IDs e notas semânticas. A rodada de renderização e carregamento de
templates também passou, com 58 testes. `ruff check` e `git diff --check` passaram.
As verificações foram locais, sem chamadas pagas a provedores. Frente e verso
foram verificados em 1280, 390 e 320 px, com imagens inspecionadas.

Comando da rodada inicial:

```sh
MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
.venv/bin/python -m pytest -q \
  tests/integration/test_mandarin_modern_flow.py \
  tests/services/test_mandarin_rendering.py \
  tests/services/test_export_tabular_bundle.py \
  tests/services/test_anki_id_registry.py \
  tests/services/test_semantic_anki_fields.py \
  --junitxml=output/previews/mandarin/regression.xml
```

Revisão visual em Chromium e inspeção de pacote não equivalem à aceitação no
aplicativo Anki/AnkiDroid/iOS.
