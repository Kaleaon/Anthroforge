// JS share-code codec + vocabulary tests. Run with: node tests/test_sharecode_js.mjs
// (no test runner dependency; exits non-zero on the first failure.)
// Covers: JS encode -> JS decode round-trip, Python-generated preset
// codes (from library/presets/INDEX.json) decoding in JS, corruption
// detection, and the JS vocabulary translation mirroring core/vocabulary.py.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import zlib from 'node:zlib';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const AFShareCode = require(path.join(ROOT, 'telegram-miniapp', 'sharecode.js'));
const AFVocabulary = require(path.join(ROOT, 'telegram-miniapp', 'vocabulary.js'));
const AFPresets = require(path.join(ROOT, 'telegram-miniapp', 'presets.js'));
const AFRecord = require(path.join(ROOT, 'telegram-miniapp', 'record.js'));

const record = {
  format: 'anthroforge.character',
  version: 1,
  id: 'chr_testjs000000000000000001',
  name: 'JS Test',
  base: { body: 'af_body_neutral_v1', head: 'af_head_neutral_v2' },
  sliders: { 'body.belly.protrusion': 0.62, 'body.chubby': 0.30000000000000004 },
  species_preset: null,
  parts: [],
  fur: {},
  materials: {},
  identity: {},
};

// 1. JS encode -> JS decode is lossless.
const comp = zlib.deflateSync(AFShareCode.canonicalBytes(record), { level: 9 });
const code = AFShareCode.encodeShareCodeWith(record, comp);
assert.ok(code.startsWith('AF1-'));
const back = await AFShareCode.decodeShareCode(code);
assert.deepEqual(back, record);

// 2. Async encode path (CompressionStream) round-trips too.
const code2 = await AFShareCode.encodeShareCode(record);
assert.deepEqual(await AFShareCode.decodeShareCode(code2), record);

// 3. Python-generated preset codes decode in JS (cross-language proof:
//    these codes were produced by the Python build script in INDEX.json).
assert.equal(AFPresets.presets.length, 6);
for (const preset of AFPresets.presets) {
  const decoded = await AFShareCode.decodeShareCode(preset.share_code);
  assert.equal(decoded.format, 'anthroforge.character');
  assert.equal(decoded.id, preset.id);
  assert.ok(Object.keys(decoded.sliders).length > 0);
  // A canonical preset record translates to itself.
  const { record: translated, warnings } = AFVocabulary.translateRecord(decoded);
  assert.deepEqual(translated, decoded);
  assert.deepEqual(warnings, []);
}

// 4. Corruption is caught by the CRC gate.
const mid = Math.floor(code.length / 2);
const bad = code.slice(0, mid) + (code[mid] === 'A' ? 'B' : 'A') + code.slice(mid + 1);
await assert.rejects(() => AFShareCode.decodeShareCode(bad), /checksum/);

// 5. Wrong prefix and empty payload are rejected.
await assert.rejects(() => AFShareCode.decodeShareCode('AF2-xxxx'), /AF1-/);
await assert.rejects(() => AFShareCode.decodeShareCode('AF1-'), /empty payload/);

// 6. JS vocabulary translation mirrors the Python module.
const web = {
  format: 'anthroforge.character',
  version: 1,
  id: 'chr_testjs000000000000000002',
  name: 'Web Fennec',
  base: { body: 'max', head: 'web_v2' },
  sliders: {
    'morph.height': 0.95, 'morph.ears': 1.42,
    'bodyslide.samson': 50, 'bodyslide.glutes': 25, 'bodyslide.meaner': 20,
    'sos.length': 1.0, 'sos.knot': 25, 'driver.jawOpen': 12,
  },
  species_preset: { preset: 'fennec', label: 'Fennec Fox Preset' },
  parts: [{ slot: 'head', part: 'head_fennec' }],
  fur: {},
  materials: { colors: { primary: '#e09f5a' } },
  identity: { source: 'telegram-miniapp', species: 'fennec' },
};
const { record: canonical, warnings } = AFVocabulary.translateRecord(web);
assert.deepEqual(canonical.base, { body: 'af_body_neutral_v1', head: 'af_head_neutral_v2' });
assert.equal(canonical.sliders['body.build.muscle'], 0.5);
assert.equal(canonical.sliders['body.himbo.legs_glutes'], 0.25);
assert.equal(canonical.sliders['head.brow.projection'], 30);
assert.deepEqual(canonical.identity.morphs, { height: 0.95, ears: 1.42 });
assert.deepEqual(canonical.identity.sos, { length: 1.0, knot: 25 });
assert.deepEqual(canonical.identity.drivers, { jawOpen: 12 });
assert.deepEqual(warnings, []);
assert.equal(canonical.identity.base_body, 'max');

// 7. Boundary size guards: > 1,000,000 chars and > 4,194,304 decompressed bytes rejected.
const MAX_CODE_CHARS = 1_000_000;
const MAX_DECOMPRESSED_BYTES = 4 * 1024 * 1024;
await assert.rejects(
  () => AFShareCode.decodeShareCode('AF1-' + 'A'.repeat(MAX_CODE_CHARS)),
  /size limit/
);
const bombComp = zlib.deflateSync(Buffer.alloc(MAX_DECOMPRESSED_BYTES + 1, 0x20), { level: 9 });
const bombCode = AFShareCode.frameFromCompressed(bombComp);
assert.ok(bombCode.length < MAX_CODE_CHARS, 'compressed bomb must fit inside character limit');
await assert.rejects(
  () => AFShareCode.decodeShareCode(bombCode),
  /expands beyond the 4194304-byte limit/
);
assert.throws(
  () => AFShareCode.canonicalBytes({ ...record, identity: { pad: 'x'.repeat(MAX_DECOMPRESSED_BYTES + 1) } }),
  /size limit/
);

// 8. Shared record helper (record.js): preserves Crockford ULID, name,
//    species_preset.label, identity.head_shape, and identity.head_sculpt
//    across Mini App -> AF1- -> Desktop v2 round-trips.
const SPECIES_PRESETS = {
  fennec: { label: 'Fennec Fox Preset' },
  wolf: { label: 'Arctic Wolf Preset' },
};
function makeMockState() {
  return {
    activeSpecies: 'fennec',
    baseBody: 'max',
    characterName: '',
    equipped: { head: 'head_fennec', ears: 'ears_fennec', tail: 'tail_fennec' },
    colors: { primary: '#e09f5a', secondary: '#fff3e0' },
    morphs: { height: 1.0, ears: 1.0, tail: 1.0 },
    bodyslide: { samson: 0, samuel: 0, samael: 0, glutes: 0, traps: 0, meaner: 0 },
    sos: { length: 1.0, knot: 0 },
    drivers: { jawOpen: 0, earPerk: 50 },
    coreSliders: {},
  };
}

let miniAppNameInput = 'Kael the Sculpted Wolf';
const miniState = makeMockState();
miniState.activeSpecies = 'wolf';
miniState.baseBody = 'maxwell';
miniState.equipped.head = 'head_wolf';
miniState.morphs.height = 1.08;
miniState.bodyslide.samson = 60;
miniState.bodyslide.meaner = 40;
miniState.sos.knot = 30;
miniState.drivers.jawOpen = 18;
miniState.headShape = {
  width: 1.14, height: 0.96, muzzleWidth: 1.28, muzzleHeight: 1.05,
  jawWidth: 1.22, cheek: 0.92, brow: 1.35,
};
miniState.headSculpt = {
  head_wolf: [0.012, -0.008, 0.025, 0.0, -0.014, 0.019],
};

const miniHelper = AFRecord.createRecordHelper({
  state: miniState,
  source: 'telegram-miniapp',
  speciesPresets: SPECIES_PRESETS,
  getName: () => miniAppNameInput,
  setName: (n) => { miniAppNameInput = n; },
});
assert.equal(globalThis.AFBuildRecord, miniHelper.buildRecord);

const miniExport = miniHelper.buildRecord();
assert.match(miniExport.id, /^chr_[0-9ABCDEFGHJKMNPQRSTVWXYZ]{26}$/);
assert.equal(miniExport.name, 'Kael the Sculpted Wolf');
assert.deepEqual(miniExport.species_preset, { preset: 'wolf', label: 'Arctic Wolf Preset' });
assert.deepEqual(miniExport.identity.head_shape, miniState.headShape);
assert.deepEqual(miniExport.identity.head_sculpt, miniState.headSculpt);
assert.equal(miniExport.identity.source, 'telegram-miniapp');

// Encode in Mini App, decode & import into Desktop v2 helper, then export .afchar.json.
const miniCode = await AFShareCode.encodeShareCode(miniExport);
const v2State = makeMockState(); // Starts without headShape/headSculpt customizations, activeSpecies='fennec'
let v2SyncCount = 0;
const v2Helper = AFRecord.createRecordHelper({
  state: v2State,
  source: 'web',
  speciesPresets: SPECIES_PRESETS,
  getName: () => v2State.characterName || v2State.activeSpecies || 'Unnamed',
  setName: (n) => { v2State.characterName = n; },
  onAfterApply: () => { v2SyncCount++; },
});

const decodedForV2 = await AFShareCode.decodeShareCode(miniCode);
v2Helper.applyRecord(decodedForV2);
assert.equal(v2SyncCount, 1);

const v2Export = v2Helper.buildRecord();
assert.equal(v2Export.id, miniExport.id);
assert.equal(v2Export.name, 'Kael the Sculpted Wolf');
assert.deepEqual(v2Export.species_preset, { preset: 'wolf', label: 'Arctic Wolf Preset' });
assert.deepEqual(v2Export.identity.head_shape, miniState.headShape);
assert.deepEqual(v2Export.identity.head_sculpt, miniState.headSculpt);
assert.equal(v2Export.identity.source, 'web');
assert.equal(v2Export.identity.base_body, 'maxwell');
assert.deepEqual(v2Export.sliders, miniExport.sliders);
assert.deepEqual(v2Export.identity.morphs, miniExport.identity.morphs);
assert.deepEqual(v2Export.identity.sos, miniExport.identity.sos);
assert.deepEqual(v2Export.identity.drivers, miniExport.identity.drivers);
assert.deepEqual(v2Export.parts, miniExport.parts);

// Canonical preset round-trip through AFRecord preserves preset id, name, head_sliders & label,
// resets previously set bodyslide sliders to 0, and preserves all preset sliders.
const pynDecoded = await AFShareCode.decodeShareCode(AFPresets.presets[2].share_code);
v2Helper.applyRecord(pynDecoded);
const pynReExported = v2Helper.buildRecord();
assert.equal(pynReExported.id, 'chr_preset_pyn');
assert.equal(pynReExported.name, 'Pyn');
assert.deepEqual(pynReExported.species_preset.head_sliders, pynDecoded.species_preset.head_sliders);
assert.ok(pynReExported.species_preset.label);
assert.equal(pynReExported.sliders['body.build.muscle'], 0);
for (const [sid, val] of Object.entries(pynDecoded.sliders)) {
  assert.ok(sid in pynReExported.sliders, `missing slider ${sid}`);
  assert.ok(Math.abs(pynReExported.sliders[sid] - val) < 1e-12, `slider ${sid} drifted`);
}

// 9. Shared import modal handler populates presets, imports valid codes, and surfaces bomb errors.
function makeElement(id = '') {
  return {
    id,
    value: '',
    textContent: '',
    children: [],
    listeners: {},
    classList: {
      classes: new Set(['hidden']),
      add(c) { this.classes.add(c); },
      remove(c) { this.classes.delete(c); },
    },
    appendChild(child) { this.children.push(child); },
    addEventListener(type, fn) { this.listeners[type] = fn; },
  };
}
const els = {
  'btn-import-sharecode': makeElement('btn-import-sharecode'),
  'af-import-modal': makeElement('af-import-modal'),
  'af-import-preset': makeElement('af-import-preset'),
  'af-import-code': makeElement('af-import-code'),
  'af-import-status': makeElement('af-import-status'),
  'af-import-cancel': makeElement('af-import-cancel'),
  'af-import-go': makeElement('af-import-go'),
};
const toasts = [];
const modalBinding = v2Helper.bindImportModal({
  document: {
    getElementById: (id) => els[id] || null,
    createElement: (tag) => makeElement(tag),
  },
  toast: (msg) => toasts.push(msg),
});
assert.equal(els['af-import-preset'].children.length, AFPresets.presets.length);

// Oversized / decompression-bomb share code displays clear error in modal status.
els['af-import-code'].value = bombCode;
const failedImport = await modalBinding.runImport();
assert.equal(failedImport, null);
assert.match(els['af-import-status'].textContent, /^⛔ Import failed: .*4194304-byte limit/);

// Valid share code imports cleanly and fires toast.
els['af-import-code'].value = miniCode;
const okImport = await modalBinding.runImport();
assert.equal(okImport.name, 'Kael the Sculpted Wolf');
assert.match(els['af-import-status'].textContent, /^✅ Imported Kael the Sculpted Wolf/);
assert.deepEqual(toasts, ['✅ Imported Kael the Sculpted Wolf']);

// 10. Both web apps reference the 4 shared scripts and v2 has zero inline duplicates.
const REPO_ROOT = path.resolve(ROOT, '..');
const v2HtmlPath = path.join(REPO_ROOT, 'anthroforge-v2', 'anthroforge_3d_pro_v2.html');
const miniHtmlPath = path.join(ROOT, 'telegram-miniapp', 'index.html');
const v2Html = readFileSync(v2HtmlPath, 'utf8');
const miniHtml = readFileSync(miniHtmlPath, 'utf8');

for (const scriptName of ['sharecode.js', 'vocabulary.js', 'presets.js', 'record.js']) {
  const canonicalPath = path.join(ROOT, 'telegram-miniapp', scriptName);
  assert.match(
    v2Html,
    new RegExp(`<script\\s+src=["']\\.\\./anthroforge-app/telegram-miniapp/${scriptName}["']\\s*></script>`),
    `v2 HTML must load shared ${scriptName}`
  );
  assert.equal(
    path.resolve(path.dirname(v2HtmlPath), '..', 'anthroforge-app', 'telegram-miniapp', scriptName),
    canonicalPath
  );
  assert.match(
    miniHtml,
    new RegExp(`<script\\s+src=["']${scriptName}["']\\s*></script>`),
    `Mini App HTML must load shared ${scriptName}`
  );
}
for (const forbidden of ['AF_VOCABULARY', 'function decodeShareCode', 'AF_PRESETS', 'buildAfcharRecord', 'applyAfcharRecord']) {
  assert.ok(!v2Html.includes(forbidden), `v2 HTML must not contain inline ${forbidden}`);
}

console.log('test_sharecode_js: all checks passed');
