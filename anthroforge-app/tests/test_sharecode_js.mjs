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

console.log('test_sharecode_js: all checks passed');
