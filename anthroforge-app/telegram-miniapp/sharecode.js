/* AF1- share-code codec — JS twin of core/sharecode.py.
 * Both decoders enforce matching input and decompressed-size limits.
 */
(function (global) {
  'use strict';
  var CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
  var MAX_CODE_CHARS = 1000000;
  var MAX_DECOMPRESSED_BYTES = 4 * 1024 * 1024;

  function canonicalStringify(value) {
    if (value === null) return 'null';
    var t = typeof value;
    if (t === 'number') {
      if (!isFinite(value)) throw new Error('non-finite number in record');
      return String(value).replace(/e([+-])(\d)$/, 'e$10$2');
    }
    if (t === 'boolean') return value ? 'true' : 'false';
    if (t === 'string') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(canonicalStringify).join(',') + ']';
    if (t === 'object') {
      var keys = Object.keys(value).sort(), parts = [];
      for (var i = 0; i < keys.length; i++) parts.push(JSON.stringify(keys[i]) + ':' + canonicalStringify(value[keys[i]]));
      return '{' + parts.join(',') + '}';
    }
    throw new Error('unsupported value in record: ' + t);
  }
  var CRC_TABLE = null;
  function crc32(bytes) {
    if (!CRC_TABLE) {
      CRC_TABLE = new Int32Array(256);
      for (var n = 0; n < 256; n++) {
        var c = n;
        for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
        CRC_TABLE[n] = c;
      }
    }
    var crc = -1;
    for (var i = 0; i < bytes.length; i++) crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ bytes[i]) & 0xFF];
    return (crc ^ -1) >>> 0;
  }
  function base64urlEncode(bytes) {
    var bin = '', CHUNK = 0x8000;
    for (var i = 0; i < bytes.length; i += CHUNK) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function frameFromCompressed(comp) {
    var crc = crc32(comp), frame = new Uint8Array(comp.length + 4);
    frame.set(comp, 0);
    frame[comp.length] = (crc >>> 24) & 255;
    frame[comp.length + 1] = (crc >>> 16) & 255;
    frame[comp.length + 2] = (crc >>> 8) & 255;
    frame[comp.length + 3] = crc & 255;
    var code = 'AF1-' + base64urlEncode(frame);
    if (code.length > MAX_CODE_CHARS) throw new Error('encoded share code exceeds the size limit');
    return code;
  }
  function encodeShareCodeWith(record, compBytes) { return frameFromCompressed(compBytes); }
  function canonicalBytes(record) {
    var bytes = new TextEncoder().encode(canonicalStringify(record));
    if (bytes.length > MAX_DECOMPRESSED_BYTES) throw new Error('character record exceeds the share-code size limit');
    return bytes;
  }
  async function zlibCompress(bytes) {
    if (typeof CompressionStream === 'undefined') throw new Error('CompressionStream unavailable in this WebView');
    var stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate'));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }
  async function encodeShareCode(record) { return frameFromCompressed(await zlibCompress(canonicalBytes(record))); }
  function base64urlDecode(text) {
    var s = String(text).replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var bin = atob(s), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  }
  async function zlibDecompress(bytes) {
    if (typeof DecompressionStream === 'undefined') throw new Error('DecompressionStream unavailable in this WebView');
    var reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate')).getReader();
    var chunks = [], total = 0;
    try {
      while (true) {
        var item = await reader.read();
        if (item.done) break;
        total += item.value.byteLength;
        if (total > MAX_DECOMPRESSED_BYTES) {
          await reader.cancel();
          throw new Error('share code expands beyond the ' + MAX_DECOMPRESSED_BYTES + '-byte limit');
        }
        chunks.push(item.value);
      }
    } finally { reader.releaseLock(); }
    var out = new Uint8Array(total), offset = 0;
    for (var i = 0; i < chunks.length; i++) { out.set(chunks[i], offset); offset += chunks[i].byteLength; }
    return out;
  }
  async function decodeShareCode(code) {
    if (typeof code !== 'string') throw new Error('share code must be a string');
    code = code.trim();
    if (code.length > MAX_CODE_CHARS) throw new Error('share code exceeds the size limit');
    if (code.indexOf('AF1-') !== 0) throw new Error("share code must start with 'AF1-'");
    var body = code.slice(4);
    if (!body) throw new Error('share code has an empty payload');
    var frame;
    try { frame = base64urlDecode(body); }
    catch (e) { throw new Error('share code is not valid base64url: ' + e.message); }
    if (frame.length <= 4) throw new Error('share code payload is too short to contain a checksum');
    var comp = frame.subarray(0, frame.length - 4);
    var expected = ((frame[frame.length - 4] << 24) | (frame[frame.length - 3] << 16) |
      (frame[frame.length - 2] << 8) | frame[frame.length - 1]) >>> 0;
    if (crc32(comp) !== expected) throw new Error('share code checksum mismatch: the code is corrupted');
    var raw;
    try { raw = await zlibDecompress(comp); }
    catch (e) { throw new Error('share code payload does not decompress: ' + e.message); }
    try { return JSON.parse(new TextDecoder().decode(raw)); }
    catch (e) { throw new Error('share code payload is not valid JSON: ' + e.message); }
  }
  function newCharacterId() {
    var rand = new Uint8Array(10);
    (global.crypto || require('crypto').webcrypto).getRandomValues(rand);
    var r = 0n;
    for (var i = 0; i < rand.length; i++) r = (r << 8n) | BigInt(rand[i]);
    var value = (BigInt(Date.now()) << 80n) | r, chars = [];
    for (var j = 0; j < 26; j++) { chars.push(CROCKFORD[Number(value & 31n)]); value >>= 5n; }
    return 'chr_' + chars.reverse().join('');
  }
  var api = { canonicalStringify: canonicalStringify, canonicalBytes: canonicalBytes, crc32: crc32,
    base64urlEncode: base64urlEncode, base64urlDecode: base64urlDecode, frameFromCompressed: frameFromCompressed,
    encodeShareCodeWith: encodeShareCodeWith, encodeShareCode: encodeShareCode,
    decodeShareCode: decodeShareCode, newCharacterId: newCharacterId };
  global.AFShareCode = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
