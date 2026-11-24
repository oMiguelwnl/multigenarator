import { studioApi as api } from './studio-api';
import { useEffect, useRef, useState } from 'react';
import { SecretField } from './SecretField';
import { SelectMenu } from './SelectMenu';

type KeyName = 'openai_api_key' | 'openrouter_api_key' | 'deepl_api_key' | 'azure_speech_key' | 'database_url';
type Configuration = {
  transport: 'api' | 'openrouter' | 'codex'; model: string; azure_region: string; api_max_output_tokens: number;
  configured: Record<KeyName, boolean>;
};
const defaults: Configuration = { transport: 'api', model: 'gpt-6-luna', azure_region: 'brazilsouth', api_max_output_tokens: 2048, configured: { openai_api_key: false, openrouter_api_key: false, deepl_api_key: false, azure_speech_key: false, database_url: false } };
const emptyKeys: Record<KeyName, string> = { openai_api_key: '', openrouter_api_key: '', deepl_api_key: '', azure_speech_key: '', database_url: '' };
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
  const saveInFlight = useRef<Promise<void> | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
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

  async function saveConfiguration() {
    if (saveInFlight.current) {
      await saveInFlight.current;
      return saveConfiguration();
    }
    if (!dirty) return;
    const { configured: _, ...preferences } = config;
    const pending = (async () => {
      const result = await api('connections', 'PUT', { ...preferences, ...keys });
      setConfig(result); setKeys(emptyKeys); setDirty(false);
      setMessage('Configurações salvas no cofre do Windows. A próxima produção usará estas configurações.');
    })();
    saveInFlight.current = pending;
    try { await pending; }
    finally { if (saveInFlight.current === pending) saveInFlight.current = null; }
  }

  function saveKeyOnBlur() {
    if (!dirty || !Object.values(keys).some(key => key.trim())) return;
    void saveConfiguration().catch(error => setMessage(error instanceof Error ? error.message : 'Não foi possível salvar a chave.'));
  }

  function update(patch: Partial<Configuration>) { setConfig(previous => ({ ...previous, ...patch })); setDirty(true); setModels([]); }
  function updateTransport(value: string) {
    if (value === 'api' || value === 'openrouter' || value === 'codex') update({ transport: value });
  }
  const apiProvider = config.transport === 'openrouter' ? 'openrouter' : 'openai';
  const apiKeyName: KeyName = config.transport === 'openrouter' ? 'openrouter_api_key' : 'openai_api_key';
  const locked = busy || !ready;

  return <>
    <div className="page-heading"><div><h1>Provedores e conexões</h1><p className="muted">Configure os serviços que suas produções usam para gerar texto, tradução e áudio.</p></div><span className="badge draft">Uso pessoal · local</span></div>
    <div className="connection-status" role="status">{message}</div>
    {!ready && !busy && <div className="panel connection-section"><h2>Abra o estúdio local</h2><p>A prévia HTML mostra esta tela, mas não recebe chaves. Use o arquivo <strong>Abrir Estúdio.cmd</strong> da pasta frontend para abrir a versão conectada.</p><p className="field-note">O acesso fica restrito a este computador. Nunca cole suas chaves no chat.</p></div>}
    <form className="connections-form" onSubmit={event => { event.preventDefault(); void action(saveConfiguration); }}>
      <fieldset disabled={locked} className="connection-section panel">
        <legend>Geração dos cartões</legend>
        <label>Conexão<SelectMenu value={config.transport} onChange={updateTransport} options={[{ value: 'api', label: 'OpenAI · chave de API' }, { value: 'openrouter', label: 'OpenRouter · chave de API' }, { value: 'codex', label: 'ChatGPT · login pelo Codex local' }]}/></label>
        {config.transport !== 'codex' ? <>
          <SecretField name={apiKeyName} label={`Chave ${apiProvider === 'openrouter' ? 'do OpenRouter' : 'da OpenAI'}`} configured={config.configured[apiKeyName]} pending={keys[apiKeyName]} placeholder="Cole sua chave de API" onChange={value => { setKeys(previous => ({ ...previous, [apiKeyName]: value })); setDirty(true); }} onBlur={saveKeyOnBlur}/>
          <p className="field-note">{apiProvider === 'openrouter' ? 'A cobrança e os limites seguem sua conta OpenRouter. Consulte os modelos depois de salvar a chave.' : 'A cobrança e os limites seguem sua conta de API.'}</p>
          <KeyActions name={apiKeyName} provider={apiProvider} configured={config.configured[apiKeyName]} hasPendingKey={Boolean(keys[apiKeyName].trim())} dirty={dirty} action={action} saveConfiguration={saveConfiguration} setConfig={setConfig} setMessage={setMessage}/>
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
        <div className="connection-model"><label>Modelo<input value={config.model} maxLength={240} pattern="[-a-zA-Z0-9._:/]+" list="available-models" required onChange={event => { setConfig({ ...config, model: event.target.value }); setDirty(true); }}/><datalist id="available-models">{models.map(model => <option key={model.id} value={model.id}>{model.name}</option>)}</datalist></label><button type="button" className="button secondary" disabled={dirty} onClick={() => void action(async () => { const result = await api('models', 'POST'); setModels(result); setMessage(`${result.length} modelos encontrados. Escolha um modelo de texto disponível e salve.`); })}>Consultar modelos</button></div>
        <p className="field-note">Salve a conexão antes de consultar os modelos. IDs do OpenRouter incluem o provedor, como autor/modelo. A qualidade dos cartões ainda precisa de avaliação por idioma.</p>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Tradução · DeepL</legend>
        <SecretField name="deepl_api_key" label="Chave do DeepL" configured={config.configured.deepl_api_key} pending={keys.deepl_api_key} placeholder="Cole sua chave de API" onChange={value => { setKeys(previous => ({ ...previous, deepl_api_key: value })); setDirty(true); }} onBlur={saveKeyOnBlur}/>
        <KeyActions name="deepl_api_key" provider="deepl" configured={config.configured.deepl_api_key} hasPendingKey={Boolean(keys.deepl_api_key.trim())} dirty={dirty} action={action} saveConfiguration={saveConfiguration} setConfig={setConfig} setMessage={setMessage}/>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Áudio · Azure Speech</legend>
        <SecretField name="azure_speech_key" label="Chave do Azure Speech" configured={config.configured.azure_speech_key} pending={keys.azure_speech_key} placeholder="Cole a chave do recurso Speech" onChange={value => { setKeys(previous => ({ ...previous, azure_speech_key: value })); setDirty(true); }} onBlur={saveKeyOnBlur}/>
        <label>Região do recurso<input value={config.azure_region} required maxLength={40} pattern="[a-z][a-z0-9]+" onChange={event => update({ azure_region: event.target.value })}/></label>
        <p className="field-note">Use a região exibida no seu recurso Azure, por exemplo brazilsouth ou eastus.</p>
        <KeyActions name="azure_speech_key" provider="azure" configured={config.configured.azure_speech_key} hasPendingKey={Boolean(keys.azure_speech_key.trim())} dirty={dirty} action={action} saveConfiguration={saveConfiguration} setConfig={setConfig} setMessage={setMessage}/>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Banco de dados · PostgreSQL</legend>
        <SecretField name="database_url" label="URL de conexão" configured={config.configured.database_url} pending={keys.database_url} placeholder="postgresql+psycopg://usuário:senha@localhost:5432/multilang" onChange={value => { setKeys(previous => ({ ...previous, database_url: value })); setDirty(true); }} onBlur={saveKeyOnBlur}/>
        <p className="field-note">Use a URL do seu PostgreSQL. A senha fica criptografada no cofre local do Windows.</p>
        <KeyActions name="database_url" provider="database" configured={config.configured.database_url} hasPendingKey={Boolean(keys.database_url.trim())} dirty={dirty} action={action} saveConfiguration={saveConfiguration} setConfig={setConfig} setMessage={setMessage}/>
      </fieldset>
      <fieldset disabled={locked} className="connection-section panel"><legend>Controle de uso</legend>{config.transport !== 'codex' ? <label>Limite de tokens de saída por chamada de API<input type="number" min={256} max={8192} required value={config.api_max_output_tokens} onChange={event => { setConfig({ ...config, api_max_output_tokens: Number(event.target.value) }); setDirty(true); }}/></label> : <p>As chamadas pelo Codex têm tempo máximo de 120 segundos. Os limites de uso seguem sua conta ChatGPT.</p>}<p className="field-note">Não é um limite financeiro: uma palavra pode exigir várias chamadas. Estimativa de custo ainda indisponível; acompanhe o consumo no provedor.</p></fieldset>
      <div className="connection-save"><p className="field-note">Chaves criptografadas para seu usuário do Windows. Campos vazios preservam as chaves salvas. A verificação consulta apenas metadados, sem gerar cartões ou áudio.</p><button className="button primary" disabled={locked || !dirty}>{busy ? 'Aguarde…' : 'Salvar configurações'}</button></div>
    </form>
  </>;
}

function KeyActions({ name, provider, configured, hasPendingKey, dirty, action, saveConfiguration, setConfig, setMessage }: { name: KeyName; provider: string; configured: boolean; hasPendingKey: boolean; dirty: boolean; action: (operation: () => Promise<void>) => Promise<void>; saveConfiguration: () => Promise<void>; setConfig: (config: Configuration) => void; setMessage: (message: string) => void }) {
  return <div className="connection-actions"><button type="button" className="button secondary" disabled={!configured && !hasPendingKey} onClick={() => void action(async () => { await saveConfiguration(); const result = await api(`check/${provider}`, 'POST'); setMessage(result.message); })}>Verificar conexão</button><button type="button" className="text-button" disabled={!configured || dirty} onClick={() => void action(async () => { setConfig(await api(`keys/${name}`, 'DELETE')); setMessage('Credencial removida do cofre local.'); })}>Remover credencial</button></div>;
}
