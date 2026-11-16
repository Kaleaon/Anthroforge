"use strict";
/**
 * apply_sliders.js — AnthroForge slider runtime (viewport side).
 *
 * The Python Core Service (APP_BLUEPRINT §2.3) resolves a character's
 * sparse slider vector against canonical records and ships per-base
 * instances; THIS module is what the Babylon.js viewport runs to turn
 * (bind-pose positions + instances + vector) into deformed positions.
 *
 * Pipeline order (same as Babylon's MorphTargetManager relative to the
 * skeleton): morph deltas apply in BIND space, skinning deforms after.
 * Deltas are bind-pose-referenced, so `positions` must be the mesh's
 * bind-pose position buffer, never an already-posed one.
 *
 * Fold guard: every value is hard-clamped to its record's [min, max];
 * a value beyond `safe_max` (the QA-verified fold-free ceiling from the
 * canonical record) is clamped to safe_max and reported in `warnings`.
 * The runtime never silently applies an out-of-QA deformation.
 *
 * Core API:
 *   applySliderVector(positions, indices, instances, vector, records)
 *     positions : Float32Array, bind pose, n*3 (not mutated)
 *     indices   : Uint32Array | number[], n*3 triangle indices
 *     instances : { sliderId: { indices: number[], delta: number[] } }
 *                 delta is the sparse field at value +1.0 (flat xyz)
 *     vector    : { sliderId: value }  (sparse — absent = default 0)
 *     records   : { sliderId: { range: {min, max, safe_max} } }
 *   -> { positions, normals, warnings }
 *
 * Babylon adapter: applyToBabylonMesh(mesh, instances, vector, records)
 *   Expects a global BABYLON (the v2 app loads it from CDN). Reads the
 *   mesh position kind, applies the core, writes back positions +
 *   recomputed normals, refreshes bounds.
 *
 * Self-test:  node apply_sliders.js --selftest output/fixture_head.json
 */

function clampValue(id, value, records, warnings) {
  const rec = records[id];
  if (!rec || !rec.range) return value;
  const { min, max, safe_max } = rec.range;
  let v = value;
  if (typeof min === "number") v = Math.max(min, v);
  if (typeof max === "number") v = Math.min(max, v);
  if (v !== value) {
    warnings.push({ slider: id, requested: value, applied: v,
                    note: "hard clamp to record range" });
    value = v;
  }
  if (typeof safe_max === "number" && v > safe_max) {
    warnings.push({ slider: id, requested: value, applied: safe_max,
                    note: "fold guard: clamped to QA safe_max" });
    v = safe_max;
  }
  return v;
}

/** Area-weighted vertex normals (same convention as the Python QA). */
function computeVertexNormals(positions, indices) {
  const n = positions.length / 3;
  const normals = new Float32Array(positions.length);
  for (let f = 0; f < indices.length; f += 3) {
    const a = indices[f] * 3, b = indices[f + 1] * 3, c = indices[f + 2] * 3;
    const ux = positions[b] - positions[a], uy = positions[b + 1] - positions[a + 1], uz = positions[b + 2] - positions[a + 2];
    const vx = positions[c] - positions[a], vy = positions[c + 1] - positions[a + 1], vz = positions[c + 2] - positions[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    for (const o of [a, b, c]) {
      normals[o] += nx; normals[o + 1] += ny; normals[o + 2] += nz;
    }
  }
  for (let i = 0; i < n; i++) {
    const o = i * 3;
    const l = Math.hypot(normals[o], normals[o + 1], normals[o + 2]) || 1;
    normals[o] /= l; normals[o + 1] /= l; normals[o + 2] /= l;
  }
  return normals;
}

function applySliderVector(positions, indices, instances, vector, records) {
  const out = Float32Array.from(positions); // bind pose is never mutated
  const warnings = [];
  for (const [id, raw] of Object.entries(vector)) {
    const inst = instances[id];
    if (!inst) {
      warnings.push({ slider: id, requested: raw, applied: 0,
                      note: "no instance for this base — skipped" });
      continue;
    }
    const v = clampValue(id, raw, records || {}, warnings);
    if (v === 0) continue;
    const idx = inst.indices, d = inst.delta;
    for (let k = 0; k < idx.length; k++) {
      const o = idx[k] * 3, p = k * 3;
      out[o]     += v * d[p];
      out[o + 1] += v * d[p + 1];
      out[o + 2] += v * d[p + 2];
    }
  }
  return { positions: out,
           normals: computeVertexNormals(out, indices),
           warnings };
}

/** Babylon adapter — mirrors how the Core Service drives the viewport. */
function applyToBabylonMesh(mesh, instances, vector, records) {
  if (typeof BABYLON === "undefined") {
    throw new Error("applyToBabylonMesh needs a global BABYLON");
  }
  const kind = BABYLON.VertexBuffer.PositionKind;
  const bind = mesh.getVerticesData(kind);
  const idx = mesh.getIndices();
  const res = applySliderVector(Float32Array.from(bind), idx,
                                instances, vector, records);
  mesh.updateVerticesData(kind, res.positions, false, false);
  if (BABYLON.VertexData && BABYLON.VertexData.ComputeNormals) {
    const normals = new Float32Array(res.positions.length);
    BABYLON.VertexData.ComputeNormals(res.positions, idx, normals);
    mesh.updateVerticesData(BABYLON.VertexBuffer.NormalKind, normals,
                            false, false);
  } else {
    mesh.updateVerticesData(BABYLON.VertexBuffer.NormalKind, res.normals,
                            false, false);
  }
  if (mesh.refreshBoundingInfo) mesh.refreshBoundingInfo(true);
  return res.warnings;
}

// ---------------------------------------------------------------------------
// Self-test against the Python-authored fixture (output/fixture_head.json).
// ---------------------------------------------------------------------------
function selftest(path) {
  const fs = require("fs");
  const fx = JSON.parse(fs.readFileSync(path, "utf8"));
  const positions = Float32Array.from(fx.positions);
  const indices = fx.indices;
  const instances = { [fx.record.id]: fx.instance };
  const records = { [fx.record.id]: { range: fx.record.range } };
  const anchor = fx.anchor_vertices[0];
  const disp = (res) => {
    const o = anchor * 3;
    return Math.hypot(res.positions[o] - positions[o],
                      res.positions[o + 1] - positions[o + 1],
                      res.positions[o + 2] - positions[o + 2]);
  };
  const bindCopy = Float32Array.from(positions);

  const r1 = applySliderVector(positions, indices, instances,
                               { [fx.record.id]: 1.0 }, records);
  console.log("value +1.0: anchor displacement = %s (expected 0.0600)",
              disp(r1).toFixed(4));
  console.log("value +1.0: warnings = %j", r1.warnings);
  const nl = Math.hypot(r1.normals[anchor * 3], r1.normals[anchor * 3 + 1],
                        r1.normals[anchor * 3 + 2]);
  console.log("value +1.0: anchor normal length = %s", nl.toFixed(4));

  const r2 = applySliderVector(positions, indices, instances,
                               { [fx.record.id]: 2.0 }, records);
  console.log("value +2.0: anchor displacement = %s (safe_max %s -> expect %s)",
              disp(r2).toFixed(4), fx.record.range.safe_max,
              (0.06 * fx.record.range.safe_max).toFixed(4));
  console.log("value +2.0: warnings = %j", r2.warnings);

  let mutated = false;
  for (let i = 0; i < positions.length; i++) {
    if (positions[i] !== bindCopy[i]) { mutated = true; break; }
  }
  console.log("bind pose untouched: %s", !mutated);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { applySliderVector, applyToBabylonMesh,
                     computeVertexNormals };
}
if (typeof require !== "undefined" && require.main === module) {
  const args = process.argv.slice(2);
  if (args[0] === "--selftest" && args[1]) selftest(args[1]);
  else console.log("usage: node apply_sliders.js --selftest <fixture.json>");
}
