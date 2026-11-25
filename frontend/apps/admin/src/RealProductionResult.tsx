import { useEffect, useMemo, useState } from 'react';
import { pageSize, productionResult } from './result-api';
import type { ResultPage, ReviewNote } from './result-api';

export function RealProductionResult({ productionId }: { productionId: string }) {
  const api = useMemo(() => productionResult(productionId), [productionId]);
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState({ q: '', offset: 0 });
  const [page, setPage] = useState<ResultPage>();
  const [selected, setSelected] = useState('');
  const [changes, setChanges] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [readError, setReadError] = useState('');
  const [approvalError, setApprovalError] = useState('');
  const [notice, setNotice] = useState('');
  const dirty = Object.keys(changes).length > 0;
  const locked = saving || dirty;
  const note = page?.notes.find(item => item.id === selected) ?? page?.notes[0];

  const approved = page?.approval.latest;

  useEffect(() => {
    const controller = new AbortController();
    setPage(undefined);
    setReadError('');
    setApprovalError('');
    setError('');
    api.page(query.q, query.offset, controller.signal).then(result => {
      if (controller.signal.aborted) return;
      if (!result.notes.length && query.offset > 0) {
        setQuery({ ...query, offset: Math.max(0, Math.ceil(result.total / pageSize) - 1) * pageSize });
      } else setPage(result);
    }).catch(reason => {
      if (!controller.signal.aborted) setReadError(reason instanceof Error ? reason.message : 'Falha ao carregar as notas.');
    });
    return () => controller.abort();
  }, [api, query]);

  function reload() {
    setChanges({});
    setQuery({ ...query });
  }
  async function save(action: () => Promise<ReviewNote>) {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const updated = await action();
      setSelected(updated.id);
      reload();
      setNotice('Alteração salva.');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao salvar a alteração.');
    } finally {
      setSaving(false);
    }
  }

  async function approve() {
    if (locked || !page) return;
    setSaving(true);
    setApprovalError('');
    setNotice('');
    try {
      const approval = await api.approve(page.approval.revision);
      setPage({ ...page, approval });
    } catch (reason) {
      setApprovalError(reason instanceof Error ? reason.message : 'Falha ao aprovar a revisão.');
    } finally {
      setSaving(false);
    }
  }

  return <section className="panel" aria-label="Revisão das notas">
    <div className="panel-heading"><h2>Revisão das notas</h2>
      {!locked && <a className="button secondary" href={api.exportUrl} download>Baixar deck atual (.apkg)</a>}
    </div>
    {page && <div aria-label="Aprovação da produção">
      <p role="status"><strong>{{
        pending: 'Revisão pendente',
        approved: 'Revisão aprovada',
        needs_approval: 'A edição atual requer nova aprovação',
      }[page.approval.state]}</strong></p>
      {approved && <>
        <details>
          <summary>Última aprovação · <time dateTime={approved.approvedAt}>
            {new Date(approved.approvedAt).toLocaleString('pt-BR')}
          </time> · <code>{approved.snapshotSha256.slice(0, 12)}</code></summary>
          <p>Operador: {approved.operator}</p>
          <p>Versão aprovada (SHA-256): <code style={{ overflowWrap: 'anywhere' }}>{approved.snapshotSha256}</code></p>
        </details>
        <div className="review-toolbar">
          <a className="button secondary" href={api.approvedExportUrl(approved.snapshotSha256, 'csv')} download>CSV da versão aprovada</a>
          <a className="button secondary" href={api.approvedExportUrl(approved.snapshotSha256, 'tsv')} download>TSV da versão aprovada</a>
        </div>
      </>}
      {page.approval.state !== 'approved' && <button className="button primary"
        disabled={locked || !note || !!approvalError} onClick={() => void approve()}>Aprovar revisão</button>}
      {approvalError && <p role="alert">{approvalError} <button className="text-button" onClick={reload}>Recarregar revisão</button></p>}
    </div>}
    <form className="review-toolbar" onSubmit={event => {
      event.preventDefault();
      if (!locked) { setNotice(''); setQuery({ q: search.trim(), offset: 0 }); }
    }}>
      <label>Buscar nas notas<input type="search" maxLength={200} value={search} disabled={locked} onChange={event => setSearch(event.target.value)}/></label>
      <button className="button secondary" disabled={locked}>Buscar</button>
    </form>
    {notice && <p className="field-note" role="status">{notice}</p>}
    {readError ? <div className="empty"><p role="alert">{readError}</p><button onClick={reload}>Tentar novamente</button></div>
      : !page ? <p className="empty" role="status">Carregando notas…</p>
      : !note ? <p className="empty">Nenhuma nota encontrada.</p>
      : <>
        <nav className="review-toolbar" aria-label="Paginação das notas">
          <button className="text-button" disabled={locked || query.offset === 0} onClick={() => setQuery({ ...query, offset: query.offset - pageSize })}>Anterior</button>
          <span>{query.offset + 1} a {query.offset + page.notes.length} de {page.total}</span>
          <button className="text-button" disabled={locked || query.offset + page.notes.length >= page.total} onClick={() => setQuery({ ...query, offset: query.offset + pageSize })}>Próxima</button>
        </nav>
        <div className="review-layout"><div className="card-list">{page.notes.map(item =>
          <button className={'card-list-item' + (item.id === note.id ? ' chosen' : '')} aria-pressed={item.id === note.id} disabled={locked}
            key={item.id} onClick={() => { setSelected(item.id); setError(''); setNotice(''); }}>
            <span className="card-list-copy"><strong>{item.title}</strong><small>{item.model}</small></span>
          </button>)}</div>
          <article className="review-detail"><h3>{note.title}</h3>
            {note.fields.map(field => <div className="review-field" key={field.name}>
              {field.editable ? <label>{field.name}<textarea aria-label={field.name} value={changes[field.name] ?? field.text} disabled={saving} maxLength={6000}
                onChange={event => {
                  const next = { ...changes, [field.name]: event.target.value };
                  if (next[field.name] === field.text) delete next[field.name];
                  setChanges(next); setNotice('');
                }}/></label> : <><strong>{field.name}</strong>{field.text && <p>{field.text}</p>}</>}
              {field.audio.map((number, index) => <audio key={index} controls preload="none" aria-label={'Áudio de ' + field.name} src={api.audioUrl(number)}/>)}
              {field.imageField && <>
                {field.hasImage && <img alt={'Imagem de ' + note.title} src={api.imageUrl(note, field.name)}/>}
                <label>Selecionar PNG<input type="file" accept="image/png,.png" disabled={locked} onChange={event => {
                  const file = event.target.files?.[0];
                  event.target.value = '';
                  if (file) void save(() => api.upload(note, field.name, file));
                }}/></label>
                {field.hasImage && <button className="text-button" disabled={locked} onClick={() => void save(() => api.edit(note, { [field.name]: '' }))}>Remover imagem</button>}
              </>}
            </div>)}
            {dirty && <div className="detail-actions">
              <button className="button primary" disabled={saving || Object.values(changes).some(text => !text.trim())} onClick={() => void save(() => api.edit(note, changes))}>Salvar texto</button>
              <button className="button secondary" disabled={saving} onClick={() => setChanges({})}>Descartar alterações</button>
            </div>}
            {error && <div><p role="alert">{error}</p><button className="text-button" onClick={reload}>Descartar alterações e recarregar nota</button></div>}
          </article>
        </div></>}
  </section>;
}
