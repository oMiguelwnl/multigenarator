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
2. Mantenha Inglês + Frequência e clique em Simular produção.
3. Confira as etapas ilustrativas e o resultado com seis registros.
4. Busque uma palavra, filtre pendências, vire o cartão e edite o conteúdo.
5. Alterar uma frase invalida o áudio ilustrativo e exige nova revisão.

Outras configurações podem ser salvas como rascunhos nesta sessão. Os seletores
representam o planejamento; não afirmam suporte qualificado para cada combinação.
Todos os dados são em memória: recarregar descarta rascunhos e edições. As rotas
de demonstração usam `#producoes`, `#nova` e `#resultado`.

Não há chamadas à API, provedores, banco, geração real, áudio real, exportação ou
publicação comercial. Os textos são fixtures da interface, não inventários ou
cartões aprovados. A prévia não é o template final do Anki. Nenhum resultado da
curadoria da arquitetura é copiado ou certificado pelo protótipo.

## Estrutura

`apps/admin/src/` contém a interface administrativa. A separação futura proposta
é `apps/web/` para loja/gerador/biblioteca e `packages/` para componentes
compartilhados; essas pastas serão criadas quando houver consumidores reais.

Decisões e dependências: `docs/product-interface.md`, na raiz do repositório.
