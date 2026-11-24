import { useEffect, useRef, useState } from 'react';

type Option<T extends string> = { value: T; label: string };

export function SelectMenu<T extends string>({ value, options, onChange, disabled, describedBy }: {
  value: T; options: readonly Option<T>[]; onChange: (value: T) => void;
  disabled?: boolean; describedBy?: string;
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const selected = options.find(option => option.value === value);

  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, [open]);

  return <div className="select-menu" ref={root}>
    <button type="button" className="select-trigger" aria-haspopup="listbox" aria-expanded={open} aria-describedby={describedBy} disabled={disabled}
      onClick={() => setOpen(previous => !previous)} onKeyDown={event => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault(); setOpen(true);
          requestAnimationFrame(() => root.current?.querySelector<HTMLButtonElement>('[role=option]')?.focus());
        } else if (event.key === 'Escape') setOpen(false);
      }}>{selected?.label ?? value}<span aria-hidden="true">⌄</span></button>
    {open && <div className="select-options" role="listbox" aria-label="Escolha uma opção" onKeyDown={event => {
      const items = Array.from(root.current?.querySelectorAll<HTMLButtonElement>('[role=option]') ?? []);
      const index = items.indexOf(document.activeElement as HTMLButtonElement);
      if (event.key === 'Escape') { setOpen(false); root.current?.querySelector<HTMLButtonElement>('.select-trigger')?.focus(); }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); items[(index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      }
    }}>{options.map(option => <button type="button" role="option" aria-selected={option.value === value} className="select-option" key={option.value}
      onClick={() => { onChange(option.value); setOpen(false); root.current?.querySelector<HTMLButtonElement>('.select-trigger')?.focus(); }}>{option.label}</button>)}</div>}
  </div>;
}
