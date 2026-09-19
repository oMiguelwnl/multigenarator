# Qualificação linguística assistida por IA

## Objetivo e decisão

Implementar a proposta aprovada pelo usuário: fontes reais → registros e ocorrências verificáveis → proposta por IA → julgamento em contexto separado → validação determinística → acordo ou fila de incerteza → rascunho utilizável de vocabulário e importância. O primeiro exercício usa 20 grafias candidatas de português; o contrato atende os 22 idiomas modernos do catálogo. Grafias candidatas não são identidades pedagógicas já aprovadas.

A coleta, preparação, análise morfológica, medição e pacotes de revisão já existem. A evolução reutiliza esses serviços e acrescenta a execução de revisões por máquina; não amplia artificialmente o contrato histórico de revisão de fundamentos coreanos. A revisão humana autenticada continua disponível com sua semântica original.

## Contratos e autoridade

- Todos os resultados novos declaram origem de máquina e `production_eligible=false`.
- Proposta e julgamento têm IDs de execução/contexto distintos, modelo solicitado/respondido e revisão conhecida ou explicitamente desconhecida. Mesmo modelo em dois contextos não significa independência comprovada.
- O modelo retorna somente decisões tipadas e referências às evidências fornecidas. Metadados de execução são adicionados pelo executor, nunca aceitos como afirmações do modelo.
- Cada decisão vincula pacote, item, tipo e fontes exatas. Trechos e offsets devem reproduzir o texto original NFC. Correções são propostas novas; fontes e contagens permanecem intactas.
- Frequência e dispersão só vêm de observações reais. Frases didáticas geradas não entram como corpus. Não se inventam sentidos, confidências calibradas, licenças, recibos humanos ou qualificação de produção.
- Discordâncias, dados insuficientes e análises inconclusivas ficam numa fila com motivos. Acordo produz mapeamentos de rascunho que podem ser aproveitados sem redigitar tudo.
- Calibração com rótulos de máquina é identificada como tal: mede concordância com esses rótulos. Não substitui avaliação linguística contra referência independente.

## Execução e segurança

O modo local verifica referências `path+SHA`, prepara/reutiliza pacotes e exporta pedidos. A importação offline permite usar agentes desta sessão sem chamadas de API do repositório. A alternativa LiteLLM usa transporte injetável, JSON estrito, timeout, teto de saída, nenhuma ferramenta e nenhum retry oculto. Fontes e propostas são dados não confiáveis, isolados das instruções.

Cada tentativa de API reserva seu custo máximo antes de chamar. Orçamento, preços declarados com origem, limite de chamadas e tokens são explícitos. Retomada verifica as entradas e os artefatos concluídos; não repete chamadas concluídas nem libera reservas de tentativas cujo resultado é desconhecido. Não há chamadas pagas nesta implementação sem orçamento explícito.

O pipeline é local e retomável. Aquisição remota continua pelos adaptadores catalogados existentes, preservando limites, direitos não resolvidos e Retry-After. Referências de observações são explícitas; nunca se escolhe um arquivo pela ordem de glob. Sementes preservam idioma solicitado/efetivo e transformações NFC; `hr→sh` é somente aproximação de sementes, `nb→no` somente host, `zh` não certifica variante. UD test continua separado da calibração.

Quando o pacote apresenta apenas uma amostra por fonte, a projeção para IA pode enriquecer uma nova versão com as demais ocorrências já verificadas e detalhes do registro lexical preparado. Deve vincular os itens ao inventário original, preservar contagens e registrar cobertura/exclusões/limites explicitamente. A fonte e o pacote anterior permanecem intactos; informação já disponível não deve virar uma falsa pendência de aquisição.

## Restrições globais

- Nenhum deploy, push ou merge.
- Nenhuma alteração dos nove campos Anki ou do campo Image vazio.
- Nenhuma alteração ou incorporação da refatoração concorrente.
- Sem dependências novas; Python/Pydantic/LiteLLM/CLI e validadores existentes.
- Sem ativação automática de perfis, redistribuição ou produção.
- Verificar software offline e executar um piloto real de fonte com revisões de agentes identificadas honestamente; exemplos de teste permanecem rotulados como mock.

## Aceitação

Comandos integrados permitem preparar pipeline, exportar proposta/julgamento, importar respostas, reconciliar, produzir rascunho/relatório, estimar e executar chamadas com orçamento e calibrar/avaliar rótulos de máquina. Testes cobrem adulteração, duplicatas JSON, prompt injection como dados, citações/offsets, conflitos, retomada, orçamento e separação de autoridade. O piloto PT20 gera artefatos verificáveis e relata cobertura real, sem afirmar 22 idiomas qualificados.
