---
task: 061-output-deck-design
type: quick
assurance: self_checked
---

# Quick Task 061: Lógica e protótipo de decks de produção oral

## Objetivo e limites

Entregar a lógica completa e um protótipo visual interativo de cards de produção oral, com perguntas em inglês. Definir uma família de decks própria, com três níveis de 1000 cards por idioma, temas propostos, instruções gramaticais, contexto, respostas válidas e áudio da frase no verso. Nesta etapa, entregar design e mock: não implementar gerador, API, APKG, síntese, gravação ou avaliação automática de fala.

**Baseline:** app Python/Typer; `SupportedLanguage` contém 23 idiomas, incluindo `la`; note types e templates existentes são separados. Explicitar o tratamento de inglês como língua-alvo quando a língua de origem também é inglês, e a política própria do latim. Preservar mudanças prévias do usuário em `src/`, templates e testes. Não alterar SPEC, ROADMAP ou arquivos de produção. O role `.planning/templates/roles/planner.md` está ausente; planejamento adaptado ao contrato quick recuperado, sem restaurar arquivos removidos. As instruções AGENTS atuais dispensam fluxo GSD obrigatório.

<tasks>
<task id="061-01" type="auto">
  <name>Especificar o deck e seus critérios de qualidade</name>
  <files>docs/output-deck-design.md</files>
  <action>Documentar objetivo oral; frente/verso; tentativa antes da revelação; estrutura gramatical em vez de “classe da frase”; contexto e registro; currículo em três níveis; matriz de temas proposta; uma dificuldade principal por card; dicas graduais; alternativas naturais; rubrica de autoavaliação; áudio após resposta; campos e identidade estável; adaptação linguística; pipeline futuro e revisão. Separar decisões confirmadas, propostas e questões futuras. Incluir exemplos concretos e melhorias úteis sem prometer pontuação automática, aceitação de qualquer tradução ou eficácia comprovada do desenho.</action>
  <verify><automated>python3 -c 'from pathlib import Path; p=Path("docs/output-deck-design.md"); assert p.is_file() and len(p.read_text()) in range(5001, 1000000); print("Design substantivo presente")'</automated>Revisar coerência entre campos, exemplos, rubrica, escopo multilíngue e contagens de níveis.</verify>
</task>
<task id="061-02" type="auto">
  <name>Criar o protótipo visual e verificar os estados</name>
  <files>docs/prototypes/output-deck.html; preview e evidências locais opcionais em .multilang/verification/output-deck-design/</files>
  <action>Criar fragmento HTML/CSS/JS apropriado para visualização inline, com exemplos, frente, dicas, verso, autoavaliação demonstrativa e temas claro/escuro. Marcar áudio como demonstração sem som real. Usar conteúdo fixo e fontes locais, sem chamadas a provedores. Se necessário, criar wrapper standalone local. Verificar disposição, legibilidade, ausência de overflow e funcionamento de revelar/dicas/reiniciar nas larguras 360 e 736 pixels.</action>
  <verify><automated>python3 -c 'from pathlib import Path; p=Path("docs/prototypes/output-deck.html"); s=p.read_text(); assert len(s) in range(5001, 1000000) and chr(60)+"style" in s and chr(60)+"script" in s; print("Protótipo presente")'</automated>Inspeção renderizada e interação com ferramenta de navegador disponível; registrar falha ou indisponibilidade sem alegar verificação visual concluída.</verify>
</task>
</tasks>

## ui_proof_slots

| slot_id | claim | route_state | required_evidence_kinds | minimum_observations | expected_artifact_types | validation_command | environment | viewport | manual_acceptance_required | claim_limit |
|---|---|---|---|---|---|---|---|---|---|---|
| output-layout | Frente e verso permanecem legíveis em claro/escuro | preview local: frente e verso, ambos os temas | runtime, screenshot | 8: 2 larguras × 2 temas × 2 faces | screenshots locais e registro de observações | `python3 -m http.server 8765 --bind 127.0.0.1 --directory .multilang/verification/output-deck-design` + navegação/resize/screenshot pela ferramenta disponível | navegador local, wrapper do mesmo fragmento | 360×800 e 736×900 | false | apenas mock renderizado, sem aceitação de clientes Anki |
| output-interaction | Dica, revelação e reinício funcionam sem antecipar a resposta | frente → dica → verso → reinício | runtime | 1 ciclo completo por largura | registro local de interação | mesma URL local + interações pela ferramenta disponível | mesmo navegador | 360×800 e 736×900 | false | áudio é placeholder; sem síntese, reprodução, gravação ou avaliação real |

Disponibilidade: preferir `agent-browser` se instalado (`command -v agent-browser`); caso ausente, usar navegador integrado disponível ou runner de navegador já existente no projeto, registrando a ferramenta efetivamente usada. Não instalar frameworks para esta entrega. Evidências devem identificar estado, viewport, tema, observação, resultado e caminho. Metadados padrão: `visibility=local_only`, `retention=local_task_artifact`, `sensitivity=synthetic_content`, `safe_to_publish=false`. A inspeção não comprova validação linguística nativa nem entrega de deck estudável.
