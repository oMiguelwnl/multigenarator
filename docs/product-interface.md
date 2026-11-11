# Interfaces do Multilang — decisões e proposta inicial

## Decisões confirmadas na discussão

- Público: pessoas que estudam idiomas por conta própria com Anki.
- Idioma inicial da interface: português; suporte a computador e celular.
- Idioma de apoio por deck, separado do idioma estudado e da interface:
  Português (`pt`), Inglês (`en`) ou Espanhol (`es`), conforme contrato `bdb0548`
  da arquitetura. Para Coreano, apenas Português está disponível atualmente.
- Três experiências: operação administrativa, loja de decks e gerador pessoal.
- Loja e gerador compartilham conta e biblioteca; administração tem acesso restrito.
- Frequência é o produto central; fundamentos, fonética e gramática complementam
  necessidades específicas de cada idioma. Não há teto de 3.000 cartões.
- Refold é referência conceitual para oferta organizada de materiais, não uma
  identidade visual a copiar nem evidência de resultados do Multilang.
- Painel deve acomodar todos os tipos existentes, conforme capacidades qualificadas.
- Operador configura, inicia e confere o resultado final; validações automáticas
  permanecem durante a execução. Revisão humana intermediária não é o padrão.
- Cartões reais ainda dependem das mudanças e curadoria da branch de arquitetura.
- Geração de texto, tradução, áudio e decks reais continua adiada.

## Entrega atual

Protótipo local navegável de Produções, Nova produção e Resultado/revisão.
Busca, filtros, edição, frente/verso, rascunhos e processamento simulado permitem
discutir o fluxo. Fixtures em memória; sem chamadas de rede da aplicação.
São seis registros fictícios de interface em inglês, com cenários de conclusão,
revisão e falha. Indicadores e tempos não representam execução real.
Os registros usam Português como idioma de apoio. O seletor permite salvar
rascunhos com outras opções válidas; a simulação fica disponível apenas para
Inglês + Frequência + apoio em Português. O idioma de apoio aparece na lista,
no resumo da configuração e no resultado. Alterar um rascunho não relabela os
cartões demonstrativos de outra produção.

Direção visual escolhida pelo usuário: tema escuro sóbrio, grafite e azul.
Superfícies neutras com níveis distintos, azul reservado a ações/seleção, cores
semânticas para estados e tipografia auxiliar maior. Indicadores compõem um resumo
único. No celular, navegação compacta, formulários empilhados, revisão com lista
horizontal e detalhe abaixo. Tokens e critérios estão em `frontend/DESIGN.md`.

## Organização proposta

Frontend TypeScript/React; backend Python/FastAPI existente. Dois aplicativos
futuros em `frontend/apps/admin` e `frontend/apps/web`; componentes extraídos para
`frontend/packages` quando compartilhados. Esta entrega inicia apenas admin.
O backend precisa impor permissões; ocultar controles no navegador não autoriza
ou restringe acesso a dados. Não colocar credenciais de provedores no frontend.

## Contratos a alinhar com a arquitetura

- Inventários versionados, identidade lexical, sentidos, formas e evidências.
- Matriz de modalidades disponíveis por idioma, com pré-requisitos e bloqueios.
- Listagem e detalhes de produções com contagem separada de identidades e cartões.
- Estados por etapa/item, erros recuperáveis e regras reais de retomada/cancelamento.
- Leitura/edição de versões, invalidação de dependências, revisão e aprovação.
- Entrega autorizada de áudio e downloads; prévia baseada nos templates reais.
- Edições aprovadas e preservação de GUIDs na exportação e atualização.
- Persistência de rascunhos e histórico; permissões por proprietário.
- `supportLanguage` do protótipo corresponde a `support_language` (`pt`, `en`,
  `es`) do backend. Novas produções devem enviar a escolha explícita, com Português
  como padrão da interface, sem depender da política legada de valor ausente.
- Na retomada, usar o idioma de apoio persistido no job, em modo somente leitura;
  não sobrescrever jobs antigos que tenham valor ausente com o padrão de novas
  produções. O backend continua responsável por rejeitar mudanças e combinações
  inválidas. Ainda não há fluxo de retomada no protótipo.

A branch visual deriva de `75af417` da arquitetura. Alterações posteriores não
chegam automaticamente: combinar contratos e incorporar mudanças explicitamente.
O contrato de idioma de apoio foi espelhado a partir de `bdb0548`, sem incorporar
esse commit do backend à branch visual.
Não substituir a fila existente nem executar comandos construídos do formulário.

## Etapas posteriores propostas

1. Avaliar o protótipo e definir estados/interações com o backend.
2. Integrar o painel a capacidades efetivamente disponíveis.
3. Construir loja: catálogo por idioma, página de produto, amostra, compra,
   biblioteca, instruções de importação e atualizações.
4. Construir gerador pessoal: lista/contexto, conferência de sentidos, configuração,
   consumo previsto, acompanhamento, revisão e download privado.

## Decisões ainda abertas

Nome/identidade comercial, idiomas e edições de lançamento, preço/cobrança,
pagamentos, limites e créditos, atualização de produtos, suporte, hospedagem,
autenticação, backups, privacidade, permissões de distribuição e qualificação
final de cada produto. Compra avulsa e gerador por créditos são propostas,
não decisões fechadas. Cobertura lexical e compreensão não podem ser inferidas
do número de cartões nem de alegações de outros produtos.
