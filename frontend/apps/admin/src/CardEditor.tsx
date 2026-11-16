import { useEffect, useRef, useState } from 'react';
import type { Card } from './model';

type Patch = Pick<Card, 'definition' | 'sentence' | 'translation' | 'image'>;

export function CardEditor({ card, onSave, onCancel }: { card: Card; onSave: (patch: Patch) => void; onCancel: () => void }) {
  const [image, setImage] = useState(card.image);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const version = useRef(0);
  useEffect(() => () => { version.current++; }, []);

  async function selectImage(file?: File) {
    if (!file) return;
    const request = ++version.current;
    setError('');
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size === 0 || file.size > 5_000_000) {
      setError('Escolha uma imagem PNG, JPG ou WebP de até 5 MB.');
      return;
    }
    setBusy(true);
    try {
      const bitmap = await createImageBitmap(file);
      try {
        if (bitmap.width * bitmap.height > 20_000_000) throw new Error('dimensions');
        const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(bitmap.width * scale));
        canvas.height = Math.max(1, Math.round(bitmap.height * scale));
        const context = canvas.getContext('2d');
        if (!context) throw new Error('canvas');
        context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
        const normalized = canvas.toDataURL('image/png');
        if (request === version.current) setImage(normalized);
      } finally { bitmap.close(); }
    } catch {
      if (request === version.current) setError('Não foi possível abrir a imagem. Use outro arquivo com até 20 megapixels.');
    } finally {
      if (request === version.current) setBusy(false);
    }
  }

  return <form className="edit-form" onSubmit={event => {
    event.preventDefault();
    if (busy) return;
    const data = new FormData(event.currentTarget);
    onSave({ definition: String(data.get('definition')), sentence: String(data.get('sentence')), translation: String(data.get('translation')), image });
  }}>
    <label>Definição<textarea name="definition" required maxLength={2000} defaultValue={card.definition}/></label>
    <label>Frase<textarea name="sentence" required maxLength={2000} defaultValue={card.sentence}/></label>
    <label>Tradução<textarea name="translation" required maxLength={2000} defaultValue={card.translation}/></label>
    <div className="card-image-field">
      <label htmlFor="card-image">Imagem <span className="field-note">(opcional)</span></label>
      <p id="image-help" className="field-note">PNG, JPG ou WebP, até 5 MB. Escolha uma imagem que ajude a lembrar a palavra.</p>
      {image ? <img className="card-image-preview" src={image} alt={`Imagem escolhida para ${card.word}`}/> : <p className="image-empty">Este cartão ainda não tem imagem.</p>}
      <input id="card-image" type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} aria-describedby="image-help image-status" onChange={event => { void selectImage(event.target.files?.[0]); event.target.value = ''; }}/>
      {image && <button type="button" className="text-button" disabled={busy} onClick={() => { setImage(undefined); setError(''); }}>Remover imagem</button>}
      <p id="image-status" className="field-note" role="status">{busy ? 'Preparando imagem…' : error || (image ? 'Imagem pronta. Salve para aplicar ao cartão.' : 'A imagem ficará apenas nesta sessão.')}</p>
    </div>
    <div className="form-actions"><button type="button" className="button secondary" onClick={onCancel}>Cancelar</button><button className="button primary" disabled={busy}>Salvar alteração</button></div>
  </form>;
}
