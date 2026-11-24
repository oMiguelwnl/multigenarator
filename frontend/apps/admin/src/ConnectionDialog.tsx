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
    <div className="connection-dialog-heading"><h2 id={titleId}>{title}</h2><button type="button" className="dialog-close" aria-label="Fechar" onClick={() => dialog.current?.close()}>×</button></div>
    {children}
  </dialog>;
}
