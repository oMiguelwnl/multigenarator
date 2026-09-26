# Plano: novo template visual do Anki

Data: 2026-09-20.
Status: prévia aprovada pelo usuário; integração, prévia final e amostra demonstrativa concluídas.

## Objetivo e decisões

Criar um template mais agradável para estudar, com hierarquia clara entre palavra, pronúncia, definição, exemplo e tradução.

**Direção confirmada pelo usuário:** minimalista e escura, com poucos elementos e destaque discreto de cor.

**Escopo confirmado pelo usuário:** cartão de frequência. Começar pelo template principal usado nessa modalidade, incluindo sua aplicação à frequência em coreano e a verificação da herança de CSS do mandarim.

**Sequência confirmada pelo usuário:** ver como ficará antes de implementar. A primeira entrega é uma prévia independente de frente e verso. A integração ao programa fica para depois de o usuário avaliar e aprovar essa proposta concreta.

O usuário respondeu “ok” após receber a prévia, autorizando a integração da proposta. O template foi integrado ao fluxo de frequência. Nenhuma coleção pessoal do Anki foi modificada.

## Resultado da execução

- Criado `frequency_card.md` e registrado no perfil de frequência e no carregador. O template anterior continua atendendo à gramática coreana; o mandarim de listas pessoais mantém a base anterior.
- Preservados os contratos de campos, referências de áudio, identidades e revelação da tradução no escopo desta alteração.
- Entregues a [prévia final](../output/previews/frequency/index.html), um `.apkg` com sete notas de demonstração e os trechos de Frente, Verso e Estilo. As [instruções de uso](anki-template-minimal-dark.md) explicam a aplicação e a restauração em decks existentes.
- A suíte isolada de template/exportação passou com 120 testes. No diretório compartilhado, passaram 41 testes focados e, ao final, os cinco testes de integração de exportação.
- O Chromium validou 84 estados em 360, 768 e 1440 px, os controles da prévia, texto ampliado a 200% e foco de teclado. As capturas foram inspecionadas visualmente.
- O pacote demonstrativo foi inspecionado, os dois MP3 locais foram decodificados e a inclusão dos templates no wheel foi confirmada. Ruff passou nos arquivos Python envolvidos.

Relatórios, capturas, pacote e trechos: `output/previews/frequency/artifacts/`. Os áudios usados na demonstração são de um piloto local com revisão pendente. A importação/reprodução no Anki nativo e os clientes AnkiDroid/AnkiMobile não foram testados.

## Primeira prévia entregue

`output/previews/frequency/proposal.html` mostra a palavra demonstrativa **gather**, definição, IPA, exemplo e tradução revelada por **Mostrar resposta**. O usuário pode experimentar cor de destaque e espaçamento pelos ajustes da prévia quando disponíveis na interface.

Na primeira entrega, foram validados o formato do fragmento e a sintaxe JavaScript. Naquele momento, não havia navegador conectado nem executável disponível. Posteriormente, o Chromium foi instalado com autorização e a prévia final foi verificada. Os controles de áudio das prévias HTML permanecem ilustrativos.

Essa primeira etapa criou apenas o plano e a prévia. Na integração posterior, os exportadores e o mandarim foram relidos para preservar as alterações simultâneas de outras tarefas.

## Diagnóstico anterior à implementação

- `src/multilang/templates/normal_card.md` contém frente, verso e CSS. O estilo efetivo usa fundo escuro, fonte serifada, largura máxima de 680 px e várias regras antigas sobrepostas por declarações finais.
- A frente já apresenta palavra, IPA opcional, definição, imagem opcional e exemplo, com áudio da palavra e da frase. A tradução permanece oculta até o verso. O redesign deve preservar essa sequência de estudo.
- `src/multilang/services/card_template_loader.py` carrega e valida as referências aos campos. A localização dos rótulos de frequência em inglês depende atualmente de trechos exatos de HTML: alterações no markup precisam considerar esse vínculo.
- `src/multilang/domain/source_profiles.py` associa tanto `frequency` quanto `korean-grammar` ao template principal. O carregador acrescenta fontes e regras de quebra específicas para coreano.
- O template de mandarim recebe o CSS do template principal seguido de suas próprias regras. Remover seletores ou alterar regras globais pode afetar essa variante.
- As exportações passam por `src/multilang/services/exporting/package.py` e `src/multilang/services/exporting/fields.py`. Os arquivos antigos `export_anki_package.py` e `semantic_anki_fields.py` são entradas de compatibilidade.
- Os cartões semânticos também usam o carregador. Reconhecimento e formas importantes compartilham a apresentação principal; cartões reversos, de escuta e de lacuna possuem frentes específicas e reutilizam o verso/CSS.
- Highlights/listas pessoais, latim, japonês e fundamentos têm templates próprios. Não devem ser presumidos idênticos ao cartão principal.

## Direção visual proposta

| Elemento | Proposta inicial |
| --- | --- |
| Fundo | Grafite quase preto, com superfície do cartão apenas um pouco mais clara |
| Cores | Texto claro, informação secundária em cinza e um único acento suave, inicialmente verde-sálvia |
| Tipografia | Fonte sem serifa disponível no sistema; manter alternativas adequadas para IPA e alfabetos de cada idioma |
| Palavra | Elemento de maior destaque, aproximadamente 36–40 px no desktop, com redução proporcional no celular |
| Corpo | Aproximadamente 18 px, entrelinha confortável e linhas de comprimento limitado |
| Composição | Coluna única, alinhamento à esquerda, espaços consistentes e separadores discretos |
| Áudio | Controles próximos da palavra/frase, com área de toque confortável e indicação de foco visível |
| Imagem | Bloco opcional com proporção preservada, sem reservar espaço quando o campo estiver vazio |
| Decoração | Bordas e sombra discretas; sem brilhos ou animações decorativas |

Tamanhos e tonalidades são valores de partida para a prévia, não critérios de aprovação rígidos. A informação não deve depender exclusivamente de cor.

## Comportamento de frente e verso

| Conteúdo | Frente | Verso |
| --- | --- | --- |
| Palavra e IPA disponível | Visíveis | Visíveis |
| Áudio da palavra | Disponível | Preservar o comportamento de reprodução do Anki |
| Definição | Visível | Visível |
| Imagem, quando preenchida | Visível | Visível |
| Exemplo e áudio da frase | Visíveis/disponíveis | Visíveis/disponíveis |
| Tradução | Oculta | Revelada junto ao exemplo |

Esse quadro descreve o cartão principal. As frentes específicas de escuta, reverso e lacuna mantêm seus respectivos desafios.

## Etapas de execução

### 1. Preparar a proposta visual

Apresentar primeiro a prévia interativa `output/previews/frequency/proposal.html`, com alternância entre frente e verso e ajustes opcionais de cor e espaçamento. Essa demonstração usa conteúdo fixo e controles de áudio ilustrativos, sem reproduzir mídia.

Depois da avaliação inicial, completar a prévia com amostras suficientes para verificar o desenho:

- cartão curto, palavra longa e definição com várias linhas;
- cartão sem IPA, sem imagem e com imagem;
- conteúdo latino, coreano e mandarim, respeitando os campos de cada variante;
- estados de frente/verso e visualização estreita/larga.

Usar conteúdo demonstrativo e mídia local já disponível. A prévia não deve depender de fontes remotas, geração de novos textos ou síntese paga de áudio. Identificar controles apenas ilustrativos; aparência no navegador não comprova reprodução no Anki.

**Entrega:** proposta concreta de frente e verso para avaliar o visual. Aguardar a aprovação dessa proposta antes de avançar à integração; a escolha de direção minimalista escura não equivale à aprovação do desenho final.

### 2. Integrar o template

Após a aprovação visual, criar `src/multilang/templates/frequency_card.md` e registrá-lo no carregador e no perfil `frequency`. Manter `normal_card.md` para os consumidores fora do escopo, particularmente gramática coreana. Essa separação impede que o redesign de frequência mude silenciosamente outra modalidade.

Preservar as seções que o carregador reconhece e consolidar o novo CSS em uma definição coerente, em vez de acrescentar outra camada de sobrescritas. No mandarim, selecionar a nova base somente para `frequency`; `word-list` mantém sua base anterior. Latim e japonês possuem markup próprio e ficam fora desta primeira proposta do cartão principal; uma adaptação visual desses templates exige prévia própria.

Preservar nomes e ordem dos campos, IDs dos modelos/decks, GUIDs das notas e referências aos arquivos de áudio. A mudança é de apresentação; conteúdo linguístico, quantidade de cartões e divisão por níveis continuam sob os contratos existentes.

Revisar os seletores usados pelo mandarim e as regras acrescentadas para coreano. Se o novo HTML exigir mudar a localização dos rótulos, ajustar esse vínculo em `card_template_loader.py` e verificá-lo nos testes existentes.

Manter a renderização segura já usada pelos exportadores: não interpolar conteúdo dos campos em código JavaScript nem inserir dependências externas. A tradução deve continuar oculta na frente e aparecer no verso, inclusive nos cartões semânticos que reutilizam o template.

**Entrega:** template carregável pelo programa. A prévia final deve ser regenerada a partir das mesmas seções efetivamente exportadas, evitando divergência entre a demonstração e o `.apkg`.

### 3. Validar apresentação e compatibilidade

Atualizar os testes existentes que fixam o visual antigo para refletirem o desenho novo. Preservar as verificações de comportamento e de exportação. Acrescentar testes apenas onde houver uma lacuna relevante, sem transformar cada valor de CSS em um teste isolado.

Executar os testes focados, sem chamadas a provedores:

```bash
MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_semantic_anki_fields.py tests/services/test_native_anki_learning.py tests/integration/test_v13_normal_template_export_contract.py -q
```

Verificar no navegador, em larguras de 360 px, 768 px e 1440 px:

- frente e verso sem texto cortado nem rolagem horizontal;
- conteúdo longo com rolagem vertical natural;
- campos opcionais vazios sem lacunas artificiais;
- acentos, IPA, Hangul e caracteres chineses legíveis;
- áudio alinhado sem comprimir a frase ou sobrepor o texto;
- tradução oculta/revelada corretamente;
- aparência coerente com e sem a classe de modo noturno;
- fontes aumentadas e foco dos controles ainda utilizáveis.

Verificar explicitamente que `korean-grammar`, listas pessoais, highlights e modelos independentes mantêm seus templates anteriores. O mandarim de frequência deve receber a nova base; o mandarim de listas pessoais, a anterior.

Reutilizar as ferramentas de navegador disponíveis no projeto, sem instalar uma nova infraestrutura de testes visuais. Registrar capturas e resultados da prévia final.

**Entrega:** testes focados aprovados e evidências visuais dos tamanhos previstos. Documentar qualquer plataforma não testada.

### 4. Gerar uma amostra importável e instruções

Produzir um `.apkg` demonstrativo com poucos cartões, conteúdo de exemplo e mídia local apropriada. Usar identidades de demonstração separadas das notas de estudo, para que a amostra possa ser experimentada sem reutilizar os IDs de produção.

Inspecionar o pacote para confirmar campos, templates e mídia. Quando houver um cliente Anki disponível, testar a importação em um perfil descartável, a passagem frente/verso e a reprodução dos dois áudios. Registrar separadamente o que foi observado no navegador, no pacote e no aplicativo.

Entregar também os trechos finais de Frente, Verso e Estilo, com instruções para aplicar o visual a decks existentes e recuperar o estilo anterior. Não presumir que editar o repositório modifica arquivos `.apkg` já gerados ou uma coleção já importada. Qualquer teste de atualização de notas existentes deve usar uma coleção descartável e comparar contagem de notas e histórico antes/depois.

**Entrega:** prévia, template integrado, amostra `.apkg` e instruções de aplicação. A compatibilidade com AnkiDroid/AnkiMobile só deve ser afirmada se houver teste nesses clientes.

## Arquivos previstos

| Arquivo | Papel |
| --- | --- |
| `src/multilang/templates/frequency_card.md` | Novo template de frequência, criado após a aprovação da prévia |
| `src/multilang/domain/source_profiles.py` | Direcionamento exclusivo do perfil de frequência |
| `src/multilang/services/card_template_loader.py` | Registro, seleção da base do mandarim e localização dos rótulos |
| `tests/services/test_card_template_loader.py` | Contratos do template, compartilhamento de CSS e variantes |
| `tests/services/test_export_anki_package.py` | Modelo e exportação `.apkg` |
| `tests/integration/test_v13_normal_template_export_contract.py` | Integração e campos exportados |
| `tests/services/test_semantic_anki_fields.py` | Ajustes apenas se houver lacuna de regressão nas variantes semânticas |
| `output/previews/frequency/proposal.html` | Proposta independente mostrada antes da implementação |
| `output/previews/frequency/index.html` | Prévia final derivada do template após a integração |
| `docs/anki-template-minimal-dark.md` | Uso, instalação e recuperação do estilo anterior |

Artefatos de verificação e a amostra `.apkg` podem ficar em `output/previews/frequency/artifacts/`. A escolha do nome do diretório não implica dependência do antigo fluxo GSD.

## Critérios de conclusão

1. O novo visual segue a direção minimalista escura confirmada pelo usuário.
2. Frente, verso, campos opcionais e controles de áudio estão organizados e legíveis nos tamanhos previstos.
3. A tradução mantém o comportamento atual; os campos e identificadores de produção permanecem compatíveis.
4. Coreano, mandarim e variantes semânticas atingidas pelo compartilhamento do template foram verificados.
5. A prévia final corresponde ao HTML/CSS que o programa realmente exporta.
6. Há uma amostra importável e instruções claras para aplicar o template.
7. Os resultados distinguem verificações automáticas, inspeção visual e testes realizados no Anki; limitações são registradas.

## Fora do escopo inicial

Recriação de conteúdo, geração de áudio, alteração de banco de dados, mudanças de pipeline, novos modos de estudo, gerenciamento de múltiplos temas e redesign dos demais templates independentes. A gramática coreana não deve herdar o novo visual apenas por compartilhar o template anterior.
