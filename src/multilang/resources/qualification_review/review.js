"use strict";
(() => {
  const packet = JSON.parse(document.getElementById("packet").textContent);
  const byId = new Map(packet.items.map(item => [item.item_id, item]));
  const decisions = new Map();
  const edits = new Map();
  const kinds = {lexical: "Verbete", form: "Forma", case: "Caso"};
  const states = {pending: "Sem decisão", accepted: "Aceitar", corrected: "Corrigir", rejected: "Rejeitar", inconclusive: "Inconclusivo"};
  const criteria = {frequency: "Frequência", irregularity: "Irregularidade", unpredictability: "Imprevisibilidade", ambiguity: "Ambiguidade", unexpected_pronunciation: "Pronúncia inesperada", prerequisite: "Pré-requisito", learning_difficulty: "Dificuldade"};
  let page = 0;
  const pageSize = 10;
  const $ = id => document.getElementById(id);
  const node = (tag, text, cls) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = String(text);
    if (cls) element.className = cls;
    return element;
  };
  function message(text, error = false) {
    $("message").textContent = text;
    $("message").className = error ? "error" : "";
  }
  function field(parent, label, value = "", type = "text") {
    const wrapper = node("label", label);
    const input = document.createElement(type === "textarea" ? "textarea" : "input");
    input.setAttribute("aria-label", label);
    if (type !== "textarea") input.type = type;
    input.value = value === null || value === undefined ? "" : String(value);
    input.maxLength = type === "textarea" ? 2000000 : 4096;
    wrapper.append(input);
    parent.append(wrapper);
    return input;
  }
  function select(parent, label, options, value) {
    const wrapper = node("label", label);
    const input = document.createElement("select");
    input.setAttribute("aria-label", label);
    for (const [key, text] of Object.entries(options)) {
      const option = node("option", text); option.value = key; input.append(option);
    }
    input.value = value;
    wrapper.append(input); parent.append(wrapper);
    return input;
  }
  function object(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
  function keys(value, allowed, required = []) {
    if (!object(value) || Object.keys(value).some(k => !allowed.includes(k)) || required.some(k => !Object.hasOwn(value, k))) throw Error("Campos JSON ausentes ou desconhecidos.");
  }
  function rating(value) {
    if (typeof value !== "string" && typeof value !== "number") throw Error("Nota inválida.");
    if (String(value).trim() === "" || !Number.isFinite(Number(value)) || Number(value) < 0 || Number(value) > 1) throw Error("As notas devem estar entre 0 e 1.");
  }
  function resolvedSense(value) {
    if (value !== null && value !== undefined && (typeof value !== "string" || !value.trim() || ["unknown", "unresolved", "none", "null", "?", "unk", "x"].includes(value.trim().toLowerCase()))) throw Error("Informe um sentido resolvido. Use o campo vazio para sentido ainda desconhecido.");
  }
  function tokens(value, text) {
    if (!Array.isArray(value) || value.length > 4096) throw Error("Lista de tokens inválida.");
    const characters = Array.from(text);
    let previous = 0;
    for (const token of value) {
      keys(token, ["start", "end", "text", "lemma", "pos", "sense_id", "features"], ["start", "end", "text", "lemma", "pos"]);
      resolvedSense(token.sense_id);
      if (!Number.isInteger(token.start) || !Number.isInteger(token.end) || token.start < previous || token.end <= token.start || characters.slice(token.start, token.end).join("") !== token.text || !token.lemma || !token.pos) throw Error("Token sem correspondência exata na frase original.");
      previous = token.end;
    }
  }
  function validateDecision(value) {
    const item = byId.get(value.item_id);
    if (!item || value.item_sha256 !== item.item_sha256 || value.kind !== item.kind) throw Error("Decisão não corresponde ao pacote original.");
    const common = ["kind", "item_id", "item_sha256", "decision", "reason"];
    const additions = item.kind === "form" ? ["include", "ratings", "canonical_sense_id", "analysis_confidence"] : item.kind === "lexical" ? ["corrected_lemma", "corrected_pos", "canonical_sense_id"] : ["corrected_tokens", "expected_match"];
    keys(value, [...common, ...additions], common);
    if (!["accepted", "corrected", "rejected", "inconclusive"].includes(value.decision) || typeof value.reason !== "string" || !value.reason.trim() || value.reason.length > 4000) throw Error("Escolha uma decisão e descreva o motivo.");
    const resolved = ["accepted", "corrected"].includes(value.decision);
    if (item.kind !== "case") resolvedSense(value.canonical_sense_id);
    if (item.kind === "form") {
      if (resolved && typeof value.include !== "boolean") throw Error("Indique se esta forma deve ter card.");
      if (!resolved && value.include !== null && value.include !== undefined) throw Error("Rejeitado ou inconclusivo não pode fornecer um rótulo de seleção.");
      keys(value.ratings || {}, Object.keys(criteria));
      for (const score of Object.values(value.ratings || {})) rating(score);
      if (value.analysis_confidence !== null && value.analysis_confidence !== undefined) rating(value.analysis_confidence);
    } else if (item.kind === "lexical") {
      if (resolved && !value.canonical_sense_id) throw Error("Informe um identificador explícito de sentido.");
      if (value.decision === "corrected" && (!value.corrected_lemma || !value.corrected_pos)) throw Error("A correção exige lema e classe gramatical.");
      if (value.decision !== "corrected" && (value.corrected_lemma || value.corrected_pos)) throw Error("Use Corrigir para substituir o lema ou a classe.");
    } else {
      if (resolved && typeof value.expected_match !== "boolean") throw Error("Defina o resultado esperado do matching.");
      if (value.decision === "corrected") tokens(value.corrected_tokens, item.text);
      else if (value.corrected_tokens !== null && value.corrected_tokens !== undefined) throw Error("Use Corrigir para substituir os tokens.");
    }
    return value;
  }
  function renderItem(item) {
    const card = node("article", undefined, "review-item");
    const existing = edits.get(item.item_id) || decisions.get(item.item_id);
    const head = node("div", undefined, "item-head");
    head.append(node("h2", item.kind === "case" ? item.text : item.kind === "form" ? `${item.text} ← ${item.lemma}` : item.lemma));
    head.append(node("span", `${kinds[item.kind]} · ${states[decisions.get(item.item_id)?.decision || "pending"]}`, "badge"));
    card.append(head, node("p", item.item_id, "meta"));
    const sourceDetails = node("details", undefined, "source");
    sourceDetails.append(node("summary", `Fontes (${item.sources.length})`));
    for (const source of item.sources) {
      sourceDetails.append(node("p", `${source.source_id} · ${source.record_id} · documento ${source.document_id || "não informado"}`, "meta"), node("code", source.source_sha256), node("pre", source.excerpt));
    }
    card.append(sourceDetails);
    const proposal = node("details", undefined, "proposal");
    proposal.open = !(packet.split === "evaluation" && item.kind === "case");
    proposal.append(node("summary", packet.split === "evaluation" && item.kind === "case" ? "Mostrar proposta automática (oculta inicialmente)" : "Proposta e evidências"));
    const fact = Object.create(null);
    if (item.kind === "lexical") { fact.pos = item.pos; fact.glosses = item.glosses; fact.source_sense_ids = item.source_sense_ids; fact.proposed_sense_id = item.proposed_sense_id; }
    else if (item.kind === "form") { fact.pos = item.pos; fact.features = item.features; fact.canonical_sense_id = item.canonical_sense_id; fact.measurements = item.measurements; fact.proposed_ratings = item.proposed_ratings; fact.missing_reasons = item.missing_reasons; fact.measurement_sha256 = item.measurement_sha256; }
    else { fact.tokens = item.proposal_tokens; fact.expected_match = item.expected_match; fact.behavior_tags = item.behavior_tags; fact.model_fingerprint = item.model_fingerprint; }
    proposal.append(node("pre", JSON.stringify(fact, null, 2))); card.append(proposal);
    const editor = node("fieldset"); editor.append(node("legend", "Decisão do revisor"));
    const choice = select(editor, "Decisão", states, existing?.decision || "pending");
    const reason = field(editor, "Justificativa", existing?.reason || "", "textarea"); reason.maxLength = 4000;
    let include, sense, lemma, pos, confidence, corrected, expected;
    const ratings = new Map();
    if (item.kind === "form") {
      include = select(editor, "Incluir card próprio?", {unknown: "Sem decisão", yes: "Sim", no: "Não"}, existing?.include === true ? "yes" : existing?.include === false ? "no" : "unknown");
      sense = field(editor, "Sentido canônico revisado (opcional)", existing?.canonical_sense_id);
      confidence = field(editor, "Confiança atribuída pelo revisor à análise (0–1; opcional)", existing?.analysis_confidence, "number"); confidence.min = "0"; confidence.max = "1"; confidence.step = "any";
      const rubric = node("div", undefined, "ratings wide");
      for (const [key, label] of Object.entries(criteria)) {
        const input = field(rubric, `${label} (0–1; vazio = não avaliado)`, existing?.ratings?.[key], "number"); input.min = "0"; input.max = "1"; input.step = "any"; ratings.set(key, input);
      }
      editor.append(rubric);
    } else if (item.kind === "lexical") {
      sense = field(editor, "Identificador do sentido revisado", existing?.canonical_sense_id);
      lemma = field(editor, "Lema corrigido (somente Corrigir)", existing?.corrected_lemma);
      pos = field(editor, "POS corrigido — UPOS (somente Corrigir)", existing?.corrected_pos);
    } else {
      expected = select(editor, "O matching deve aceitar este caso?", {unknown: "Sem decisão", yes: "Sim", no: "Não"}, existing?.expected_match === true ? "yes" : existing?.expected_match === false ? "no" : "unknown");
      corrected = field(editor, "Tokens corrigidos — JSON (somente Corrigir)", existing?.corrected_tokens ? JSON.stringify(existing.corrected_tokens, null, 2) : "", "textarea");
      corrected.className = "token-editor"; corrected.parentElement.className = "wide";
      editor.append(node("p", 'Formato: [{"start":2,"end":6,"text":"went","lemma":"go","pos":"VERB","sense_id":"motion","features":{"Tense":"Past"}}]. Offsets contam caracteres Unicode da frase original. Uma resposta negativa pode usar [].', "hint wide"));
    }
    const read = () => {
      const value = {kind: item.kind, item_id: item.item_id, item_sha256: item.item_sha256, decision: choice.value, reason: reason.value};
      if (item.kind === "form") {
        value.include = include.value === "unknown" ? null : include.value === "yes";
        value.canonical_sense_id = sense.value.trim() || null;
        value.analysis_confidence = confidence.value.trim() || null;
        value.ratings = Object.create(null);
        for (const [key, input] of ratings) if (input.value.trim()) value.ratings[key] = input.value;
      } else if (item.kind === "lexical") {
        value.canonical_sense_id = sense.value.trim() || null;
        value.corrected_lemma = lemma.value.trim() || null;
        value.corrected_pos = pos.value.trim() || null;
      } else {
        value.expected_match = expected.value === "unknown" ? null : expected.value === "yes";
        value.corrected_tokens = corrected.value.trim() ? JSON.parse(corrected.value) : null;
      }
      return value;
    };
    editor.addEventListener("input", () => { try { edits.set(item.item_id, read()); } catch { /* Preserve prior valid editor state until JSON is complete. */ } });
    card.append(editor);
    const actions = node("div", undefined, "item-actions");
    const save = node("button", "Registrar decisão"); save.type = "button";
    save.addEventListener("click", () => { try { decisions.set(item.item_id, validateDecision(read())); edits.delete(item.item_id); message("Decisão registrada nesta página. Baixe o JSON para preservá-la."); render(); } catch (error) { message(error.message, true); } });
    const clear = node("button", "Voltar a pendente", "secondary"); clear.type = "button";
    clear.addEventListener("click", () => { decisions.delete(item.item_id); edits.delete(item.item_id); render(); });
    actions.append(save, clear); card.append(actions); return card;
  }
  function filtered() {
    const query = $("search").value.toLocaleLowerCase();
    return packet.items.filter(item => ($("kind").value === "all" || item.kind === $("kind").value) && ($("status").value === "all" || (decisions.get(item.item_id)?.decision || "pending") === $("status").value) && (!query || [item.item_id, item.lemma || "", item.text || ""].join(" ").toLocaleLowerCase().includes(query)));
  }
  function render() {
    const visible = filtered(); const pages = Math.max(1, Math.ceil(visible.length / pageSize)); page = Math.min(page, pages - 1);
    $("items").replaceChildren(...visible.slice(page * pageSize, (page + 1) * pageSize).map(renderItem));
    $("page").textContent = `${page + 1} / ${pages} · ${visible.length} itens · ${decisions.size} decisões registradas`;
    $("previous").disabled = page === 0; $("next").disabled = page + 1 >= pages;
  }
  for (const name of ["search", "kind", "status"]) $(name).addEventListener("input", () => { page = 0; render(); });
  $("previous").addEventListener("click", () => { page--; render(); });
  $("next").addEventListener("click", () => { page++; render(); });
  $("download").addEventListener("click", () => {
    try {
      const reviewer = $("reviewer").value.trim(); const expertise = $("expertise").value.trim();
      if (!reviewer || !expertise) throw Error("Preencha o identificador e a experiência declarada do revisor.");
      if (edits.size) throw Error("Há edições não registradas. Registre a decisão ou volte o item a pendente antes de baixar.");
      const submission = {schema_version: 1, packet_sha256: packet.packet_sha256, reviewer_id: reviewer, expertise_declaration: expertise, reviewed_at: new Date().toISOString(), decisions: [...decisions.values()].sort((a, b) => a.item_id.localeCompare(b.item_id)), receipt_id: null};
      const blob = new Blob([JSON.stringify(submission, null, 2) + "\n"], {type: "application/json"});
      const url = URL.createObjectURL(blob); const link = node("a"); link.href = url; link.download = `multilang-review-${packet.language}-${packet.packet_sha256.slice(0, 12)}.json`; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      message("JSON baixado. A importação verificará o pacote original e a autoria declarada.");
    } catch (error) { message(error.message, true); }
  });
  $("resume").addEventListener("change", async event => {
    try {
      const file = event.target.files[0]; if (!file) return;
      if (file.size > 32 * 1024 * 1024) throw Error("JSON excede 32 MiB.");
      if (decisions.size || edits.size) throw Error("Para retomar outro JSON, abra novamente este HTML. As decisões atuais foram preservadas.");
      const submission = JSON.parse(await file.text());
      keys(submission, ["schema_version", "packet_sha256", "reviewer_id", "expertise_declaration", "reviewed_at", "decisions", "receipt_id"], ["schema_version", "packet_sha256", "reviewer_id", "expertise_declaration", "reviewed_at", "decisions"]);
      if (submission.schema_version !== 1 || submission.packet_sha256 !== packet.packet_sha256 || !Array.isArray(submission.decisions) || submission.decisions.length > 5000 || typeof submission.reviewer_id !== "string" || typeof submission.expertise_declaration !== "string") throw Error("JSON pertence a outro pacote ou contém metadados inválidos.");
      const resumed = new Map();
      for (const value of submission.decisions) { if (resumed.has(value.item_id)) throw Error("Decisão duplicada."); resumed.set(value.item_id, validateDecision(value)); }
      for (const [key, value] of resumed) decisions.set(key, value);
      $("reviewer").value = submission.reviewer_id; $("expertise").value = submission.expertise_declaration;
      message("Decisões retomadas. O próximo download será um novo rascunho sem assinatura."); render();
    } catch (error) { message(error.message, true); }
    event.target.value = "";
  });
  $("summary").textContent = `${packet.language} · ${packet.split} · ${packet.items.length} itens · pacote ${packet.packet_sha256}`;
  render();
})();
