# Melhorias de geração e estrutura — implementação

O [plano de implementação](superpowers/plans/2026-09-13-generation-architecture-improvements.md)
foi executado no projeto existente, conforme a solicitação de dispensar GSD/GSDD.
As mudanças mantêm os comandos públicos e os contratos de exportação.

## Mudanças entregues

- Definições recebem evidência lexical e registram idioma real, origem, fallback,
  rascunho e decisão de qualidade. Ausência de fonte e ambiguidade não promovem
  candidatos automaticamente. O serviço usa cache versionado, tentativas
  limitadas, circuit breaker, logs e limites de transporte.
- O fluxo nativo mantém até 10.000 conceitos conhecidos na validação local e
  envia uma projeção limitada ao modelo. O modo estrito continua rejeitando um
  conceito desconhecido adicional.
- Dez registradores organizam os comandos da CLI. `cli.py` passou de 4.597 para
  1.642 linhas; dependências e configurações continuam substituíveis pela
  interface pública existente.
- Onze serviços foram agrupados nos pacotes de vocabulário, áudio, revisão e
  exportação. Os imports antigos apontam para os mesmos módulos de implementação.
  Os novos serviços de definição ficam no pacote de conteúdo.
- Onze repositórios legados respeitam transações explícitas da aplicação. O
  escopo `repository_transaction` permite composição atômica, inclusive depois
  de leituras que iniciaram uma transação implicitamente, e preserva savepoints.
- A regra de qualidade de tradução passou para o domínio, removendo sua
  dependência de um serviço. O CI verifica todos os módulos e testes com Ruff.

O mapa dos módulos e as regras de transação estão em
[Arquitetura](architecture.md). As mudanças de comportamento, os limites e a
atualização dos índices lexicais estão em
[Qualidade da geração](generation-quality.md).

## Revisão e verificação

Revisões independentes compararam as alterações com uma cópia anterior à
implementação, preservando o trabalho de qualificação linguística que já estava
em andamento. Foram corrigidos problemas de commit em savepoint, serialização
com campos excluídos, escape duplicado de caracteres, cache inválido persistente,
evidência grande demais, leitura de proveniência persistida em JSON e
configurações da CLI que perdiam o ponto de injeção. O orçamento de repetição
das definições também respeita seu limite sem impedir o startup quando a
configuração geral de tentativas é maior. As verificações preservam NFC no
coreano e a correção editorial russa já existente.

As verificações usam providers offline e bancos descartáveis. O registro técnico
local fica em `.multilang/verification/generation-improvements/`, incluindo
relatórios dos revisores, logs e resultados JUnit.

| Verificação | Resultado |
|---|---|
| Regressão integrada final: CLI, conteúdo nativo, geração de texto, cache, exportação e runtime | 193 testes aprovados |
| Repositórios, domínio, segurança e serviços reorganizados | 417 testes aprovados |
| Transações, imports e fronteiras de domínio | 85 testes aprovados |
| Definições e adapters após revisão | 123 testes aprovados; 3 casos de Kiwi real fora dessa seleção, exercitados anteriormente |
| Contexto nativo e serialização | 23 testes aprovados |
| Fluxos legados e fixtures lexicais | 139 testes aprovados na execução ampla; 4 falhas de fixtures corrigidas e cobertas por uma reexecução de 8 testes aprovada |
| CLI de frequência com 3.000 cartões | Cenário isolado aprovado; os dois cenários completos de integração também passaram na execução ampla |
| Ruff em `src`, `tests` e migration nativa | Sem violações |
| Distribuição Python | `sdist` e `wheel` construídos; novos módulos e caminhos de compatibilidade conferidos no wheel |
| Documentação | Build com `mkdocs --strict` aprovado |

As seleções se sobrepõem e seus números não representam um total de testes
distintos. A verificação foi direcionada às áreas alteradas; não foi executada
uma rodada integral de todos os testes do repositório. As falhas das fixtures
foram corrigidas com textos e idiomas coerentes e uma expectativa de erro
atualizada, mantendo as exigências de evidência e os bloqueios de exportação.

## Limites operacionais

A política padrão admite reprodução da fonte ou usa seu fallback. Reescritas
precisam de revisão independente; nenhum aprovador humano é instalado
automaticamente. Índices antigos sem idioma declarado continuam legíveis, mas
precisam receber metadados verdadeiros antes de fornecer definições prontas.

Os testes sintéticos verificam o comportamento do software. A qualidade
linguística de baralhos reais, as aprovações humanas e os direitos de distribuição
dependem das fontes e do processo de
[qualificação linguística](linguistic-qualification.md).
