/* Shared character record builder, applier, and import-modal controller.
 *
 * Used by both telegram-miniapp/index.html and anthroforge-v2/anthroforge_3d_pro_v2.html
 * as a classic IIFE script (works over file:// and HTTP without ES module CORS issues).
 * Varying UI hooks (source name, species preset metadata, character name accessors,
 * toast callback, and post-apply UI sync) are passed explicitly via createRecordHelper.
 */
(function (global) {
  'use strict';

  var DEFAULT_HEAD_SHAPE = {
    width: 1.0,
    height: 1.0,
    muzzleWidth: 1.0,
    muzzleHeight: 1.0,
    jawWidth: 1.0,
    cheek: 1.0,
    brow: 1.0
  };
  var VALID_BASE_BODIES = ['max', 'maxine', 'maxwell', 'bara'];
  var SAFE_CHAR_ID = /^[A-Za-z0-9_-]+$/;

  function cloneJson(value) {
    if (value === null || typeof value !== 'object') return value;
    return JSON.parse(JSON.stringify(value));
  }

  function resetAndApplyHeadShape(target, incoming) {
    Object.keys(target).forEach(function (k) {
      if (!(k in DEFAULT_HEAD_SHAPE)) delete target[k];
    });
    Object.keys(DEFAULT_HEAD_SHAPE).forEach(function (k) {
      target[k] = DEFAULT_HEAD_SHAPE[k];
    });
    if (incoming && typeof incoming === 'object' && !Array.isArray(incoming)) {
      Object.keys(incoming).forEach(function (k) {
        target[k] = incoming[k];
      });
    }
  }

  function createRecordHelper(options) {
    var opts = options || {};
    var state = opts.state;
    if (!state || typeof state !== 'object') {
      throw new Error('AFRecord.createRecordHelper requires a state object');
    }
    if (!state.headShape || typeof state.headShape !== 'object' || Array.isArray(state.headShape)) {
      state.headShape = cloneJson(DEFAULT_HEAD_SHAPE);
    }
    if (!state.headSculpt || typeof state.headSculpt !== 'object' || Array.isArray(state.headSculpt)) {
      state.headSculpt = {};
    }
    if (!state.coreSliders || typeof state.coreSliders !== 'object' || Array.isArray(state.coreSliders)) {
      state.coreSliders = {};
    }

    function getShareCode() {
      return opts.shareCode || global.AFShareCode || null;
    }
    function getVocabulary() {
      return opts.vocabulary || global.AFVocabulary || null;
    }
    function getPresets() {
      return opts.presets || global.AFPresets || null;
    }

    var shareCodeMod = getShareCode();
    var charId = (typeof opts.characterId === 'string' && SAFE_CHAR_ID.test(opts.characterId))
      ? opts.characterId
      : (shareCodeMod && typeof shareCodeMod.newCharacterId === 'function'
          ? shareCodeMod.newCharacterId()
          : 'chr_web');
    var storedName = '';
    var storedSpeciesPreset = null;
    var storedSpeciesKey = null;
    var storedFur = {};
    var storedUnmappedSliders = null;

    function buildRecord() {
      var sliders = {};
      // Canonical sliders imported from a preset/code go in first:
      // a bodyslide key below overwrites its canonical twin, because
      // the UI's own sliders are the current truth.
      Object.keys(state.coreSliders || {}).forEach(function (k) { sliders[k] = state.coreSliders[k]; });
      Object.keys(state.morphs || {}).forEach(function (k) { sliders['morph.' + k] = state.morphs[k]; });
      Object.keys(state.bodyslide || {}).forEach(function (k) { sliders['bodyslide.' + k] = state.bodyslide[k]; });
      Object.keys(state.sos || {}).forEach(function (k) { sliders['sos.' + k] = state.sos[k]; });
      Object.keys(state.drivers || {}).forEach(function (k) { sliders['driver.' + k] = state.drivers[k]; });

      var parts = Object.keys(state.equipped || {}).map(function (slot) {
        return { slot: slot, part: state.equipped[slot] };
      });

      var rawName = typeof opts.getName === 'function' ? opts.getName() : storedName;
      var name = (typeof rawName === 'string' && rawName.trim())
        || (typeof storedName === 'string' && storedName.trim())
        || 'Unnamed';

      var activeSpecies = state.activeSpecies || 'fennec';
      var speciesMap = opts.speciesPresets || {};
      var presetMeta = speciesMap[activeSpecies] || {};
      var fallbackLabel = presetMeta.label || activeSpecies;
      var speciesPreset;
      if (storedSpeciesPreset && storedSpeciesKey === activeSpecies) {
        speciesPreset = cloneJson(storedSpeciesPreset);
        if (!speciesPreset.preset) speciesPreset.preset = activeSpecies;
        if (!speciesPreset.label) speciesPreset.label = fallbackLabel;
      } else {
        speciesPreset = {
          preset: activeSpecies,
          label: fallbackLabel
        };
      }

      var sourceName = typeof opts.source === 'function' ? opts.source() : (opts.source || 'web');
      var identity = {
        source: sourceName,
        species: activeSpecies,
        head_shape: cloneJson(state.headShape || {}),
        head_sculpt: cloneJson(state.headSculpt || {})
      };
      if (storedUnmappedSliders && Object.keys(storedUnmappedSliders).length) {
        identity.unmapped_sliders = cloneJson(storedUnmappedSliders);
      }

      var raw = {
        format: 'anthroforge.character',
        version: 1,
        id: charId,
        name: name,
        base: { body: state.baseBody || 'max', head: 'web_v2' },
        sliders: sliders,
        species_preset: speciesPreset,
        parts: parts,
        fur: cloneJson(storedFur || {}),
        materials: { colors: cloneJson(state.colors || {}) },
        identity: identity
      };

      var vocab = getVocabulary();
      if (vocab && typeof vocab.translateRecord === 'function') {
        var translated = vocab.translateRecord(raw);
        translated.warnings.forEach(function (w) { console.warn('[vocabulary]', w); });
        return translated.record;
      }
      return raw;
    }

    function applyRecord(record) {
      if (!record || record.format !== 'anthroforge.character') {
        throw new Error('not an AnthroForge character record');
      }
      if (typeof record.id === 'string' && SAFE_CHAR_ID.test(record.id)) {
        charId = record.id;
      }
      if (typeof record.name === 'string') {
        storedName = record.name;
        if (typeof opts.setName === 'function') opts.setName(record.name);
      }

      var sliders = record.sliders || {};
      var identity = record.identity || {};
      var recSpecies = (record.species_preset && typeof record.species_preset.preset === 'string' && record.species_preset.preset)
        || (typeof identity.species === 'string' && identity.species)
        || null;
      if (recSpecies) {
        state.activeSpecies = recSpecies;
      }
      if (record.species_preset && typeof record.species_preset === 'object' && !Array.isArray(record.species_preset)) {
        storedSpeciesPreset = cloneJson(record.species_preset);
        storedSpeciesKey = state.activeSpecies || 'fennec';
      } else {
        storedSpeciesPreset = null;
        storedSpeciesKey = null;
      }

      storedFur = (record.fur && typeof record.fur === 'object' && !Array.isArray(record.fur))
        ? cloneJson(record.fur)
        : {};
      storedUnmappedSliders = (identity.unmapped_sliders && typeof identity.unmapped_sliders === 'object' && !Array.isArray(identity.unmapped_sliders))
        ? cloneJson(identity.unmapped_sliders)
        : null;

      state.headSculpt = (identity.head_sculpt && typeof identity.head_sculpt === 'object' && !Array.isArray(identity.head_sculpt))
        ? cloneJson(identity.head_sculpt)
        : {};
      if (!state.headShape || typeof state.headShape !== 'object' || Array.isArray(state.headShape)) {
        state.headShape = {};
      }
      resetAndApplyHeadShape(state.headShape, identity.head_shape);

      [['morphs', state.morphs], ['sos', state.sos], ['drivers', state.drivers]].forEach(function (pair) {
        var vals = identity[pair[0]];
        var target = pair[1];
        if (vals && typeof vals === 'object' && target && typeof target === 'object') {
          Object.keys(vals).forEach(function (k) {
            if (k in target) target[k] = vals[k];
          });
        }
      });

      if (state.bodyslide && typeof state.bodyslide === 'object') {
        Object.keys(state.bodyslide).forEach(function (k) {
          state.bodyslide[k] = 0;
        });
      }
      var vocab = getVocabulary();
      var core = {};
      Object.keys(sliders).forEach(function (cid) {
        var inv = (vocab && typeof vocab.canonicalToWebSlider === 'function')
          ? vocab.canonicalToWebSlider(cid)
          : null;
        if (inv) {
          var parts = inv[0].split('.');
          if (parts[0] === 'bodyslide' && state.bodyslide && parts[1] in state.bodyslide) {
            state.bodyslide[parts[1]] = sliders[cid] * inv[1];
          } else {
            core[cid] = sliders[cid];
          }
        } else {
          core[cid] = sliders[cid];
        }
      });
      state.coreSliders = core;

      if (identity.base_body && VALID_BASE_BODIES.indexOf(identity.base_body) >= 0) {
        state.baseBody = identity.base_body;
      }

      if (record.materials && record.materials.colors && typeof record.materials.colors === 'object' && state.colors) {
        Object.keys(record.materials.colors).forEach(function (k) {
          if (k in state.colors) state.colors[k] = record.materials.colors[k];
        });
      }

      (record.parts || []).forEach(function (entry) {
        if (entry && entry.slot && entry.part && state.equipped && entry.slot in state.equipped) {
          state.equipped[entry.slot] = entry.part;
        }
      });

      if (typeof opts.onAfterApply === 'function') {
        opts.onAfterApply(record);
      }
      return record;
    }

    function bindImportModal(modalOptions) {
      var mopts = modalOptions || {};
      var doc = mopts.document || global.document;
      if (!doc || typeof doc.getElementById !== 'function') return null;

      var importBtn = doc.getElementById('btn-import-sharecode');
      var importModal = doc.getElementById('af-import-modal');
      var importPreset = doc.getElementById('af-import-preset');
      var importCode = doc.getElementById('af-import-code');
      var importStatus = doc.getElementById('af-import-status');
      var cancelBtn = doc.getElementById('af-import-cancel');
      var goBtn = doc.getElementById('af-import-go');
      var toastFn = mopts.toast || opts.toast || null;

      var presetsMod = getPresets();
      if (importPreset && presetsMod && Array.isArray(presetsMod.presets)) {
        presetsMod.presets.forEach(function (p) {
          var o = doc.createElement('option');
          o.value = p.share_code;
          o.textContent = p.name;
          importPreset.appendChild(o);
        });
      }

      async function runImport() {
        try {
          var code = ((importCode && importCode.value) || '').trim();
          if (!code && importPreset && importPreset.value) code = importPreset.value;
          if (!code) throw new Error('paste a share code or pick a preset');
          var sc = getShareCode();
          if (!sc || typeof sc.decodeShareCode !== 'function') {
            throw new Error('share-code codec not loaded');
          }
          var record = await sc.decodeShareCode(code);
          applyRecord(record);
          var label = record.name || 'character';
          if (importStatus) {
            importStatus.textContent = '✅ Imported ' + label +
              ' — ' + Object.keys(record.sliders || {}).length + ' sliders.';
          }
          if (typeof toastFn === 'function') toastFn('✅ Imported ' + label);
          if (importModal && importModal.classList) {
            setTimeout(function () { importModal.classList.add('hidden'); }, 900);
          }
          return record;
        } catch (err) {
          if (importStatus) {
            importStatus.textContent = '⛔ Import failed: ' + (err && err.message ? err.message : String(err));
          }
          return null;
        }
      }

      if (importBtn && importModal) {
        importBtn.addEventListener('click', function () { importModal.classList.remove('hidden'); });
        if (cancelBtn) {
          cancelBtn.addEventListener('click', function () { importModal.classList.add('hidden'); });
        }
        if (goBtn) {
          goBtn.addEventListener('click', runImport);
        }
      }

      return { runImport: runImport };
    }

    if (opts.exposeGlobal !== false) {
      global.AFBuildRecord = buildRecord;
    }

    return {
      buildRecord: buildRecord,
      applyRecord: applyRecord,
      bindImportModal: bindImportModal,
      getCharacterId: function () { return charId; }
    };
  }

  var api = {
    DEFAULT_HEAD_SHAPE: DEFAULT_HEAD_SHAPE,
    createRecordHelper: createRecordHelper
  };
  global.AFRecord = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
