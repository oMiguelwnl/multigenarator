# Multilang — Graphite + Blue

## Direção

O estúdio usa uma linguagem de software operacional: superfícies grafite,
tipografia de interface e azul reservado para ações, foco e seleção. A
interface prioriza a leitura de produções, a configuração de rascunhos e a
revisão dos cartões.

Não há imagens de banco, gráficos decorativos, gradientes ou dados promocionais.
As telas de produção, progresso, histórico e cartões continuam explicitamente
demonstrativas. A tela de conexões permanece ligada ao serviço local, sem
expor credenciais na interface.

## Paleta

Os tokens em `apps/admin/src/styles.css` são a fonte de verdade.

| Papel | Token | Cor |
| --- | --- | --- |
| Fundo | `--canvas` | `#101318` |
| Navegação | `--sidebar` | `#0C0F14` |
| Superfície | `--surface` | `#171C24` |
| Superfície elevada | `--surface-raised` | `#1D2430` |
| Texto principal | `--text` | `#EEF2F8` |
| Texto de apoio | `--text-muted` | `#9DAABD` |
| Ação principal | `--accent` | `#3568E8` |
| Foco, links e seleção | `--accent-text` | `#98B9FF` |
| Seleção de fundo | `--accent-soft` | `#1B2B48` |
| Concluído | `--success` | `#7DD3B0` |
| Revisão necessária | `--warning` | `#E8BF79` |
| Incompleto | `--danger` | `#F1A5AC` |

O azul identifica ações e seleção; neutros preservam a hierarquia das telas
operacionais. Rótulos de estado acompanham as cores, sem depender delas.
Controles têm bordas mais fortes que separadores. A fonte do sistema evita
requisições externas.

## Composição e acessibilidade

- Navegação lateral em telas largas; em telas menores, marca e botão Menu
  abrem uma folha de tela inteira com links em alvos de 56 px.
- A visão geral agrupa contagens numa faixa e aproxima o próximo item de
  revisão da lista de produções.
- Formulários, resumo do rascunho, estados vazios e revisão preservam a ordem e
  o conteúdo existentes.
- Tabelas e a faixa de cartões podem rolar dentro das próprias regiões; a página
  não precisa rolar horizontalmente.
- Menu móvel expõe seu estado, fecha por seleção ou Escape, mantém o foco no
  menu e o devolve ao botão ao fechar. Alvos têm pelo menos 44 px, foco visível,
  nomes acessíveis e campos legíveis em telefone. Animações respeitam
  `prefers-reduced-motion`.
- Hashes, estados demonstrativos, regras do formulário e fluxos locais de
  credenciais não dependem da composição visual.

## Verificação

`npm test` cobre regras do protótipo, arquivos de origem e prévia Anki;
`npm run build` verifica tipos e empacota a interface. Esses comandos não
substituem uma revisão visual e de acessibilidade em navegadores.
