import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { demoCards, demoProduction, canSimulateDraft } from './demo';
import { editCard, selectCards, canExport, saveProductionDraft, availableSupportLanguages, isSupportLanguageAllowed, changeStudyLanguage, changeMaterial, progressPercentage, recordCompletedDeck, supportLanguageLabels } from './model';
import type { Card, CompletedDeck, Draft } from './model';
import { sourceKindFor } from './source-files';
import { SourceFileInput } from './SourceFileInput';
import { AnkiTemplatePreview } from './AnkiTemplatePreview';
import { CardEditor } from './CardEditor';
import { Connections } from './Connections';
import './styles.css';
import { loadDrafts, persistDraft } from './draft-store';

type Screen = 'connections' | 'productions' | 'history' | 'new' | 'result';
const createDraft = (): Draft => ({ id: crypto.randomUUID(), ...demoProduction });
const stages = ['Vocabulário', 'Texto e tradução', 'Áudio', 'Validações', 'Resultado'];
const labels = { ready: 'Concluído', review: 'Revisar', failed: 'Incompleto' };

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    menu: <path d="M4 6h16M4 12h16M4 18h16"/>,
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
    connections: <><path d="M8 4v5M16 4v5M6 9h12v3a6 6 0 0 1-12 0ZM12 18v4"/></>,
    close: <path d="m6 6 12 12M6 18 18 6"/>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.layers}</svg>;
}

function Badge({ status }: { status: Card['status'] }) { return <span className={`badge ${status}`}><span className="dot"/>{labels[status]}</span>; }

function App() {
  const initialScreen = (): Screen => location.hash.startsWith('#conexoes') ? 'connections' : location.hash === '#nova' ? 'new' : location.hash === '#resultado' ? 'result' : location.hash === '#historico' ? 'history' : 'productions';
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [cards, setCards] = useState<Card[]>(demoCards);
  const [selected, setSelected] = useState('01');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [editing, setEditing] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState(true);
  const [savingDraft, setSavingDraft] = useState(false);
  useEffect(() => {
    let active = true;
    loadDrafts().then(items => { if (active) setDrafts(items); })
      .catch(() => { if (active) setToast('Não foi possível abrir os rascunhos deste navegador.'); })
      .finally(() => { if (active) setLoadingDrafts(false); });
    return () => { active = false; };
  }, []);
  const [draft, setDraft] = useState<Draft>(createDraft);
  const [step, setStep] = useState(-1);
  const [isPaused, setIsPaused] = useState(false);
  const [history, setHistory] = useState<CompletedDeck[]>([]);
  const [activeDeck, setActiveDeck] = useState<CompletedDeck | null>(null);
  const [toast, setToast] = useState('');
  const [productionQuery, setProductionQuery] = useState('');
  const [readingFile, setReadingFile] = useState(false);
  const mobileMenuToggleRef = useRef<HTMLButtonElement>(null);
  const mobileMenuCloseRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLElement>(null);
  useEffect(() => { const onHash = () => { setScreen(initialScreen()); setEditing(false); }; window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash); }, []);
  useEffect(() => {
    if (!mobileMenuOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileMenuOpen(false);
    };
    const keepFocusInMenu = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;
      const items = mobileMenuRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
      if (!items?.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (!mobileMenuRef.current?.contains(document.activeElement)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    const closeOnDesktop = () => {
      if (window.innerWidth > 900) setMobileMenuOpen(false);
    };
    const focusTimer = window.setTimeout(() => mobileMenuCloseRef.current?.focus(), 50);
    window.addEventListener('keydown', closeOnEscape);
    window.addEventListener('keydown', keepFocusInMenu);
    window.addEventListener('resize', closeOnDesktop);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.clearTimeout(focusTimer);
      window.removeEventListener('keydown', closeOnEscape);
      window.removeEventListener('keydown', keepFocusInMenu);
      window.removeEventListener('resize', closeOnDesktop);
      mobileMenuToggleRef.current?.focus();
    };
  }, [mobileMenuOpen]);
  useEffect(() => {
    if (step < 0 || isPaused) return;
    const timer = window.setTimeout(() => {
      if (step < stages.length) setStep(step + 1);
      else {
        const completedDeck: CompletedDeck = {
          id: draft.id,
          name: draft.name.trim(),
          language: draft.language,
          supportLanguage: draft.supportLanguage,
          kind: draft.kind,
          completedAt: new Date().toISOString(),
          cards: demoCards.map(card => ({ ...card })),
        };
        setHistory(previous => recordCompletedDeck(previous, completedDeck));
        setActiveDeck(completedDeck);
        setStep(-1);
        setIsPaused(false);
        setCards(completedDeck.cards.map(card => ({ ...card })));
        setSelected(completedDeck.cards[0]?.id ?? '');
        setQuery('');
        setFilter('all');
        go('result');
        setToast('Simulação concluída. O histórico e os cartões são demonstrativos.');
      }
    }, 850);
    return () => window.clearTimeout(timer);
  }, [step, isPaused]);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 6500); return () => clearTimeout(timer); }, [toast]);
  const go = (next: Screen) => { setScreen(next); location.hash = next === 'connections' ? 'conexoes' : next === 'new' ? 'nova' : next === 'result' ? 'resultado' : next === 'history' ? 'historico' : 'producoes'; setEditing(false); window.scrollTo(0, 0); };
  const visible = selectCards(cards, query, filter);
  const current = visible.find(c => c.id === selected) || visible[0];
  const pending = cards.filter(c => c.status !== 'ready').length;
  const progress = progressPercentage(step, stages.length);
  const sampleEnabled = canSimulateDraft(draft);
  const sourceKind = sourceKindFor(draft.kind);
  const matchingDemo = 'vocabulário essencial inglês'.includes(productionQuery.toLocaleLowerCase().trim());
  const isEditingDraft = drafts.some(item => item.id === draft.id);
  const closeMobileMenu = () => setMobileMenuOpen(false);
  const startNew = () => {
    if (step >= 0) {
      setToast('Conclua ou retome a simulação em andamento antes de iniciar outra.');
      go('new');
      return;
    }
    setDraft(createDraft());
    setActiveDeck(null);
    go('new');
  };
  const openDeck = (deck: CompletedDeck) => {
    setActiveDeck(deck);
    setCards(deck.cards.map(card => ({ ...card })));
    setSelected(deck.cards[0]?.id ?? '');
    setQuery('');
    setFilter('all');
    go('result');
  };
  const saveDraft = async () => {
    if (readingFile || savingDraft || loadingDrafts) return;
    if (!draft.name.trim()) { setToast('Dê um nome à produção antes de salvar.'); return; }
    if (!isSupportLanguageAllowed(draft.language, draft.supportLanguage)) { setToast('Selecione um idioma de apoio disponível para este idioma estudado.'); return; }
    setSavingDraft(true);
    try {
      const [saved] = saveProductionDraft([], draft);
      await persistDraft(saved);
      setDrafts(previous => [saved, ...previous.filter(item => item.id !== saved.id)]);
      setToast('Rascunho salvo neste navegador.');
      setDraft(createDraft()); go('productions');
    } catch {
      setToast('Falha ao salvar o rascunho. Confira o espaço disponível e tente novamente.');
    } finally { setSavingDraft(false); }
  };

  return <div className="shell">
    <a className="skip-link" href="#conteudo" onClick={event => { event.preventDefault(); document.getElementById('conteudo')?.focus(); }}>Ir para o conteúdo</a>
    <aside className="sidebar">
      <a className="brand" href="#producoes" onClick={() => go('productions')}><BrandMark/></a>
      <div className="workspace"><span className="workspace-icon"><Icon name="layers"/></span><div>Estúdio de produção<small>Seu espaço de trabalho</small></div></div>
      <p className="nav-label">Operação</p>
      <button ref={mobileMenuToggleRef} className="mobile-nav-toggle" type="button" aria-expanded={mobileMenuOpen} aria-controls="primary-navigation" onClick={() => setMobileMenuOpen(true)}><Icon name="menu" size={18}/><span>Menu</span></button>
      <nav ref={mobileMenuRef} id="primary-navigation" className={mobileMenuOpen ? 'mobile-nav-open' : ''} aria-label="Navegação principal" onClick={event => { if (event.target === event.currentTarget) closeMobileMenu(); }}>
        <div className="mobile-nav-heading"><span>Navegação</span><button ref={mobileMenuCloseRef} className="mobile-nav-close" type="button" aria-label="Fechar menu" onClick={closeMobileMenu}><Icon name="close"/></button></div>
        <a className={screen === 'productions' ? 'active' : ''} aria-current={screen === 'productions' ? 'page' : undefined} href="#producoes" onClick={closeMobileMenu}><Icon name="grid"/>Produções<span className="nav-count">{1 + drafts.length}</span></a>
        <a className={screen === 'new' ? 'active' : ''} aria-current={screen === 'new' ? 'page' : undefined} href="#nova" onClick={event => { event.preventDefault(); startNew(); closeMobileMenu(); }}><Icon name="plus"/>Nova produção</a>
        <a className={screen === 'history' ? 'active' : ''} aria-current={screen === 'history' ? 'page' : undefined} href="#historico" onClick={event => { event.preventDefault(); go('history'); closeMobileMenu(); }}><Icon name="clock"/>Histórico<span className="nav-count">{history.length}</span></a>
        <a className={screen === 'result' ? 'active' : ''} aria-current={screen === 'result' ? 'page' : undefined} href="#resultado" onClick={closeMobileMenu}><Icon name="book"/>Resultado e revisão</a>
        <a className={screen === 'connections' ? 'active' : ''} aria-current={screen === 'connections' ? 'page' : undefined} href="#conexoes" onClick={closeMobileMenu}><Icon name="connections"/>Provedores e conexões</a>
      </nav>
      <div className="profile"><span className="avatar">MR</span><div>Meu estúdio<small>Administrador · demonstração</small></div></div>
    </aside>

    <main id="conteudo" tabIndex={-1}>
      <header className="topbar"><span>Estúdio <span className="crumb">/</span> {screen === 'connections' ? 'Provedores e conex\u00f5es' : screen === 'new' ? (isEditingDraft ? 'Editar produção' : 'Nova produção') : screen === 'result' ? 'Resultado e revisão' : screen === 'history' ? 'Histórico' : 'Produções'}</span><span className="prototype"><span className="dot"/>{screen === 'connections' ? 'Conexão local' : 'Protótipo navegável'}</span></header>
      {screen !== 'connections' && <div className="demo-banner">Rascunhos ficam salvos neste navegador. Geração e revisão usam dados demonstrativos.</div>}
      {step >= 0 && <section className={`generation-banner ${isPaused ? 'paused' : ''}`} aria-label="Progresso da geração demonstrativa">
        <div className="generation-banner-heading"><strong>{isPaused ? 'Geração pausada' : 'Geração em andamento'}</strong><span>{progress}%</span></div>
        <progress aria-label={`Progresso da geração demonstrativa: ${progress}%`} max={100} value={progress}/>
        <div className="generation-banner-footer"><span>{step < stages.length ? `Etapa: ${stages[step]}` : 'Finalizando o deck'}</span><button className="button secondary" onClick={() => setIsPaused(paused => !paused)}>{isPaused ? 'Retomar geração' : 'Pausar geração'}</button></div>
        <p>Simulação local. Na versão real, o progresso virá do job no backend; pausa/retomada usará checkpoints, e o histórico e os arquivos virão da API de exports.</p>
      </section>}
      <div className={`page${screen === 'connections' ? ' page-connections' : ''}`}>
      {screen === 'connections' && <Connections/>}
      {screen === 'productions' && <>
        <div className="page-heading"><div><h1>Produções</h1><p className="muted">Acompanhe cada etapa e confira os resultados.</p></div><button className="button primary" onClick={startNew}><Icon name="plus"/>Nova produção</button></div>
        <div className="production-overview">
          <div className="stats" aria-label="Resumo ilustrativo das produções"><Stat icon="layers" label="Produções no estúdio" value={String(1 + drafts.length)} caption="Inclui rascunhos e demonstrações"/><Stat icon="check" label="Cartões concluídos" value={String(cards.length - pending).padStart(2, '0')} caption="Estado ilustrativo de validação"/><Stat icon="clock" label="Itens para conferir" value={String(pending).padStart(2, '0')} caption="Revisões e resultados incompletos" accent/></div>
          {drafts.length > 0 ? (
            <section className="attention"><span className="attention-icon"><Icon name="layers" size={22}/></span><div>
              <h2>Retomar rascunho</h2><p>{drafts[0].name}</p>
              <button className="text-button" onClick={() => { setDraft(drafts[0]); go('new'); }}>Continuar produção <Icon name="arrow" size={16}/></button>
            </div></section>
          ) : pending > 0 && (
            <section className="attention"><span className="attention-icon"><Icon name="book" size={22}/></span><div>
              <h2>Revisar produção de exemplo</h2><p>{pending} cartões precisam de atenção no exemplo.</p>
              <button className="text-button" onClick={() => go('result')}>Revisar resultado <Icon name="arrow" size={16}/></button>
            </div></section>
          )}
        </div>
        <section className="panel production-panel"><div className="panel-heading"><div><h2>Suas produções</h2><p className="muted">Do primeiro rascunho à edição final.</p></div><Search value={productionQuery} onChange={setProductionQuery} placeholder="Buscar produção"/></div>
          <div className="table-wrap" role="region" aria-label="Lista de produções" tabIndex={0}><table className="productions-table" role="table"><thead role="rowgroup"><tr role="row"><th scope="col" role="columnheader">PRODUÇÃO</th><th scope="col" role="columnheader">MODALIDADE</th><th scope="col" role="columnheader">SITUAÇÃO</th><th scope="col" role="columnheader">ITENS</th><th scope="col" role="columnheader"><span className="sr-only">Abrir</span></th></tr></thead><tbody role="rowgroup">
          {matchingDemo && <tr role="row"><td role="cell"><div className="production-name"><span className="language-tile">EN</span><div><strong>{demoProduction.name}</strong><small>Estudo: {demoProduction.language} · Apoio: {supportLanguageLabels[demoProduction.supportLanguage]}</small><small>Demonstração · edição de exemplo</small></div></div></td><td role="cell" data-label="Modalidade">{demoProduction.kind}</td><td role="cell" data-label="Situação"><Badge status="review"/></td><td role="cell" data-label="Itens">6 cartões</td><td role="cell"><button className="text-button" onClick={() => go('result')} aria-label="Abrir resultado de Inglês">Abrir <Icon name="arrow" size={15}/></button></td></tr>}
          {drafts.filter(d => d.name.toLocaleLowerCase().includes(productionQuery.toLocaleLowerCase().trim())).map(d => <tr role="row" key={d.id}><td role="cell"><div className="production-name"><span className="language-tile neutral"><Icon name="layers"/></span><div><strong>{d.name}</strong><small>Estudo: {d.language} · Apoio: {supportLanguageLabels[d.supportLanguage]}</small><small>{sourceKindFor(d.kind) ? (d.attachment ? `Arquivo: ${d.attachment.file.name}` : 'Arquivo pendente') : 'Salvo neste navegador'}</small></div></div></td><td role="cell" data-label="Modalidade">{d.kind}</td><td role="cell" data-label="Situação"><span className="badge draft">Rascunho</span></td><td role="cell" data-label="Itens">—</td><td role="cell"><button className="text-button" onClick={() => { setDraft(d); go('new'); }} aria-label={`Editar produção ${d.name}`}>Editar <Icon name="arrow" size={15}/></button></td></tr>)}
          </tbody></table></div>
          {!matchingDemo && !drafts.some(d => d.name.toLocaleLowerCase().includes(productionQuery.toLocaleLowerCase().trim())) && <div className="empty"><h3>Nenhuma produção encontrada</h3><p>Experimente outro nome ou veja todas as produções.</p><button className="button secondary" onClick={() => setProductionQuery('')}>Limpar busca</button></div>}
          <div className="panel-footer"><span>Rascunhos salvos neste navegador.</span><span>Atualizado nesta sessão</span></div>
        </section>
        <div className="bottom-note"><Icon name="book" size={17}/><p>Um inventário revisado é o ponto de partida. A qualidade acompanha toda a produção.</p></div>
      </>}

      {screen === 'history' && <>
        <button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><div><h1>Histórico de decks</h1><p className="muted">Gerações concluídas e seus cartões completos.</p></div><span className="badge draft">Demonstração</span></div>
        <section className="panel production-panel">
          <div className="panel-heading"><div><h2>Decks concluídos</h2><p className="muted">Os registros deste protótipo duram apenas nesta sessão.</p></div></div>
          {history.length > 0 ? <div className="table-wrap" role="region" aria-label="Histórico de decks concluídos" tabIndex={0}><table><thead><tr><th>Deck</th><th>Idioma</th><th>Modalidade</th><th>Cartões</th><th>Concluído em</th><th><span className="sr-only">Abrir</span></th></tr></thead><tbody>
            {history.map(deck => <tr key={deck.id}><td><div className="production-name"><span className="language-tile neutral"><Icon name="layers"/></span><div><strong>{deck.name}</strong><small>Concluído · demonstração</small></div></div></td><td>{deck.language}</td><td>{deck.kind}</td><td>{deck.cards.length}</td><td>{new Date(deck.completedAt).toLocaleString('pt-BR')}</td><td><button className="text-button" onClick={() => openDeck(deck)} aria-label={`Abrir deck ${deck.name}`}>Ver deck <Icon name="arrow" size={15}/></button></td></tr>)}
          </tbody></table></div> : <div className="empty"><Icon name="clock" size={32}/><h3>Nenhum deck concluído nesta sessão</h3><p>Execute a simulação de Inglês + Frequência para ver um deck completo aqui.</p><button className="button primary" onClick={startNew}><Icon name="plus"/>Nova produção</button></div>}
          <div className="panel-footer"><span>Protótipo: histórico mantido somente em memória.</span><span>Na versão real, consultar jobs e exports persistidos pela API.</span></div>
        </section>
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
                if (next.highlightInput !== draft.highlightInput) setToast('Para coreano, o apoio é português e os destaques usam o modo de trechos de leitura.');
                else if (next.supportLanguage !== draft.supportLanguage) setToast('Para coreano, o idioma de apoio foi ajustado para português.');
              }}>{['Inglês', 'Coreano', 'Japonês', 'Latim', 'Espanhol', 'Francês', 'Alemão', 'Italiano', 'Português', 'Polonês', 'Turco', 'Romeno', 'Russo', 'Holandês', 'Mandarim', 'Tcheco', 'Dinamarquês', 'Finlandês', 'Grego', 'Croata', 'Húngaro', 'Norueguês', 'Sueco'].map(l => <option key={l} value={l}><span>{l}</span></option>)}</select></label>
              <label>Idioma de apoio<select value={draft.supportLanguage} disabled={draft.language === 'Coreano'} aria-describedby={draft.language === 'Coreano' ? 'support-language-help korean-support-constraint' : 'support-language-help'} onChange={event => {
                const value = event.target.value;
                if (isSupportLanguageAllowed(draft.language, value)) setDraft({ ...draft, supportLanguage: value });
              }}>{availableSupportLanguages(draft.language).map(code => <option key={code} value={code}><span>{supportLanguageLabels[code]}</span></option>)}</select></label>
            </div>
            <p className="field-note support-language-help" id="support-language-help">Idioma das definições, traduções das frases e rótulos dos cartões deste deck. O aplicativo continua em português.</p>
            {draft.language === 'Coreano' && <p className="field-note language-constraint" id="korean-support-constraint">Para coreano, apenas português está disponível como idioma de apoio.</p>}
            <label>Tipo de material<select value={draft.kind} onChange={event => {
              const next = changeMaterial(draft, event.target.value);
              setDraft(next);
              if (draft.attachment && !next.attachment) setToast('O tipo de material mudou. Selecione o arquivo adequado para esta modalidade.');
            }}>{['Frequência', 'Lista personalizada', 'Destaques de leitura', 'Escrita e fundamentos', 'Pronúncia e fonética', 'Gramática', 'Latim clássico'].map(k => <option key={k} value={k}><span>{k}</span></option>)}</select></label>
            <p className="field-note">O catálogo definitivo dependerá das modalidades qualificadas para cada idioma. A simulação usa Inglês + Frequência, com apoio em português.</p>
          </fieldset>
          <fieldset disabled={step >= 0}><legend><span className="number">02</span> Conteúdo e apresentação</legend>
            {sourceKind ? <>
              {sourceKind === 'highlights' && <><label>O que os destaques contêm?<select value={draft.highlightInput ?? 'text'} disabled={draft.language === 'Coreano'} aria-describedby="highlight-input-help" onChange={event => {
                const mode = event.target.value;
                if (mode === 'text' || (mode === 'vocabulary' && draft.language !== 'Coreano')) setDraft({ ...draft, highlightInput: mode });
              }}><option value="text"><span>Trechos de leitura — extrair palavras</span></option><option value="vocabulary"><span>Palavras ou expressões — um item por destaque</span></option></select></label><p className="field-note highlight-input-help" id="highlight-input-help">{draft.language === 'Coreano' ? 'Coreano usa apenas trechos de leitura para análise linguística.' : draft.highlightInput === 'vocabulary' ? 'Cada destaque será tratado como uma palavra ou expressão. Para uma lista simples com um item por linha, use Lista personalizada.' : 'O sistema identificará palavras nos trechos destacados quando a integração estiver disponível.'}</p></>}
              <SourceFileInput key={`${draft.id}:${draft.kind}`} kind={sourceKind} attachment={draft.attachment} disabled={step >= 0} onBusyChange={setReadingFile} onChange={attachment => setDraft(previous => previous.id === draft.id && previous.kind === draft.kind ? { ...previous, attachment } : previous)}/>
            </> : <div className="source-box"><Icon name="book"/><div><strong>{sampleEnabled ? 'Inventário demonstrativo' : 'Inventário de demonstração indisponível'}</strong><p>{sampleEnabled ? '6 identidades · 6 cartões · apoio em português' : 'Esta configuração pode ser salva como rascunho.'}</p><small>{sampleEnabled ? 'Não representa a curadoria da branch de arquitetura.' : 'A simulação completa continua limitada ao exemplo de Inglês + Frequência.'}</small></div><span className="badge draft">{sampleEnabled ? 'Exemplo' : 'Rascunho'}</span></div>}
            <AnkiTemplatePreview key={`${draft.kind}:${draft.language}`} deckType={draft.kind} language={draft.language}/>
          </fieldset>
          <fieldset><legend><span className="number">03</span> Áudio e execução</legend><div className="source-box"><Icon name="sound"/><div><strong>Palavra e frase, em faixas separadas</strong><p>Azure é a direção prevista para produção.</p><small>Seleção de voz e áudios reais aguardam integração.</small></div></div><p className="field-note">O sistema seguirá suas validações e apresentará o resultado completo, incluindo pendências.</p></fieldset>
          <div className="form-actions"><button type="button" className="button secondary" disabled={step >= 0 || readingFile || savingDraft || loadingDrafts} onClick={saveDraft}>{savingDraft ? 'Salvando…' : readingFile ? 'Lendo arquivo…' : isEditingDraft ? 'Salvar alterações' : 'Salvar rascunho'}</button><button className="button primary" disabled={!sampleEnabled || step >= 0}>{step >= 0 ? (isPaused ? 'Pausada' : 'Simulando…') : 'Simular produção'}<Icon name="arrow" size={16}/></button></div>
          {!sampleEnabled && <p className="field-note" role="status">{sourceKind ? 'Salve o rascunho com seu arquivo. A geração a partir de arquivos será habilitada após a integração com o sistema.' : 'Você pode salvar este rascunho. Para explorar o resultado de exemplo, selecione Inglês, Frequência e apoio em Português.'}</p>}
        </form>
        <aside className="summary panel"><h2>Sua produção</h2><dl><dt>Idioma estudado</dt><dd>{draft.language}</dd><dt>Idioma de apoio</dt><dd>{supportLanguageLabels[draft.supportLanguage]}</dd><dt>Material</dt><dd>{draft.kind}</dd><dt>{sourceKind ? 'Arquivo' : 'Conteúdo'}</dt><dd>{sourceKind ? (draft.attachment?.file.name ?? 'Ainda não anexado') : sampleEnabled ? '6 itens de exemplo' : 'Sem inventário de exemplo'}</dd>{sourceKind === 'highlights' && <><dt>Interpretar como</dt><dd>{draft.highlightInput === 'vocabulary' ? 'Palavras ou expressões' : 'Trechos de leitura'}</dd></>}<dt>Execução</dt><dd>{sampleEnabled ? 'Até o resultado final' : 'Somente rascunho'}</dd><dt>Custo real</dt><dd>Nenhuma chamada paga</dd></dl><hr/><h3>Etapas do processamento</h3><ol className="stage-list" aria-live="polite">{stages.map((s, i) => <li key={s} className={step >= i ? 'stage-active' : ''}><span>{step > i ? <><Icon name="check" size={14}/><span className="sr-only">Concluído:</span></> : i + 1}</span>{s}{step === i && <small>Simulando</small>}</li>)}</ol><p className="field-note">O tempo e os estados apresentados nesta simulação são fictícios.</p></aside>
        </div>
      </>}

      {screen === 'result' && <>
        <button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><div><h1>{activeDeck?.name ?? demoProduction.name} <span className="title-language">{activeDeck?.language ?? demoProduction.language}</span></h1><p className="muted">Idioma de apoio: <strong>{supportLanguageLabels[activeDeck?.supportLanguage ?? demoProduction.supportLanguage]}</strong>. Confira o conteúdo e suas pendências.</p></div><button className="button secondary" disabled={!canExport(cards, true)} title="A exportação exige integração com o backend">Exportar para Anki</button></div>
        <div className="result-summary"><span><strong>{cards.length}</strong> cartões de exemplo</span><span><i className="dot green"/><strong>{cards.length - pending}</strong> concluídos</span><span><i className="dot amber"/><strong>{pending}</strong> para conferir</span><span className="result-hint">Exportação e áudio real indisponíveis no protótipo</span></div>
        <section className="panel review-panel"><div className="review-toolbar"><div className="tabs" role="group" aria-label="Filtrar cartões"><button aria-pressed={filter === 'all'} className={filter === 'all' ? 'selected' : ''} onClick={() => { setFilter('all'); setEditing(false); }}>Todos <span>{cards.length}</span></button><button aria-pressed={filter === 'pending'} className={filter === 'pending' ? 'selected' : ''} onClick={() => { setFilter('pending'); setEditing(false); }}>Pendências <span>{pending}</span></button></div><Search value={query} onChange={q => { setQuery(q); setEditing(false); }} placeholder="Buscar palavra"/></div>
        <div className="review-layout"><div className="card-list" role="group" aria-label="Cartões da produção">{visible.map(c => <button key={c.id} className={`card-list-item ${current?.id === c.id ? 'chosen' : ''}`} aria-pressed={current?.id === c.id} onClick={() => { setSelected(c.id); setEditing(false); }}><span className="item-number">{c.id}</span><span className="card-list-copy"><strong>{c.word}</strong><small>{c.definition || 'Conteúdo não concluído'}</small><span className={`card-state ${c.status}`}><span className="dot"/>{labels[c.status]}</span></span>{current?.id === c.id && <Icon name="arrow" size={15}/>}</button>)}{visible.length === 0 && <p className="empty">Nenhum cartão com esses filtros.</p>}</div>
        {current ? <div className="review-detail"><div className="detail-heading"><span className="tiny-label">RESULTADO DEMONSTRATIVO</span><Badge status={current.status}/></div>
          <AnkiTemplatePreview key={`${activeDeck?.id ?? 'demo'}:${current.id}`} deckType={activeDeck?.kind ?? demoProduction.kind} language={activeDeck?.language ?? demoProduction.language} card={current}/>
          <div className={`finding ${current.status === 'ready' ? 'finding-neutral' : ''}`}><strong>{current.status === 'failed' ? 'Conteúdo incompleto' : current.audio === 'outdated' ? 'O texto foi alterado' : current.audio === 'missing' ? 'Áudio pendente' : current.status === 'review' ? 'Conteúdo para conferir' : 'Nenhuma pendência no cenário demonstrativo'}</strong><p>{current.audio === 'outdated' ? 'Tradução, áudio e validações precisam ser conferidos novamente.' : current.status === 'failed' ? 'A produção real deverá permitir recuperar a etapa que falhou.' : current.status !== 'ready' ? 'Este registro ilustra uma pendência. A revisão real virá das evidências do sistema.' : 'Os estados são fictícios e não certificam a qualidade deste conteúdo.'}</p></div>
          {editing ? <CardEditor key={current.id} card={current} onCancel={() => setEditing(false)} onSave={patch => { setCards(cards.map(c => c.id === current.id ? editCard(c, patch) : c)); setEditing(false); setToast('Alteração aplicada nesta sessão. Conteúdo alterado fica pendente de revisão.'); }}/> : <div className="detail-actions"><button className="button secondary" onClick={() => setEditing(true)}>Editar conteúdo</button><span className="field-note">Alterações ficam apenas nesta sessão.</span></div>}
        </div> : <div className="review-detail empty"><Icon name="search" size={32}/><h2>Nenhum resultado</h2><p>Altere a busca ou volte para todos os cartões.</p><button className="button secondary" onClick={() => { setFilter('all'); setQuery(''); }}>Limpar filtros</button></div>}
        </div></section>
      </>}
      <footer className="page-footer"><span className="page-footer-brand"><BrandMark/><span className="footer-caption">Estúdio de produção</span></span><span>Estúdio local</span></footer>
      </div>
    </main>
    {toast && <div className="toast" role="status">{toast}<button aria-label="Fechar mensagem" onClick={() => setToast('')}><Icon name="close" size={18}/></button></div>}
  </div>;
}

function BrandMark() {
  return <><svg className="brand-symbol" viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" aria-hidden="true"><path d="M5 32V9l15 9L35 9v23"/><path d="M5 9v23l15-9 15 9M20 18v5"/></svg><span className="brand-wordmark">multilang</span></>;
}

function Search({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) { return <label className="search"><Icon name="search" size={17}/><span className="sr-only">{placeholder}</span><input type="search" value={value} placeholder={placeholder} onChange={e => onChange(e.target.value)}/></label>; }
function Stat({ icon, label, value, caption, accent }: { icon: string; label: string; value: string; caption: string; accent?: boolean }) { return <div className={`stat ${accent ? 'stat-accent' : ''}`}><div className="stat-top"><span>{label}</span><Icon name={icon}/></div><strong>{value}</strong><small>{caption}</small></div>; }

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
