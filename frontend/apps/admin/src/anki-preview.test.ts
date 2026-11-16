import { test } from 'node:test';
import assert from 'node:assert/strict';

const preview = await import('./anki-preview.ts').catch(() => undefined);
const fixtureTemplate = {
  fields: ['word', 'Definition', 'Translation', 'word_audio'],
  front: '<div>{{word}}</div>{{#Definition}}<p>{{Definition}}</p>{{/Definition}}<span>{{word_audio}}</span>',
  back: '{{FrontSide}}<hr>{{#Translation}}<div id="translation">{{Translation}}</div>{{/Translation}}',
  css: 'body { color: #222; }',
};
const fixtureManifest = {
  version: 1,
  catalog: {
    'frequency:en': 'frequency',
    'korean-grammar:ko': 'grammar',
    'japanese-kana:ja': 'kana',
    'korean-hangul:ko': 'hangul',
    'korean-pronunciation:ko': 'korean-pronunciation',
    'phoneme:ru': 'phoneme',
    'latin-mvp:la': 'latin',
    'word-list:en': 'word-list',
    'kindle-highlights:en': 'highlights',
  },
  templates: {
    frequency: fixtureTemplate,
    grammar: fixtureTemplate,
    kana: fixtureTemplate,
    hangul: fixtureTemplate,
    'korean-pronunciation': fixtureTemplate,
    phoneme: fixtureTemplate,
    latin: fixtureTemplate,
    'word-list': fixtureTemplate,
    highlights: fixtureTemplate,
  },
};

test('selects the exporter template for each supported deck type', () => {
  assert.ok(preview, 'the Anki preview renderer has not been implemented');
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Frequência', 'Inglês'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Lista personalizada', 'Inglês'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Destaques de leitura', 'Inglês'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Gramática', 'Coreano'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Escrita e fundamentos', 'Coreano'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Escrita e fundamentos', 'Japonês'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Pronúncia e fonética', 'Coreano'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Pronúncia e fonética', 'Russo'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Latim clássico', 'Latim'), fixtureTemplate);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Gramática', 'Inglês'), undefined);
});

test('builds safe example fields from the selected exported field schema', () => {
  assert.ok(preview, 'the Anki preview renderer has not been implemented');
  const fields = preview.buildPreviewFields(
    ['word', 'Definitions', 'Example Sentence', 'Translation', 'Image', 'word_audio'],
    { word: 'notice', definition: 'Perceber.', sentence: 'I notice the sign.', translation: 'Eu noto a placa.' },
  );
  assert.deepEqual(fields, {
    word: 'notice',
    Definitions: 'Perceber.',
    'Example Sentence': 'I notice the sign.',
    Translation: 'Eu noto a placa.',
    Image: '',
    word_audio: '[sound:preview-audio.mp3]',
  });
});

test('renders front and back with Anki fields, sections, audio placeholders, and safe values', () => {
  assert.ok(preview, 'the Anki preview renderer has not been implemented');
  const fields = {
    word: '<img src=x onerror=alert(1)>',
    Definition: 'A definition',
    Translation: 'Uma tradução',
    word_audio: '[sound:preview-word.mp3]',
  };
  const front = preview.renderAnkiPreviewDocument(fixtureTemplate, fields, 'front');
  const back = preview.renderAnkiPreviewDocument(fixtureTemplate, fields, 'back');

  assert.match(front, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(front, /<img src=x/);
  assert.match(front, /A definition/);
  assert.match(front, /replay-button/);
  assert.match(back, /A definition/);
  assert.match(back, /Uma tradução/);
  assert.match(back, /preview-back #translation/);
  assert.match(back, /Content-Security-Policy/);
});

test('omits empty optional fields and does not expand unavailable deck templates', () => {
  assert.ok(preview, 'the Anki preview renderer has not been implemented');
  const front = preview.renderAnkiPreviewDocument(
    fixtureTemplate,
    { word: 'gather', Definition: '', Translation: '', word_audio: '' },
    'front',
  );
  assert.doesNotMatch(front, /<p><\/p>/);
  assert.equal(preview.getAnkiTemplate(fixtureManifest, 'Pronúncia e fonética', 'Espanhol'), undefined);
});
