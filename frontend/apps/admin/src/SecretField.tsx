import { useEffect, useState } from 'react';
import { studioApi } from './studio-api';

export function SecretField({ name, label, configured, pending, onChange, onBlur, placeholder }: {
  name: string; label: string; configured: boolean; pending: string;
  onChange: (value: string) => void; onBlur: () => void; placeholder: string;
}) {
  const [editing, setEditing] = useState(false);
  const [revealed, setRevealed] = useState('');
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    if (configured && !pending) { setEditing(false); setVisible(false); setRevealed(''); }
    if (!configured) { setRevealed(''); setVisible(false); }
  }, [configured, pending]);
  async function toggle() {
    if (visible) { setVisible(false); setRevealed(''); return; }
    if (editing || !configured) { setVisible(true); return; }
    try {
      const result = await studioApi(`keys/${name}/reveal`, 'POST');
      setRevealed(result.value); setVisible(true); setError('');
    } catch { setError('Não foi possível mostrar o valor.'); }
  }
  return <div className="secret-field">
    <label>{label}<span className="secret-control">
      {configured && !editing ? <input type={visible ? 'text' : 'password'} readOnly autoComplete="off" value={visible ? revealed : '••••••••••••'} aria-label={`${label} ${visible ? 'visível' : 'oculta'}`}/>
        : <input type={visible ? 'text' : 'password'} autoComplete="off" maxLength={4096} value={pending} placeholder={placeholder} onChange={event => onChange(event.target.value)} onBlur={onBlur}/>}
      <button type="button" className="secret-eye" aria-label={visible ? `Ocultar ${label}` : `Mostrar ${label}`} aria-pressed={visible} onClick={() => void toggle()}>
        <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="3"/>{!visible && <path d="M4 20 20 4"/>}</svg>
      </button>
    </span></label>
    {configured && !editing && <button type="button" className="text-button secret-replace" onClick={() => { setEditing(true); setVisible(false); setRevealed(''); }}>Substituir</button>}
    {error && <span className="field-note" role="alert">{error}</span>}
  </div>;
}
