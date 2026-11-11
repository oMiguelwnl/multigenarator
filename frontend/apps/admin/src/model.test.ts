import { test } from 'node:test';
import assert from 'node:assert/strict';
import { editCard, selectCards, canExport } from './model.ts';
import * as model from './model.ts';
import * as demo from './demo.ts';

const card = { id: '1', word: 'gather', definition: 'Reunir.', sentence: 'We gather here.', translation: 'Nós nos reunimos aqui.', status: 'ready' as const, audio: 'available' as const };

test('changing the sentence invalidates the audio and review without mutating history', () => {
  const edited = editCard(card, { sentence: 'We gather every week.' });
  assert.equal(edited.audio, 'outdated');
  assert.equal(edited.status, 'review');
  assert.equal(card.sentence, 'We gather here.');
  assert.equal(card.audio, 'available');
});

test('saving unchanged fields preserves review and audio', () => {
  assert.deepEqual(editCard(card, { sentence: card.sentence }), card);
});

test('translation changes require review but do not invalidate target-language audio', () => {
  const edited = editCard(card, { translation: 'Reunimo-nos aqui.' });
  assert.equal(edited.status, 'review');
  assert.equal(edited.audio, 'available');
});

test('search and pending filter compose', () => {
  const pending = { ...card, id: '2', word: 'enough', status: 'review' as const };
  assert.deepEqual(selectCards([card, pending], 'ENO', 'pending'), [pending]);
  assert.deepEqual(selectCards([card], 'gather', 'pending'), []);
});

test('export is unavailable for demonstration data even when all cards are ready', () => {
  assert.equal(canExport([card], true), false);
  assert.equal(canExport([], false), false);
  assert.equal(canExport([{ ...card, audio: 'outdated' }], false), false);
});

test('saving an edited draft updates its identity without duplicating the production', () => {
  assert.equal(typeof model.saveProductionDraft, 'function');
  const original = { id: 'first', name: ' Inglês ', language: 'Inglês', supportLanguage: 'pt' as const, kind: 'Frequência' };
  const other = { ...original, id: 'second', name: 'Outra produção' };
  const saved = model.saveProductionDraft([], original);
  assert.equal(saved[0].name, 'Inglês');
  const existing = [...saved, other];
  const updated = model.saveProductionDraft(existing, { ...original, name: 'Inglês revisado' });
  assert.deepEqual(updated, [{ ...original, name: 'Inglês revisado' }, other]);
  assert.equal(existing[0].name, 'Inglês');
  assert.equal(original.name, ' Inglês ');
});

test('separate draft identities can share a name and blank names cannot be saved', () => {
  assert.equal(typeof model.saveProductionDraft, 'function');
  const draft = { id: 'first', name: 'Vocabulário', language: 'Inglês', supportLanguage: 'pt' as const, kind: 'Frequência' };
  const saved = model.saveProductionDraft([draft], { ...draft, id: 'second' });
  assert.equal(saved.length, 2);
  assert.throws(() => model.saveProductionDraft(saved, { ...draft, name: '  ' }));
  assert.equal(saved.length, 2);
});

test('support language choices match the architecture contract and Korean restriction', () => {
  assert.equal(typeof model.availableSupportLanguages, 'function');
  assert.deepEqual(model.availableSupportLanguages('Alemão'), ['pt', 'en', 'es']);
  assert.deepEqual(model.availableSupportLanguages('Coreano'), ['pt']);
});

test('changing the study language preserves a valid support language or selects Portuguese for Korean', () => {
  assert.equal(typeof model.changeStudyLanguage, 'function');
  const draft = { id: 'first', name: 'Vocabulário', language: 'Alemão', supportLanguage: 'es' as const, kind: 'Frequência' };
  const french = model.changeStudyLanguage(draft, 'Francês');
  assert.equal(french.supportLanguage, 'es');
  const korean = model.changeStudyLanguage(draft, 'Coreano');
  assert.deepEqual(korean, { ...draft, language: 'Coreano', supportLanguage: 'pt' });
  assert.equal(draft.supportLanguage, 'es');
  assert.equal(model.changeStudyLanguage(korean, 'Inglês').supportLanguage, 'pt');
});

test('saving rejects support languages outside the deck contract', () => {
  const draft = { id: 'first', name: 'Vocabulário', language: 'Coreano', kind: 'Frequência' };
  for (const supportLanguage of ['en', 'es', 'fr', undefined]) {
    assert.throws(() => model.saveProductionDraft([], { ...draft, supportLanguage }), /support language/i);
  }
  assert.throws(() => model.saveProductionDraft([], { ...draft, language: 'Alemão', supportLanguage: 'fr' }), /support language/i);
});

test('editing support language updates only its draft and preserves other productions', () => {
  const first = { id: 'first', name: 'Vocabulário', language: 'Alemão', supportLanguage: 'pt' as const, kind: 'Frequência' };
  const second = { ...first, id: 'second', supportLanguage: 'en' as const };
  const saved = model.saveProductionDraft([first, second], { ...first, supportLanguage: 'es' });
  assert.equal(saved.length, 2);
  assert.equal(saved[0].supportLanguage, 'es');
  assert.equal(saved[1].supportLanguage, 'en');
  assert.equal(first.supportLanguage, 'pt');
});

test('simulation only accepts the language pair and material present in the fixture', () => {
  assert.equal(typeof demo.canSimulateDraft, 'function');
  const draft = { id: 'first', name: 'Meu rascunho', language: 'Inglês', supportLanguage: 'pt' as const, kind: 'Frequência' };
  assert.equal(demo.canSimulateDraft(draft), true);
  for (const supportLanguage of ['en', 'es'] as const) {
    assert.equal(demo.canSimulateDraft({ ...draft, supportLanguage }), false);
  }
  assert.equal(demo.canSimulateDraft({ ...draft, language: 'Coreano' }), false);
  assert.equal(demo.canSimulateDraft({ ...draft, kind: 'Lista personalizada' }), false);
});
