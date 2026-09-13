# Plano detalhado: qualificação linguística e política de importância

**Solicitação:** planejar e implementar o fluxo completo nesta sessão.
**Data:** 2026-09-13.
**Base verificada:** `1f949e44dcd7b98dbd910fa129f8abaabdd88248`.
**Especificação técnica:** `../specs/2026-09-13-linguistic-qualification.md`.

O objetivo é transformar fontes linguísticas em candidatos rastreáveis, medir
ocorrências, permitir revisão local, calibrar a seleção de formas importantes e
encaminhar decisões aprovadas para a geração e exportação já existentes.

O trabalho usa Python, Pydantic, Typer, os modelos Stanza/Kiwi/Fugashi existentes,
SQLAlchemy, HTML/JavaScript local e pytest. Não exige outro serviço de aplicação.
A execução foi dividida entre implementação, revisão independente e integração,
com testes antes das mudanças de comportamento.

## Regras que valem para todas as etapas

- Preservar os nomes, a ordem e a formatação dos campos Anki. Metadados de lema,
  sentido, análise, fonte e aprovação ficam internos.
- Preservar os três níveis Core de 1000 identidades. Todas as formas importantes
  aprovadas são adicionais; o piloto de 100 entradas não substitui esse Core.
- Preservar NFC, maiúsculas, acentos e posições comprovadas no texto. Não inventar
  sentidos, probabilidades, avaliações humanas ou decisões sobre licenças.
- Manter separados: análise do modelo, medição de corpus, decisão do revisor,
  calibração da regra e aprovação para produção.
- Continuar na branch solicitada. Usar listas explícitas nos commits e preservar
  alterações anteriores do usuário. O inventário inicial está em
  `.multilang/verification/qualification/before.json`.
- Limitar arquivos, registros, grades de parâmetros, HTML e requisições externas.
- Manter fontes brutas, modelos e pacotes reais de revisão em `.multilang`.
  Versionar código, documentação e resultados agregados.
- Não usar GSDD como fluxo ou dependência operacional, fazer deploy, push, merge,
  migração em banco real ou chamadas pagas sem orçamento específico aprovado.

## 1. Corrigir a análise contextual e a comparação entre modelos

**Arquivos:** `services/contextual_morphology.py`,
`services/vocabulary_evaluation.py` e respectivos testes em `tests/services`.
Os caminhos de serviços são relativos a `src/multilang`.

- [x] Escrever regressões para contrações com posições comprovadas, como `ao`,
  contrações sem alinhamento comprovado, como `do`, posições ausentes/sobrepostas,
  palavras desconhecidas, pontuação japonesa e preservação das palavras ao redor.
- [x] Executar as regressões antes da implementação para comprovar a falta do
  comportamento esperado, sem confundir isso com ausência de modelos instalados.
- [x] Preservar `analyze(language, text) -> ContextualAnalysis`; acrescentar trechos
  bloqueados explícitos e limitados, mantendo compatibilidade com entradas antigas.
- [x] Aceitar componentes de um token composto somente quando o fornecedor informa
  posições exatas, consecutivas, sem sobreposição e cobrindo todo o token original.

```python
cursor = parent.start_char
for child in parent.words:
    assert type(child.start_char) is int and type(child.end_char) is int
    assert child.start_char == cursor
    assert text[child.start_char:child.end_char] == child.text
    cursor = child.end_char
assert cursor == parent.end_char
```

- [x] Quando essa prova falha, preservar o trecho bloqueado e seus componentes,
  sem deduzir posições por busca de texto ou sufixos. Quando a saída do fornecedor
  puder ser processada, cobrir o texto por tokens exatos ou trechos bloqueados;
  falhas globais permanecem indisponíveis/inconclusivas.
- [x] Omitir atributos ausentes do UniDic; reconhecer pontuação somente com categoria
  nativa e evidência Unicode. Valores lexicais ausentes continuam inconclusivos.
- [x] Manter as diferenças entre os inventários UD e Kiwi/UniDic explícitas.
  Métricas incompatíveis de coreano/japonês ficam nulas, com motivo; divergências
  reais em métricas compatíveis continuam contando como erros.
- [x] Versionar o comportamento e o avaliador. Executar testes focados e exemplos
  reais de português, inglês, coreano e japonês, preservando evidência antes/depois.

**Resultado esperado:** aproveitar evidência contextual válida sem transformar
análises incompletas em correspondências aprovadas do alvo.

## 2. Medir evidências de importância sem inventar notas

**Arquivos:** `domain/form_evidence.py`, `services/form_evidence.py` e
`tests/services/test_form_evidence.py`.

**Contratos:** `EvidenceOccurrence`, `CorpusEvidenceContext`,
`FormEvidenceMeasurement` e `FormEvidenceReport`.

- [x] Testar duplicação de ocorrências físicas, cópias de documentos, ausência de
  limites documentais, NFC incorreto, origem/divisão incorretas, sentidos ausentes,
  valores extremos e independência da ordem de entrada.
- [x] Identificar cada ocorrência por fonte, documento quando conhecido, frase e
  posições. Agrupar por idioma, lema, classe, forma, análise e sentido quando resolvido.
- [x] Rejeitar ocorrências ambíguas/incompatíveis, preservar seus motivos e deduplicar
  os registros físicos e documentos copiados antes de medir.
- [x] Calcular com Decimal, mantendo os denominadores explícitos:

```python
frequencia_por_milhao = ocorrencias * 1_000_000 / tokens_medidos
dispersao = documentos_com_a_forma / documentos_distintos_medidos
```

- [x] Sem limites documentais comprovados, manter contagem de documentos e dispersão
  nulas. Um identificador do arquivo-fonte não vira um documento fictício.
- [x] Derivar a nota de frequência pelo percentil empírico de posto médio:
  `(grupos com contagem menor + grupos empatados / 2) / total de grupos`.
  Guardar método e hash da população. Um grupo isolado recebe `0,5`.
- [x] Calcular os postos por histograma, evitando percorrer toda a população para
  cada forma. Não apresentar o percentil como probabilidade/confiança do modelo.
- [x] Preservar indicações explícitas das fontes como propostas. Irregularidade,
  imprevisibilidade, ambiguidade, pronúncia e critérios pedagógicos não medidos
  permanecem ausentes até evidência ou julgamento revisado.
- [x] Preservar formas observadas mesmo sem nota final; não replicar uma contagem
  automaticamente em todos os sentidos de um lema.

**Resultado esperado:** relatório reproduzível com contagens e limitações reais,
sem selecionar formas por uma pontuação preenchida artificialmente.

## 3. Calibrar critérios com revisão autenticada e avaliação separada

**Arquivos:** `domain/lexical_identity.py`, `services/importance_calibration.py`,
`tests/domain/test_important_form_criteria.py` e testes de calibração.

- [x] Separar `ImportantFormCriteria`, que representa uma proposta, de
  `ImportantFormPolicy`, que continua exigindo aprovação. Preservar JSON, campos
  e hash da política existente com uma regressão de compatibilidade.
- [x] Compartilhar a função de pontuação entre seleção e calibração. Ausência de
  confiança revisada ou de evidência necessária não autoriza uma forma.
- [x] Aceitar uma grade explícita de 1 a 256 critérios e custos explícitos para
  falsos positivos e falsos negativos; exigir exemplos avaliáveis das duas classes.
- [x] Autenticar o pacote e a submissão originais, inclusive identidade do revisor,
  propósito da assinatura, idioma, perfil, rubrica e divisão de dados.
- [x] Escolher a proposta que minimiza `FP × custo_FP + FN × custo_FN`.
  Resolver empates pelo hash dos critérios, com precisão decimal e arredondamento fixos.
- [x] Informar TP/FP/FN/TN, precisão, revocação, formas selecionadas e motivos dos
  casos excluídos. Não esconder casos inconclusivos no denominador.
- [x] Guardar no resultado o pacote, decisões autenticadas, grade e objetivo completos.
  Reexecutar essa calibração antes da avaliação para detectar adulterações do relatório.
- [x] Avaliar a regra congelada em dados separados. Verificar sobreposição de fontes,
  documentos e textos, incluindo todas as ocorrências medidas além dos exemplos visíveis.
- [x] Manter `production_eligible=false`. A calibração não assina nem aprova uma
  política de produção. Testar adulteração, vazamento de avaliação, empates e casos ausentes.

**Resultado esperado:** saber como uma regra foi escolhida e onde ela erra, sem
confundir a proposta calibrada com autorização de uso em produção.

## 4. Disponibilizar a revisão no navegador e importar decisões

**Arquivos:** `services/qualification_review.py`, recursos em
`resources/qualification_review/`, `resources/qualification_rubric.json` e testes.

- [x] Criar pacotes imutáveis limitados com itens lexicais, formas e casos contextuais,
  vinculados aos hashes de idioma/perfil/rubrica/divisão e fontes.
- [x] Criar decisões tipadas para aceitar, corrigir, rejeitar ou deixar inconclusivo.
  Correções mantêm lema, classe, sentido e posições explícitos quando aplicáveis.
- [x] Registrar identidade do revisor, experiência declarada, data com fuso e hashes
  do pacote/itens. A declaração de experiência não comprova credenciais profissionais.
- [x] Implementar HTML local com busca, filtros, paginação, trechos das fontes,
  propostas, medições e motivos. Ocultar inicialmente respostas do modelo na avaliação.
- [x] Permitir baixar o JSON de decisões parciais e reabri-lo para continuar.
  Manter decisões separadas dos dados originais e permitir voltar a pendente.
- [x] Incorporar dados de modo seguro, usar `textContent` para texto linguístico e
  restringir scripts/estilos por CSP. Não usar rede, CDN, armazenamento automático
  ou chaves de assinatura no navegador.
- [x] Revalidar pacote, itens e alterações permitidas na importação. Uma submissão
  válida sem assinatura permanece rascunho. A assinatura exige o propósito
  `qualification-review` e o mesmo identificador do revisor esperado.
- [x] Testar retomada, decisões parciais, hashes/divisões incorretos, duplicatas,
  Unicode, terminadores de script, chaves especiais, limites, symlinks e receipts inválidos.
- [x] Exercitar o navegador real com fixtures sintéticas e pacotes reais de 500 itens
  em português/coreano, em desktop e celular. Não criar aprovações para dados reais.

**Resultado esperado:** revisão utilizável sem servidor ou deploy, com importação
que distingue claramente rascunho e decisão autenticada.

## 5. Adquirir fontes e preparar pilotos reproduzíveis nos 22 idiomas

**Arquivos:** `services/qualification_corpora.py`,
`services/qualification_observations.py`, `services/qualification_pilot.py` e testes.

- [x] Implementar aquisição HTTPS limitada para projetos Wikimedia permitidos,
  sem redirecionamentos arbitrários e respeitando limites e pedidos de espera.
- [x] Congelar seleção, IDs de página/revisão, primeira publicação, texto extraído,
  resposta original, licença declarada, atribuição, idioma, registro e hashes.
  A aquisição não concede aprovação de redistribuição.
- [x] Buscar amostras modestas de português/inglês em registros identificados quando
  acessíveis. Registrar indisponibilidade/limitação remota, sem presumir cobertura equivalente.
- [x] Observar parágrafos de documentos e UD de treino por modelos locais. Preservar
  análise completa, posições, trechos bloqueados, unidades ignoradas e denominadores.
- [x] Exigir recibo de aquisição e hash para UD train. UD test permanece diagnóstico
  de avaliação; não pode ser renomeado como treino ou usado para calibrar a seleção.
- [x] Selecionar 100 grafias com entrada lexical disponível pela ordem declarada da
  semente de frequência. Preservar todos os sentidos/formas relacionados, sem escolher
  automaticamente um sentido. Manter categorias desconhecidas em fila explícita.
- [x] Criar pacotes separados de léxico, formas e 200 casos de avaliação. Dividir
  arquivos por limite de tamanho/itens sem descartar propostas.
- [x] Concluir português/inglês, depois turco/coreano/japonês/chinês e os demais
  idiomas, aplicando o mesmo processo aos 22 pacotes linguísticos.
- [x] Manter dados brutos locais e gerar índice de revisão e relatório agregado com
  hashes, cobertura e limitações. Nenhum pacote de máquina é uma referência humana aprovada.

**Resultado esperado:** entradas reais e auditáveis para iniciar a revisão de cada
língua. Frequência em uma pequena amostra não demonstra frequência geral equilibrada.

## 6. Integrar CLI, vocabulário, geração, áudio e exportação

**Arquivos:** `qualification_cli.py`, montagem em `vocabulary_cli.py`,
`services/qualification_bridge.py`, `services/qualification_workload.py`, testes
correspondentes e integração em `test_native_generated_edition.py`.

- [x] Expor os comandos sob `multilang native vocabulary qualification`: medição,
  carga de trabalho, exportação/importação de revisão, payload de assinatura,
  calibração, avaliação, preparação de piloto, aquisição e observação de corpus.
- [x] Validar hashes e entradas antes das operações, recusar sobrescrita e fornecer
  erros seguros. Descoberta/aquisição são explícitas; não há download oculto nem
  chamada paga ao preparar, medir ou revisar.
- [x] Expor seleção de páginas por estratégia e aquisição com seleção congelada
  opcional, exigindo o hash correspondente e IDs compatíveis.
- [x] Converter decisões autenticadas em `VocabularyReview` e payloads de assinatura
  do importador existente. Manter pendentes formas sem vínculo contextual nativo completo.
- [x] Aplicar correções lexicais em uma preparação derivada nova: novos IDs, prova
  da correção e origem preservada. A nova preparação continua sujeita às aprovações nativas.
- [x] Calcular a carga da seleção inteira: identidades, formas, cards opcionais,
  texto, áudio da palavra/frase, cache comprovado e preços declarados.
- [x] Contar conteúdo/áudio por unidade de conteúdo; cards de reversão/escuta que
  compartilham essa unidade não multiplicam chamadas indevidamente.
- [x] Sem seleção/preços/textos/áudio finais, registrar custo ou tamanho desconhecido
  como nulo. Não descartar formas aprovadas para caber em quantidade ou orçamento.
- [x] Exercitar o percurso completo com providers e autoridade sintéticos explícitos:
  revisão → importação → conteúdo/áudio → aprovação de teste → edição → `.apkg`.
- [x] Conferir campos Anki, imagem vazia, IDs e reimportação; testar o backend oficial
  em coleção descartável, sem declarar aceitação dos clientes gráficos/móveis.

**Resultado esperado:** o novo fluxo alimenta a aplicação existente e informa o
trabalho necessário antes de qualquer geração paga.

## 7. Revisar, verificar e entregar

- [x] Submeter os componentes a revisão independente e corrigir achados concretos
  com regressões, incluindo proveniência completa, limites documentais e calibração adulterada.
- [x] Executar os testes focados e a regressão nativa com os cuidados já conhecidos
  para AnyIO no sandbox; manter modelos reais serializados.
- [x] Isolar a verificação da refatoração concorrente: base Git registrada mais os
  arquivos desta entrega. Revalidar também os dois percursos de geração/exportação
  no workspace compartilhado e a montagem real da CLI.
- [x] Conferir Ruff, wheel/sdist, recursos incluídos e construção estrita da documentação.
  Não houve mudança de dependências que exigisse atualizar o lockfile.
- [x] Comparar os arquivos e o índice anteriores. Preservar alterações concorrentes,
  inclusive a navegação compartilhada do MkDocs e a ampliação de lint da CI.
- [x] Registrar os commits de código com listas explícitas de arquivos próprios:
  `060bb28` (análise contextual) e `91ef40c` (qualificação).
- [x] Consolidar os 22 pilotos, seus diagnósticos e hashes; atualizar o relatório e
  registrar o commit da documentação, sem incluir arquivos da refatoração paralela.
- [x] Entregar plano, guia, índice local de revisão e resultados, com as pendências
  de conteúdo claramente descritas. Não realizar deploy.

## Critério de conclusão e pendência real

O software está entregue quando os artefatos existem, os comandos os utilizam,
a integração passa e os resultados podem ser conferidos. A verificação contabiliza
451 casos distintos de teste da aplicação, além das verificações do navegador,
agregador de relatórios, distribuição e backend oficial do Anki.

A qualificação do conteúdo exige decisões reais sobre sentidos, formas, naturalidade,
pronúncia e utilidade; corpus adequados e revisão das fontes/licenças; avaliação
independente e, para geração paga, orçamento explícito. A implementação fornece os
mecanismos para isso, mas não fabrica essas decisões. Os pilotos de máquina e os
receipts sintéticos de teste não autorizam produção.

Guia de uso: `../../linguistic-qualification.md`. Resultados efetivos:
`../../linguistic-qualification-results.md`. Evidências locais:
`.multilang/verification/qualification/verification-summary.json`.

## Resultado da execução

Foram preparados e conferidos 22 pilotos, com 2200 palavras-base, 11842 candidatos
lexicais, 31425 propostas de formas do dicionário, 233 grupos medidos associados
aos pilotos, 4400 casos de avaliação e 152 pacotes de revisão. Não houve falhas de
integridade nos pilotos, avaliações ou corpora. A medição contextual dos pilotos
usa apenas amostras de português/inglês; os demais 20 ainda precisam de corpus
adequado. Nenhum idioma recebeu qualificação humana ou aprovação de produção.

As avaliações locais registraram 3512 análises completas e 888 inconclusivas; esses
estados não atestam correção linguística. As limitações da semente croata `hr → sh`
e a normalização NFC de três sementes gregas estão registradas com proveniência.
