import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { saveProductionDraft, availableSupportLanguages, isSupportLanguageAllowed, changeStudyLanguage, changeMaterial, supportLanguageLabels } from './model';
import type { Draft } from './model';
import { LANGUAGE_CODES } from './anki-preview';
import { materialId, materialLabels, languageName, repairProduction, startProduction, statusLabels } from './production-api';
import { useProductions } from './use-productions';
import { RealProductionResult } from './RealProductionResult';
import { sourceKindFor } from './source-files';
import { SourceFileInput } from './SourceFileInput';
import { AnkiTemplatePreview } from './AnkiTemplatePreview';
import { Connections } from './Connections';
import { SelectMenu } from './SelectMenu';
import './styles.css';
import { loadDrafts, persistDraft } from './draft-store';

type Screen = 'connections' | 'productions' | 'history' | 'new' | 'result';
const createDraft = (): Draft => ({ id: crypto.randomUUID(), name: '', language: 'Inglês', supportLanguage: 'pt', kind: 'Frequência' });

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

function App() {
  const initialScreen = (): Screen => location.hash.startsWith('#conexoes') ? 'connections' : location.hash === '#nova' ? 'new' : location.hash.startsWith('#resultado') ? 'result' : location.hash === '#historico' ? 'history' : 'productions';
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { items, catalog, error: connectionError, refresh } = useProductions();
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [resultId, setResultId] = useState<string | undefined>(() => location.hash.split('?')[0].split('/')[1]);
  const repairAttempt = useRef<{ version: string; id: string } | null>(null);
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
  const [toast, setToast] = useState('');
  const [productionQuery, setProductionQuery] = useState('');
  const [readingFile, setReadingFile] = useState(false);
  const mobileMenuToggleRef = useRef<HTMLButtonElement>(null);
  const mobileMenuCloseRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLElement>(null);
  useEffect(() => { const onHash = () => { setScreen(initialScreen()); setResultId(location.hash.split('/')[1]); }; window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash); }, []);
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
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 6500); return () => clearTimeout(timer); }, [toast]);
  const go = (next: Screen, id?: string) => {
    const routes = { connections: 'conexoes', new: 'nova', result: 'resultado', history: 'historico', productions: 'producoes' };
    location.hash = routes[next] + (id ? '/' + id : '');
    setScreen(next); setResultId(id); window.scrollTo(0, 0);
  };
  const sourceKind = sourceKindFor(draft.kind);
  const languageCode = LANGUAGE_CODES[draft.language];
  const kind = materialId(draft.kind);
  const offered = kind && catalog[languageCode]?.includes(kind);
  const compatibleSupport = ['frequency', 'word-list', 'highlights'].includes(kind ?? '') || draft.supportLanguage === 'pt';
  const canStart = offered && compatibleSupport && (!sourceKind || (draft.attachment && previewReady));
  const matching = (name: string) => name.toLocaleLowerCase().includes(productionQuery.trim().toLocaleLowerCase());
  const visibleDrafts = drafts.filter(d => !items.some(job => job.id === d.id));
  const completed = items.filter(job => job.status === 'completed');
  const isEditingDraft = drafts.some(item => item.id === draft.id);
  const closeMobileMenu = () => setMobileMenuOpen(false);
  const startNew = () => { setDraft(createDraft()); setPreviewReady(false); go('new'); };
  async function generate() {
    if (!canStart || submitting.current || !draft.name.trim()) return;
    submitting.current = true; setBusy(true);
    try {
      const job = await startProduction(draft, draft.id);
      refresh(); go('result', job.id);
    } catch (e) { setToast(e instanceof Error ? e.message : 'Falha ao iniciar a produção.'); }
    finally { submitting.current = false; setBusy(false); }
  }
  const activeJob = items.find(item => item.id === resultId);
  async function repair() {
    if (!activeJob || submitting.current) return;
    submitting.current = true; setBusy(true);
    const version = activeJob.id + '/' + activeJob.updatedAt;
    if (repairAttempt.current?.version !== version) repairAttempt.current = { version, id: crypto.randomUUID() };
    try { await repairProduction(activeJob.id, repairAttempt.current.id); refresh(); }
    catch (e) { setToast(e instanceof Error ? e.message : 'Falha ao corrigir a produção.'); }
    finally { submitting.current = false; setBusy(false); }
  }
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
        <a className={screen === 'productions' ? 'active' : ''} aria-current={screen === 'productions' ? 'page' : undefined} href="#producoes" onClick={closeMobileMenu}><Icon name="grid"/>Produções<span className="nav-count">{items.length + visibleDrafts.length}</span></a>
        <a className={screen === 'new' ? 'active' : ''} aria-current={screen === 'new' ? 'page' : undefined} href="#nova" onClick={event => { event.preventDefault(); startNew(); closeMobileMenu(); }}><Icon name="plus"/>Nova produção</a>
        <a className={screen === 'history' ? 'active' : ''} aria-current={screen === 'history' ? 'page' : undefined} href="#historico" onClick={event => { event.preventDefault(); go('history'); closeMobileMenu(); }}><Icon name="clock"/>Histórico<span className="nav-count">{completed.length}</span></a>
        <a className={screen === 'result' ? 'active' : ''} aria-current={screen === 'result' ? 'page' : undefined} href="#resultado" onClick={closeMobileMenu}><Icon name="book"/>Resultado e revisão</a>
        <a className={screen === 'connections' ? 'active' : ''} aria-current={screen === 'connections' ? 'page' : undefined} href="#conexoes" onClick={closeMobileMenu}><Icon name="connections"/>Provedores e conexões</a>
      </nav>
      <div className="profile"><span className="avatar">MR</span><div>Meu estúdio<small>Administrador local</small></div></div>
    </aside>

    <main id="conteudo" tabIndex={-1}>
      <header className="topbar"><span>Estúdio <span className="crumb">/</span> {screen === 'connections' ? 'Provedores e conex\u00f5es' : screen === 'new' ? (isEditingDraft ? 'Editar produção' : 'Nova produção') : screen === 'result' ? 'Resultado e revisão' : screen === 'history' ? 'Histórico' : 'Produções'}</span><span className="prototype"><span className="dot"/>Estúdio local</span></header>
      {screen !== 'connections' && connectionError && <div className="demo-banner" role="status">{connectionError} <button className="text-button" onClick={refresh}>Tentar novamente</button></div>}
      <div className={`page${screen === 'connections' ? ' page-connections' : ''}`}>
      {screen === 'connections' && <Connections/>}
      {screen === 'productions' && <>
        <div className="page-heading"><div><h1>Produções</h1><p className="muted">Acompanhe cada etapa e confira os resultados.</p></div><button className="button primary" onClick={startNew}><Icon name="plus"/>Nova produção</button></div>
        <div className="stats"><Stat icon="layers" label="Produções" value={String(items.length)} caption="Registradas no Estúdio"/><Stat icon="clock" label="Em andamento" value={String(items.filter(j => j.status === 'running' || j.status === 'queued').length)} caption="Em execução ou na fila"/><Stat icon="check" label="Concluídas" value={String(completed.length)} caption="Resultado disponível"/></div>
        <section className="panel production-panel"><div className="panel-heading"><h2>Suas produções</h2><Search value={productionQuery} onChange={setProductionQuery} placeholder="Buscar produção"/></div>
          <div className="table-wrap"><table className="productions-table"><thead><tr><th>Produção</th><th>Material</th><th>Situação</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>
          {items.filter(job => matching(job.name)).map(job => <tr key={job.id}><td><strong>{job.name}</strong><small>{languageName(job.language)}</small></td><td data-label="Material">{materialLabels[job.kind]}</td><td data-label="Situação">{statusLabels[job.status]}</td><td><button className="text-button" onClick={() => go('result', job.id)}>Abrir produção</button></td></tr>)}
          {visibleDrafts.filter(d => matching(d.name)).map(d => <tr key={d.id}><td><strong>{d.name}</strong></td><td data-label="Material">{d.kind}</td><td data-label="Situação">Rascunho</td><td><button className="text-button" onClick={() => { setDraft(d); setPreviewReady(false); go('new'); }}>Editar rascunho</button></td></tr>)}
          </tbody></table></div>
          {![...items, ...visibleDrafts].some(d => matching(d.name)) && <p className="empty">{productionQuery ? 'Nenhuma produção corresponde à busca.' : 'Crie sua primeira produção para acompanhar o andamento aqui.'}</p>}
        </section>
      </>}

      {screen === 'history' && <><div className="page-heading"><h1>Histórico de decks</h1></div>
        <section className="panel production-panel">{completed.map(job => <div className="panel-heading" key={job.id}><div><h2>{job.name}</h2><p>{new Date(job.updatedAt).toLocaleString('pt-BR')}</p></div><button className="text-button" onClick={() => go('result', job.id)}>Revisar deck</button></div>)}
          {!completed.length && <p className="empty">Os decks concluídos aparecerão aqui.</p>}</section></>}

      {screen === 'new' && <>
        <button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><div><h1>{isEditingDraft ? 'Editar produção' : 'Uma nova produção'}</h1><p className="muted">Configure uma vez. Confira o resultado ao final.</p></div><span className="badge draft">Rascunho</span></div>
        <div className="form-layout"><form className="panel configuration" onSubmit={e => { e.preventDefault(); void generate(); }}>
          <fieldset disabled={busy}><legend><span className="number">01</span> O que vamos preparar?</legend>
            <label>Nome da produção<input required maxLength={100} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })}/></label>
            <div className="two-fields">
              <label>Idioma estudado<SelectMenu value={draft.language} onChange={value => {
                const next = changeStudyLanguage(draft, value);
                setDraft(next);
                if (next.highlightInput !== draft.highlightInput) setToast('Para coreano, o apoio é português e os destaques usam o modo de trechos de leitura.');
                else if (next.supportLanguage !== draft.supportLanguage) setToast('Para coreano, o idioma de apoio foi ajustado para português.');
              }} options={['Inglês', 'Coreano', 'Japonês', 'Latim', 'Espanhol', 'Francês', 'Alemão', 'Italiano', 'Português', 'Polonês', 'Turco', 'Romeno', 'Russo', 'Holandês', 'Mandarim', 'Tcheco', 'Dinamarquês', 'Finlandês', 'Grego', 'Croata', 'Húngaro', 'Norueguês', 'Sueco'].map(l => ({ value: l, label: l }))}/></label>
              <label>Idioma de apoio<SelectMenu value={draft.supportLanguage} disabled={draft.language === 'Coreano'} describedBy={draft.language === 'Coreano' ? 'support-language-help korean-support-constraint' : 'support-language-help'} onChange={value => {
                if (isSupportLanguageAllowed(draft.language, value)) setDraft({ ...draft, supportLanguage: value });
              }} options={availableSupportLanguages(draft.language).map(code => ({ value: code, label: supportLanguageLabels[code] }))}/></label>
            </div>
            <p className="field-note support-language-help" id="support-language-help">Idioma das definições, traduções das frases e rótulos dos cartões deste deck. O aplicativo continua em português.</p>
            {draft.language === 'Coreano' && <p className="field-note language-constraint" id="korean-support-constraint">Para coreano, apenas português está disponível como idioma de apoio.</p>}
            <label>Tipo de material<SelectMenu value={draft.kind} onChange={value => {
              const next = changeMaterial(draft, value);
              setDraft(next);
              if (draft.attachment && !next.attachment) setToast('O tipo de material mudou. Selecione o arquivo adequado para esta modalidade.');
            }} options={['Frequência', 'Lista personalizada', 'Destaques de leitura', 'Escrita e fundamentos', 'Pronúncia e fonética', 'Gramática', 'Latim clássico'].map(k => ({ value: k, label: k }))}/></label>
            <p className="field-note">As modalidades disponíveis dependem do idioma e dos recursos do backend.</p>
          </fieldset>
          <fieldset disabled={busy}><legend><span className="number">02</span> Conteúdo e apresentação</legend>
            {sourceKind ? <>
              {sourceKind === 'highlights' && <><label>O que os destaques contêm?<SelectMenu value={draft.highlightInput ?? 'text'} disabled={draft.language === 'Coreano'} describedBy="highlight-input-help" onChange={mode => {
                if (mode === 'text' || (mode === 'vocabulary' && draft.language !== 'Coreano')) setDraft({ ...draft, highlightInput: mode });
              }} options={[{ value: 'text', label: 'Trechos de leitura — extrair palavras' }, { value: 'vocabulary', label: 'Palavras ou expressões — um item por destaque' }]}/></label><p className="field-note highlight-input-help" id="highlight-input-help">{draft.language === 'Coreano' ? 'Coreano usa apenas trechos de leitura para análise linguística.' : draft.highlightInput === 'vocabulary' ? 'Cada destaque será tratado como uma palavra ou expressão. Para uma lista simples com um item por linha, use Lista personalizada.' : 'Confira na prévia as palavras reconhecidas nos trechos.'}</p></>}
              <SourceFileInput key={`${draft.id}:${draft.kind}`} kind={sourceKind} languageCode={languageCode} highlightMode={draft.highlightInput ?? 'text'} onPreviewReady={setPreviewReady} attachment={draft.attachment} disabled={busy} onBusyChange={setReadingFile} onChange={attachment => setDraft(previous => previous.id === draft.id && previous.kind === draft.kind ? { ...previous, attachment } : previous)}/>
            </> : draft.kind === 'Frequência' ? <label>Nível de frequência<SelectMenu value={String(draft.level ?? 1)} onChange={value => setDraft({ ...draft, level: Number(value) })} options={[1, 2, 3].map(level => ({ value: String(level), label: `Nível ${level}` }))}/></label> : null}
            <AnkiTemplatePreview key={`${draft.kind}:${draft.language}`} deckType={draft.kind} language={draft.language}/>
          </fieldset>
          <fieldset><legend><span className="number">03</span> Execução</legend><p>Ao gerar, o Estúdio executa o fluxo da modalidade selecionada. Os serviços de texto, tradução e áudio configurados podem ter custo.</p></fieldset>
          <div className="form-actions"><button type="button" className="button secondary" disabled={busy || readingFile || savingDraft || loadingDrafts} onClick={saveDraft}>{savingDraft ? 'Salvando…' : 'Salvar rascunho'}</button><button className="button primary" disabled={busy || readingFile || savingDraft || !canStart}>{busy ? 'Iniciando…' : 'Gerar produção'}</button></div>
          {!canStart && <p className="field-note" role="status">{!offered ? 'A geração desta combinação está indisponível no serviço local.' : !compatibleSupport ? 'Esta modalidade requer português como idioma de apoio.' : 'Anexe um arquivo com itens reconhecidos na prévia.'}</p>}
        </form>
        <aside className="summary panel"><h2>Sua produção</h2><dl><dt>Idioma estudado</dt><dd>{draft.language}</dd><dt>Idioma de apoio</dt><dd>{supportLanguageLabels[draft.supportLanguage]}</dd><dt>Material</dt><dd>{draft.kind}</dd>{sourceKind && <><dt>Arquivo</dt><dd>{draft.attachment?.file.name ?? 'Ainda não anexado'}</dd></>}</dl></aside>
        </div>
      </>}

      {screen === 'result' && <><button className="back-link" onClick={() => go('productions')}><Icon name="back" size={17}/>Produções</button>
        <div className="page-heading"><h1>{activeJob?.name ?? 'Resultado e revisão'}</h1></div>
        {activeJob ? <><section className="panel panel-heading" aria-live="polite"><div><h2>{statusLabels[activeJob.status]}</h2><p>{activeJob.message}</p></div>{activeJob.status === 'failed' && activeJob.jobId && <button className="button secondary" disabled={busy} onClick={repair}>Corrigir e reprocessar</button>}</section>
        {activeJob.canDownload && <RealProductionResult key={activeJob.id} productionId={activeJob.id}/>}</> : <div className="panel empty"><p>Abra uma produção para acompanhar a execução ou revisar seus cartões.</p><button className="button secondary" onClick={() => go('productions')}>Ver produções</button></div>}</>}
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
