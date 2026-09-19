# Avaliação documental independente e expansão lexical

> Execução autorizada pelo pedido “faça”, em continuação ao relatório de qualificação. Usar testes antes do código e revisão independente. Permanecer na branch atual, com checkout de verificação isolado e arquitetura nativa.

**Objetivo:** executar uma avaliação real da seleção de formas sem misturar documentos da calibração e ampliar/revisar os candidatos lexicais ainda insuficientes.

**Arquitetura:** extensão optativa `document-partition-evaluation-1`, mantendo os contratos históricos intactos. A fonte CoNLL-U completa comprova documentos, observações, população e denominador. Referências compartilháveis são produzidas por projeção determinística do dicionário, sem exemplos de corpus ou notas de revisão. O experimento congela partições, referências, seleção de itens e grade antes dos novos rótulos de avaliação.

**Tecnologias:** Python/Pydantic, leitores nativos, `measure_form_evidence`, contratos de revisão por IA e Typer existentes. Nenhum provedor pago novo, deploy ou alteração dos campos dos cards.

## Restrições e revisão

- Não reinterpretar `evidence_source_keys` históricos nem remover a proteção de `_source_keys`.
- Documento/frase copiado sob outro ID ou arquivo continua sendo sobreposição.
- Todas as observações que influenciam frequência/população/denominador pertencem à partição verificada, inclusive as não selecionadas para revisão.
- Fontes desconhecidas não podem se declarar referências isentas. Somente projeções verificadas pelo produtor determinístico são compartilhadas.
- Revisão de IA, acurácia de anotações UD e consentimento do usuário são declarações distintas; nenhum resultado habilita produção automaticamente.
- Corpus, dicionário, índices, artefatos e respostas de revisão têm limites, hashes e persistência imutável. Dados brutos permanecem locais.

## 1. Partição documental verificável

Arquivos: `services/qualification_evaluation_partitions.py` e seu teste homônimo.

- [x] Escrever testes vermelhos para fonte adulterada, documento inventado, IDs repetidos, texto copiado e ausência de limites documentais.
- [x] Implementar `DocumentPartitionInput`, `EvaluationDocumentPartition`, `prepare_evaluation_partition`, `verify_evaluation_partition`, `compare_evaluation_partitions` e exportação.
- [x] Preservar todos os frames/tokens originais, seleções/exclusões e as observações derivadas das anotações UD alinhadas. Não atribuir sentidos.
- [x] Comparar conteúdo de documentos/frases, não somente nomes; permitir arquivo comum apenas com prova completa de separação.

## 2. Referências linguísticas reproduzíveis

Arquivos: `services/qualification_evaluation_references.py` e teste correspondente.

- [x] Demonstrar falha para referência genérica autodeclarada, arquivo/hash divergente e projeção adulterada.
- [x] Implementar `DictionaryReferenceInput`, `DictionaryReferenceRegistry`, `prepare_dictionary_references` e `verify_dictionary_references`.
- [x] Projetar somente lema/classe, formas/tags e glosas das identidades selecionadas; excluir exemplos, observações, métricas, rótulos e metadados de revisão.
- [x] Vincular registros à fonte original e ao produtor/versionamento exatos. Reexecutar a projeção antes de aceitar a isenção de compartilhamento.

## 3. Pacotes e experimento congelado

Arquivos: `services/qualification_partition_review.py`, `services/qualification_partition_evaluation.py`, respectivos testes e `qualification_evaluation_cli.py`; registrar subgrupo na CLI de IA existente.

- [x] Testar adulteração de medição, fonte não declarada, ocorrência escondida, mudança de grade/registro após congelamento e partições contaminadas.
- [x] `prepare_partition_review` mede a população inteira, seleciona grupos explicitamente e cria cada `FormReviewItem` com todas as frases distintas do grupo. Se exceder o limite de fontes, rejeitar; não truncar silenciosamente.
- [x] `freeze_partition_experiment` vincula os dois pacotes, as partições completas, registro único e grade/custos de erro. As decisões ainda não fazem parte desse congelamento.
- [x] `calibrate_partition_importance` reutiliza a aritmética/calibração existente após conferir o pacote exato. `evaluate_partition_importance` verifica o experimento inteiro e aplica a política congelada uma vez ao segundo conjunto.
- [x] Expor `ai evaluation prepare-partition`, `prepare-references`, `prepare-review`, `freeze`, `calibrate` e `evaluate`, usando referências `{path, sha256}` e os artefatos nativos.

## 4. Execução e revisão linguística

- [x] Preparar partição de calibração com documentos já conhecidos e a reserva de 20 documentos novos do preflight v2. Medir as duas populações separadamente.
- [x] Fixar seleção determinística de até 20 grupos de avaliação antes de examinar seus rótulos; congelar a grade existente, sem otimizar usando o teste.
- [x] Executar proposta e julgamento reais separados, com fontes, contextos e metadados honestos. Omitir critérios sem evidência e preservar abstenções.
- [x] Executar calibração e avaliação; reportar TP/FP/FN/TN, cobertura e exclusões, sem promover métricas da calibração como generalização.
- [x] Revisar os 44 itens lexicais inconclusivos com as fontes completas; preservar os 14 rejeitados e identificar substitutos fundamentados quando disponíveis.
- [x] Ampliar os preparados EL/PL/RO/RU/FI/CS/HR/ZH usando os registros locais mais completos; medir cobertura antes/depois e escopo de IPA. Nenhum corpus de teste entra no ranking.

## 5. Verificação e entrega

- [x] Rodar os novos testes e regressões pertinentes no checkout isolado; verificar CLI, lint, build e documentação.
- [x] Revisão independente dos contratos, testes de contaminação e alegações dos relatórios.
- [x] Registrar resultados em `docs/independent-evaluation.md` e artefatos em `.multilang/verification/evaluation-expansion/`.
- [x] Preparar commits somente dos arquivos próprios, conferidos por hash; guardar os hashes dos commits executados em `commits.json`. Os decks finais exigem vocabulário/ranking/conteúdo/áudio qualificados; esta execução não substitui esses dados por aprovações artificiais.

## Resultado da execução

- 185 testes, lint, formatação, build e documentação estrita aprovados.
- CLI real: calibração TP2/TN7; avaliação TP1/TN15, 16/20 casos cobertos, quatro abstenções. Nenhum ajuste da grade após a avaliação.
- Revisão lexical: 183 acordos, 18 rejeições e nove incertezas entre os mesmos 210 itens. Foram identificadas 18 alternativas documentadas para próxima revisão.
- Oito fontes ampliadas; 224.774 candidatos nativos e 311 candidatos croatas separados. Nenhuma certificação automática de IPA ou produção.
- Relatório completo: `docs/independent-evaluation.md`; resultados e commits: `.multilang/verification/evaluation-expansion/`.
