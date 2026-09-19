# Execução da qualificação e preparação dos decks completos

Pedido aprovado: executar as etapas restantes após a aprovação do piloto PT.
Branch: `feature/roadmap-4-0-native-architecture`. Arquitetura nativa, sem workflow GSDD.

1. Congelar o estado inicial, os hashes e um checkout de verificação; preservar alterações concorrentes.
2. Registrar a aprovação do usuário vinculada ao APKG PT exato. A aprovação de apresentação e áudio não equivale a uma licença ou revisão dos demais idiomas.
3. Recuperar evidência original para `trabalho`, `grandes` e `veja`; executar proposta e julgamento separados; consolidar uma nova rodada sem sobrescrever decisões anteriores.
4. Vincular fontes linguísticas às avaliações de importância. Declarar o percurso pedagógico autoral e manter desconhecido qualquer critério sem evidência. Não inventar resultados de aprendizes. Calibrar somente critérios sustentáveis; separar regressão já observada de avaliação nova.
5. Executar a revisão dos 210 candidatos preparados em 21 idiomas, com citações exatas e contextos separados. Conferir sentido, classe, uso e pronúncia selecionada. Preservar reprovações e abstenções.
6. Investigar e preparar uma fonte croata com vínculo explícito de variante, lema, classe e sentido. Não converter indiscriminadamente servo-croata em croata. Conservar o caminho próprio de Latim.
7. Medir por idioma candidatos distintos, identidades, IPA, direitos, ranks e conteúdo/mídia disponíveis. Preparar cargas concretas para três níveis de mil cards, sem completar listas com duplicatas ou sentidos arbitrários.
8. Corrigir lacunas demonstradas do pipeline com testes de regressão antes da implementação. Reutilizar contratos, artefatos e CLI existentes.
9. Gerar conteúdo e pacotes localmente onde as evidências permitirem. Preparar lotes pagos exatos; as autorizações Azure anteriores já foram consumidas e não serão reutilizadas.
10. Verificar os artefatos, executar os testes pertinentes no checkout isolado e registrar resultados e bloqueios específicos. Fazer commits apenas dos arquivos próprios, sem deploy ou publicação de dados/fontes.

Critério de conclusão: evidência executada e verificável para cada etapa. Um pedido preparado, uma lista com 3.000 linhas ou acordo entre modelos não representa por si só um deck completo qualificado. Bloqueios externos devem permanecer explícitos.

Evidências locais: `.multilang/verification/deck-completion/`.

## Estado após a execução

| Etapa | Resultado verificável | Limite restante |
|---|---|---|
| 1 | Estado inicial e checkout isolado preservados | Alterações concorrentes fora desta entrega |
| 2 | Aprovação vinculada ao SHA-256 do APKG de dez cards | Aprovação não estendida aos demais itens |
| 3 | Três pendências PT resolvidas com fontes e pareceres separados | `dia` reaberto na rodada posterior de importância |
| 4 | Dez acordos de importância, 40 notas sustentadas; calibração TP=2/TN=8 | Uma abstenção, 22 notas sem dados e avaliação externa à calibração pendente |
| 5 | 210 revisões: 152 acordos, 14 rejeições, 44 dúvidas/divergências | Expansão e resolução dos itens inconclusivos |
| 6 | Suplemento concreto de `kuća` com fontes croatas e julgamento separado | Qualificação de pronúncia e cobertura HR em escala |
| 7 | 24 arquivos conferidos e 22 inventários de carga preparados | Nenhum Core moderno de 3000 identidades está qualificado |
| 8 | Recuperação de sentido original e consolidação multilíngue implementadas | Evolução versionada da separação de fontes exige contrato próprio |
| 9 | Piloto aprovado preservado e evidências de revisão consolidadas | Conteúdo, orçamento exato, áudio e exportação das edições completas não executados |
| 10 | 227 testes passaram; lint, empacotamento e documentação verificados | Qualidade linguística em escala não é demonstrada pelos testes de código |

Relatório: [qualificação e prontidão](../../deck-completion.md). Os dados da etapa 7 descrevem o inventário congelado anterior às novas revisões; o relatório final distingue esse levantamento das rodadas executadas nesta entrega.
