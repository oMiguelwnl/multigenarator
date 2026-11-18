import { useEffect, useState } from 'react';

type KeyName = 'openai_api_key' | 'deepl_api_key' | 'azure_speech_key';
type Configuration = {
  transport: 'api' | 'codex'; model: string; azure_region: string; api_max_output_tokens: number;
  configured: Record<KeyName, boolean>;
};
const defaults: Configuration = { transport: 'api', model: 'gpt-6-luna', azure_region: 'brazilsouth', api_max_output_tokens: 2048, configured: { openai_api_key: false, deepl_api_key: false, azure_speech_key: false } };
const emptyKeys = { openai_api_key: '', deepl_api_key: '', azure_speech_key: '' };
let sessionBootstrap: Promise<unknown> | undefined;

async function api(path: string, method = 'GET', payload?: unknown) {
  if (!['http:', 'https:'].includes(location.protocol)) throw new Error('Esta prévia não armazena credenciais. Abra o estúdio pelo iniciador local.');
  const response = await fetch(`/studio-api/${path}`, { method, credentials: 'same-origin', cache: 'no-store', signal: AbortSignal.timeout(45000), headers: payload === undefined ? {} : { 'Content-Type': 'application/json' }, body: payload === undefined ? undefined : JSON.stringify(payload) });
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('O serviço local não está disponível. Abra o estúdio pelo iniciador local.');
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Não foi possível concluir a operação.');
  return result;
}

export function Connections() {
  const [config, setConfig] = useState<Configuration>(defaults);
  const [keys, setKeys] = useState(emptyKeys);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState('Conectando ao serviço local…');
  const [models, setModels] = useState<{ id: string; name: string }[]>([]);
  const [loginUrl, setLoginUrl] = useState('');
  const [connected, setConnected] = useState<boolean | null>(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const token = new URLSearchParams(location.hash.split('?')[1] || '').get('session');
        if (token) {
          history.replaceState(null, '', '#conexoes');
          sessionBootstrap = api('session', 'POST', { token });
        }
        await sessionBootstrap;
        const result = await api('connections');
        if (active) { setConfig(result); setReady(true); setMessage('Configurações carregadas. Nenhuma chamada de geração foi executada.'); }
      } catch (error) { if (active) setMessage(error instanceof Error ? error.message : 'Serviço local indisponível.'); }
      finally { if (active) setBusy(false); }
    }
    void load();
    return () => { active = false; };
  }, []);

  async function action(operation: () => Promise<void>) {
    setBusy(true); setMessage('Aguarde…');
    try { await operation(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Não foi possível concluir.'); }
    finally { setBusy(false); }
  }

  function update(patch: Partial<Configuration>) { setConfig(previous => ({ ...previous, ...patch })); setDirty(true); setModels([]); }
  const locked = busy || !ready;

  return <>
    <div className="page-heading"><div><h1>Provedores e conexões</h1><p className="muted">Configure integrações para uso futuro. Esta tela não gera cartões nem áudio.</p></div><span className="badge draft">Uso pessoal · local</span></div>
    <div className="connection-status" role="status">{message}</div>
    {!ready && !busy && <div className="panel connection-section"><h2>Abra o estúdio local</h2><p>A prévia HTML mostra esta tela, mas não recebe chaves. Use o arquivo <strong>Abrir Estúdio.cmd</strong> da pasta frontend para abrir a versão conectada.</p><p className="field-note">O acesso fica restrito a este computador. Nunca cole suas chaves no chat.</p></div>}
    <form className="connections-form" onSubmit={event => { event.preventDefault(); void action(async () => {
      const { configured: _, ...preferences } = config;
      const result = await api('connections', 'PUT', { ...preferences, ...keys });
      setConfig(result); setKeys(emptyKeys); setDirty(false);
      setMessage('Configurações salvas no cofre do Windows. A próxima tarefa usará estes valores quando a integração estiver habilitada.');
    }); }}>
      <fieldset disabled={locked} className="connection-section panel">
        <legend>Geração dos cartões</legend>
        <label>Conexão<select value={config.transport} onChange={event => update({ transport: event.target.value as Configuration['transport'] })}><option value="api">OpenAI · chave de API</option><option value="codex">ChatGPT · login pelo Codex local</option></select></label>
        {config.transport === 'api' ? <>
          <label>Chave da OpenAI<input type="password" autoComplete="off" maxLength={4096} value={keys.openai_api_key} placeholder={config.configured.openai_api_key ? 'Chave salva · preencha para substituir' : 'Cole sua chave de API'} onChange={event => { setKeys({ ...keys, openai_api_key: event.target.value }); setDirty(true); }}/></label>
          <p className="field-note">A cobrança e os limites seguem sua conta de API.</p>
          <KeyActions name="openai_api_key" provider="openai" configured={config.configured.openai_api_key} dirty={dirty} action={action} setConfig={setConfig} setMessage={setMessage}/>
        </> : <>
          <p>Entre na página oficial da OpenAI. Sua senha e os tokens de login não passam pelo formulário do Multilang.</p>
          <p className="field-note">Integração para uso pessoal local. Para venda ou hospedagem, use API ou a integração comercial oficial. O login fica separado da sua sessão principal do Codex.</p>
          <div className="connection-actions">
            <button type="button" className="button secondary" onClick={() => void action(async () => { const result = await api('codex/login', 'POST'); setLoginUrl(result.url); setMessage('Abra a página oficial abaixo e conclua o login. Depois clique em Verificar login.'); })}>Entrar com ChatGPT</button>
            <button type="button" className="button secondary" onClick={() => void action(async () => { const result = await api('codex/status', 'POST'); setConnected(result.connected); if (result.connected) setLoginUrl(''); setMessage(result.connected ? 'ChatGPT conectado. Consulte os modelos disponíveis.' : 'Login ainda não concluído.'); })}>Verificar login</button>
            <button type="button" className="text-button" onClick={() => void action(async () => { await api('codex/logout', 'POST'); setConnected(false); setLoginUrl(''); setModels([]); setMessage('ChatGPT desconectado do Multilang.'); })}>Desconectar</button>
          </div>
          {loginUrl && <a className="button primary login-link" href={loginUrl} target="_blank" rel="noopener noreferrer">Abrir login oficial da OpenAI</a>}
          <p className="field-note">{connected === null ? 'Login ainda não verificado.' : connected ? 'Conta conectada.' : 'Conta desconectada.'}</p>
        </>}
        <div className="connection-model"><label>Modelo<input value={config.model} maxLength={120} pattern="[a-zA-Z0-9._:\-]+" list="available-models" required onChange={event => { setConfig({ ...config, model: event.target.value }); setDirty(true); }}/><datalist id="available-models">{models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)}</datalist></label><button type="button" className="button secondary" disabled={dirty} onClick={() => void action(async () => { const result = await api('models', 'POST'); setModels(result); setMessage(`${result.length} modelos encontrados. Escolha um modelo de texto disponível e salve.`); })}>Consultar modelos</button></div>
        <p className="field-note">Salve a conexão antes de consultar. Luna só poderá ser usado se estiver disponível na sua conta. A qualidade dos cartões ainda precisa de avaliação por idioma.</p>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Tradução · DeepL</legend>
        <label>Chave do DeepL<input type="password" autoComplete="off" maxLength={4096} value={keys.deepl_api_key} placeholder={config.configured.deepl_api_key ? 'Chave salva · preencha para substituir' : 'Cole sua chave de API'} onChange={event => { setKeys({ ...keys, deepl_api_key: event.target.value }); setDirty(true); }}/></label>
        <KeyActions name="deepl_api_key" provider="deepl" configured={config.configured.deepl_api_key} dirty={dirty} action={action} setConfig={setConfig} setMessage={setMessage}/>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Áudio · Azure Speech</legend>
        <label>Chave do Azure Speech<input type="password" autoComplete="off" maxLength={4096} value={keys.azure_speech_key} placeholder={config.configured.azure_speech_key ? 'Chave salva · preencha para substituir' : 'Cole a chave do recurso Speech'} onChange={event => { setKeys({ ...keys, azure_speech_key: event.target.value }); setDirty(true); }}/></label>
        <label>Região do recurso<input value={config.azure_region} required maxLength={40} pattern="[a-z][a-z0-9]+" onChange={event => update({ azure_region: event.target.value })}/></label>
        <p className="field-note">Use a região exibida no seu recurso Azure, por exemplo brazilsouth ou eastus.</p>
        <KeyActions name="azure_speech_key" provider="azure" configured={config.configured.azure_speech_key} dirty={dirty} action={action} setConfig={setConfig} setMessage={setMessage}/>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Controle de uso</legend>{config.transport === 'api' ? <label>Limite de tokens de saída por chamada de API<input type="number" min={256} max={8192} required value={config.api_max_output_tokens} onChange={event => { setConfig({ ...config, api_max_output_tokens: Number(event.target.value) }); setDirty(true); }}/></label> : <p>As chamadas pelo Codex têm tempo máximo de 120 segundos. Os limites de uso seguem sua conta ChatGPT.</p>}<p className="field-note">Não é um limite financeiro: uma palavra pode exigir várias chamadas. Estimativa de custo ainda indisponível; acompanhe o consumo no provedor.</p></fieldset>
      <div className="connection-save"><p className="field-note">Chaves criptografadas para seu usuário do Windows. Campos vazios preservam as chaves salvas. A verificação consulta apenas metadados, sem gerar cartões ou áudio.</p><button className="button primary" disabled={locked || !dirty}>{busy ? 'Aguarde…' : 'Salvar configurações'}</button></div>
    </form>
  </>;
}

function KeyActions({ name, provider, configured, dirty, action, setConfig, setMessage }: { name: KeyName; provider: string; configured: boolean; dirty: boolean; action: (operation: () => Promise<void>) => Promise<void>; setConfig: (config: Configuration) => void; setMessage: (message: string) => void }) {
  return <div className="connection-actions"><span className="field-note">{configured ? 'Chave salva · não verificada nesta tela' : 'Nenhuma chave salva'}</span><button type="button" className="button secondary" disabled={!configured || dirty} onClick={() => void action(async () => { const result = await api(`check/${provider}`, 'POST'); setMessage(result.message); })}>Verificar conexão</button><button type="button" className="text-button" disabled={!configured || dirty} onClick={() => void action(async () => { setConfig(await api(`keys/${name}`, 'DELETE')); setMessage('Chave removida do cofre local.'); })}>Remover chave</button></div>;
}
