# Segunda rodada de qualificação por IA

Plano aprovado na conversa: selecionar pendências, apresentar perguntas específicas e fontes enriquecidas, executar proposta e julgamento separados, consolidar decisões com histórico, distinguir abstenção de decisão negativa e preparar prévia local. Nenhum deploy, chamada paga sem orçamento, alteração dos campos Anki existentes ou incorporação das alterações concorrentes.

## Contratos e decisões

- Reutilizar os contratos imutáveis de revisão existentes. Não alterar a interpretação nem os hashes dos pedidos da primeira rodada.
- Uma rodada nova referencia o resultado anterior, os hashes antigos e novos de cada item e o pacote enriquecido. As perguntas de acompanhamento são tarefas de revisão, não evidência linguística citável.
- Selecionar somente incertezas/divergências; os acordos existentes permanecem identificados pela rodada de origem. Correções que exigem nova análise ou medição continuam explícitas; não redistribuir contagens por suposição.
- A consolidação valida novamente cada resultado e sua relação com o antecessor. Rejeitar itens estranhos, resultados repetidos, rodadas antigas que tentam substituir decisões mais recentes e mistura de idioma/perfil/rubrica.
- A falta de uma nota usada na grade de calibração é abstenção, nunca rótulo negativo. Usar o mesmo conjunto elegível para comparar políticas. Negativo linguístico utilizável é uma análise resolvida com `include=false`.
- A prévia é um artefato local identificado como rascunho de máquina. Não cria recibos humanos, perfis qualificados, mídia fictícia ou autorização de produção. Campos sem conteúdo verificado permanecem explicitamente pendentes.

## Execução

- [x] Testar e corrigir cobertura das métricas; acrescentar diagnóstico de prontidão da calibração.
- [x] Testar e implementar seleção de pendências, classificação de motivos, perguntas específicas e enriquecimento verificável.
- [x] Testar e implementar consolidação de rodadas, rascunho consolidado e relatório de alterações.
- [x] Integrar preparação, consolidação, prontidão e prévia na CLI existente, com arquivos imutáveis e retomada.
- [x] Executar nova proposta e julgamento reais dos 42 itens pendentes de português; importar e reconciliar as respostas.
- [x] Consolidar com os 102 acordos anteriores, gerar relatório e prévia, medir o que realmente ficou resolvido e o que exige outras fontes.
- [x] Rodar verificações relevantes em cópia isolada, revisar segurança/proveniência, atualizar o guia e registrar commits somente desta entrega.

## Critérios de aceitação

Nenhum item perdido ou aprovado por falta de resposta; resultados antigos permanecem reproduzíveis. Alteração de fontes, decisões, contexto, idioma ou inventário é detectada. Testes mostram que notas ausentes não aumentam verdadeiros negativos nem falsos negativos. Retomada reproduz os mesmos artefatos. O piloto e a prévia relatam os limites reais, separando funcionamento do software de suficiência linguística.

## Resultados verificados

- Rodada real: 42 itens revisados por dois agentes em contextos separados; 37 acordos (26 lexicais e 11 de formas), cinco incertezas. Modelo exato desconhecido, registrado como tal.
- Histórico: os 102 acordos iniciais permanecem na origem; a campanha tem 139 acordos e cinco pendências nos mesmos 144 itens.
- Importância: dois rótulos positivos (`vista`, `viu`) e nove negativos em acordo. Os 11 ainda não têm as seis notas subjetivas; quatro grupos não têm consenso. A grade diagnóstica da rubrica completa registra 15 abstenções e zero rótulos utilizáveis. Não há política calibrada ou aprovação de produção.
- Verificação entre itens: dois acordos de `beber` tinham o mesmo identificador de sentido e glosas diferentes. O caso real reproduziu um bloqueio da prévia; a correção preserva ambos em `conflicting_lexical_mappings` e na fila de dúvidas. Permanecem 126 mapeamentos aproveitáveis, 125 identidades propostas e dez cartões na prévia local. As cinco pendências individuais e esse conflito derivado são distintos; a preparação automática seguinte seleciona somente as primeiras.
- Rodadas seguintes: preparação reproduz a raiz contra o pipeline verificado e cada elo contra a projeção anterior; admite lotes e mantém os hashes v1. Reutiliza a mesma evidência, sem fingir aquisição de novas fontes.
- Validação: 248 testes distintos aprovados na cópia isolada (`229` na regressão, `45` na ancestralidade e `70` após a correção do conflito, com sobreposição), Ruff, build de sdist/wheel e documentação estrita. Revisão independente dos vínculos de ancestralidade e da preservação dos conflitos sem achados materiais.

Evidências locais: `.multilang/verification/ai-followup/`. O guia de operação é [Qualificação linguística por IA](../../ai-linguistic-qualification.md).
