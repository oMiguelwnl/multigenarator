# Conclusão do piloto linguístico — plano de implementação

> Execução aprovada na conversa. Usar testes de comportamento antes das mudanças e revisão independente das integrações. A autorização existente dispensa repetir perguntas de aprovação do desenho.

**Objetivo:** concluir o percurso de fontes a um piloto APKG com dez cards PT e preparar/operar a mesma execução por idioma, registrando qualquer dado ou autorização realmente indisponível.

**Arquitetura:** novos contratos de revisão dirigida e projeção de observações integram os serviços de qualificação. O piloto reutiliza os contratos nativos de conteúdo/áudio/exportação, sem promover avaliações de máquina a aprovação humana ou alterar o Core.

**Stack:** Python, Pydantic, pytest, serviços nativos, Azure Speech configurado, genanki.

**Spec:** [Desenho aprovado](../specs/2026-09-19-machine-pilot-completion-design.md).

## Restrições globais

- Nenhum deploy/push/merge, nenhum GSDD operacional, nenhuma mudança dos fields Anki.
- Preservar revisões v1, corpus original e alterações concorrentes; registrar novos hashes para derivações.
- Não fabricar fontes, contagens, testes de aprendizes, recibos humanos, mídia ou identidade do modelo.
- Azure real depende de orçamento delimitado. Importação de mídia deve conferir texto, locale, voz, hash e integridade.
- Prototipagem local e aceitação de produção são estados distintos e visíveis.

## Foco da revisão

Reabertura de um acordo ultrapassado deve falhar; suplemento alterado deve falhar; uma ocorrência não pode ser contada em dois sentidos; conflito entre glosas não pode desaparecer silenciosamente; falta de áudio ou aprovação não pode virar mídia fictícia ou habilitar produção. Incluir testes dessas condições nas respectivas tarefas.

## 1. Revisão dirigida, conflitos e dados derivados

Arquivos: criar `services/qualification_machine_revision.py` e seus testes; integrar `qualification_machine_campaign.py` e uma CLI própria de revisão dirigida. O novo plano consome a campanha verificada, IDs efetivos, motivo e fontes suplementares verificadas; produz pacote e proveniência por item. Preservar `MachineFollowupPlan` v1. A campanha passa a aceitar planos novos sem mudar a interpretação de rodadas antigas.

- [x] Testar reabertura de dois acordos conflitantes, seleção limitada, cobertura exata, contexto novo, rejeição de stale/tampering e replay v1.
- [x] Implementar plano dirigido e sua consolidação, com comandos de preparação/importação existentes reutilizados.
- [x] Corrigir a leitura de `newdoc_id` em novas importações CoNLL-U, mantendo o formato anterior e documentando o novo comportamento.
- [x] Implementar projeções versionadas por ocorrência, com correspondência de texto/offset/fonte e nova medição pelo serviço existente.
- [x] Executar revisão real de `beber` e dos cinco casos PT; aplicar somente decisões sustentadas, com proposta e julgamento em contextos distintos.

Verificação mínima: uma revisão antiga não substitui decisões novas; `aberto` pode ser derivado como ADJ citando gold real; `veja` mantém a distinção entre `Mood=Sub` da fonte e função diretiva; duas ocorrências de `boa` nunca produzem quatro contagens.

## 2. Importância: evidência e avaliação

Reutilizar `qualification_machine_calibration`, `form_evidence` e os corpora locais de calibração/teste. Criar adaptadores de pacotes somente onde os formatos existentes não atendem.

- [x] Preparar fontes/notas disponíveis por dimensão e registrar as 66 avaliações inicialmente ausentes.
- [x] Executar calibração exploratória com critérios sustentados, sem apresentar a grade reduzida como rubrica integral.
- [x] Medir ocorrências do corpus de avaliação congelado, preparar rótulos de importância e executar revisão independente.
- [x] Avaliar a política congelada no conjunto separado e publicar cobertura, abstenções, falsos positivos e falsos negativos.

Verificação mínima: nenhum vazamento de corpus entre calibração e avaliação; rótulos vêm de decisões reais, ausência não vira zero; métricas declaram concordância com avaliações de máquina e tamanho da amostra.

## 3. Conteúdo, áudio e APKG do piloto

Criar `services/qualification_machine_pilot.py`, módulos auxiliares focados se necessários, CLI `qualification_pilot_cli.py` e testes. Reutilizar a exportação semântica modelo B e contratos nativos, com tudo de origem máquina/pending.

- [x] Testar seleção de mappings sem conflitos, IPA vinculada ao candidato/variante, pedidos imutáveis e importação de conteúdo/julgamento completos.
- [x] Implementar geração por arquivos e validação do conteúdo, análise local do alvo e julgamento independente, sem `ReviewedSenseBinding` fictício.
- [x] Preparar manifestos Azure com limites e retomada; executar áudio real somente com teto disponível, ou importar mídia real exata já disponível.
- [x] Exportar dez cards com áudio real, campos preservados, GUIDs estáveis e `Image` vazio.
- [x] Verificar SQLite/ZIP/mídia do APKG, ausência de placeholders e retomada sem duplicações. Conferência em cliente Anki, quando disponível, deve ser registrada separadamente.

Verificação mínima: arquivo ausente, alterado ou de outro texto/voz falha; pacote completo exige vinte mídias verificadas para dez cards. Nenhuma configuração de produção é habilitada pelo piloto.

## 4. Execução por idioma e entrega

Criar inventário/manifesto de lote por idioma a partir dos candidatos e perfis existentes; registrar variantes e impedimentos. Reutilizar os mesmos serviços e testes em todos os códigos suportados.

- [x] Preparar lotes pequenos dos 22 idiomas modernos e manter o caminho de Latim separado. Resultado: 21 lotes de dez; croata bloqueado por falta de IPA nas fontes disponíveis.
- [x] Executar o que as fontes, pronúncia e autorização permitem; registrar resultados e bloqueios específicos de cada idioma. PT tem o piloto completo; os novos lotes ainda exigem julgamento de conteúdo e pronúncia, além de orçamento próprio para áudio.
- [x] Rodar regressão relevante em checkout isolado, Ruff, build e documentação estrita. Resultado: 179 testes distintos passaram, assim como Ruff, wheel/sdist e MkDocs estrito.
- [x] Revisão independente final, correções verificadas e commits por domínio contendo somente arquivos desta entrega.

## Registro de execução

- Revisão PT executada: `beber` unificado, 128 mapeamentos lexicais sem conflito e seis projeções por ocorrência. Três dúvidas nos registros agregados permanecem explicitamente inconclusivas.
- Importância: 66 avaliações da rubrica integral registradas como indisponíveis. Calibração e teste separado executados com frequência medida; a política exploratória não selecionou os 14 casos positivos consensuais do teste e não foi promovida.
- Piloto PT: dez conteúdos julgados separadamente, análise local completa dos exemplos, vinte áudios Azure reais, 384 caracteres, sem repetição, dentro do lote autorizado pelo usuário. APKG exportado e verificado: dez notas/cards/GUIDs, vinte mídias válidas e Image vazio. Abertura nos clientes Anki ainda pendente.
- Revisão independente corrigiu dois problemas: IPA vinculada a lema/POS antes de uma correção e leitura de mídia antes da verificação de limites. Regressões reproduziram as falhas antes das correções.
- Expansão exportada e conferida em `languages-v2/`: 21 pedidos, 210 candidatos, hashes válidos, dez lemas distintos por língua; croata bloqueado e Latim separado. A preparação não executou chamadas de provedores nem declarou novos idiomas qualificados.


Evidências e decisões operacionais: `.multilang/verification/ai-completion/`. Análise inicial confirmou IPA PT disponível, mídia PT ausente e configurações de provedores presentes sem validar a conta. O plano não considera uma configuração presente como autorização irrestrita de gasto.
