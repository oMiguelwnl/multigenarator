import { useState } from 'react';
import { studioApi as api } from './studio-api';
import type { ApiKeyName, Configuration } from './Connections';

export function ProviderKeys({ provider, config, beforeChange, onUpdate, onMessage }: {
  provider: ApiKeyName; config: Configuration;
  beforeChange: () => Promise<void>; onUpdate: (config: Configuration) => void; onMessage: (message: string) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [label, setLabel] = useState('');
  const [value, setValue] = useState('');
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const keys = config.extra_keys.filter(entry => entry.provider === provider);
  const extraActive = keys.some(entry => entry.active);

  async function add() {
    if (!label.trim() || !value.trim()) return;
    setBusy(true); setError('');
    try {
      await beforeChange();
      const result: Configuration = await api(`keys/${provider}`, 'POST', { label: label.trim(), value: value.trim() });
      onUpdate(result);
      setLabel(''); setValue(''); setAdding(false);
      onMessage(result.extra_keys.at(-1)?.active ? 'Chave adicional salva e ativada.' : 'Chave adicional salva no cofre local. Selecione-a para usá-la.');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Não foi possível salvar a chave.'); }
    finally { setBusy(false); }
  }

  async function change(path: string, method: 'POST' | 'DELETE', message: string, id?: string) {
    setBusy(true); setError('');
    try {
      await beforeChange();
      onUpdate(await api(path, method));
      if (id) setRevealed(previous => { const next = { ...previous }; delete next[id]; return next; });
      onMessage(message);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Não foi possível alterar a chave.'); }
    finally { setBusy(false); }
  }

  async function toggle(id: string) {
    if (revealed[id]) {
      setRevealed(previous => { const next = { ...previous }; delete next[id]; return next; });
      return;
    }
    try {
      const result = await api(`keys/${provider}/${id}/reveal`, 'POST');
      setRevealed(previous => ({ ...previous, [id]: result.value }));
      setError('');
    } catch { setError('Não foi possível mostrar a chave.'); }
  }

  return <div className="provider-keys">
    <div className="provider-keys-heading"><h3>Chaves adicionais</h3><button type="button" className="text-button" onClick={() => { setAdding(previous => !previous); setLabel(''); setValue(''); setError(''); }}>{adding ? 'Cancelar' : 'Adicionar outra chave'}</button></div>
    {config.configured[provider] && !extraActive && <p className="field-note">Chave principal em uso.</p>}
    {config.configured[provider] && extraActive && <button type="button" className="text-button" disabled={busy} onClick={() => void change(`keys/${provider}/primary/activate`, 'POST', 'Chave principal ativada.')}>Usar chave principal</button>}
    {keys.map(entry => <div className="provider-key-row" key={entry.id}>
      <div className="provider-key-info"><strong>{entry.label}</strong><code>{revealed[entry.id] ?? '••••••••••••'}</code></div>
      {entry.active && <span className="provider-key-active">Em uso</span>}
      <button type="button" className="provider-key-eye" aria-label={`${revealed[entry.id] ? 'Ocultar' : 'Mostrar'} ${entry.label}`} disabled={busy} onClick={() => void toggle(entry.id)}><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="3"/>{!revealed[entry.id] && <path d="M4 20 20 4"/>}</svg></button>
      {!entry.active && <button type="button" className="text-button" disabled={busy} onClick={() => void change(`keys/${provider}/${entry.id}/activate`, 'POST', `${entry.label} ativada.`)}>Usar esta</button>}
      <button type="button" className="text-button" disabled={busy} onClick={() => void change(`keys/${provider}/${entry.id}`, 'DELETE', 'Chave adicional removida.', entry.id)}>Remover</button>
    </div>)}
    {adding && <div className="provider-key-add"><label>Nome da chave<input maxLength={80} value={label} placeholder="Ex.: Reserva" onChange={event => setLabel(event.target.value)} onKeyDown={event => { if (event.key === 'Enter') { event.preventDefault(); void add(); } }}/></label><label>Nova chave<input type="password" autoComplete="off" maxLength={4096} value={value} placeholder="Cole a chave de API" onChange={event => setValue(event.target.value)} onKeyDown={event => { if (event.key === 'Enter') { event.preventDefault(); void add(); } }}/></label><button type="button" className="button secondary" disabled={busy || !label.trim() || !value.trim()} onClick={() => void add()}>Salvar chave</button></div>}
    {error && <p role="alert" className="field-note">{error}</p>}
  </div>;
}
