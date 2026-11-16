/* Web <-> Core vocabulary — JS twin of anthroforge-app/core/vocabulary.py.
 *
 * The Babylon web apps speak a rendering vocabulary (morph.* scale
 * factors, bodyslide.* .osd differentials, sos.* rig values,
 * driver.* pose drivers, on web bodies max/maxwell/maxine/bara with
 * head web_v2). The Python Core speaks canonical slider records on
 * af_body_neutral_v1 / af_head_neutral_v2. Only the six bodyslide.*
 * keys have a defensible canonical counterpart (approximate bridges —
 * an .osd differential is not the learned Core field; scale converts
 * the 0-100 web value to the canonical range). The morph, sos and
 * driver prefixes have no canonical counterpart and are carried
 * losslessly under identity (morphs/sos/drivers), where the web UI
 * reads them back on import. Slider ids that are already canonical
 * (body.* / head.*) pass through untouched; only a web-prefixed id
 * the table does not know is preserved under
 * identity.unmapped_sliders, never silently dropped.
 *
 * Single source of truth is core/vocabulary.py; this file must stay
 * in sync with it — tests/test_vocabulary.py parses this table and
 * compares it entry-for-entry with the Python module.
 */
(function (global) {
  'use strict';

  var AF_VOCABULARY = {
    "version": 1,
    "base_body_map": {
      "max": "af_body_neutral_v1",
      "maxwell": "af_body_neutral_v1",
      "maxine": "af_body_neutral_v1",
      "bara": "af_body_neutral_v1"
    },
    "head_map": {
      "web_v2": "af_head_neutral_v2"
    },
    "slider_map": {
      "bodyslide.samson": ["body.build.muscle", 0.01],
      "bodyslide.samuel": ["body.belly.protrusion", 0.01],
      "bodyslide.samael": ["body.himbo.lean", 0.01],
      "bodyslide.glutes": ["body.himbo.legs_glutes", 0.01],
      "bodyslide.traps": ["body.himbo.arms_traps", 0.01],
      "bodyslide.meaner": ["head.brow.projection", 1.5]
    },
    "carried_prefixes": {
      "morph.": "morphs",
      "sos.": "sos",
      "driver.": "drivers"
    }
  };

  function canonicalToWebSlider(canonicalId) {
    var keys = Object.keys(AF_VOCABULARY.slider_map);
    for (var i = 0; i < keys.length; i++) {
      var entry = AF_VOCABULARY.slider_map[keys[i]];
      if (entry[0] === canonicalId) return [keys[i], 1 / entry[1]];
    }
    return null;
  }

  // Translate a web-vocabulary record to canonical Core form.
  // Returns { record: <canonical record>, warnings: [<strings>] }.
  // The input record is never mutated. Already-canonical records pass
  // through unchanged and un-warned.
  function translateRecord(record) {
    var warnings = [];
    var out = {};
    var k;
    for (k in record) out[k] = record[k];
    var slidersIn = record.sliders || {};
    var identityIn = record.identity || {};
    var identityOut = {};
    for (k in identityIn) identityOut[k] = identityIn[k];

    var baseIn = record.base || {};
    var baseOut = {};
    for (k in baseIn) baseOut[k] = baseIn[k];
    if (typeof baseIn.body === 'string' && AF_VOCABULARY.base_body_map[baseIn.body]) {
      baseOut.body = AF_VOCABULARY.base_body_map[baseIn.body];
      if (!identityOut.base_body) identityOut.base_body = baseIn.body;
    }
    if (typeof baseIn.head === 'string' && AF_VOCABULARY.head_map[baseIn.head]) {
      baseOut.head = AF_VOCABULARY.head_map[baseIn.head];
      if (!identityOut.base_head) identityOut.base_head = baseIn.head;
    }
    out.base = baseOut;

    var slidersOut = {};
    var carried = {};
    var unmapped = {};
    var prefixes = Object.keys(AF_VOCABULARY.carried_prefixes);
    var WEB_PREFIXES = ['morph.', 'bodyslide.', 'sos.', 'driver.'];
    Object.keys(slidersIn).forEach(function (sid) {
      var value = slidersIn[sid];
      var entry = AF_VOCABULARY.slider_map[sid];
      if (entry) {
        slidersOut[entry[0]] = value * entry[1];
        return;
      }
      var isWeb = WEB_PREFIXES.some(function (p) { return sid.indexOf(p) === 0; });
      if (!isWeb) {
        // Already canonical (body.* / head.* registry ids): pass through.
        slidersOut[sid] = value;
        return;
      }
      for (var i = 0; i < prefixes.length; i++) {
        if (sid.indexOf(prefixes[i]) === 0) {
          var section = AF_VOCABULARY.carried_prefixes[prefixes[i]];
          if (!carried[section]) carried[section] = {};
          carried[section][sid.slice(prefixes[i].length)] = value;
          return;
        }
      }
      unmapped[sid] = value;
      warnings.push("slider '" + sid + "' has no canonical mapping; preserved under identity.unmapped_sliders");
    });
    out.sliders = slidersOut;

    Object.keys(carried).forEach(function (section) {
      var merged = identityOut[section] || {};
      var vals = carried[section];
      Object.keys(vals).forEach(function (key) { merged[key] = vals[key]; });
      identityOut[section] = merged;
    });
    if (Object.keys(unmapped).length) {
      var mergedUnmapped = identityOut.unmapped_sliders || {};
      Object.keys(unmapped).forEach(function (key) { mergedUnmapped[key] = unmapped[key]; });
      identityOut.unmapped_sliders = mergedUnmapped;
    }
    out.identity = identityOut;
    return { record: out, warnings: warnings };
  }

  var api = {
    table: AF_VOCABULARY,
    translateRecord: translateRecord,
    canonicalToWebSlider: canonicalToWebSlider
  };
  global.AFVocabulary = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
