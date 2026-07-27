---
mode: quick
task: 032-adaptar-template-normal-gemini
runtime: opencode
assurance: self_checked
status: human_needed
completed: 2026-07-27
duration: 8m
commits: none
---

# Quick Task 032 Summary: Adaptar template normal ao visual Gemini

O template normal agora usa a paleta escura ergonômica, proporções e hierarquia tipográfica da referência Gemini, preservando integralmente o contrato Anki, o reveal fixo de Translation e a composição CSS do Mandarin.

## Resultado

- O front continua sendo o único DOM de conteúdo; o back reutiliza `{{FrontSide}}` e revela `#translation` com o script fixo preexistente.
- A ordem exata de referências, condicionais de IPA/Image, ambos os áudios, labels e imagem opcional foi preservada.
- O CSS efetivo usa página `#121212`, card `#1E1E1E`, texto `#EAEAEA`, muted `#A0A0A0`, divisor `#333333`, shell de 460px, padding `28px 24px`, borda de 1px, raio de 8px e shadow de referência.
- O hero azul, callout azul e chrome circular azul deixaram de controlar o layout; exemplo e tradução agora seguem o tratamento textual simples da referência.
- Mandarin frequency e word-list continuam iguais, com o CSS normal completo como prefixo e o CSS próprio intacto como sufixo.
- Aceitação visual em Anki Desktop/mobile permanece `human_needed`, conforme o limite explícito do plano.

## Arquivos alterados

| Arquivo | Alteração |
|---|---|
| `tests/services/test_card_template_loader.py` | Regressões selector-aware para o visual Gemini, contratos normais e composição Mandarin. |
| `src/multilang/templates/normal_card.md` | Layout/CSS Gemini, mantendo markup, campos, áudio, mídia e reveal existentes. |
| `.planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md` | Bundle JSON com 11 observações automatizadas e fallback humano Desktop/mobile. |
| `.planning/quick/032-adaptar-template-normal-gemini/032-SUMMARY.md` | Este registro de execução. |

`tests/integration/test_v13_normal_template_export_contract.py` foi executado somente como verificação e permaneceu inalterado.

## TDD: RED → GREEN

1. **Inspeção inicial:** o diff sujo existente foi preservado. A inspeção executável confirmou como `true` os condicionais IPA/Image, ambos os áudios, example panel, Translation oculta, `FrontSide`/reveal, `_balanced_div`, `_last_css_value`, regressão de referências exatas e composição Mandarin.
2. **Teste primeiro:** as expectativas antigas do hero azul foram substituídas por contratos Gemini e verificações de último valor CSS por seletor, antes de editar o template.
3. **RED esperado:** `uv run pytest tests/services/test_card_template_loader.py -q` produziu `1 failed, 23 passed`; a única falha foi a nova expectativa `#121212`, diante do valor ainda implementado `#0a1220`.
4. **GREEN focado:** após a edição do template, o mesmo comando produziu `24 passed`.
5. **GREEN integrado:** loader + suíte de exportação verification-only produziram `29 passed`.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `git diff --unified=0 -- src/multilang/templates/normal_card.md tests/services/test_card_template_loader.py` (inicial/final) | Executado; os hunks preexistentes e finais foram inspecionados sem restaurar o worktree. |
| Inspeções `uv run python -c ...` de anchors e templates gerados | 10/10 anchors preservados e 13/13 observações finais verdadeiras. |
| `uv run pytest tests/services/test_card_template_loader.py -q` (RED) | `1 failed, 23 passed`, falha atribuível somente ao novo contrato Gemini. |
| `uv run pytest tests/services/test_card_template_loader.py -q` (GREEN) | `24 passed`. |
| `uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q` | `29 passed`. |
| `npx -y gsdd-cli ui-proof validate .../UI-PROOF.md` | Incompatível: a versão instalada imprimiu help e não oferece o subcomando `ui-proof`; nenhum passe do validator foi alegado. |
| Parser JSON independente do fence de `UI-PROOF.md` | Válido; 11 observações, campos obrigatórios presentes, artifacts com metadados de privacidade e resultado `human_needed`. |
| `git diff --check --` nos três artefatos do plano | Passou; apenas avisos informativos de futura conversão LF→CRLF nos dois arquivos rastreados. |
| `git diff --cached --name-only` | Vazio; nada foi staged. |

A primeira tentativa do parser JSON local teve erro de quoting porque Bash interpretou os backticks do fence Markdown; a repetição sem backticks literais passou. Isso não alterou arquivos nem evidência do produto.

## Segurança e limites

- Nenhum `innerHTML`, asset externo, referência Anki nova ou JavaScript derivado de campos foi adicionado.
- O único script continua sendo o reveal fixo de `translation` já existente.
- O escopo não foi ampliado para sanitização de campos, conforme a decisão de risco do plano.
- `overflow-wrap`, largura limitada, `box-sizing`, imagem contida e SVG nativo de replay foram mantidos.

## Riscos aceitos e evidência pendente

- O usuário aceitou explicitamente prosseguir apesar do falso-positivo do plan checker sobre executar a suíte preexistente verification-only. A suíte foi apenas executada e não editada.
- Source/test evidence não prova pixels, fontes instaladas, controles nativos ou WebViews do Anki. Permanecem quatro observações humanas: front/back no Desktop e front/back em mobile portrait, incluindo Translation, imagem e áudio.
- `agent-browser` não foi usado porque uma superfície de browser comum não equivale aos WebViews nativos exigidos.

## Estado do worktree e Git

- As mudanças não commitadas anteriores em `normal_card.md` e `test_card_template_loader.py` foram evoluídas, não descartadas.
- Mudanças sujas e artefatos não relacionados no worktree — inclusive outras quick tasks — não foram alterados por esta execução.
- Nenhum `git add`, commit, amend, checkout, reset, clean ou push foi executado.
- **Commit:** ausente por restrição explícita do plano e do usuário.

## Desvios do plano

- **Incompatibilidade de ferramenta:** o `gsdd-cli` instalado não possui `ui-proof validate`; a incompatibilidade foi registrada honestamente e o JSON foi validado por parser independente.
- Fora isso, o plano foi executado dentro dos arquivos e limites declarados.

## Stubs e threat flags

- Nenhum stub impeditivo encontrado nos artefatos alterados.
- Nenhuma nova superfície de endpoint, autenticação, acesso a arquivo, schema ou trust boundary foi introduzida.

## Self-Check: PASSED

- Os quatro arquivos declarados existem e são substantivos.
- A verificação final repetiu `29 passed`, validou o JSON/UI proof e confirmou os limites de segurança no template gerado.
- `HEAD` permaneceu em `d3c915fa1ccc004da2e00206de1ee06d943f54a8`, sem staging ou diff na suíte integration verification-only.
- `git diff --check` passou para os quatro arquivos desta quick task.
