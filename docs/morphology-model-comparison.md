# Escolha e comparação de modelos morfológicos

O modelo de análise pode ser escolhido por idioma. A comparação mede se uma
alternativa melhora lema, classe gramatical e traços morfológicos, mantendo os
mesmos exemplos e critérios. O nome de um perfil não garante maior precisão.

## Perfis disponíveis

| Perfil | Seleção no registro Stanza fixado | Uso |
|---|---|---|
| `fast` | Seleção anterior, preferindo `nocharlm` quando disponível | Padrão compatível com os modelos e manifestos existentes |
| `balanced` | Pacote `default`, sem substituir CharLM por `nocharlm` | Comparar o modelo padrão completo |
| `accurate` | Pacote `default_accurate` | Comparar a alternativa indicada pelo registro, que pode exigir um transformer |

Os três perfis podem selecionar os mesmos arquivos em alguns idiomas. O catálogo
identifica essas equivalências; não são três modelos distintos por definição.
Coreano e japonês continuam usando Kiwi e Fugashi/UniDic, respectivamente, e
aceitam somente `fast`. Latim mantém seu caminho próprio.

```bash
uv run --no-sync multilang native vocabulary model-options
uv run --no-sync multilang native vocabulary model-options --language ru
uv run --no-sync multilang native vocabulary prepare-model ru --profile balanced
uv run --no-sync multilang native vocabulary models --language ru --profile balanced
```

Somente `prepare-model` baixa arquivos. Consultar opções, analisar e comparar
funcionam sem rede. Um perfil ausente ou alterado é informado como indisponível;
o sistema não troca silenciosamente para outro modelo. Preparar uma alternativa
preserva o manifesto de `fast`. Os arquivos compartilhados continuam vinculados
aos hashes do registro Stanza 1.10.0.

Transformers também precisam dos pesos e do tokenizer externos. A preparação
fixa uma revisão do repositório permitido e hashes dos arquivos locais; a análise
carrega esses arquivos sem código remoto. Layouts de checkpoint que não possam
ser carregados por esse caminho são recusados. Modelos maiores exigem mais
memória, armazenamento e tempo de carregamento.

## Seleção por idioma

Em `.env`, configure somente as línguas que deseja alterar, depois de preparar e
avaliar os respectivos modelos:

```dotenv
MULTILANG_NATIVE_LANGUAGE_MODEL_PROFILES={"ru":"balanced","de":"balanced","tr":"balanced"}
```

O exemplo demonstra a configuração; não é uma recomendação baseada em medição.
O valor padrão é `{}`. A seleção alcança o runtime, a análise, a avaliação e a
coleta de observações para qualificação. Os comandos de modelos, análise e
avaliação aceitam `--profile` para substituir a configuração naquela execução:

```bash
uv run --no-sync multilang native vocabulary analyze ru sentence.txt --profile balanced
uv run --no-sync multilang native vocabulary analyze ru sentence.txt --profile fast
```

A mudança de perfil altera o fingerprint da análise. Vínculos linguísticos
revisados para o modelo anterior não autenticam automaticamente uma análise
produzida por outro perfil.

## Comparação reproduzível

O catálogo oferece os conjuntos oficiais de desenvolvimento alemão GSD e turco
IMST, fixados na versão UD `r2.16`:

```bash
uv run --no-sync multilang native vocabulary acquire de corpus-dev --root .multilang/sources
uv run --no-sync multilang native vocabulary acquire tr corpus-dev --root .multilang/sources
```

O recibo informa o arquivo, SHA-256, URL e licença. Use esse arquivo e esse hash
no pedido abaixo, com `split: "dev"`. A aquisição exige uma URL de desenvolvimento
explícita no catálogo; idiomas sem essa entrada são recusados antes do download.
O recibo de aquisição não concede aprovação de redistribuição nem revisão
linguística. Os conjuntos de treino e teste mantêm seus identificadores próprios.

Crie um arquivo `comparison.json` com os caminhos e SHA-256 dos corpora locais.
Este exemplo contém um marcador que deve ser substituído pelo hash real:

```json
{
  "model_root": ".multilang/models/stanza-1.10.0",
  "datasets": [
    {
      "language": "ru",
      "corpus": "data/ru-dev.conllu",
      "corpus_sha256": "SUBSTITUA_PELO_SHA256_DO_CORPUS",
      "split": "dev"
    }
  ],
  "profiles": ["fast", "balanced", "accurate"],
  "max_sentences": 200,
  "timeout_seconds": 600,
  "threads": 1
}
```

```bash
sha256sum data/ru-dev.conllu
sha256sum comparison.json
uv run --no-sync multilang native vocabulary compare-models \
  comparison.json REQUEST_SHA256 comparison-report
```

Substitua `REQUEST_SHA256` pelo hash exibido para o pedido. O diretório de saída
deve ser novo. O pedido aceita até 22 datasets, perfis únicos incluindo `fast`,
1–5000 frases, 1–3600 segundos por execução e 1–8 threads. Os caminhos relativos
são interpretados a partir do diretório de trabalho do comando.

A CLI verifica os bytes do arquivo de entrada. Já `request_sha256` no relatório
identifica o pedido validado em JSON canônico, permitindo reconhecer o mesmo
pedido mesmo quando a indentação do arquivo muda.

Cada execução ocorre em processo separado, sequencialmente, com limite de tempo.
Os perfis recebem a mesma amostra determinística, selecionada do corpus inteiro.
O relatório registra hashes dos dados e da amostra, versões, fingerprints,
métricas, contagens, duração e pico de memória do processo. O tempo inclui a
verificação dos artefatos, o carregamento do analisador e a avaliação; não
representa somente latência por frase nem o tempo total da CLI. Carga da
máquina e cache do sistema também influenciam esse tempo; uma execução isolada
não estabelece a capacidade de processamento em produção.

O diretório final é publicado somente ao terminar o pedido inteiro. Para lotes
longos, use um pedido e uma saída por idioma: uma interrupção não permite retomar
automaticamente avaliações parciais. Comece com uma amostra pequena para validar
a execução e amplie a avaliação antes de decidir uma mudança de modelo.

Ausência de modelo, perfil não suportado, equivalência, timeout e falha aparecem
explicitamente. Diagnósticos por traço distinguem campo ausente de valor
divergente em tokens alinhados. Tokens sem correspondência e referências sem
intervalo são contados separadamente. Os critérios das métricas permanecem iguais. As métricas UD
incompatíveis com as representações nativas de coreano e japonês continuam nulas.

Na acurácia de traços, uma palavra só conta como correta quando todos os seus
traços anotados coincidem com a referência. Acertar o lema e a classe gramatical
não basta para acertar essa métrica: um único caso, gênero ou número divergente
já torna aquele conjunto de traços incorreto.

## Como interpretar o resultado

Uma recomendação exige corpus de desenvolvimento (`dev`), ganho em pelo menos
uma métrica comparável e nenhuma regressão nas demais métricas ou na cobertura.
Empates preservam `fast`. O split de teste (`test`) serve para diagnóstico e
confirmação, sem escolher modelos. Declare a divisão real da fonte; renomear
dados de teste como desenvolvimento invalida essa separação.

A comparação não altera a configuração, não ativa perfis e não concede
qualificação linguística. Ela fornece evidência para a decisão do operador e
para correções futuras. O [fluxo de revisão e calibração](linguistic-qualification.md)
continua responsável pelas decisões linguísticas.

## Evidência local da implementação

O inventário usado na validação identificou 22 analisadores `fast` disponíveis.
Há seleções Stanza alternativas em 15 idiomas: `pt`, `es`, `en`, `fr`, `de`, `it`,
`pl`, `tr`, `ru`, `nl`, `da`, `nb`, `sv`, `fi` e `zh`. Em `ro`, `hu`, `cs`, `hr`
e `el`, as seleções dos perfis são iguais. `ko` e `ja` usam os analisadores nativos.
Isso descreve opções do registro, não ganhos de precisão medidos.

Foram preparados os modelos `balanced` de russo, alemão e turco, preservando os
bytes dos três manifestos legados. Os testes cobrem também carregamento real de
um transformer pequeno inteiramente local e regressão com o modelo real de inglês.
Esses testes validam a integração; a comparação de qualidade usa os corpora.

As avaliações anteriores de 200 frases ajudam a localizar os erros. No russo,
os campos ausentes mais frequentes incluem `NameType`, `PronType` e `NumForm`.
No alemão, as divergências se concentram em caso e gênero. No turco, há campos
ausentes e valores divergentes de caso, número e pessoa. Essas contagens históricas incluem falhas de alinhamento entre os campos
ausentes. O diagnóstico por ocorrência descrito abaixo separa essas situações,
sem retirar erros do denominador das métricas originais. Essas contagens são por
traço; uma palavra pode contribuir com mais de um erro.

### Piloto de 19/09/2026

Foram comparados `fast` e `balanced` em **25 frases por idioma**, selecionadas
deterministicamente dos corpora locais de teste. Cada par recebeu as mesmas
frases e os mesmos denominadores. Os seis processos concluíram; os três
relatórios publicados coincidem com suas respectivas saídas da CLI.

| Idioma | Lemas: fast → balanced | Classe gramatical: fast → balanced | Traços: fast → balanced |
|---|---|---|---|
| Alemão | 98,82% → 98,82% | 95,27% → 95,27% | 84,28% → 82,97% |
| Turco | 96,90% → 97,35% | 94,25% → 94,69% | 86,99% → 86,18% |
| Russo | 97,41% → 96,98% | 96,77% → 96,98% | 80,84% → 85,02% |

O russo ganhou 12 conjuntos de traços corretos, de 232 para 244 entre 287
palavras elegíveis, mas perdeu dois lemas corretos. O alemão perdeu três conjuntos
de traços corretos entre 229; o turco ganhou um lema e uma classe gramatical
corretos, mas perdeu um conjunto de traços entre 123. A precisão e a cobertura
dos limites dos tokens permaneceram iguais entre os perfis de cada idioma.

Nenhum candidato apresentou ganho sem regressão nas demais métricas. Além disso, o split
é `test`: os relatórios são diagnósticos e não recomendam nem ativam modelos.
A configuração padrão foi preservada. As amostras pequenas não substituem uma
avaliação ampla de desenvolvimento, nem devem ser comparadas diretamente com
os percentuais anteriores calculados sobre 200 frases.

| Idioma | Tempo registrado em segundos: fast → balanced | Pico de memória em MiB: fast → balanced |
|---|---|---|
| Alemão | 492,51 → 390,56 | 578,77 → 879,54 |
| Turco | 101,27 → 191,68 | 560,15 → 637,52 |
| Russo | 230,34 → 340,00 | 609,72 → 695,12 |

Execução em CPU, uma thread por analisador, sob carga compartilhada. A diferença
de tempo no alemão não demonstra que `balanced` seja mais rápido: cache e carga
variaram durante o piloto. Os perfis `accurate` não foram medidos neste piloto.

As evidências locais estão em `.multilang/verification/model-comparison/`:
`pilot-summary.json` agrega os resultados; `pilot-25-{de,tr,ru}/manifest.json`
e seus diretórios `artifacts/` preservam hashes, métricas e observações.
Os pedidos correspondentes são `pilot-25-{de,tr,ru}-request.json`.
`machine-context.json` registra versões e uma observação dos recursos disponíveis.

A integração foi verificada com 154 testes focados nesta rodada, além dos testes
separados já concluídos com inglês real e um transformer pequeno local. A revisão
independente do código não deixou pendências abertas.

## Diagnóstico por ocorrência

O comando `diagnose` lê uma comparação de perfis ou uma avaliação individual
produzida pelo avaliador versão 3. Ele usa somente os artefatos existentes, sem
carregar modelos, chamar provedores ou acessar a rede.

```bash
sha256sum comparison-report/manifest.json
uv run --no-sync multilang native vocabulary diagnose \
  comparison-report MANIFEST_FILE_SHA256 diagnostics-report
```

Substitua `MANIFEST_FILE_SHA256` pelo SHA-256 dos **bytes de manifest.json**,
não pelo campo `comparison_sha256` ou `evaluation_sha256`. A saída deve ser um
diretório novo, fora do artefato de origem. O mesmo comando aceita um diretório
criado por `evaluate`; nesse caso, o perfil é identificado como `recorded`, pois
a avaliação individual não informa necessariamente o nome do perfil.

São publicados três arquivos:

- `diagnostics.json`: métricas e contagens originais, grupos de divergências,
  motivos de análises inconclusivas, incompatibilidades e transições por perfil.
- `cases.jsonl`: ocorrências e transições completas, com frase, palavra, intervalo,
  valores esperado e observado, fingerprint, identificador estável e referência
  ao hash e à linha de `observations.jsonl`.
- `report.md`: resumo legível com grupos prioritários e exemplos. Os exemplos
  são limitados; `cases.jsonl` contém todos os casos aceitos pelo limite do relatório.

O manifesto de diagnóstico registra hashes de `cases.jsonl` e `report.md`;
`diagnostics_sha256` identifica seu próprio conteúdo canônico sem esse campo.
Entradas alteradas, inconsistências entre manifestos e observações, caminhos
externos, symlinks e arquivos especiais são recusados. Há limites de 256 MiB
de entradas, 128 MiB de saída, 100 mil registros e 250 mil verificações por
avaliação. Exceder um limite interrompe a operação sem publicar relatório parcial.

### Categorias e denominadores

`token_unmatched` indica que o analisador não produziu um token com o mesmo
intervalo da referência. Esse token continua no denominador original de lema,
classe e traços, mas seus campos não são classificados como `feature_missing`.
`reference_span_missing` indica que a própria referência não tem intervalo
alinhável. `predicted_token_unmatched` registra tokens previstos sem correspondência.

Nos tokens alinhados, as categorias são `lemma_different`, `pos_different`,
`feature_missing` e `feature_different`. Cada grupo informa seu denominador e
confusões de valores: os grupos por campo usam tokens alinhados que possuem
aquele campo na referência, agrupados por classe gramatical. Essas taxas não
substituem a acurácia original, que exige acertar todo o conjunto de traços.
Uma palavra pode aparecer em vários grupos.

Os contadores `feature_diagnostics` de novas comparações têm `schema_version: 2`,
com `unaligned_tokens` e `unaligned_reference_tokens`. Comparações antigas
continuam legíveis; o diagnóstico é recalculado das observações, sem reescrever
o relatório original. O avaliador e seus critérios continuam na versão 3.

### Ganhos, regressões e investigação

O pareamento exige referências, amostras e ocorrências idênticas. Para cada
métrica elegível, informa `resolved`, `introduced`, `persistent` e
`unchanged_correct`. O ganho líquido é `resolved - introduced`. O pareamento
é feito para cobertura dos tokens de referência, lema, classe e conjunto de
traços; a precisão dos tokens previstos permanece na tabela de métricas
originais. Um perfil indisponível ou uma amostra diferente não recebe
transições inventadas.

Coreano e japonês preservam as métricas UD incompatíveis como `null`. Seus
relatórios mostram cobertura, bloqueios e motivos de análises inconclusivas.
Diferenças de inventário não viram erros linguísticos nem notas de zero.

Todos os casos começam com `cause_status: unreviewed`: divergência com uma
anotação não prova defeito do modelo. Para investigar, abra a linha de evidência,
confira a referência e compare a saída original do analisador com o resultado
normalizado. Se a saída original não foi salva, reproduza apenas os casos
selecionados com os mesmos artefatos e registre a nova evidência separadamente.
O comando de diagnóstico não executa essa reprodução nem altera decisões de revisão.

Comece pelos relatórios existentes para validar a ferramenta. Para desenvolver
correções, use amostras reais de desenvolvimento e transforme defeitos confirmados
em testes de regressão. Reserve dados independentes para a validação final;
as amostras de teste já examinadas não devem ser renomeadas como desenvolvimento.
O diagnóstico não recomenda, ativa ou qualifica modelos.

### Diagnósticos reproduzidos em 19/09/2026

O processamento das observações do piloto de 25 frases detalhou as mudanças
abaixo em `fast → balanced`. Os valores são contagens de palavras cujo conjunto
completo de traços passou de incorreto para correto ou fez o caminho inverso.

| Idioma | Traços: resolvidos | Traços: introduzidos | Saldo |
|---|---:|---:|---:|
| Russo | 15 | 3 | +12 |
| Alemão | 4 | 7 | -3 |
| Turco | 4 | 5 | -1 |

As duas regressões de lema no russo correspondem a `КА` (referência `КА`,
`balanced`: `ка`) e `основном` (referência `основное`, `balanced`: `основной`).
São divergências reproduzíveis com a referência, ainda sem confirmação da causa
linguística. Não justificam regras especiais para essas palavras.

Nas avaliações nativas existentes de 200 frases, o coreano apresentou 189
análises inconclusivas: 114 com bloqueios, 55 com análise malformada ou sem
alinhamento e 20 com análise ambígua ou incompleta. Foram registrados 276
bloqueios de projeção lexical composta. O japonês apresentou 131 análises
inconclusivas com bloqueios: 200 ocorrências de morfologia não resolvida e 129
de token lexical desconhecido. Contagens de bloqueios são por ocorrência,
não por frase; uma frase pode conter vários bloqueios.

As métricas originais foram reconciliadas com as observações e preservadas.
Nenhum perfil foi ativado. Essas avaliações permanecem amostras de teste já
examinadas, sem servir como validação independente de correções futuras.

## Correções dos adaptadores

As divergências foram confrontadas com a saída original dos analisadores e
com suas convenções documentadas. As correções atuam na projeção dessa saída:

- **Russo:** numerais `NUM` ou `ADJ` escritos inteiramente com dígitos decimais
  recebem `NumForm=Digit` quando o modelo omite esse campo, conforme a
  [definição do Russian UD](https://universaldependencies.org/ru/feat/NumForm.html).
  Valores explícitos permanecem intactos. Formas escritas por extenso, algarismos
  romanos, sufixos e expressões ambíguas não recebem essa inferência.
- **Japonês:** prefixos e categorias conhecidas de sufixos passam pelo helper
  `unidic_to_upos`, seguindo as regras de afixos da
  [tabela de conversão japonesa](https://udjapanese.github.io/UD_converion_table/POS.html).
  A conversão usa a classe e o lema do dicionário, sem fabricar lemas para
  palavras desconhecidas. Não equivale à conversão contextual completa para UD.
- **Coreano:** a projeção conserva intervalos exatos em `surface_spans`, inclusive
  pontuação e grupos sem assinatura lexical. Morfemas de comprimento zero são
  aceitos somente quando ancorados no intervalo comprovado do mesmo grupo.
  Posições de palavras que recomeçam em outra frase deixam de fundir grupos.
  OOV em qualquer alternativa, compostos sem projeção lexical segura e
  discordâncias entre alternativas continuam impedindo uma análise completa.

A investigação dos modelos Stanza fixados mostrou que `NumForm` e `NameType`
não fazem parte dos traços previstos pelo modelo russo usado no diagnóstico.
Caso, gênero, nomes próprios e escolhas ambíguas de lema não são preenchidos
por regras especiais para palavras do corpus. As divergências investigadas de
alemão e turco dependem da interpretação contextual do modelo; nessa primeira
rodada, os perfis desses idiomas foram mantidos.

Esta primeira reavaliação usou `contextual-morphology-3` e a política coreana
`kiwi-top2-consensus-v2`. Serviço, worker e comparação compartilham o cálculo do
fingerprint contextual. Registros históricos continuam legíveis, mas vínculos
e identidades revisados sob a política anterior precisam de nova análise e
revisão antes de autenticar resultados novos. Não basta trocar a versão no JSON.

Análise completa indica que o adaptador projetou a evidência exigida. Não atesta
sentido, qualidade pedagógica ou equivalência com as anotações UD. Os critérios
do avaliador e os denominadores permanecem iguais; as acurácias UD incompatíveis
com Kiwi e UniDic continuam nulas.

### Reavaliação das correções em 19/09/2026

Foram executados novamente os analisadores locais, em `fast`, sobre as mesmas
200 frases de cada idioma alterado. Os hashes das fontes, as referências, os
denominadores e os critérios do avaliador foram conferidos. Os artefatos
anteriores permaneceram intactos. Estas são medições de regressão em amostras
de teste já examinadas, sem qualificação linguística independente.

| Idioma | Medida | Antes | Depois |
|---|---|---:|---:|
| Russo | Conjuntos de traços corretos | 1851/2342 — 79,04% | 1885/2342 — 80,49% |
| Japonês | Frases com análise completa | 69/200 — 34,50% | 141/200 — 70,50% |
| Japonês | Cobertura dos intervalos da referência | 92,41% | 96,42% |
| Japonês | Precisão dos intervalos previstos | 99,08% | 98,95% |
| Coreano | Frases com análise completa | 11/200 — 5,50% | 11/200 — 5,50% |
| Coreano | Cobertura dos intervalos da referência | 40,36% | 79,29% |
| Coreano | Precisão dos intervalos previstos | 88,45% | 99,39% |

No russo, 34 palavras adicionais acertaram todo o conjunto de traços; lema,
classe gramatical e alinhamento não regrediram. No japonês, os 200 bloqueios
causados pelo mapeamento incompleto desapareceram; permanecem 129 ocorrências
desconhecidas. A maior cobertura japonesa veio acompanhada da pequena redução
de precisão dos intervalos registrada na tabela.

No coreano, conservar os intervalos recuperou evidência de palavras válidas
sem liberar frases ainda ambíguas. Permanecem 189 frases inconclusivas, com
38 bloqueios por OOV, 393 por projeção lexical composta e 60 por morfologia
não resolvida. Os bloqueios agora incluem problemas que antes desapareciam
quando a projeção da frase falhava por completo. Mais bloqueios registrados
não significam, nesse caso, mais defeitos introduzidos.

Os erros contextuais restantes de alemão e turco exigem avaliação de modelos
ou revisão linguística em dados de desenvolvimento. Seus modelos não foram
substituídos e não foi produzida uma nova medição de qualidade desses idiomas
nesta correção.

Evidência local: `.multilang/verification/morphology-corrections/`, com
`{ru,ja,ko}-comparison.json`, avaliações em `evaluations/` e relatórios de
ocorrências em `diagnostics-{ru,ja,ko}/`. A comparação registra os hashes dos
artefatos originais e as transições de status de cada frase.

### Continuação: categorias coreanas e revisão de evidências

A política atual é `contextual-morphology-4`, com `kiwi-top2-consensus-v3`.
Numerais `SN`, partículas `JK*`/`JX` e a partícula coordenadora `JC` podem ser
projetados quando o intervalo contém exatamente um morfema conhecido, com forma
igual ao texto original e lema fornecido pelo analisador. O helper
`kiwi_to_upos` segue a [tabela Sejong–UPOS publicada](https://universaldependencies.org/udw20/papers/2020.udw2020-1.12.pdf).
Formas estrangeiras `SL`, caracteres chineses `SH`, terminações e grupos compostos
sem projeção comprovada continuam bloqueados.

Os sinais `<`, `>` e `~` passam a ser separados nos intervalos exatos fornecidos
pelo Kiwi quando recebem uma tag explícita de pontuação. Eles pertencem à
categoria Unicode de símbolos, mas constam como pontuação no
[contrato do Kiwi](https://github.com/bab2min/Kiwi/blob/main/README.md#품사-태그).
A tag genérica `SW` continua exigindo pontuação Unicode. Sobreposição, OOV e
discordância entre as duas alternativas continuam impedindo aceitação; as
assinaturas lexicais originais e a verificação de strict-i+1 são preservadas.

A execução nativa nas mesmas 200 frases recuperou 40 bloqueios locais: os
bloqueios não resolvidos passaram de 60 para 20, com 393 compostos e 38 OOV
preservados. A cobertura dos intervalos UD passou de 1.957/2.468 (79,29%) para
2.001/2.468 (81,08%). A precisão passou de 1.957/1.969 (99,39%) para
2.001/2.016 (99,26%), expondo diferenças adicionais de segmentação nativa.
As 11 frases completas permaneceram completas; as 189 inconclusivas continuam
bloqueadas. Isso melhora a evidência disponível sem conceder concordância
artificial entre análises. Os denominadores e as métricas incompatíveis nulas
foram conferidos novamente.

No japonês, a investigação confirmou que os oito desencontros adicionais com UD
vêm da segmentação dos afixos já produzida pelo dicionário. Os 4.475 intervalos
anteriormente retidos ficaram intactos, e todos os intervalos novos correspondem
ao texto original. As 129 ocorrências ainda bloqueadas não têm lema conhecido;
não recebem um lema inventado para elevar a cobertura.

A auditoria local não encontrou vínculos contextuais ativos, identidades
coreanas no cache lexical nem um ponteiro ativo de frequência coreana. Encontrou
3.000 identidades antigas em um pacote de piloto inativo e dez cópias em seu banco
de piloto. Os 60 recibos históricos foram validados e preservados. Uma alteração
no fingerprint muda o objeto aprovado; esses recibos não aprovam automaticamente
identidades novas. As políticas anteriores permanecem legíveis para auditoria.

A nova tentativa no PostgreSQL configurado concluiu o inventário somente de
leitura. A falha anterior foi classificada incorretamente como expiração: o
pooler rejeitava `statement_timeout` nos parâmetros de conexão. DNS e TLS
funcionavam. Aplicar os limites com `SET LOCAL` dentro de `BEGIN READ ONLY`
permitiu consultar o mesmo endpoint; as transações terminaram com `ROLLBACK`.

Foram encontrados dois jobs coreanos pendentes. Um ainda não possui candidatos;
o outro contém 20 identidades `kiwi-top2-consensus-v1`, exatamente iguais às
posições 1–20 do inventário histórico. Não foram encontrados textos gerados,
revisões, exports nem metadados de vínculos contextuais nas tabelas consultadas.
Essas contagens se referem ao banco, schema e credenciais configurados.
Os candidatos exigem reanálise e revisão antes de retomar a geração. O job de
3.000 itens também exige revalidar a fonte antiga antes de retomá-la. A auditoria
preservou os dois jobs, as identidades e os recibos históricos.

A reanálise local dessas 20 entradas foi executada com o Kiwi atual e produziu
uma fila pendente em `revalidation-staging/current-policy-run/`. Dezenove entradas
apresentaram discordância entre as duas análises; a outra exigiu revisão de uma
composição lexical. Nenhuma recebeu proposta automática de identidade. Sete
também preservam marcadores numéricos dentro do lema histórico, como `가격03`,
sem um campo separado que justifique remover o marcador automaticamente.

O status técnico `resolved` do Kiwi indica que as alternativas foram retornadas;
ele não equivale à concordância entre elas nem à aprovação da fonte. A fila
registra esses estados separadamente, junto com os hashes, intervalos e referências
anteriores. Também distingue a posição da linha na fonte do rank de frequência
publicado. Todas as entradas exigem nova revisão e não possuem autoridade de
importação ou ativação. Os 14 testes do script de staging passaram; os bytes das
fontes foram conferidos antes e depois da execução real.

Evidência local desta continuação: `.multilang/verification/morphology-followup/`,
incluindo a auditoria em `revalidation/` e a investigação de casos nativos em
`native/`. Nenhum recibo de aprovação foi criado por essa auditoria.

### Comparação em desenvolvimento com 200 frases

Foram preparados e executados os três perfis de alemão e turco sobre 200 frases
dos conjuntos oficiais de desenvolvimento UD `r2.16`. Os pesos e tokenizers
dos modelos `accurate` ficaram fixados localmente; as comparações ocorreram
sem rede, em processos separados e com uma thread por analisador.

| Idioma | Perfil | Lemas | Classe gramatical | Conjuntos de traços |
|---|---|---:|---:|---:|
| Alemão | `fast` | 97,19% | 95,84% | 88,69% |
| Alemão | `balanced` | 97,19% | 95,98% | 88,85% |
| Alemão | `accurate` | 97,30% | 97,16% | 89,84% |
| Turco | `fast` | 94,32% | 93,95% | 87,70% |
| Turco | `balanced` | 94,53% | 94,16% | 87,53% |
| Turco | `accurate` | 96,37% | 94,89% | 91,72% |

O `accurate` alemão acrescentou 3 lemas, 38 classes e 22 conjuntos de traços
corretos. No turco, acrescentou 39 lemas, 18 classes e 47 conjuntos de traços
corretos. A cobertura dos intervalos permaneceu igual em ambos; a precisão
turca passou de 94,36% para 94,40%. As contagens de tokens elegíveis e os
critérios do avaliador foram preservados.

A análise completa alemã permaneceu em 163/200 frases. No turco, passou de
200 para 199, com uma frase bloqueada; análise completa não é sinônimo de
acerto linguístico. O diagnóstico registra essa mudança separadamente dos
ganhos nas métricas comparáveis.

A primeira execução alemã de `accurate` atingiu o limite de 1.200 segundos.
Um novo pedido manteve fonte, amostra e modelos e elevou o limite para 1.800
segundos, repetindo também `fast`. Foram conferidos os fingerprints, as
observações, os denominadores e as métricas do baseline antes de reconciliar
os resultados. O relatório original com timeout permaneceu intacto.

O custo foi maior: na comparação alemã repetida, `fast` levou 160,39 segundos
e `accurate`, 809,86; no turco, 183,12 e 1.096,68 segundos. Esses tempos incluem
carregamento e verificação dos arquivos sob carga compartilhada. Os relatórios
também preservam o pico de memória de cada processo.

A escolha de desenvolvimento selecionou `accurate` nos dois idiomas. Entre
candidatos sem regressão nas métricas comparáveis, a regra declarada antes da
confirmação prioriza traços, classe, lema, cobertura e precisão; empates usam
memória e tempo. O `balanced` turco perdeu dois conjuntos de traços corretos
e não foi elegível. No alemão, `accurate` superou o outro candidato elegível.

As amostras efetivas de desenvolvimento e teste não compartilham textos. Nos
corpora alemães completos há seis textos repetidos; o corpus turco não apresentou
textos nem documentos explícitos compartilhados entre os splits. A sobreposição
com o treinamento dos modelos permanece desconhecida. A confirmação usa as
200 frases de teste já examinadas anteriormente e não concede qualificação
linguística independente.

O procedimento de confirmação vincula os fingerprints e manifestos dos dois
modelos, o pedido exato e a amostra histórica à decisão de desenvolvimento.
Alterar qualquer identidade, pedido ou amostra impede a confirmação. Uma
regressão no teste rejeita o candidato escolhido; não escolhe outro perfil.
Os sete testes locais desse procedimento passaram após corrigir os problemas
encontrados na revisão independente.

Evidência: `de-development/`, `de-accurate-retry-development/`,
`tr-development/`, `development-selection.json`, `selection-review.json` e
os diagnósticos correspondentes em
`.multilang/verification/morphology-followup/`.

### Confirmação dos candidatos e decisão final

Os mesmos modelos selecionados em desenvolvimento foram executados nas amostras
históricas de 200 frases de teste. Os hashes dos modelos, fontes, pedidos e
amostras coincidiram com os registrados antes da confirmação. Os baselines
mantiveram as métricas históricas; nenhuma amostra ou métrica foi substituída.

| Idioma | Lemas: fast → accurate | Classe gramatical: fast → accurate | Traços: fast → accurate |
|---|---|---|---|
| Alemão | 97,53% → 97,31% | 96,13% → 96,94% | 86,93% → 90,08% |
| Turco | 95,90% → 97,86% | 93,94% → 93,76% | 88,25% → 88,96% |

O alemão ganhou 66 conjuntos de traços e 26 classes corretas, mas perdeu sete
lemas corretos. O turco ganhou 33 lemas e sete conjuntos de traços corretos,
mas perdeu três classes corretas. Os diagnósticos por ocorrência distinguem
os casos corrigidos dos novos desencontros; o saldo não significa ausência de
regressões individuais.

Nenhum dos dois candidatos cumpriu o critério de confirmação sem regressão nas
métricas comparáveis. **Os dois idiomas permanecem em `fast`, e a configuração
não foi alterada.** O teste não foi usado para escolher outro candidato nem
ajustar regras para palavras específicas. Os modelos preparados continuam
disponíveis para investigação, sem qualificação ou transferência de revisões.

Os relatórios finais ficam em `de-confirmation/`, `tr-confirmation/`,
`diagnostics-de-confirmation/` e `diagnostics-tr-confirmation/`. A decisão
consolidada, com os hashes correspondentes, está em `profile-decision.json`.

A continuação foi verificada com 415 testes focados do projeto, sete testes do
procedimento local de confirmação e 14 testes do staging. A conferência
independente da execução coreana verificou também os 20 registros e a integridade
dos arquivos, sem carregar novamente o modelo. A retomada dos candidatos
coreanos depende de nova revisão da fonte e das identidades; a fila pendente
contém a evidência necessária para essa etapa e não concede aprovação.
