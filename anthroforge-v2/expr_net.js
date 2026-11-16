(async () => {
  const out = { scripts: [...document.scripts].map(s => s.src), babylon: typeof window.BABYLON };
  try { const r = await fetch('https://cdn.jsdelivr.net/npm/babylonjs@7.31.2/babylon.js', { method: 'HEAD' }); out.fetch = r.status; }
  catch (e) { out.fetchError = String(e); }
  return out;
})()