# Interfaces do Multilang — decisões e proposta inicial

## Decisões confirmadas na discussão

- Público: pessoas que estudam idiomas por conta própria com Anki.
- A loja e o gerador pessoal serão lançados no Brasil, com preços e cobranças em real brasileiro (BRL, R$).
- A marca é Multilang. O catálogo público acompanha as edições que o criador produzir e aprovar.
  No lançamento, todas as edições públicas terão explicações e traduções em português do Brasil.
- Idioma inicial da interface: português; suporte a computador e celular.
- Idioma de apoio por deck, separado do idioma estudado e da interface:
  Português (`pt`), Inglês (`en`) ou Espanhol (`es`), conforme contrato `bdb0548`
  da arquitetura. Para Coreano, apenas Português está disponível atualmente.
- Três experiências: operação administrativa, loja de decks e gerador pessoal.
- Loja e Gerador pessoal são sites separados, com entradas e navegação próprias.
  A Loja apresenta e vende edições prontas; o Gerador atende listas e destaques pessoais.
- A conta compartilhada permanece como plano para os dois sites, com compras na
  biblioteca da Loja e produções privadas no Gerador. A administração tem acesso restrito.
- Frequência é o produto central; fundamentos, fonética e gramática complementam
  necessidades específicas de cada idioma. Não há teto de 3.000 cartões.
- Refold é referência conceitual para oferta organizada de materiais, não uma
  identidade visual a copiar nem evidência de resultados do Multilang.
- A Loja segue a lógica comercial das páginas de decks da Refold: benefício de
  aprendizado, conteúdo incluído, amostra e oferta por edição. Seu escopo é vender
  decks; cursos, ferramentas de estudo online e Gerador ficam fora desse site.
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

Lista personalizada e Destaques de leitura incluem anexos locais por rascunho.
Listas usam TXT em UTF-8; destaques aceitam exportações Kindle TXT, HTML ou HTM.
O limite do protótipo é 5 MB por arquivo. É possível substituir, remover e
conferir o início de arquivos TXT; o conteúdo de HTML não é renderizado.
Nome e tamanho ficam visíveis, e o arquivo original é mantido em memória ao
salvar e reabrir o rascunho. Não há envio ao servidor nem geração a partir dele.

Nos destaques, o operador escolhe extrair palavras de trechos (`text`) ou tratar
cada destaque como palavra/expressão (`vocabulary`). Coreano aceita apenas
`text`. Um TXT de destaques usa blocos separados por `==========`; uma lista
simples com uma palavra por linha pertence à modalidade Lista personalizada.

Direção visual escolhida pelo usuário: tema escuro sóbrio, grafite e azul.
Superfícies neutras com níveis distintos, azul reservado a ações/seleção, cores
semânticas para estados e tipografia auxiliar maior. Indicadores compõem um resumo
único. No celular, navegação compacta, formulários empilhados, revisão com lista
horizontal e detalhe abaixo. Tokens e critérios estão em `frontend/DESIGN.md`.

## Organização proposta

O Estúdio usa TypeScript/React. Os dois sites públicos têm diretórios próprios
e abrem localmente, inclusive sem hospedagem:

- Loja: `frontend/apps/web/index.html`, com catálogo, demonstração e ajuda para
  baralhos prontos. O Gerador não faz parte de sua navegação nem de suas seções.
- Gerador pessoal: `frontend/apps/generator/index.html`, com entrada própria e
  instruções para listas e destaques. Upload, revisão, orçamento e geração ainda
  não estão implementados nessa prévia.

Os sites mantêm a marca Multilang e a direção grafite e azul. A primeira
demonstração da Loja reaproveita uma amostra de interface do Estúdio. A integração
futura de catálogo, conta e bibliotecas usará o backend Python/FastAPI existente.
Separar os sites não exige duplicar o motor de geração ou o cadastro do aluno.
Domínios, hospedagem e implantação independente serão definidos posteriormente.
Login e compartilhamento de acesso entre os sites ainda não estão implementados;
as sessões deverão ser restritas a cada site, com permissões impostas pelo backend.
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
- Upload autorizado de arquivos com validação no servidor, limites de tamanho e
  retenção definida. O nome enviado pelo navegador não deve virar um caminho de
  arquivo no servidor. A referência de upload deve alimentar o fluxo de entrada
  existente; o frontend não deve montar comandos de terminal.
- `highlightInput` corresponde a `highlight_input`. A validação local do anexo
  não substitui os parsers de listas/destaques, a análise linguística ou a
  conferência da quantidade final de cartões no backend.
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

## Oferta e copy de lançamento

O benefício central é construir vocabulário para acompanhar séries, livros e conversas
no idioma estudado, com contexto e apoio em português. A chamada aprovada para a Loja
é "Aprenda o vocabulário para acompanhar séries, livros e conversas."
O texto de apoio é "Construa sua base no idioma com decks para Anki, palavras
frequentes, exemplos e explicações em português."
O botão principal "Escolher meu idioma" leva ao catálogo; "Experimentar um cartão"
oferece uma demonstração sem cadastro. O catálogo vazio
informa que ainda não há decks à venda, sem simular estoque ou compra.

A página apresenta o catálogo, explica o papel do vocabulário na compreensão,
detalha os componentes dos decks e responde às dúvidas de compra. Economia de
preparo é um benefício secundário, não a promessa principal. A demonstração atual
continua identificada como amostra de interface; não representa uma edição à venda.

Cada página de produto deverá seguir esta sequência quando houver uma edição aprovada:

1. Nome específico do idioma e objetivo, por exemplo "Vocabulário essencial de inglês".
2. Público, pré-requisitos, seleção do vocabulário e conteúdo incluído. Separar
   identidades lexicais e cartões; não usar faixas de frequência como certificados.
3. Amostra real daquela versão, com frente, verso e os áudios efetivamente incluídos.
4. Preço final em BRL, compra avulsa, entrega e condições de atualização junto à compra.
5. Dúvidas sobre importação, escolha da edição, estudo e atendimento.

Catálogo com busca e filtros por idioma e tipo deve refletir as edições publicadas.
Não oferecer idiomas sem edição aprovada nem adicionar produtos fictícios para
preencher a vitrine. Depoimentos entram após existirem relatos próprios autorizados.

A página de cada edição publicada deverá mostrar exemplos reais daquela
versão, áudio quando incluído, conteúdo, preço total e uma ação de compra. Depoimentos
exigem autorização e origem verificável. Alegações de cobertura dependem da medição
da edição em material independente, com resultados distintos para fala e escrita.
Promessas de aprender mais rápido que outros métodos, superioridade comprovada e
prazos para fluência exigem evidência própria antes de entrar na copy.

Referências consultadas para a estrutura comercial: [catálogo da Refold](https://refold.la/decks)
e [página do deck de espanhol](https://refold.la/decks/buy/fundamental-vocabulary-to-learn-spanish).
O Multilang adapta a apresentação ao seu produto, sem reproduzir resultados,
depoimentos, áudios nativos ou garantias comerciais de terceiros.

Proposta para avaliação pelo criador, em compra avulsa e sem assinatura:

| Oferta | Preço sugerido | Condição |
| --- | --- | --- |
| Uma edição de frequência, um nível | R$ 39,90 | Testar como primeira oferta. Incluir correções dessa edição. |
| Três níveis de frequência do mesmo idioma | R$ 99,90 | Ofertar quando os três estiverem publicados. Economiza R$ 19,80 frente às três compras avulsas propostas. |
| Gerador pessoal | Piloto a R$ 14,90 por até 100 cartões entregues | Validar margem por idioma antes de aceitar pedidos. Mostrar quantidade e total antes da confirmação, reconciliar falhas e oferecer reprocessamento ou restituição proporcional. |

São hipóteses de preço. Uma referência brasileira anuncia por R$ 119 um baralho
de inglês voltado a concursos, para outro público. Antes de aprovar os valores,
descontar do preço taxas, tributos, estornos e suporte; no Gerador, também
texto, tradução, áudio e reprocessamento. Depois de abrir vendas, acompanhar
visita à edição, interação com a amostra, início de pagamento, compra confirmada
e reembolso, com contagens agregadas e sem registrar vocabulário pessoal.
Comparar conversão e margem por edição após mudanças de preço ou copy.
[Referência brasileira](https://voceservidor.com.br/materias/ingles)

## Decisões operacionais para implementar antes da venda

| Área | Direção escolhida | Verificação para abrir ao público |
| --- | --- | --- |
| Autenticação | Catálogo e amostra livres. Uma conta para compras e gerações, acesso por link de e-mail de uso único e curta validade, sessões revogáveis em cookies seguros. MFA obrigatório para operação administrativa. | Testar expiração, segundo uso do link, recuperação de acesso e isolamento de pedidos, anexos e downloads entre duas contas. |
| Backups | PostgreSQL com recuperação pontual e janela de 30 dias. Versões dos pacotes aprovados e manifestos em armazenamento privado. Cópias criptografadas e acesso de restauração separado do usuário de produção. | Metas iniciais de perda máxima de 1 hora e recuperação em até 8 horas. Testar restauração do banco, concessões de acesso e download dos pacotes antes da venda e trimestralmente. Reaplicar exclusões pendentes após restauração. |
| Privacidade | Coletar e-mail, referência do pedido e dados fiscais necessários. Checkout hospedado. Restringir anexos ao titular e ao processamento autorizado. Excluir originais ao concluir ou cancelar, com expiração máxima de 7 dias para abandonados ou falhos. A biblioteca mantém resultados privados até a exclusão ou encerramento aplicável. | Publicar finalidades, bases legais, operadores, transferências, prazos, exceções fiscais e canal de direitos. Verificar exclusão inclusive nos provedores contratados e expiração das cópias. Excluir texto de leitura dos logs, métricas, catálogo e treinamento. |
| Direitos | Licença de uso pessoal nos termos da edição, respeitando as licenças de terceiros. Registrar por edição origem, atribuição e permissão de distribuição comercial de inventário, texto, áudio, imagens e modelos. | Arquivar a evidência e incluir créditos exigidos no pacote e na ficha. Com direito desconhecido, a edição fica em rascunho. Anexos pessoais do Gerador ficam fora do catálogo. |
| Qualificação | O criador aprova uma versão imutável. Validar identidade lexical, sentidos, explicações em português, tradução, alvo na frase, mídia, esquema, GUIDs e contagens. Fazer revisão linguística por amostragem e ampliar a revisão se surgirem erros recorrentes. | Antes de publicar, registrar relatório e responsável, conferir que a amostra corresponde à versão e testar importação e atualização no Anki, inclusive com progresso e imagem pessoal. Retirar a versão da venda se aparecer defeito grave. |
| Suporte | Central curta de importação, áudio, atualização e cobrança; formulário ou e-mail com protocolo, confirmação imediata e acesso ao pedido de cancelamento no site. Meta inicial de primeira resposta humana em até dois dias úteis. | Testar recebimento e acompanhamento no endereço real, definir responsável e publicar identificação do fornecedor, termos, entrega e política de arrependimento. |

Referências para a implementação brasileira: [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
e [Decreto do comércio eletrônico](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d7962.htm).

Hospedagem será escolhida depois da criação do site. Permanecem para aprovação
os preços e a política comercial. O provedor de pagamentos, a primeira edição
qualificada e os fornecedores de infraestrutura serão definidos antes das vendas.
