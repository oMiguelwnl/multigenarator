# Preparação linguística e revisão do vocabulário

Os nomes e a ordem dos fields Anki são preservados. A entrada linguística é um
registro interno que distingue idioma, lema, classe gramatical, sentido e formas
observadas. Ela não acrescenta campos ao cartão.

## Preparar arquivos sem gerar cartões

Para consolidar preparados existentes e deixar a geração para depois:

```bash
uv run --no-sync multilang native vocabulary prepare-deck-inputs \
  REQUEST.json REQUEST_SHA256 output/reports/vocabulary-preparation/NEW_RUN
```

O request declara todos os idiomas esperados, arquivos de candidatos e hashes,
prioridades de preparação e, opcionalmente, corpora apenas para diagnóstico.
O contrato está em `services/deck_preparation.py`. A saída precisa ser nova;
somente é publicada quando todos os idiomas terminam sem erro.

Cada idioma recebe `vocabulary.json`, `forms.jsonl` e `report.json`. O pacote
inclui resumo, request reproduzível e manifesto de integridade. Os lemas e
classes são agrupados preservando caixa, acentos e sentidos alternativos.
Prioridade de superfície não é frequência de um sentido nem currículo revisado;
bandas propostas não aprovam automaticamente 3.000 entradas. Formas candidatas
não são cartões selecionados. O latim mantém seu percurso clássico separado.

O comando não chama LLM, tradução, áudio, banco ou exportador Anki e não lê o
`.env` para executar provedores. A disponibilidade literal de lemas num corpus
de diagnóstico, quando calculada, usa toda a base candidata e não certifica a
meta de 90% em fala ou escrita. Anotações ausentes entram como não cobertas.

### Revisar pela sessão atual, sem API de provedor

O script `scripts/review_vocabulary_in_session.py` permite ao assistente revisar
os arquivos pela sessão atual do ChatGPT/Codex. Ele não lê o `.env`, não executa
outro agente e não chama OpenRouter, OpenAI API, tradução, áudio ou geração.
O processamento do assistente continua sujeito aos limites da sessão/plano;
a assinatura não é convertida em chave de API do projeto.

O comando `next` verifica o manifesto dos pacotes, reutiliza um pedido pendente
ou exporta o próximo subconjunto ainda não revisado. O assistente lê as evidências
em `request.json` e produz uma resposta com os índices exatos de sentidos e
formas. O comando `import` valida essa resposta e grava uma proposta imutável.
Uma correção usa `--supersedes DIRETORIO_DA_REVISAO_ANTERIOR`, preservando o
histórico e exigindo o mesmo pedido e as mesmas fontes. Correções concorrentes
não são resolvidas silenciosamente pela data do arquivo.

```bash
.venv/bin/python scripts/review_vocabulary_in_session.py next \
  --packets CAMINHO_DOS_PACOTES --manifest-sha256 HASH_DO_MANIFESTO \
  --requests PEDIDOS --reviews REVISOES --language ja --batch-size 8

.venv/bin/python scripts/review_vocabulary_in_session.py import \
  --request PEDIDO --request-sha256 HASH_DO_PEDIDO --response RESPOSTA.json \
  --context-id IDENTIFICADOR_DA_SESSAO --output NOVA_REVISAO

.venv/bin/python scripts/review_vocabulary_in_session.py report \
  --packets CAMINHO_DOS_PACOTES --manifest-sha256 HASH_DO_MANIFESTO \
  --requests PEDIDOS --reviews REVISOES --output NOVO_RELATORIO
```

`report` reconstrói as decisões a partir das respostas, confere os pedidos
contra os pacotes originais e conta cada unidade apenas uma vez. Mantém separados
grupos de lema/classe, fragmentos de revisão, candidatos de sentido e pares de
forma/sentido. Não converte esses números em cartões finais ou porcentagem de
cobertura. As propostas possuem `production_eligible=false` e não substituem
a importação de um inventário validado. A geração permanece adiada.

### Validação de dificuldade antes da geração futura

`SentenceCurriculum`, quando anexado à proveniência de uma entrada, acompanha
tanto geração como regeneração. A validação usa análise contextual local, com
hash do modelo e da frase, lema/classe do alvo, vocabulário previamente
introduzido, características morfológicas permitidas e limites de unidades
lexicais. Uma análise ausente, alterada ou incompleta reprova essa validação.
Espaços ou caracteres japoneses não substituem a contagem de unidades analisadas.

O contrato não certifica domínio do aluno, desambiguação de sentidos ou
naturalidade. A sequência preparatória ainda usa ordem provisória de fontes;
não ativa automaticamente o currículo em todos os cartões. É necessário concluir
a curadoria e qualificar as análises e os limites por idioma antes dessa ativação.

Esses arquivos são uma entrada para revisão; não substituem o bundle aprovado
de `import-reviewed-vocabulary`. A proposta de política de frases é registrada
com ativação desligada. Na solicitação atual, conteúdo e decks ficam adiados até
o usuário retomar explicitamente a geração.

O [fluxo de qualificação](linguistic-qualification.md) acrescenta medição de
frequência/dispersão, revisão em HTML local, calibração com decisões autenticadas
e pilotos por língua. O formulário permite salvar decisões e retomá-las depois.

| Cartão ilustrativo | Palavra exibida | Informação interna |
|---|---|---|
| Verbo na forma de referência | `go` | Lema `go`, verbo, sentido de deslocamento |
| Forma importante no passado | `went` | Mesmo sentido, forma observada, passado |
| Outra forma importante | `gone` | Mesmo sentido, outra análise e contexto |

As formas só viram cartões quando a política de importância e suas evidências
forem revisadas. Não são produzidas todas as conjugações automaticamente. Cada
forma tem significado, explicação e áudios adequados àquela ocorrência. A ligação
com o lema e os identificadores ficam no banco e no manifest. `Image` fica vazio.
O Core contém 3000 identidades por língua, em três níveis; as formas importantes
aprovadas são cartões adicionais no nível do lema, conforme o plano mestre.

## Bibliotecas e idiomas

```bash
uv sync --locked --extra dev --extra nlp
uv run --no-sync multilang native vocabulary sources
uv run --no-sync multilang native vocabulary models
```

O extra `nlp` instala Stanza e PyTorch para CPU. O runtime usa Stanza em 19
línguas europeias e no chinês simplificado, Kiwi no coreano e Fugashi/UniDic no
japonês. Os 22 códigos são `pt es en fr de it pl tr ro ru nl ko da nb sv fi hu cs
hr el ja zh`. Latim continua com seu caminho próprio. A instalação do modelo
ocorre somente por comando explícito:

```bash
uv run --no-sync multilang native vocabulary prepare-model pt
```

Estão fixados o manifest Stanza 1.10.0, seu SHA-256, processadores e dependências.
Os bytes instalados também recebem hashes. Disponibilidade local não ativa um
perfil. A análise normal não baixa modelos e recusa modelos ausentes ou alterados.

A [seleção e comparação de modelos](morphology-model-comparison.md) permite
preparar alternativas por idioma e medir seus resultados na mesma amostra antes
de alterar a configuração.

## Fontes reais e preparação

O [catálogo pesquisado](multilingual-source-research.md) contém URLs e condições
de uso por língua. Wiktextract fornece lemas, classes, possíveis sentidos,
exemplos, formas e pronúncias. O croata usa Croatian Wordnet ligado aos synsets
exatos de Princeton WordNet 3.0. UD fornece frases anotadas para diagnóstico.

```bash
uv run --no-sync multilang native vocabulary acquire en dictionary
uv run --no-sync multilang native vocabulary acquire pt corpus-test
```

O primeiro comando baixa o arquivo compartilhado de todas as línguas, uma vez.
O resultado informa nome e SHA-256 do arquivo local. `split-dictionary` separa
os registros por língua em uma única passagem. Consulte `--help` para os
argumentos posicionais. A seleção inicial usa `wordfreq`; ela não define sentidos
nem o ranking final. Maiúsculas e acentos originais são preservados.

Exemplo com a partição portuguesa já adquirida nesta entrega:

```bash
uv run --no-sync multilang native vocabulary prepare pt \
  .multilang/verification/real-languages/dictionaries/pt.jsonl \
  a71bc171d61eda9eb24fa942bfbc323b007133eecbfd307d074400027a638ed3 \
  .multilang/vocabulary/pt-example --seed-words 6000
```

O diretório de saída deve ser novo. Para incluir corpus, forneça `--corpus`,
`--corpus-sha256` e a divisão `--corpus-split`. Corpus de teste não pode alimentar
o ranking. Croata exige `--dictionary-format croatian-wordnet`, `--glosses` e
`--glosses-sha256`; as duas fontes ficam vinculadas ao manifest.

A preparação escreve `candidates.jsonl`, `review.jsonl`, `sources.json`,
`manifest.json` e, quando fornecido, o corpus de referência. Todos os sentidos
começam pendentes. Limites de bytes, expansão, linhas, tokens, registros e saída
agregada impedem arquivos excessivos; uma falha não publica resultado parcial.
Lotes que excedam o limite podem ser divididos por conjuntos explícitos de lemas,
preservando todos os sentidos e formas desses lemas.

## Entrada de revisão e importação

```bash
uv run --no-sync multilang native vocabulary review-template \
  .multilang/vocabulary/pt-example SOURCE_ID SOURCE_VERSION review.json
```

`SOURCE_ID` e `SOURCE_VERSION` são identificadores declarados pelo responsável
pela fonte. O perfil precisa autorizar esse `SOURCE_ID`. O template contém hashes
dos registros originais, lema, classe, decisão pendente e sentido ainda vazio.
O revisor associa a evidência a um sentido estável. Posição na lista de frequência
e hash do registro não são usados como substitutos de sentido.

Uma forma observada também informa frase exata, posição inicial/final, análise
morfológica, modelo usado e vínculo revisado com o sentido. Para inspecionar uma
frase em arquivo UTF-8 NFC:

```bash
uv run --no-sync multilang native vocabulary analyze en sentence.txt
```

O resultado separa texto (`went`), lema (`go`), POS e traços (`Tense=Past`), quando
a análise os sustenta. Contrações sem alinhamento exato ficam inconclusivas;
não são resolvidas por cortar sufixos ou procurar substrings. Ambiguidade de
sentido exige evidência adicional.

`VocabularyReview` reúne decisões de sentidos, observações, agregações e política
de formas importantes. Agregações nomeiam ocorrências distintas; analisar de
novo a mesma ocorrência não aumenta a contagem. A contagem declarada precisa
corresponder à evidência autenticada, e todos os itens selecionados são preservados.

```bash
uv run --no-sync multilang native vocabulary review-payloads \
  review.json REVIEW_SHA256 profile.json
uv run --no-sync multilang native vocabulary compile-review \
  PREPARATION_DIR review.json REVIEW_SHA256 profile.json COMPILED_DIR
```

Os nomes em maiúsculas são argumentos a substituir pelos caminhos, identificadores
e SHA-256 obtidos nos arquivos. `profile.json` é um `LanguageProfile` com fonte,
normalização e versões explícitas. O comportamento contextual atual é
`contextual-morphology-2`; use a versão e o fingerprint exatos retornados pela
análise. Bindings antigos não autenticam automaticamente uma análise nova.
Não copie evidências sintéticas dos testes.

Receipts são assinados pelo operador, com `SignedEvidence.sign` e a chave
`MULTILANG_NATIVE_EVIDENCE_SIGNING_KEY`, depois da revisão. A ordem é: bindings
contextuais, política de importância, sentidos, formas e agregações. Insira cada
receipt no documento antes de produzir os payloads dependentes. Os arquivos de
receipt ficam em `MULTILANG_NATIVE_EVIDENCE_DIR/<receipt_id>.json`. Assinatura
comprova a origem da decisão; não comprova que uma tradução está correta.

Após registrar um perfil qualificado pelo comando existente `register-profile`:

```bash
uv run --no-sync multilang native import-reviewed-vocabulary \
  COMPILED_DIR/bundle.json BUNDLE_FILE_SHA256 pt PROFILE_VERSION DATASET_VERSION
```

A importação recompila e verifica as decisões, persiste identidades e formas e
cria uma edição de preparação. Apenas as formas do bundle entram no snapshot.
O bundle completo, incluindo observações e agregações, permanece em
`MULTILANG_NATIVE_EVIDENCE_DIR/artifacts/<sha256>`; o dataset guarda a referência.
Reimportar o mesmo bundle preserva IDs e versão. Esse passo não aprova distribuição,
ranking, conteúdo ou produção. A API de importação aceita o formato
`reviewed-vocabulary` com o mesmo contrato; seus limites HTTP continuam menores
que os do arquivo local.

## Gerar, revisar e concluir uma frase

```bash
uv run --no-sync multilang native draft-content request.json draft.json
```

O primeiro passo exige perfil válido e provedor habilitado, gera conteúdo plain
text validado e guarda o rascunho original. Ele não precisa que uma frase ainda
desconhecida já tenha sido revisada. O arquivo tem permissão `0600`.

Analise a frase, revise os vínculos de seus tokens e importe o
`ContextualBindingSet` assinado com `native import-contextual-bindings`. Cada
binding liga ocorrência, análise, identidade, sentido e conceito. Assine os
bindings individuais antes do conjunto; o conjunto também vincula namespace e
versão do perfil. Um conjunto privado não pode ser reaproveitado no Core.

```bash
uv run --no-sync multilang native complete-content-draft draft.json
```

A conclusão confere o original armazenado, a identidade atual, as permissões e
o matcher. Funciona com chamadas ao provedor desligadas. Não aceita texto editado
como se ainda fosse o retorno original do provedor. O conteúdo resultante fica
pendente da revisão de qualidade já existente; áudio e exportação seguem os
serviços existentes. Os rascunhos são operações locais do CLI. Inclua os
diretórios de rascunhos, bindings e evidências no backup dos arquivos locais.

## O que significa a pendência

Ter biblioteca, modelo e dicionário não basta para afirmar que existem 3000
verbetes corretos e prontos para distribuição em cada língua. A implementação
agora prepara e conserva a entrada necessária. A liberação ainda exige:

- Decisões reais sobre sentidos, formas importantes, qualidade e direitos das fontes.
- Corpora adequados para frequência e avaliação independente com unidades e
  etiquetas compatíveis com cada analisador, especialmente coreano e japonês.
- Revisão de definições, exemplos, traduções, leituras e áudios, com orçamento
  definido para a geração paga. Nenhuma chamada paga foi feita nesta preparação.
- Aceitação nos clientes Anki exigidos pelo plano. O teste local do núcleo Anki
  não equivale à validação em todos os aplicativos desktop e móveis.

Os campos dos cartões não são uma pendência. Deploy foi excluído por decisão do
usuário. Consulte o [relatório de preparação real](multilingual-readiness.md)
para resultados por língua e a distinção entre candidatos e conteúdo aprovado.
