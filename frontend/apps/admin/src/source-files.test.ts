import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as sources from './source-files.ts';

test('source formats distinguish word lists from Kindle exports', () => {
  assert.equal(typeof sources.sourceKindFor, 'function');
  assert.equal(sources.sourceKindFor('Lista personalizada'), 'word-list');
  assert.equal(sources.sourceKindFor('Destaques de leitura'), 'highlights');
  assert.equal(sources.sourceKindFor('Frequência'), undefined);
  assert.equal(sources.acceptedSourceFiles('word-list'), '.txt');
  assert.equal(sources.acceptedSourceFiles('highlights'), '.txt,.html,.htm');
});

test('a UTF-8 text file keeps its original bytes and offers a bounded literal preview', async () => {
  assert.equal(typeof sources.readSourceFile, 'function');
  const contents = '\uFEFFcafé\r\n안녕하세요\r\nreunir pessoas\r\n<script>literal text</script>\n' + 'x'.repeat(3000);
  const file = new File([contents], 'palavras.TXT', { type: 'text/plain' });
  const result = await sources.readSourceFile(file, 'word-list');
  assert.equal(result.file, file);
  assert.deepEqual(new Uint8Array(await result.file.arrayBuffer()), new TextEncoder().encode(contents));
  assert.ok(result.preview.startsWith('café\r\n안녕하세요'));
  assert.ok(result.preview.includes('<script>literal text</script>'));
  assert.ok(result.preview.length <= sources.MAX_PREVIEW_CHARACTERS);
  assert.equal(result.previewTruncated, true);
});

test('HTML exports are kept as attachments without a rendered preview', async () => {
  assert.equal(typeof sources.readSourceFile, 'function');
  const file = new File(['<div class="noteText"><img src="https://example.invalid/private">hello</div>'], 'Kindle.HTM');
  const result = await sources.readSourceFile(file, 'highlights');
  assert.equal(result.file, file);
  assert.equal(result.preview, undefined);
  await assert.rejects(sources.readSourceFile(file, 'word-list'), /\.txt/);
});

test('unsupported, oversized and empty files fail before their content is read', async () => {
  assert.equal(typeof sources.readSourceFile, 'function');
  let reads = 0;
  const unreadable = { name: 'list.txt', size: sources.MAX_SOURCE_BYTES + 1, arrayBuffer: async () => { reads++; throw new Error('must not read'); } } as File;
  await assert.rejects(sources.readSourceFile(unreadable, 'word-list'), /5 MB/);
  await assert.rejects(sources.readSourceFile({ ...unreadable, name: 'list.pdf', size: 100 } as File, 'word-list'), /\.txt/);
  await assert.rejects(sources.readSourceFile({ ...unreadable, size: 0 } as File, 'word-list'), /vazio/);
  assert.equal(reads, 0);
});

test('invalid UTF-8, binary content and whitespace-only files receive actionable errors', async () => {
  assert.equal(typeof sources.readSourceFile, 'function');
  await assert.rejects(sources.readSourceFile(new File([new Uint8Array([0xff, 0xfe, 0xff])], 'list.txt'), 'word-list'), /UTF-8/);
  await assert.rejects(sources.readSourceFile(new File(['word\u0000other'], 'list.txt'), 'word-list'), /texto/);
  await assert.rejects(sources.readSourceFile(new File(['\uFEFF \n\t'], 'list.txt'), 'word-list'), /vazio/);
});

test('read failures do not expose file contents or system details', async () => {
  assert.equal(typeof sources.readSourceFile, 'function');
  const file = { name: 'list.txt', size: 100, arrayBuffer: async () => { throw new Error('private system details'); } } as File;
  await assert.rejects(sources.readSourceFile(file, 'word-list'), error => {
    assert.ok(error instanceof Error);
    assert.match(error.message, /selecione.*novamente/i);
    assert.ok(!error.message.includes('private system details'));
    return true;
  });
});
