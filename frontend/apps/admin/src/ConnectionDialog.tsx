import { useEffect, useId, useRef } from 'react';
import type { ReactNode } from 'react';

export function ConnectionDialog({ title, children, onClose, tone = 'neutral' }: {
  title: string; children: ReactNode; onClose: () => void; tone?: 'neutral' | 'success' | 'error';
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    dialog.current?.showModal();
    return () => dialog.current?.close();
  }, []);

  return <dialog ref={dialog} className={`connection-dialog ${tone}`} aria-labelledby={titleId} onClose={onClose}>
    <div className="connection-dialog-heading"><h2 id={titleId}>{title}</h2><button type="button" className="dialog-close" aria-label="Fechar" onClick={() => dialog.current?.close()}><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M5 5 19 19M19 5 5 19"/></svg></button></div>
    {children}
  </dialog>;
}
