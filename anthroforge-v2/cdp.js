// Minimal CDP driver: launch headless Chrome, load a page, evaluate JS, print result.
// Usage: node cdp.js <url> <exprFile> [waitMs]
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');

const url = process.argv[2];
const exprFile = process.argv[3];
const waitMs = parseInt(process.argv[4] || '3000', 10);
const expr = fs.readFileSync(exprFile, 'utf8');
const PORT = 9333;

function getJson(path) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: PORT, path }, r => {
      let d = ''; r.on('data', c => d += c); r.on('end', () => res(JSON.parse(d)));
    }).on('error', rej);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const chrome = spawn(process.env.HOME + '/workspace/tools/chrome/chrome-linux64/chrome', [
    '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage',
    '--ignore-certificate-errors',
    ...(process.env.https_proxy ? ['--proxy-server=' + process.env.https_proxy] : []),
    `--remote-debugging-port=${PORT}`, '--remote-allow-origins=*', 'about:blank'
  ], { stdio: 'ignore' });
  try {
    let targets = null;
    for (let i = 0; i < 50; i++) { try { targets = await getJson('/json'); break; } catch { await sleep(200); } }
    if (!targets) throw new Error('chrome debug endpoint never came up');
    const page = targets.find(t => t.type === 'page');
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);
    let id = 0; const pending = new Map();
    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
      if (msg.method === 'Runtime.consoleAPICalled') {
        const txt = msg.params.args.map(a => a.value ?? a.description ?? '').join(' ');
        console.log('[console]', txt);
      }
      if (msg.method === 'Runtime.exceptionThrown') {
        console.log('[exception]', JSON.stringify(msg.params.exceptionDetails).slice(0, 2000));
      }
    };
    const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    await send('Runtime.enable');
    await send('Page.enable');
    await send('Page.navigate', { url });
    await sleep(waitMs);
    const result = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    console.log(JSON.stringify(result.result && result.result.result, null, 1).slice(0, 12000));
    ws.close();
  } finally { chrome.kill('SIGKILL'); }
})().catch(e => { console.error('DRIVER ERROR', e); process.exit(1); });
