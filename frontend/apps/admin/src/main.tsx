import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { demoCards, demoProduction, canSimulateDraft } from './demo';
import { editCard, selectCards, canExport, saveProductionDraft, availableSupportLanguages, isSupportLanguageAllowed, changeStudyLanguage, supportLanguageLabels } from './model';
import type { Card, Draft } from './model';
import './styles.css';

type Screen = 'productions' | 'new' | 'result';
const createDraft = (): Draft => ({ id: crypto.randomUUID(), ...demoProduction });
const stages = ['Vocabulário', 'Texto e tradução', 'Áudio', 'Validações', 'Resultado'];
const labels = { ready: 'Concluído', review: 'Revisar', failed: 'Incompleto' };

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    plus: <path d="M12 5v14M5 12h14"/>,
    arrow: <path d="m9 5 7 7-7 7"/>,
    book: <><path d="M12 5v15M12 5C8 2 4 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-2-10 1Z"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    search: <><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></>,
    sound: <><path d="m11 4-6 5H2v6h3l6 5ZM16 8c3 2 3 6 0 8M19 4c6 4 6 12 0 16"/></>,
    layers: <><path d="m12 2 10 6-10 6L2 8ZM2 12l10 6 10-6M2 16l10 6 10-6"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/></>,
    back: <path d="m10 5-7 7 7 7M3 12h18"/>,
    flip: <><path d="M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4"/></>,
    close: <path d="m6 6 12 12M6 18 18 6"/>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.layers}</svg>;
}

function Badge({ status }: { status: Card['status'] }) { return <span className={`badge ${status}`}><span className="dot"/>{labels[status]}</span>; }

function App() {
  const initialScreen = (): Screen => location.hash === '#nova' ? 'new' : location.hash === '#resultado' ? 'result' : 'productions';
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [cards, setCards] = useState<Card[]>(demoCards);
  const [selected, setSelected] = useState('01');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [back, setBack] = useState(false);
  const [editing, setEditing] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [draft, setDraft] = useState<Draft>(createDraft);
  const [step, setStep] = useState(-1);
  const [toast, setToast] = useState('');
  const [productionQuery, setProductionQuery] = useState('');
  useEffect(() => { const onHash = () => { setScreen(initialScreen()); setEditing(false); }; window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash); }, []);
  useEffect(() => {
    if (step < 0) return;
    const timer = window.setTimeout(() => {
      if (step < stages.length - 1) setStep(step + 1);
      else { setStep(-1); setCards(demoCards.map(c => ({ ...c }))); setSelected('01'); setQuery(''); setFilter('all'); setBack(false); go('result'); setToast('Simulação concluída. Explore os seis registros demonstrativos.'); }
    }, 850);
    return () => window.clearTimeout(timer);
  }, [step]);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 6500); return () => clearTimeout(timer); }, [toast]);
  const go = (next: Screen) => { setScreen(next); location.hash = next === 'new' ? 'nova' : next === 'result' ? 'resultado' : 'producoes'; setEditing(false); window.scrollTo(0, 0); };
  const visible = selectCards(cards, query, filter);
  const current = visible.find(c => c.id === selected) || visible[0];
  const pending = cards.filter(c => c.status !== 'ready').length;
  const sampleEnabled = canSimulateDraft(draft);
  const matchingDemo = 'vocabulário essencial inglês'.includes(productionQuery.toLocaleLowerCase().trim());
  const isEditingDraft = drafts.some(item => item.id === draft.id);
  const startNew = () => { setDraft(createDraft()); go('new'); };
  const saveDraft = () => {
    if (!draft.name.trim()) { setToast('Dê um nome à produção antes de salvar.'); return; }
    if (!isSupportLanguageAllowed(draft.language, draft.supportLanguage)) { setToast('Selecione um idioma de apoio disponível para este idioma estudado.'); return; }
    setDrafts(previous => saveProductionDraft(previous, draft));
    setToast(isEditingDraft ? 'Rascunho atualizado nesta sessão.' : 'Rascunho salvo nesta sessão. Recarregar a página limpa os dados demonstrativos.');
    setDraft(createDraft()); go('productions');
  };

  return <div className="shell">
    <a className="skip-link" href="#conteudo" onClick={event => { event.preventDefault(); document.getElementById('conteudo')?.focus(); }}>Ir para o conteúdo</a>
    <aside className="sidebar">
      <a className="brand" href="#producoes" onClick={() => go('productions')}><span className="brand-mark">m<span>·</span></span>multilang<span className="brand-period">.</span></a>
      <div className="workspace"><span className="workspace-icon"><Icon name="layers"/></span><div>Estúdio de produção<small>Seu espaço de trabalho</small></div></div>
      <p className="nav-label">OPERAÇÃO</p>
      <nav aria-label="Navegação principal">
        <a className={screen === 'productions' ? 'active' : ''} aria-current={screen === 'productions' ? 'page' : undefined} href="#producoes"><Icon name="grid"/>Produções<span className="nav-count">{1 + drafts.length}</span></a>
        <a className={screen === 'new' ? 'active' : ''} aria-current={screen === 'new' ? 'page' : undefined} href="#nova" onClick={event => { event.preventDefault(); startNew(); }}><Icon name="plus"/>Nova produção</a>
        <a className={screen === 'result' ? 'active' : ''} aria-current={screen === 'result' ? 'page' : undefined} href="#resultado"><Icon name="book"/>Resultado e revisão</a>
      </nav>
      <div className="sidebar-note"><span className="tiny-label">FLUXO DE TRABALHO</span><p>Configure a produção.<br/>Confira o resultado ao final.</p></div>
      <div className="profile"><span className="avatar">MR</span><div>Meu estúdio<small>Administrador · demonstração</small></div></div>
    </aside>

    <main id="conteudo" tabIndex={-1}>
      <header className="topbar"><span>Estúdio <span className="crumb">/</span> {screen === 'new' ? (isEditingDraft ? 'Editar produção' : 'Nova produção') : screen === 'result' ? 'Resultado e revisão' : 'Produções'}</span><span className="prototype"><span className="dot"/>Protótipo navegável</span></header>
      <div className="demo-banner">Dados demonstrativos · Alterações duram apenas nesta sessão. Nenhuma geração real é executada.</div>
      <div className="page">
      {screen === 'productions' && <>
        <div className="page-heading"><div><h1>Produções</h1><p className="muted">Acompanhe cada etapa e confira os resultados.</p></div><button className="button primary" onClick={startNew}><Icon name="plus"/>Nova produção</button></div>
        <div className="stats"><Stat icon="layers" label="Produções nesta sessão" value={String(1 + drafts.length)} caption="Inclui rascunhos e demonstrações"/><Stat icon="check" label="Cartões concluídos" value={String(cards.length - pending).padStart(2, '0')} caption="Estado ilustrativo de validação"/><Stat icon="clock" label="Itens para conferir" value={String(pending).padStart(2, '0')} caption="Revisões e resultados incompletos" accent/></div>
        <section className="attention"><span className="attention-icon"><Icon name="book" size={26}/></span><div><h2>Uma produção está pronta para você conferir.</h2><p>Explore os cartões de exemplo e veja como tratar as pendências.</p></div><button className="text-button" onClick={() => go('result')}>Revisar resultado <Icon name="arrow" size={16}/></button></section>
        <section className="panel production-panel"><div className="panel-heading"><div><h2>Suas produções</h2><p className="muted">Do primeiro rascunho à edição final.</p></div><Search value={productionQuery} onChange={setProductionQuery} placeholder="Buscar produção"/></div>
          <div className="table-wrap" role="region" aria-label="Lista de produções; role horizontalmente para ver todas as colunas" tabIndex={0}><table><thead><tr><th>PRODUÇÃO</th><th>MODALIDADE</th><th>SITUAÇÃO</th><th>ITENS</th><th><span className="sr-only">Abrir</span></th></tr></thead><tbody>
          {matchingDemo && <tr><td><div className="production-name"><span className="language-tile">EN</span><div><strong>{demoProduction.name}</strong><small>Estudo: {demoProduction.language} · Apoio: {supportLanguageLabels[demoProduction.supportLanguage]}</small><small>Demonstração · edição de exemplo</small></div></div></td><td>{demoProduction.kind}</td><td><Badge status="review"/></td><td>6 cartões</td><td><button className="text-button" onClick={() => go('result')} aria-label="Abrir resultado de Inglês">Abrir <Icon name="arrow" size={15}/></button></td></tr>}
          {drafts.filter(d => d.name.toLocaleLowerCase().includes(productionQuery.toLocaleLowerCase().trim())).map(d => <tr key={d.id}><td><div className="production-name"><span className="language-tile neutral"><Icon name="layers"/></span><div><strong>{d.name}</strong><small>Estudo: {d.language} · Apoio: {supportLanguageLabels[d.supportLanguage]}</small><small>Salvo nesta sessão</small></div></div></td><td>{d.kind}</td><td><span className="badge draft">Rascunho</span></td><td>—</td><td><button className="text-button" onClick={() => { setDraft(d); go('new'); }} aria-label={`Editar produção ${d.name}`}>Editar <Icon name="arrow" size={15}/></button></td></tr>)}
          </tbody></table></div>
          {!matchingDemo && !drafts.some(d => d.name.toLocaleLowerCase().includes(productionQuery.toLocaleLowerCase().trim())) && <div className="empty"><h3>Nenhuma produção encontrada</h3><p>Experimente outro nome ou veja todas as produções.</p><button className="button secondary" onClick={() => setProductionQuery('')}>Limpar busca</button></div>}
          <div className="panel-footer"><span>A lista usa somente dados deste protótipo.</span><span>Atualizado nesta sessão</span></div>
        </section>
        <div className="bottom-note"><Icon name="book" size={17}/><p>Um inventário revisado é o ponto de partida. A qualidade acompanha toda a produção.</p></div>
      </>}

      {screen === 'new' && <>
        <button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><div><h1>{isEditingDraft ? 'Editar produção' : 'Uma nova produção'}</h1><p className="muted">Configure uma vez. Confira o resultado ao final.</p></div><span className="badge draft">Rascunho</span></div>
        <div className="form-layout"><form className="panel configuration" onSubmit={e => { e.preventDefault(); if (sampleEnabled && step < 0) setStep(0); }}>
          <fieldset disabled={step >= 0}><legend><span className="number">01</span> O que vamos preparar?</legend>
            <label>Nome da produção<input required maxLength={100} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })}/></label>
            <div className="two-fields">
              <label>Idioma estudado<select value={draft.language} onChange={event => {
                const next = changeStudyLanguage(draft, event.target.value);
                setDraft(next);
                if (next.supportLanguage !== draft.supportLanguage) setToast('Para coreano, o idioma de apoio foi ajustado para português.');
              }}>{['Inglês', 'Coreano', 'Japonês', 'Latim', 'Espanhol', 'Francês', 'Alemão', 'Italiano', 'Português', 'Polonês', 'Turco', 'Romeno', 'Russo', 'Holandês', 'Mandarim', 'Tcheco', 'Dinamarquês', 'Finlandês', 'Grego', 'Croata', 'Húngaro', 'Norueguês', 'Sueco'].map(l => <option key={l}>{l}</option>)}</select></label>
              <label>Idioma de apoio<select value={draft.supportLanguage} disabled={draft.language === 'Coreano'} aria-describedby={draft.language === 'Coreano' ? 'support-language-help korean-support-constraint' : 'support-language-help'} onChange={event => {
                const value = event.target.value;
                if (isSupportLanguageAllowed(draft.language, value)) setDraft({ ...draft, supportLanguage: value });
              }}>{availableSupportLanguages(draft.language).map(code => <option key={code} value={code}>{supportLanguageLabels[code]}</option>)}</select></label>
            </div>
            <p className="field-note support-language-help" id="support-language-help">Idioma das definições, traduções das frases e rótulos dos cartões deste deck. O aplicativo continua em português.</p>
            {draft.language === 'Coreano' && <p className="field-note language-constraint" id="korean-support-constraint">Para coreano, apenas português está disponível como idioma de apoio.</p>}
            <label>Tipo de material<select value={draft.kind} onChange={e => setDraft({ ...draft, kind: e.target.value })}>{['Frequência', 'Lista personalizada', 'Destaques de leitura', 'Escrita e fundamentos', 'Pronúncia e fonética', 'Gramática', 'Latim clássico'].map(k => <option key={k}>{k}</option>)}</select></label>
            <p className="field-note">O catálogo definitivo dependerá das modalidades qualificadas para cada idioma. A simulação usa Inglês + Frequência, com apoio em português.</p>
          </fieldset>
          <fieldset disabled={step >= 0}><legend><span className="number">02</span> Conteúdo e apresentação</legend>
            <div className="source-box"><Icon name="book"/><div><strong>{sampleEnabled ? 'Inventário demonstrativo' : 'Prévia indisponível para esta combinação'}</strong><p>{sampleEnabled ? '6 identidades · 6 cartões · apoio em português' : 'Esta configuração pode ser salva como rascunho.'}</p><small>{sampleEnabled ? 'Não representa a curadoria da branch de arquitetura.' : 'O exemplo disponível usa Inglês + Frequência, com apoio em português.'}</small></div><span className="badge draft">{sampleEnabled ? 'Exemplo' : 'Rascunho'}</span></div>
            <label>Apresentação<select defaultValue="Vocabulário · modelo de interface"><option>Vocabulário · modelo de interface</option></select></label><p className="field-note">A prévia é ilustrativa. A integração deverá usar os templates reais do Anki.</p>
          </fieldset>
          <fieldset><legend><span className="number">03</span> Áudio e execução</legend><div className="source-box"><Icon name="sound"/><div><strong>Palavra e frase, em faixas separadas</strong><p>Azure é a direção prevista para produção.</p><small>Seleção de voz e áudios reais aguardam integração.</small></div></div><p className="field-note">O sistema seguirá suas validações e apresentará o resultado completo, incluindo pendências.</p></fieldset>
          <div className="form-actions"><button type="button" className="button secondary" disabled={step >= 0} onClick={saveDraft}>{isEditingDraft ? 'Salvar alterações' : 'Salvar rascunho'}</button><button className="button primary" disabled={!sampleEnabled || step >= 0}>{step >= 0 ? 'Simulando…' : 'Simular produção'}<Icon name="arrow" size={16}/></button></div>
          {!sampleEnabled && <p className="field-note" role="status">Você pode salvar este rascunho. Para explorar o resultado de exemplo, selecione Inglês, Frequência e apoio em Português.</p>}
        </form>
        <aside className="summary panel"><h2>Sua produção</h2><dl><dt>Idioma estudado</dt><dd>{draft.language}</dd><dt>Idioma de apoio</dt><dd>{supportLanguageLabels[draft.supportLanguage]}</dd><dt>Material</dt><dd>{draft.kind}</dd><dt>Conteúdo</dt><dd>{sampleEnabled ? '6 itens de exemplo' : 'Sem prévia disponível'}</dd><dt>Execução</dt><dd>{sampleEnabled ? 'Até o resultado final' : 'Somente rascunho'}</dd><dt>Custo real</dt><dd>Nenhuma chamada paga</dd></dl><hr/><h3>Etapas do processamento</h3><ol className="stage-list" aria-live="polite">{stages.map((s, i) => <li key={s} className={step >= i ? 'stage-active' : ''}><span>{step > i ? <><Icon name="check" size={14}/><span className="sr-only">Concluído:</span></> : i + 1}</span>{s}{step === i && <small>Simulando</small>}</li>)}</ol><p className="field-note">O tempo e os estados apresentados nesta simulação são fictícios.</p></aside>
        </div>
      </>}

      {screen === 'result' && <>
        <button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><div><h1>Vocabulário essencial <span className="title-language">{demoProduction.language}</span></h1><p className="muted">Idioma de apoio: <strong>{supportLanguageLabels[demoProduction.supportLanguage]}</strong>. Confira o conteúdo e suas pendências.</p></div><button className="button secondary" disabled={!canExport(cards, true)} title="A exportação exige integração com o backend">Exportar para Anki</button></div>
        <div className="result-summary"><span><strong>{cards.length}</strong> cartões de exemplo</span><span><i className="dot green"/><strong>{cards.length - pending}</strong> concluídos</span><span><i className="dot amber"/><strong>{pending}</strong> para conferir</span><span className="result-hint">Exportação e áudio real indisponíveis no protótipo</span></div>
        <section className="panel review-panel"><div className="review-toolbar"><div className="tabs" role="group" aria-label="Filtrar cartões"><button aria-pressed={filter === 'all'} className={filter === 'all' ? 'selected' : ''} onClick={() => { setFilter('all'); setEditing(false); }}>Todos <span>{cards.length}</span></button><button aria-pressed={filter === 'pending'} className={filter === 'pending' ? 'selected' : ''} onClick={() => { setFilter('pending'); setEditing(false); }}>Pendências <span>{pending}</span></button></div><Search value={query} onChange={q => { setQuery(q); setEditing(false); }} placeholder="Buscar palavra"/></div>
        <div className="review-layout"><div className="card-list" role="group" aria-label="Cartões da produção">{visible.map(c => <button key={c.id} className={`card-list-item ${current?.id === c.id ? 'chosen' : ''}`} aria-pressed={current?.id === c.id} onClick={() => { setSelected(c.id); setBack(false); setEditing(false); }}><span className="item-number">{c.id}</span><span className="card-list-copy"><strong>{c.word}</strong><small>{c.definition || 'Conteúdo não concluído'}</small><span className={`card-state ${c.status}`}><span className="dot"/>{labels[c.status]}</span></span>{current?.id === c.id && <Icon name="arrow" size={15}/>}</button>)}{visible.length === 0 && <p className="empty">Nenhum cartão com esses filtros.</p>}</div>
        {current ? <div className="review-detail"><div className="detail-heading"><span className="tiny-label">PRÉVIA ILUSTRATIVA · {back ? 'VERSO' : 'FRENTE'}</span><Badge status={current.status}/></div>
          <article className="anki-preview"><span className="card-brand">MULTILANG <span>EN / VOCABULÁRIO</span></span><h2>{current.word}</h2>{back ? <div className="card-answer"><p>{current.definition || 'Definição ainda não disponível.'}</p>{current.sentence && <blockquote>{current.sentence}<small>{current.translation}</small></blockquote>}</div> : <p className="card-instruction">Lembre o significado e revele a resposta.</p>}<div className="preview-actions"><button className="audio-button" disabled title="Nenhum arquivo de áudio está incluído nesta demonstração"><Icon name="sound" size={18}/>Áudio de exemplo indisponível</button><button className="text-button" onClick={() => setBack(!back)}>{back ? 'Ver frente' : 'Mostrar resposta'}<Icon name="flip" size={17}/></button></div></article>
          <div className={`finding ${current.status === 'ready' ? 'finding-neutral' : ''}`}><strong>{current.status === 'failed' ? 'Conteúdo incompleto' : current.audio === 'outdated' ? 'O texto foi alterado' : current.audio === 'missing' ? 'Áudio pendente' : current.status === 'review' ? 'Conteúdo para conferir' : 'Nenhuma pendência no cenário demonstrativo'}</strong><p>{current.audio === 'outdated' ? 'Tradução, áudio e validações precisam ser conferidos novamente.' : current.status === 'failed' ? 'A produção real deverá permitir recuperar a etapa que falhou.' : current.status !== 'ready' ? 'Este registro ilustra uma pendência. A revisão real virá das evidências do sistema.' : 'Os estados são fictícios e não certificam a qualidade deste conteúdo.'}</p></div>
          {editing ? <form className="edit-form" key={current.id} onSubmit={e => { e.preventDefault(); const data = new FormData(e.currentTarget); setCards(cards.map(c => c.id === current.id ? editCard(c, { definition: String(data.get('definition')), sentence: String(data.get('sentence')), translation: String(data.get('translation')) }) : c)); setEditing(false); setBack(true); setToast('Alteração aplicada nesta sessão. Conteúdo alterado fica pendente de revisão.'); }}><label>Definição<textarea name="definition" required maxLength={2000} defaultValue={current.definition}/></label><label>Frase<textarea name="sentence" required maxLength={2000} defaultValue={current.sentence}/></label><label>Tradução<textarea name="translation" required maxLength={2000} defaultValue={current.translation}/></label><div className="form-actions"><button type="button" className="button secondary" onClick={() => setEditing(false)}>Cancelar</button><button className="button primary">Salvar alteração</button></div></form> : <div className="detail-actions"><button className="button secondary" onClick={() => setEditing(true)}>Editar conteúdo</button><span className="field-note">Alterações ficam apenas nesta sessão.</span></div>}
        </div> : <div className="review-detail empty"><Icon name="search" size={32}/><h2>Nenhum resultado</h2><p>Altere a busca ou volte para todos os cartões.</p><button className="button secondary" onClick={() => { setFilter('all'); setQuery(''); }}>Limpar filtros</button></div>}
        </div></section>
      </>}
      <footer className="page-footer"><span>multilang<span className="brand-period">.</span> <span className="footer-caption">Estúdio de produção</span></span><span>Protótipo 04 · Idioma de apoio</span></footer>
      </div>
    </main>
    {toast && <div className="toast" role="status">{toast}<button aria-label="Fechar mensagem" onClick={() => setToast('')}><Icon name="close" size={18}/></button></div>}
  </div>;
}

function Search({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <label className="search"><Icon name="search" size={17}/><span className="sr-only">{placeholder}</span><input type="search" value={value} placeholder={placeholder} onChange={e => onChange(e.target.value)}/></label>; }
function Stat({ icon, label, value, caption, accent }: { icon: string; label: string; value: string; caption: string; accent?: boolean }) { return <div className={`stat ${accent ? 'stat-accent' : ''}`}><div className="stat-top"><span>{label}</span><Icon name={icon}/></div><strong>{value}</strong><small>{caption}</small></div>; }

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
