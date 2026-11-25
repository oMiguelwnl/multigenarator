import assert from 'node:assert/strict';
import test from 'node:test';
import { repairProduction, startProduction } from './production-api.ts';
import { productionResult } from './result-api.ts';

Object.defineProperty(globalThis, 'location', { value: new URL('http://127.0.0.1/') });
function recordRequests(t) {
  const received: Request[] = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    received.push(new Request(new URL(url, location.href), init));
    return Response.json({});
  });
  return received;
}

test('production submits only the options and source allowed by the material', async t => {
  const calls = recordRequests(t);
  const attachment = { file: new File(['uno\ndos'], 'palabras.TXT'), previewTruncated: false };
  const draft = { id: 'a', name: '  Curso ', language: 'Espanhol', supportLanguage: 'en', level: 2, attachment } as const;
  await startProduction({ ...draft, kind: 'Frequência' }, draft.id);
  await startProduction({ ...draft, kind: 'Lista personalizada' }, draft.id);
  await startProduction({ ...draft, kind: 'Destaques de leitura', highlightInput: 'vocabulary' }, draft.id);
  const common = { id: 'a', name: 'Curso', language: 'es', supportLanguage: 'en' };
  const source = { sourceText: 'uno\ndos', sourceExtension: 'txt' };
  assert.deepEqual(await Promise.all(calls.map(request => request.json())), [
    { ...common, kind: 'frequency', level: 2 }, { ...common, ...source, kind: 'word-list' },
    { ...common, ...source, kind: 'highlights', highlightInput: 'vocabulary' },
  ]);
});

test('repair sends its own retry identity to the production', async t => {
  const calls = recordRequests(t);
  await repairProduction('job', 'attempt');
  assert.equal(new URL(calls[0].url).pathname, '/studio-api/productions/job/repair');
  assert.equal(calls[0].method, 'POST');
  assert.deepEqual(await calls[0].json(), { id: 'attempt' });
});

test('review requests retain search terms, note revisions and raw PNG bytes', async t => {
  const calls = recordRequests(t);
  const api = productionResult('job');
  const note = { id: '9007199254740993', revision: 'rev', title: 'hola', model: 'words', fields: [] };
  await api.page('café & chá', 25, new AbortController().signal);
  await api.edit(note, { Definition: 'bebida' });
  await api.upload(note, 'Picture', new File([Uint8Array.of(137, 80)], 'pic.png'));
  await api.edit(note, { Picture: '' });
  assert.deepEqual(Object.fromEntries(new URL(calls[0].url).searchParams), { q: 'café & chá', offset: '25', limit: '25' });
  assert.equal(calls[1].method, 'PATCH');
  assert.deepEqual(await calls[1].json(), { revision: 'rev', fields: { Definition: 'bebida' } });
  assert.equal(new URL(calls[1].url).pathname, '/studio-api/productions/job/result/9007199254740993');
  assert.equal(calls[2].method, 'PUT');
  assert.equal(calls[2].headers.get('Content-Type'), 'image/png');
  assert.deepEqual(new Uint8Array(await calls[2].arrayBuffer()), Uint8Array.of(137, 80));
  assert.equal(new URL(calls[2].url).searchParams.get('revision'), 'rev');
  assert.equal(new URL(calls[2].url).searchParams.get('field'), 'Picture');
  assert.deepEqual(await calls[3].json(), { revision: 'rev', fields: { Picture: '' } });
});

test('approval submits the collection revision displayed by the Studio', async t => {
  const calls = recordRequests(t);
  await productionResult('job').approve('viewed-version');
  assert.equal(new URL(calls[0].url).pathname, '/studio-api/productions/job/approvals');
  assert.equal(calls[0].method, 'POST');
  assert.deepEqual(await calls[0].json(), { revision: 'viewed-version' });
});

test('tabular download URLs identify the production, approval and format', () => {
  const api = productionResult('job');
  for (const format of ['csv', 'tsv'] as const) {
    assert.equal(api.approvedExportUrl('a'.repeat(64), format),
      '/studio-api/productions/job/approvals/' + 'a'.repeat(64) + '/export/' + format);
  }
});
