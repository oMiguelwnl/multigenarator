import { useMemo, useState } from 'react';
import templateManifest from './anki-template-manifest.json';
import {
  buildPreviewFields,
  getAnkiTemplate,
  renderAnkiPreviewDocument,
  type AnkiTemplateManifest,
  type PreviewCard,
} from './anki-preview';

type Props = {
  deckType: string;
  language: string;
  card?: PreviewCard;
};

const manifest = templateManifest as AnkiTemplateManifest;

export function AnkiTemplatePreview({ deckType, language, card }: Props) {
  const [side, setSide] = useState<'front' | 'back'>('front');
  const template = getAnkiTemplate(manifest, deckType, language);
  const srcDoc = useMemo(() => {
    if (!template) return '';
    return renderAnkiPreviewDocument(template, buildPreviewFields(template.fields, card), side);
  }, [template, card, side]);

  if (!template) {
    return (
      <section className="anki-template-preview" aria-label="Apresentação do cartão">
        <div className="preview-heading">
          <div>
            <span className="tiny-label">TEMPLATE ANKI</span>
            <h3>Prévia indisponível</h3>
          </div>
        </div>
        <p className="field-note" role="status">
          Ainda não existe um template de exportação para {deckType.toLocaleLowerCase('pt-BR')} em {language}.
          A interface não vai substituir isso por um modelo ilustrativo.
        </p>
      </section>
    );
  }

  return (
    <section className="anki-template-preview" aria-label="Apresentação do cartão">
      <div className="preview-heading">
        <div>
          <span className="tiny-label">TEMPLATE ANKI REAL</span>
          <h3>{language} · {deckType}</h3>
        </div>
        <div className="preview-side-controls" role="group" aria-label="Lado do cartão">
          <button type="button" aria-pressed={side === 'front'} onClick={() => setSide('front')}>Frente</button>
          <button type="button" aria-pressed={side === 'back'} onClick={() => setSide('back')}>Verso</button>
        </div>
      </div>
      <iframe
        className="anki-template-frame"
        title={`Prévia do Anki: ${language}, ${deckType}, ${side === 'front' ? 'frente' : 'verso'}`}
        sandbox=""
        referrerPolicy="no-referrer"
        srcDoc={srcDoc}
      />
      <p className="field-note">
        Usa o template de exportação. Os dados são exemplos visuais; nenhum conteúdo, áudio ou deck é gerado.
      </p>
    </section>
  );
}
