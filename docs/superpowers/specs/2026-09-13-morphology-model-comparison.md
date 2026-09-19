# Seleção e comparação de modelos morfológicos

O usuário autorizou implementar a seleção de modelos por idioma e a comparação
automática propostas na conversa. O objetivo é identificar ganhos reais de
precisão e cobertura, com custos de execução visíveis. O trabalho dispensa GSD/GSDD.

## Comportamento

- Perfis `fast`, `balanced` e `accurate` selecionam somente modelos existentes no
  registro Stanza fixado. `fast` preserva exatamente a seleção atual; `balanced`
  usa o pacote padrão sem forçar `nocharlm`; `accurate` usa `default_accurate`.
- A preparação é explícita. Analisar, consultar status e comparar nunca baixam
  arquivos. Perfis compartilham arquivos verificados, mas possuem manifestos
  separados. Manifestos antigos continuam válidos como `fast`.
- Dependências externas de transformers precisam de revisão fixada, hashes dos
  arquivos e carregamento local. Nenhum nome vindo do usuário permite código
  remoto, endpoints arbitrários ou downloads durante inferência.
- `Settings.native_language_model_profiles` permite escolher um perfil por idioma.
  Configuração ausente mantém o caminho atual. Coreano e japonês mantêm seus
  analisadores nativos; variantes Stanza não são aplicadas a eles.
- A CLI permite consultar opções, preparar um perfil, analisar/avaliar com esse
  perfil e executar uma comparação declarada em JSON.

## Comparação

O pedido contém `model_root`, até 22 `datasets` (idioma, caminho, SHA-256 e split
`dev` ou `test`), perfis únicos incluindo `fast`, tamanho da amostra, limite de
tempo por execução e quantidade de threads. Cada execução acontece em processo
separado, sequencialmente, com rede desabilitada e saída limitada. O relatório
registra perfil, artefatos, métricas, cobertura, tempo e pico de memória.

Os perfis de um idioma recebem exatamente a mesma amostra determinística.
Indisponibilidade, timeout, falha e opções equivalentes ficam explícitos. Métricas
incompatíveis continuam nulas. A comparação conserva os denominadores e a regra
de concordância de todos os traços. Diagnósticos por traço distinguem ausência de
campo e diferença de valor, sem alterar a nota original.

Uma recomendação só pode vir do split de desenvolvimento: precisa melhorar pelo
menos uma métrica comparável sem piorar as demais nem a cobertura. Um empate
preserva `fast`. Dados de teste servem para confirmação, sem escolher ou ativar
modelos. Relatórios nunca concedem qualificação linguística ou aprovação humana.

## Limites desta entrega

A entrega torna a escolha e a comparação executáveis. As correções linguísticas
dos adaptadores e treinamento de modelos serão orientados pelos diagnósticos;
esta mudança não inventa mapeamentos UD/UniDic/Sejong para produzir percentuais.
Resultados reais serão registrados com seu escopo, inclusive opções ainda não
preparadas. Nenhum aumento de precisão será anunciado sem medição.

## Compatibilidade e segurança

Preservar trabalho prévio no checkout, índices de Git, contratos Anki, identidades,
revisões e hashes dos manifestos legados. Não executar provedores pagos, alterar
bancos reais, publicar, fazer commit ou usar GSD/GSDD. Rejeitar links simbólicos,
travessia de caminhos, entradas sem limites e alterações nos artefatos fixados.

## Evidência de conclusão

Testes observados falhando antes da implementação cobrem seleção, isolamento de
perfis, integridade, ausência de download implícito, configuração, CLI, isolamento
dos workers, timeout, comparação da mesma amostra e decisão restrita a `dev`.
Executar regressões afetadas, Ruff, build e documentação; realizar revisão
independente do diff desta entrega. Exercitar o fluxo com os dados locais e
registrar separadamente testes sintéticos e medições reais.
