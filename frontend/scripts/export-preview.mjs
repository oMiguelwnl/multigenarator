// Package the built, self-contained prototype for opening without a server.
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, relative, isAbsolute } from 'node:path';

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const checkout = resolve(frontend, '..');
const output = resolve(checkout, 'output/previews/admin-prototype');
const boundary = relative(checkout, output);
if (boundary.startsWith('..') || isAbsolute(boundary)) throw new Error('Preview must stay inside the checkout.');
const assets = await readdir(resolve(frontend, 'dist/assets'));
const scripts = assets.filter(name => name.endsWith('.js'));
const styles = assets.filter(name => name.endsWith('.css'));
if (scripts.length !== 1 || styles.length !== 1) throw new Error('Expected one JavaScript and one CSS bundle. Build first.');
const [html, js, css] = await Promise.all([
  readFile(resolve(frontend, 'dist/index.html'), 'utf8'),
  readFile(resolve(frontend, 'dist/assets', scripts[0]), 'utf8'),
  readFile(resolve(frontend, 'dist/assets', styles[0]), 'utf8'),
]);
const standalone = html
  .replace(/<script\b[^>]*src="[^"]+"[^>]*><\/script>/, () => `<script type="module">${js.replace(/<\/script/gi, '<\\/script')}</script>`)
  .replace(/<link\b[^>]*rel="stylesheet"[^>]*>/, () => `<style>${css.replace(/<\/style/gi, '<\\/style')}</style>`);
if (standalone === html || standalone.includes('src="/assets/')) throw new Error('Could not embed all preview assets.');
await mkdir(output, { recursive: true });
await writeFile(resolve(output, 'index.html'), standalone, 'utf8');
console.log(resolve(output, 'index.html'));
