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
divergente. Ambos continuam sendo erros na métrica original. As métricas UD
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
ausentes e valores divergentes de caso, número e pessoa. O relatório de comparação
separa essas causas sem retirar erros do denominador. Essas contagens são por
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
