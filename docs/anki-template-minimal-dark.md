# Template de frequência — Carvão

O cartão principal de frequência usa a paleta **Carvão**, escolhida pelo usuário na comparação: fundo cinza-carvão com degradê discreto, palavra e áudio em azul-gelo, texto principal em branco frio e tradução em cinza-azulado claro. O rótulo “Exemplo” mantém sua posição, tipografia e espaçamento originais, sem painel ou recuo extra. A frente apresenta palavra, IPA disponível, definição, imagem opcional e exemplo; o verso revela somente a frase traduzida, sem o rótulo “Tradução”. A frase original e a tradução compartilham a mesma coluna de texto, uma abaixo da outra.

- [Prévia interativa final](../output/previews/frequency/index.html): sete amostras renderizadas a partir dos templates carregados pelo programa.
- [Template principal](../src/multilang/templates/frequency_card.md): fonte de Frente, Verso e Estilo.
- [Trechos prontos para copiar](../output/previews/frequency/artifacts/frequency-template-parts.zip): variantes principal, inglês e coreano.
- [Deck demonstrativo `.apkg`](../output/previews/frequency/artifacts/multilang-frequency-minimal-dark-demo.apkg): sete notas, cinco modelos de demonstração e três arquivos de mídia.
- [Carvão atualizado `.apkg`](../output/decks/Multilang_Carvao_Ajustado.apkg): seis exemplos com os ícones de áudio sem círculo e o espaço entre frase e tradução reduzido.

Os artefatos em `output/previews/frequency/artifacts/` são entregas locais desta tarefa. O template fica no código; a prévia final, em `output/previews/frequency/index.html`.

## Ajuste atual de áudio e tradução

Conforme a revisão do usuário, os ícones de áudio agora ficam sem fundo e sem borda circular. A área clicável de 44 px permanece. A margem antes da tradução passou de 20 para 12 px; as fontes, as cores Carvão e os demais espaçamentos foram preservados. O `.apkg` atualizado mantém as mesmas notas, cartões, decks e mídia da entrega anterior, com alteração somente do CSS e da data dos modelos. A prévia e os nove trechos do ZIP acompanham o ajuste.

## Histórico: restauração do espaçamento da primeira prévia

O usuário confirmou `output/previews/frequency/proposal.html` como referência de layout: palavra com o IPA embaixo. O espaço antes da tradução foi restaurado de 8 para 20 px, com os 2 px de padding vertical originais. Mantêm-se a paleta Carvão, a ausência do título “Tradução” e o alinhamento das duas frases.

Os valores de fonte já coincidiam com a proposta. A palavra usa `clamp(32px, 5vw, 42px)`, portanto seu tamanho varia com a largura da janela. A comparação no Chromium, em 360, 736 e 1440 px, confirmou a mesma geometria e tipografia da referência após aplicar nela somente a remoção do título e do recuo lateral da tradução. Evidência: `reference-layout-report.json` e capturas `layout-reference-*` / `layout-exported-*`.

Passaram 11 testes focados e as 72 verificações de apresentação existentes. O pacote corrigido preserva integralmente notas, cartões, decks e mídia da entrega Carvão anterior; atualiza apenas o CSS e a data de modificação dos modelos. A inspeção do pacote passou; a importação no Anki nativo não foi executada. A prévia e os nove trechos do ZIP também foram atualizados.

## Novas exportações

O perfil `frequency` agora seleciona `frequency_card.md`. As próximas exportações feitas com este código recebem o visual descrito aqui. Pacotes `.apkg` já gerados e coleções já importadas precisam de uma atualização própria.

Esta alteração preserva os campos, sua ordem, os identificadores de produção e as referências de mídia. O contrato do cartão principal continua sendo:

```text
SortIndex, word, IPA, Definitions, Example Sentence, Translation,
word_audio, sentence_audio, Image
```

`Image` continua vazio na geração e pode ser preenchido manualmente depois. A imagem da amostra simula essa edição posterior.

O inglês mantém os rótulos em português. A frequência em coreano recebe o novo visual com suas fontes e regras de quebra de palavras. A gramática coreana continua usando `normal_card.md`. O mandarim mantém sua base anterior e seu template próprio de pinyin e tons, em frequência e listas pessoais. Os templates independentes de mandarim, japonês, latim, highlights e fundamentos ficam fora deste ajuste visual.

## Aplicar ao cartão principal já existente no Anki

A tela **Cartões… / Cards…**, dentro da edição de uma nota, permite alterar Frente, Verso e Estilo e mostra uma prévia do resultado. A edição afeta todos os cartões que usam aquele tipo de cartão, inclusive em outros decks. [Manual do Anki](https://docs.ankiweb.net/templates/intro.html#the-templates-screen).

1. Abra uma nota de frequência do cartão principal e entre em **Cartões…**. Confira se ela usa os campos listados acima.
2. Guarde o conteúdo atual de **Frente**, **Verso** e **Estilo** em três arquivos para poder restaurá-lo.
3. Extraia o ZIP dos trechos. Use a pasta `en` para frequência em inglês, `ko` para coreano ou `default` para o cartão principal dos demais idiomas com esse contrato.
4. Copie `front.html` para **Frente**, `back.html` para **Verso** e `styling.css` para **Estilo**. Mantenha os campos existentes e o tipo de nota.
5. Confira frente e verso na prévia, salve e experimente um cartão com os áudios da palavra e da frase.

Os trechos acima destinam-se ao cartão principal. Mandarim, japonês e latim usam templates próprios. Cartões de escuta, reverso e lacuna também possuem frentes específicas; eles devem manter essas frentes ao receber adaptações de estilo.

Para desfazer, restaure os três conteúdos guardados. O [template anterior](../src/multilang/templates/normal_card.md) também permanece no repositório como referência; o backup do modelo usado no seu Anki preserva eventuais personalizações e ajustes de idioma.

## Experimentar a amostra

O `.apkg` usa IDs e GUIDs exclusivos de demonstração, distintos dos identificadores registrados para produção. Ele pode ser importado para avaliar o visual; um perfil de teste permite experimentar separadamente da coleção de estudo.

A amostra em português, **casa**, contém áudio de palavra e frase reutilizado de um piloto local do Azure. Esses áudios ainda têm revisão pendente e não representam conteúdo qualificado para produção. Os demais exemplos servem à inspeção visual. Na prévia HTML, todos os ícones de áudio são ilustrativos e não reproduzem mídia.

## Paleta final escolhida: Carvão

Aplicadas exatamente as 13 cores e o degradê da opção Carvão apresentada na comparação. A versão exportada mantém o mesmo HTML de frente e verso, os campos e o alinhamento aprovado. A prévia, o pacote demonstrativo e os trechos para copiar no Anki foram regenerados.

Passaram 11 testes focados no template principal e no contrato de exportação. O Chromium validou 72 estados em 360, 768 e 1440 px; o alinhamento das frases e a posição dos rótulos permanecem idênticos aos anteriores. As capturas de computador e celular foram inspecionadas. Os nove trechos do ZIP foram comparados aos templates carregados pelo programa.

## Histórico: variante ameixa, vinho e cobre

A composição usa uma superfície em degradê discreto, de vinho para ameixa, com palavra em pêssego, texto em marfim, rótulos e áudio em cobre e tradução em rosa suave. O fundo tem uma iluminação sutil e o cartão uma sombra leve. O HTML de frente e verso, as posições, a tipografia e os espaçamentos foram preservados.

O contraste mínimo entre os textos e o ponto mais claro da superfície é de 6:1; a tradução tem contraste de 7,73:1. Passaram 11 testes focados no template e na exportação. O Chromium conferiu 72 estados; as posições e larguras das frases e dos rótulos foram comparadas à versão anterior e são idênticas em todos eles. As capturas de computador e celular foram inspecionadas. A prévia, o pacote e os nove trechos do ZIP foram atualizados a partir dos templates do programa.

## Histórico: restauração da disposição original e alinhamento das frases

Restaurados a paleta grafite, os detalhes verde-sálvia e o estilo original da seção de exemplo. O rótulo “Exemplo” permanece fora da grade das frases, com o espaçamento e a posição originais. Apenas a frase original e a tradução compartilham a mesma coluna; o rótulo “Tradução” continua removido.

Passaram 11 testes focados no template principal e no contrato de exportação. O Chromium conferiu 72 estados, incluindo frente/verso, modo normal/noturno e larguras de 360, 768 e 1440 px, além da interação da prévia e do texto ampliado a 200%. A prévia, o pacote demonstrativo e o ZIP foram regenerados; os nove trechos do ZIP foram comparados aos templates carregados pelo programa.

## Histórico: verificação da variante azul, posteriormente substituída

- 56 testes de templates, exportação e integração passaram; 16 casos de mandarim e japonês foram excluídos deste ajuste do template principal.
- Chromium: 72 estados do template principal, cobrindo seis amostras, frente/verso, 360/768/1440 px e modo normal/noturno. A interação da prévia, o texto a 200% e o foco de teclado também passaram.
- As duas frases compartilham exatamente as bordas esquerda e direita nas três larguras. O rótulo da tradução está ausente; a tradução continua oculta na frente.
- O contraste da tradução sobre o painel é de 7,92:1. As capturas do computador e do celular foram inspecionadas.
- A prévia e o `.apkg` demonstrativo foram regenerados. Os nove trechos do ZIP correspondem exatamente aos templates atuais das variantes `default`, `en` e `ko`.

Durante a verificação, o fluxo dedicado de mandarim recebeu alterações simultâneas. A checagem antiga `test_mandarin_frequency_redesign_does_not_restyle_personal_word_lists` pressupunha a herança do CSS de frequência e falhou com o novo isolamento desse fluxo; ela ficou fora da seleção acima. O teste que ainda exigia o rótulo “Tradução” no cartão principal foi atualizado para a nova apresentação.

Evidências locais: `browser-report.json`, `alignment-color-review.json` e capturas em `output/previews/frequency/artifacts/`. A aparência foi conferida no Chromium; o aplicativo Anki não foi executado neste ajuste.

## Verificação da integração anterior

| Verificação | Resultado |
| --- | --- |
| Suíte de template, campos, exportação e variantes semânticas | 120 testes aprovados em cópia do HEAD com esta alteração |
| Template, perfis e seleção no diretório de trabalho | 41 testes aprovados |
| Integração de exportação no diretório de trabalho, após as alterações paralelas | 5 testes aprovados |
| Chromium, sete amostras × frente/verso × 360/768/1440 px × modo normal/noturno | 84 estados aprovados; sem rolagem horizontal ou conteúdo fora da largura |
| Prévia interativa, texto ampliado a 200% e foco de teclado | Aprovados |
| Inspeção visual | Frente, verso, texto longo, imagem, coreano e variante de mandarim conferidos |
| Pacote e mídia | Campos e templates conferidos no SQLite; três mídias presentes; dois MP3 decodificados |
| Distribuição Python | Wheel construído; recursos `frequency_card.md` e `normal_card.md` presentes e idênticos às fontes |
| Ruff nos arquivos Python desta alteração | Aprovado |

A cópia isolada foi usada porque o diretório de trabalho continha alterações simultâneas em outros fluxos. A integração também passou no diretório compartilhado ao final. Os relatórios e capturas estão em `output/previews/frequency/artifacts/`.

A importação, a reprodução e a atualização de notas existentes no aplicativo Anki não foram testadas. As verificações de tela foram feitas no Chromium, incluindo larguras de celular; AnkiDroid e AnkiMobile não foram executados. Nenhuma coleção pessoal foi modificada nesta tarefa.
