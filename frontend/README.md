# Multilang — protótipo do estúdio

Interface local em português, React + TypeScript + Vite. O escopo desta entrega é
o painel administrativo: produções, configuração e resultado/revisão. Loja e
gerador público permanecem em planejamento.

A direção visual escolhida é grafite + azul. Paleta, hierarquia, comportamento
responsivo e referências estão em [DESIGN.md](DESIGN.md).

## Executar

Com Node.js 22.20+ e npm, a partir de `frontend/`:

```powershell
npm ci
npm run dev
```

Abra `http://127.0.0.1:5174`. Use `npm test` para as verificações de estado e
`npm run build` para verificar os tipos e empacotar. `dist/` é temporário e ignorado.

Depois do build, `npm run preview:artifact` cria uma prévia HTML independente em
`output/previews/admin-prototype/index.html`. Ela pode ser aberta diretamente,
sem servidor. O código-fonte permanece em `frontend/`.

Em ambientes Windows com certificados corporativos, o Node instalado pode
precisar de `--use-system-ca` em `NODE_OPTIONS` para instalar dependências.
Mantenha a validação TLS habilitada.

## Explorar

1. Abra a produção demonstrativa ou clique em Nova produção.
2. Mantenha Inglês + Frequência + apoio em Português e clique em Simular produção.
3. Confira as etapas ilustrativas e o resultado com seis registros.
4. Busque uma palavra, filtre pendências, veja frente/verso no template Anki e edite o conteúdo.
5. Alterar uma frase invalida o áudio ilustrativo e exige nova revisão.

Outras configurações podem ser salvas como rascunhos nesta sessão. Os seletores
representam o planejamento; não afirmam suporte qualificado para cada combinação.
Editar e salvar um rascunho atualiza a mesma produção; Nova produção começa outro
rascunho. As situações dos cartões aparecem por escrito na lista de revisão.
O idioma de apoio é salvo por rascunho: Português (`pt`), Inglês (`en`) ou
Espanhol (`es`). Coreano aceita apenas Português; selecionar Coreano ajusta o
apoio para Português e avisa sobre a mudança. A escolha aparece no resumo e na
lista de produções. O aplicativo continua em português.

A simulação só usa a combinação dos fixtures: Inglês + Frequência + apoio em
Português. Outras combinações válidas podem ser salvas, sem simulação. O resultado
mostra o idioma dos seus próprios dados, independentemente do rascunho aberto.
Todos os dados são em memória: recarregar descarta rascunhos e edições. As rotas
de demonstração usam `#producoes`, `#nova` e `#resultado`.

## Anexar arquivos

Em Nova produção, escolha uma das modalidades abaixo. A seção Conteúdo e
apresentação mostra o seletor de arquivo:

- Lista personalizada: `.txt` em UTF-8; prefira uma palavra ou expressão por linha.
- Destaques de leitura: exportação do Kindle `.txt`, `.html` ou `.htm`. No TXT,
  os destaques são separados por `==========`. Escolha entre extrair palavras de
  trechos ou usar cada destaque como palavra/expressão. Coreano aceita apenas o
  modo de trechos de leitura.

O limite local é de 5 MB por arquivo. O protótipo verifica extensão, tamanho e
leitura UTF-8; não reproduz os parsers lexicais ou certifica a estrutura Kindle.
Arquivos vazios, binários ou com codificação inválida apresentam erro próximo ao
seletor. Se uma substituição falhar, o anexo anterior é mantido.

É possível conferir até 2.000 caracteres de TXT, substituir e remover o anexo.
HTML é mantido como arquivo, sem renderizar seu conteúdo ou carregar recursos
externos. O arquivo original fica no rascunho em memória, inclusive ao reabri-lo;
nada é enviado ao servidor. Mudar a modalidade remove o anexo anterior com aviso.
Recarregar a página descarta os anexos. Rascunhos incompletos podem ser salvos.

O nome do arquivo aparece no resumo e na lista de produções. Anexar um arquivo
não habilita geração, simulação ou exportação dessas modalidades.

## Integração e limites

Não há chamadas à API, provedores, banco, geração real, áudio real, exportação ou
publicação comercial. A prévia de frente e verso usa o HTML e CSS dos modelos
Anki reais construídos pelos exportadores existentes. Os valores exibidos são
fixtures visuais, não inventários nem cartões aprovados; combinações sem
exportador/template disponível são marcadas como indisponíveis, sem substituição
por um mockup.

O catálogo usado pela interface fica em
`apps/admin/src/anki-template-manifest.json`. Depois de alterar qualquer modelo
Anki, regenere-o na raiz do repositório com
`uv run --project . python scripts/generate_anki_template_manifest.py`.
`tests/services/test_anki_template_preview.py` verifica que o catálogo não deriva
dos templates atuais.

O contrato de idioma de apoio acompanha o commit `bdb0548` da arquitetura.
O commit não foi incorporado por merge/cherry-pick: a adaptação é somente do
protótipo. A futura integração deverá enviar `support_language` explicitamente e
preservar o valor persistido ao retomar um job. Retomada de jobs ainda não existe
nesta interface.

## Estrutura

`apps/admin/src/` contém a interface administrativa. A separação futura proposta
é `apps/web/` para loja/gerador/biblioteca e `packages/` para componentes
compartilhados; essas pastas serão criadas quando houver consumidores reais.

Decisões e dependências: `docs/product-interface.md`, na raiz do repositório.
