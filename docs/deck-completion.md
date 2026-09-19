# Qualificação executada após a aprovação do piloto

Esta entrega executa revisões reais e corrige dois pontos do fluxo: recuperação dos qualificadores do dicionário original e consolidação verificável dos resultados por idioma. Os decks completos de 3 × 1000 ainda dependem de cobertura lexical, ranking, conteúdo, áudio e qualificação; as listas antigas de 3000 linhas não satisfazem essas condições.

## Português

A aprovação do usuário foi vinculada ao APKG final de dez cards, SHA-256 `594980b9b000384c3507df7f1bf5ad37993749ad9259fbe6a1be71560def14f1`. Ela registra a aceitação da apresentação e do áudio desse piloto.

As três pendências anteriores receberam proposta e julgamento concordantes:

- `trabalho`: o registro original identifica **work (physics)**. A normalização havia perdido `raw_glosses` e `topics`. A nova identidade preserva o domínio técnico sem promover o sentido à lista principal.
- `grandes`: tamanho/extensão é a acepção ampla documentada. As duas aplicações contextuais continuam preservadas. O plural não recebe card adicional neste piloto; essa é uma decisão editorial, não prova de inutilidade geral.
- `veja`: a ocorrência parentética é uma instrução ao leitor. O candidato congelado como subjuntivo fica excluído como exemplo desse modo; a etiqueta original do corpus e a projeção editorial imperativa permanecem distintas.

A campanha após essa rodada contém 142 acordos e duas rejeições, sem as três incertezas antigas. A rodada posterior de importância reabre `dia` por mistura de sentidos: a projeção final tem **141 acordos, duas rejeições e uma incerteza**. Esses números são decisões de revisão, não cards completos.

## Importância de formas adicionais

Foram vinculadas fontes de paradigma, contextos e um percurso PT-BR autoral explícito. O experimento preliminar propôs 44 das 66 notas ausentes: irregularidade, ambiguidade, imprevisibilidade e pré-requisito para 11 formas. As duas últimas dimensões referem-se somente ao percurso declarado, sem alegar aprendizagem observada.

Uma segunda proposta e seu julgamento produziram dez acordos e uma abstenção: os contextos de `dia` misturam acepções, portanto o sentido agregado continua não resolvido. A rodada final sustenta 40 notas em dez itens; as quatro notas propostas para `dia` não são promovidas como acordo. Permanecem 22 notas desconhecidas de dificuldade de aprendizagem e surpresa de pronúncia. Faltam dados reais de tentativas/erros e um inventário revisado de regras fonológicas. Nenhuma ausência foi convertida em zero.

A grade experimental foi congelada antes dos novos pareceres. Na calibração final, dez casos são utilizáveis e um permanece fora das métricas. A política escolhida usa frequência 0,25, irregularidade 0,75 e limiar 0,25: seleciona `vista` e `viu`, com TP=2, TN=8, FP=0 e FN=0. A calibração preliminar de 11 casos (TP=2/TN=9) permanece preservada, mas não substitui o resultado final mais conservador. Os revisores registraram exposição anterior aos resultados agregados; esta revisão não é apresentada como cega. São resultados ajustados a rótulos de IA nessa pequena amostra, não precisão geral comprovada.

O teste anterior já foi observado e permanece regressão conhecida. Foram reservados 20 documentos reais ainda não usados nos artefatos anteriores, com 90 frases e 2141 tokens lexicais anotados. A seleção excluiu documentos inteiros e textos repetidos antes de qualquer nova avaliação linguística. Isso prepara dados; ainda não mede frequência de formas nem desempenho.

O levantamento inicial procurava `# newdoc id` e não reconhecia `# newdoc_id`; sua afirmação de ausência de limites documentais estava errada. O preflight v2 corrige isso, preserva o original e registra 1475 documentos de treino e 242 de teste. O contrato atual ainda bloqueia o arquivo de corpus compartilhado e as 12 referências comuns de dicionário/currículo. Não foram alterados hashes para contornar essa proteção. Não há nova métrica de generalização aprovada.

## Revisões dos idiomas

Foram executadas proposta e julgamento dos 210 itens de 21 idiomas:

| Resultado | Itens |
|---|---:|
| Acordo lexical entre revisores de IA | 152 |
| Rejeição concordante | 14 |
| Dúvida de evidência ou escopo | 26 |
| Divergência entre os revisores | 18 |

As divergências incluem classe gramatical, construção obrigatória, registro de uso e associação entre sentido e pronúncia. Acordo lexical não atesta frequência do sentido, IPA, qualidade de exemplos ou qualificação de produção. O relatório conserva cada item, hash, resultado e motivo; decisões ausentes não contam como revisadas.

Para croata, foi adquirido e examinado um suplemento concreto de `kuća`, com OMW, seção explicitamente croata do Wiktionary e IPA original do Kaikki. Um julgamento separado corroborou a identidade e a compatibilidade da notação acentual com fontes primárias. Não houve conversão global de `sh` para `hr`. A entrada nativa qualificada de pronúncia e a revisão dos direitos continuam pendentes. Latim conserva seu caminho próprio.

## Cobertura para os decks completos

Foram conferidos os hashes de 24 arquivos de candidatos, aproximadamente 894 MB. EL, PL, RO, RU, FI, CS, HR e ZH têm menos de 3000 lemas distintos nesses preparados. Nos demais, quantidade suficiente de lemas ou IPA bruto também não garante cobertura das identidades frequentes corretas.

As listas antigas de 21 idiomas têm 3000 linhas com POS desconhecido. Core exige lema/classe/sentido, ocorrências atribuídas a sentidos e ranking válido separado dos testes. O bundle coreano possui um caminho próprio; sua lista de aprendizagem não fornece, sozinha, sentidos lexicais qualificados.

Foram preparados 22 inventários de carga: 66000 unidades de conteúdo e 132000 sínteses estimadas sem cache, somente para os cabeçalhos. Formas adicionais acrescem a esse volume e continuam com quantidade desconhecida, sem truncamento. Não há preço ou autorização financeira implícita nesses números. Os lotes Azure anteriores já foram consumidos; nenhuma chamada paga nova foi executada.

## Comandos e reprodução

Prefixo público completo: `multilang native vocabulary qualification ai`.

- `prepare-dictionary-evidence INPUT SHA OUTPUT`: recebe referências `{path, sha256}` de `packet` e `dictionary`, além de limites opcionais. Reconstrói o candidato pelo parser existente e verifica identidade, hash, língua e índice do sentido. Produz `evidence.jsonl`, `supplements.json` e `provenance.json`; os suplementos alimentam `prepare-revision`.
- `review-languages INPUT SHA OUTPUT`: recebe listas `requests` e `results` com referências verificáveis. Revalida os dois pareceres e exige o mesmo pacote preparado; produz `report.json` e `report.html`. Idiomas sem resultado permanecem pendentes. Correções acordadas aparecem junto da identidade original.

Os qualificadores recuperados são evidência adicional; candidatos e decisões históricos não são reescritos. A projeção normalizada agora declara que sua completude não equivale à completude do dicionário original. Strings e Unicode originais são preservados por escape JSON; entradas excessivas ou incompatíveis são rejeitadas.

Evidências locais em `.multilang/verification/deck-completion/`:

- `pilot-user-approval.json`: aprovação vinculada ao pacote exato.
- `pt-pending-result/`, `pt-campaign/`: resolução das três pendências.
- `pt-campaign-final/`: projeção vigente, incluindo a incerteza posterior de `dia`.
- `importance-audit/`, `importance/`: fontes, currículo, grade e experimento preliminar.
- `importance-admitted/`: proposta, julgamento e calibração finais; a versão original da proposta também permanece preservada.
- `fresh-evaluation/v2/`: reserva documental corrigida e motivos exatos que ainda impedem a avaliação.
- `language-reviews-final/`: consolidação dos 210 itens.
- `readiness-audit/`, `hr-review/`, `full-deck-workload/`: cobertura, fontes croatas e cargas.
- `dictionary-recovery-real/`: prova da recuperação no registro real de `trabalho`.

Código, testes e documentação pertencem à entrega; corpora, dicionários e mídia permanecem locais. Campos dos cards, `Image` vazio e prosódia do piloto aprovado são preservados. Deploy permanece fora do escopo solicitado.

## Verificação da implementação

O checkout isolado foi criado a partir do HEAD inicial e recebeu somente os arquivos desta entrega. A regressão dos comandos e serviços de fontes, evidências, revisão, campanhas, calibração e piloto passou: **227 testes**, com rede e provedores proibidos. Os testes específicos dos dois serviços novos estão incluídos nessa execução.

Ruff, a criação de wheel/sdist e a compilação estrita da documentação também passaram. A revisão independente encontrou dois erros no relatório multilíngue — contagem de itens sem dois pareceres e exibição da classe original após uma correção — que foram reproduzidos, corrigidos e verificados novamente. A recuperação do sentido técnico de `trabalho` foi executada pelo comando público contra o dicionário real, preservando seus identificadores históricos.

Essas verificações demonstram o funcionamento das mudanças de código e a integridade dos artefatos examinados. A qualidade linguística dos outros milhares de entradas continua sendo trabalho de dados e avaliação.

## Trabalho restante para as edições completas

1. Separar os contextos de `dia` por sentido, em vez de promover a medição agregada. Resolver também as 44 dúvidas/divergências lexicais da amostra multilíngue; as 14 rejeições exigem substitutos adequados.
2. Validar a política de importância fora da calibração. A proteção atual não distingue referências linguísticas reutilizáveis de observações do corpus: mudar essa regra exige um contrato versionado com proveniência verificável e testes de contaminação. Não basta ignorar hashes de fontes comuns.
3. Ampliar e qualificar o vocabulário frequente, sentidos e pronúncias de cada língua. Os oito preparados com menos de 3000 lemas e a lacuna ampla de IPA croata têm prioridade. Contagem de linhas não substitui revisão e ranking.
4. Congelar as 3000 identidades por idioma e a seleção de formas adicionais, gerar e revisar definições/exemplos/traduções e preparar o orçamento sobre os textos exatos. Somente então há um lote concreto de áudio em escala e uma edição completa para exportar.

As etapas acima não foram declaradas concluídas por esta entrega. A implementação e as revisões executadas deixam resultados verificáveis para continuá-las, sem promover dados ainda incertos a cards finais.
