// shots.js — headless screenshot driver for the A10 shell-fur test page.
// Launches the workspace Chrome (SwiftShader WebGL), loads a URL, then for
// each shot spec: evaluates a JS expression (set subject/params/camera),
// waits, and captures a PNG via CDP Page.captureScreenshot.
//
// Usage: node shots.js <url> <shots.json> <outDir>
// shots.json: [{ "name": "head_default", "expr": "AF.setSubject('head')", "waitMs": 800 }]
// The page should set window.__AF_READY === true when its scene is up.
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const url = process.argv[2];
const shots = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const outDir = process.argv[4];
fs.mkdirSync(outDir, { recursive: true });
const PORT = 9410;

function getJson(p) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: PORT, path: p }, r => {
      let d = ''; r.on('data', c => d += c); r.on('end', () => res(JSON.parse(d)));
    }).on('error', rej);
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const chrome = spawn(process.env.HOME + '/workspace/tools/chrome/chrome-linux64/chrome', [
    '--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
    '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=980,1020', '--hide-scrollbars',
    `--remote-debugging-port=${PORT}`, '--remote-allow-origins=*', 'about:blank'
  ], { stdio: 'ignore' });
  try {
    let targets = null;
    for (let i = 0; i < 60; i++) { try { targets = await getJson('/json'); break; } catch { await sleep(200); } }
    if (!targets) throw new Error('chrome debug endpoint never came up');
    const page = targets.find(t => t.type === 'page');
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);
    let id = 0; const pending = new Map();
    ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
      if (msg.method === 'Runtime.consoleAPICalled') {
        console.log('[console]', msg.params.args.map(a => a.value ?? a.description ?? '').join(' '));
      }
      if (msg.method === 'Runtime.exceptionThrown') {
        console.log('[exception]', JSON.stringify(msg.params.exceptionDetails).slice(0, 1500));
      }
    };
    const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    await send('Runtime.enable');
    await send('Page.enable');
    await send('Page.navigate', { url });

    // wait for the page's ready flag
    let ready = false;
    for (let i = 0; i < 100; i++) {
      const r = await send('Runtime.evaluate', { expression: 'window.__AF_READY === true', returnByValue: true });
      if (r.result && r.result.result && r.result.result.value === true) { ready = true; break; }
      await sleep(300);
    }
    console.log('page ready:', ready);
    const diag = await send('Runtime.evaluate', {
      expression: 'JSON.stringify(window.__AF_DIAG || document.getElementById("status")?.textContent || null)',
      returnByValue: true
    });
    console.log('diag:', diag.result && diag.result.result && diag.result.result.value);

    for (const shot of shots) {
      if (shot.expr) {
        const r = await send('Runtime.evaluate', { expression: shot.expr, awaitPromise: true, returnByValue: true });
        if (r.result && r.result.exceptionDetails) console.log('[shot-expr-exception]', JSON.stringify(r.result.exceptionDetails).slice(0, 800));
      }
      await sleep(shot.waitMs || 700);
      const cap = await send('Page.captureScreenshot', { format: 'png', fromSurface: true });
      const data = cap.result && cap.result.data;
      if (!data) { console.log('NO SCREENSHOT DATA for', shot.name); continue; }
      const file = path.join(outDir, shot.name + '.png');
      fs.writeFileSync(file, Buffer.from(data, 'base64'));
      console.log('wrote', file);
    }
    ws.close();
  } finally { chrome.kill('SIGKILL'); }
})().catch(e => { console.error('DRIVER ERROR', e); process.exit(1); });
