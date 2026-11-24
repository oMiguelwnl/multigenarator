let bootstrap: Promise<unknown> | undefined;

async function request(path: string, method: string, body?: unknown, signal?: AbortSignal) {
  if (location.protocol !== 'http:' && location.protocol !== 'https:') {
    throw new Error('Abra o Estúdio pelo iniciador local para conectar ao backend.');
  }
  const response = await fetch('/studio-api/' + path, {
    method, credentials: 'same-origin', cache: 'no-store',
    signal: signal ?? AbortSignal.timeout(45000),
    headers: body === undefined ? {} : { 'Content-Type': body instanceof Blob ? body.type || 'application/octet-stream' : 'application/json' },
    body: body instanceof Blob || body === undefined ? body : JSON.stringify(body),
  });
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('Abra o Estúdio pelo iniciador local para conectar ao backend.');
  }
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'O serviço local recusou a operação.');
  return data;
}

export async function studioApi(path: string, method = 'GET', body?: unknown, signal?: AbortSignal) {
  const [screen, params] = location.hash.split('?');
  const token = new URLSearchParams(params).get('session');
  if (token) {
    history.replaceState(null, '', screen);
    bootstrap = request('session', 'POST', { token });
  }
  await bootstrap;
  return request(path, method, body, signal);
}
