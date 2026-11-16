export type AnkiTemplateDefinition = {
  fields: string[];
  front: string;
  back: string;
  css: string;
};

export type AnkiTemplateManifest = {
  version: number;
  catalog: Record<string, string>;
  templates: Record<string, AnkiTemplateDefinition>;
};

export type PreviewCard = {
  image?: string;
  word: string;
  definition: string;
  sentence: string;
  translation: string;
};

type TemplateNode =
  | { kind: 'text'; value: string }
  | { kind: 'field'; name: string }
  | { kind: 'section'; name: string; inverted: boolean; children: TemplateNode[] };

const LANGUAGE_CODES: Readonly<Record<string, string>> = {
  Português: 'pt',
  Espanhol: 'es',
  Inglês: 'en',
  Francês: 'fr',
  Alemão: 'de',
  Grego: 'el',
  Italiano: 'it',
  Polonês: 'pl',
  Turco: 'tr',
  Romeno: 'ro',
  Russo: 'ru',
  Holandês: 'nl',
  Dinamarquês: 'da',
  Norueguês: 'nb',
  Sueco: 'sv',
  Finlandês: 'fi',
  Húngaro: 'hu',
  Tcheco: 'cs',
  Croata: 'hr',
  Latim: 'la',
  Japonês: 'ja',
  Mandarim: 'zh',
  Coreano: 'ko',
};

const OPTIONAL_FIELDS = new Set([
  'SortIndex',
  'Image',
  'Picture',
  'Gif',
  'Strokes',
  'TargetConceptId',
  'PrerequisiteConceptIds',
  'ObservedConceptIds',
  'UnknownConceptIds',
  'IPlusOnePolicy',
]);

const AUDIO_FIELDS = new Set(['Audio', 'letter_audio', 'word_audio', 'sentence_audio']);

const SAMPLE_VALUES: Readonly<Record<string, string>> = {
  Category: 'Vogais',
  'Example Word': 'think',
  'Example Sentence': 'We gather in the garden every Sunday.',
  'Sentence Translation': 'Nós nos reunimos no jardim todos os domingos.',
  'Sentence Romaji': 'Watashitachi wa mainichi benkyou shimasu.',
  'Traditional Sentence': '我們每天學習。',
  'Word Translation': 'pensar',
  'Target Word': 'gather',
  Definitions: 'Reunir; juntar em um mesmo lugar.',
  Definition: 'A forma ou o significado apresentado neste card.',
  Grammar: 'Forma e uso apresentados no contexto.',
  IPA: '/ˈɡæðər/',
  JamoOrBlock: 'ㄱ',
  Kana: 'あ',
  Mnemonic: 'Uma dica curta para lembrar a forma.',
  Pinyin: 'xué xí',
  ReadingOrName: 'giyeok',
  Romaji: 'a',
  Script: 'Hiragana',
  Sound: '/θ/',
  Spellings: 'th',
  Traditional: '學習',
  Translation: 'Nós nos reunimos no jardim todos os domingos.',
  'Word Romaji': 'gather',
  'Word Reading': 'gather',
  word: 'gather',
  Word: 'gather',
  'Sentence Furigana': 'We gather in the garden every Sunday.',
};

const AUDIO_BUTTON =
  '<a class="replay-button" title="Áudio de demonstração indisponível" aria-label="Áudio de demonstração indisponível">' +
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9H3zm13.5 3a3.5 3.5 0 0 0-2-3.16v6.32a3.5 3.5 0 0 0 2-3.16zm-2-8.5v2.06a7 7 0 0 1 0 12.88v2.06a9 9 0 0 0 0-17z"/></svg>' +
  '</a>';

export function getAnkiTemplate(
  manifest: AnkiTemplateManifest,
  deckType: string,
  language: string,
): AnkiTemplateDefinition | undefined {
  const languageCode = LANGUAGE_CODES[language];
  if (!languageCode) return undefined;

  let key: string | undefined;
  if (deckType === 'Frequência' || deckType === 'Lista personalizada' || deckType === 'Destaques de leitura') {
    const sourceType = deckType === 'Frequência'
      ? 'frequency'
      : deckType === 'Lista personalizada'
        ? 'word-list'
        : 'kindle-highlights';
    key = `${sourceType}:${languageCode}`;
  } else if (deckType === 'Escrita e fundamentos') {
    if (languageCode === 'ko') key = 'korean-hangul:ko';
    if (languageCode === 'ja') key = 'japanese-kana:ja';
  } else if (deckType === 'Pronúncia e fonética') {
    if (languageCode === 'ko') key = 'korean-pronunciation:ko';
    else if (['ru', 'pl', 'el'].includes(languageCode)) key = `phoneme:${languageCode}`;
  } else if (deckType === 'Gramática' && languageCode === 'ko') {
    key = 'korean-grammar:ko';
  } else if (deckType === 'Latim clássico' && languageCode === 'la') {
    key = 'latin-mvp:la';
  }

  if (!key || !Object.hasOwn(manifest.catalog, key)) return undefined;
  const templateId = manifest.catalog[key];
  return Object.hasOwn(manifest.templates, templateId) ? manifest.templates[templateId] : undefined;
}

export function buildPreviewFields(fields: string[], card?: PreviewCard): Record<string, string> {
  const values: Record<string, string> = {};
  for (const field of fields) {
    if (['Image', 'Picture'].includes(field) && card?.image) {
      values[field] = card.image;
    } else if (OPTIONAL_FIELDS.has(field)) {
      values[field] = '';
    } else if (AUDIO_FIELDS.has(field)) {
      values[field] = '[sound:preview-audio.mp3]';
    } else if (card && ['word', 'Word', 'Target Word', 'Example Word'].includes(field)) {
      values[field] = card.word;
    } else if (card && ['Definitions', 'Definition'].includes(field)) {
      values[field] = card.definition;
    } else if (card && field === 'Example Sentence') {
      values[field] = card.sentence;
    } else if (card && ['Translation', 'Sentence Translation'].includes(field)) {
      values[field] = card.translation;
    } else {
      values[field] = SAMPLE_VALUES[field] ?? `Exemplo de ${field}`;
    }
  }
  return values;
}

export function renderAnkiPreviewDocument(
  template: AnkiTemplateDefinition,
  fields: Record<string, string>,
  side: 'front' | 'back',
): string {
  const front = renderTemplate(template.front, fields);
  const body = side === 'front'
    ? front
    : renderTemplate(template.back, { ...fields, FrontSide: front });
  const previewCss = side === 'back'
    ? '\n.preview-back #translation { display: block !important; }\n'
    : '';
  const safeCss = template.css.replace(/<\/style/gi, '<\\/style');
  return '<!doctype html><html lang="pt"><head><meta charset="utf-8">' +
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; font-src data:">' +
    `<style>${safeCss}${previewCss}</style></head>` +
    `<body class="card"><div id="qa" class="preview-${side}">${body}</div></body></html>`;
}

function renderTemplate(source: string, fields: Record<string, string>): string {
  return renderNodes(parseTemplate(source), fields);
}

function parseTemplate(source: string): TemplateNode[] {
  const root: TemplateNode[] = [];
  const stack: Array<{ name: string; node: Extract<TemplateNode, { kind: 'section' }>; parent: TemplateNode[] }> = [];
  let current = root;
  let cursor = 0;
  const tokenPattern = /{{\s*([#/^]?)\s*([^{}]+?)\s*}}/g;

  for (const match of source.matchAll(tokenPattern)) {
    const index = match.index ?? 0;
    if (index > cursor) current.push({ kind: 'text', value: source.slice(cursor, index) });
    const prefix = match[1];
    const name = normalizeFieldName(match[2]);
    if (prefix === '#' || prefix === '^') {
      const node: Extract<TemplateNode, { kind: 'section' }> = {
        kind: 'section',
        name,
        inverted: prefix === '^',
        children: [],
      };
      current.push(node);
      stack.push({ name, node, parent: current });
      current = node.children;
    } else if (prefix === '/') {
      const section = stack.pop();
      if (!section || section.name !== name) throw new Error(`Unbalanced Anki template section: ${name}`);
      current = section.parent;
    } else {
      current.push({ kind: 'field', name });
    }
    cursor = index + match[0].length;
  }
  if (cursor < source.length) current.push({ kind: 'text', value: source.slice(cursor) });
  if (stack.length) throw new Error(`Unclosed Anki template section: ${stack[stack.length - 1].name}`);
  return root;
}

function renderNodes(nodes: TemplateNode[], fields: Record<string, string>): string {
  return nodes.map(node => {
    if (node.kind === 'text') return node.value;
    const value = Object.hasOwn(fields, node.name) ? fields[node.name] : '';
    if (node.kind === 'section') {
      const populated = value.trim().length > 0;
      return populated !== node.inverted ? renderNodes(node.children, fields) : '';
    }
    if (node.name === 'FrontSide') return value;
    if (['Image', 'Picture'].includes(node.name) && /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(value)) return `<img src="${value}" alt="Imagem do cartão" style="max-width:100%;max-height:320px;object-fit:contain">`;
    if (/^\[sound:[A-Za-z0-9._-]+\]$/.test(value)) return AUDIO_BUTTON;
    return escapeHtml(value);
  }).join('');
}

function normalizeFieldName(reference: string): string {
  const separator = reference.lastIndexOf(':');
  return (separator < 0 ? reference : reference.slice(separator + 1)).trim();
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character] ?? character);
}
