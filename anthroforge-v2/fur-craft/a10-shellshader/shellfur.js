/*
 * ShellFur — shell-stack fur for Babylon.js 7.x (AnthroForge A10 prototype).
 *
 * Technique: classic shell texturing (Lengyel et al.) adapted for meshes
 * that may have no UVs.
 *   - The source mesh is cloned N times ("shells"); shell i is extruded
 *     along its vertex normals by t_i * furLength in the vertex shader.
 *   - Each shell's fragment shader looks up a per-strand random value from
 *     a tiling noise texture, keyed by a PATTERN COORDINATE that is anchored
 *     to the *un-extruded* surface (UV if the mesh has UVs, dominant-axis
 *     projection of the base position otherwise). A fragment survives only
 *     if its strand exists (density) and this shell lies within the
 *     strand's own length — so strands taper out individually instead of
 *     all ending on the same shell.
 *   - One extra "fuzz shell" sits just past the strand tips; its fragments
 *     survive only near the silhouette (fresnel-gated discard), giving the
 *     soft rim halo without any alpha blending or sorting.
 *   - Everything is opaque + discard: no transparency pass, no sort order,
 *     depth-write on. That is the mobile/webview-friendly way to do shells.
 *
 * All shells share the source mesh's geometry (clones), so extra memory is
 * ~zero; the cost is N+2 draw calls and fragment overdraw.
 *
 * Usage:
 *   const noise = ShellFur.getNoiseTexture(scene);
 *   const fur = ShellFur.attach(scene, mesh, { shells: 16, furLength: 0.04 });
 *   fur.setParam('density', 0.8);       // live, uniform-only
 *   fur.setShellCount(24);              // rebuilds the shell clones
 *   fur.dispose();
 */
(function (global) {
  'use strict';

  const NOISE_SIZE = 256;

  BABYLON.Effect.ShadersStore['shellfurVertexShader'] = /* glsl */`
    attribute vec3 position;
    attribute vec3 normal;
    #ifdef PATTERN_UV
    attribute vec2 uv;
    #endif
    uniform mat4 world;
    uniform mat4 worldViewProjection;
    uniform float uShellT;
    uniform float uFurLength;
    uniform vec3 uBendDir;
    varying vec3 vBasePos;
    varying vec3 vNormalW;
    varying vec3 vWorldPos;
    varying float vT;
    #ifdef PATTERN_UV
    varying vec2 vUv;
    #endif
    void main(void) {
      float t = uShellT;
      vec3 p = position + normal * (t * uFurLength);
      // Quadratic droop: zero at the root, full bend at the tip.
      p += uBendDir * (t * t * uFurLength);
      vBasePos = position;
      vT = t;
      #ifdef PATTERN_UV
      vUv = uv;
      #endif
      vec4 wp = world * vec4(p, 1.0);
      vWorldPos = wp.xyz;
      vNormalW = normalize(mat3(world) * normal);
      gl_Position = worldViewProjection * vec4(p, 1.0);
    }`;

  BABYLON.Effect.ShadersStore['shellfurFragmentShader'] = /* glsl */`
    uniform sampler2D uNoise;
    uniform float uDensity;
    uniform float uPatternScale;
    uniform float uFuzz;
    uniform vec3 uRootColor;
    uniform vec3 uTipColor;
    uniform vec3 uLightDirW;
    uniform vec3 uCamPos;
    varying vec3 vBasePos;
    varying vec3 vNormalW;
    varying vec3 vWorldPos;
    varying float vT;
    #ifdef PATTERN_UV
    varying vec2 vUv;
    #endif
    void main(void) {
      #ifdef PATTERN_UV
        vec2 pat = vUv * uPatternScale;
      #else
        // Dominant-axis projection of the BASE (un-extruded) position:
        // the pattern is anchored to the surface, so the same strand
        // column is tested on every shell. Seams where the dominant axis
        // flips are invisible in a random pattern.
        vec3 an = abs(vNormalW);
        vec2 proj = (an.x > an.y && an.x > an.z) ? vBasePos.zy
                  : (an.y > an.z) ? vBasePos.xz : vBasePos.xy;
        vec2 pat = proj * uPatternScale;
      #endif
      vec2 cell = floor(pat);
      // One fetch per fragment feeds all per-strand randomness:
      //   r = strand existence, g = shade jitter / fuzz dither,
      //   b = strand length fraction.
      vec4 nz = texture2D(uNoise, (cell + vec2(0.5)) / ${NOISE_SIZE}.0);
      float t = vT;
      if (nz.r > uDensity) discard;              // strand does not exist
      if (t > 0.35 + 0.65 * nz.b) discard;       // shell past this strand's tip
      vec3 N = normalize(vNormalW);
      vec3 V = normalize(uCamPos - vWorldPos);
      float ndv = abs(dot(N, V));
      if (uFuzz > 0.0) {
        // Fuzz shell: keep fragments only near the silhouette, dithered
        // by the green noise channel so the halo is soft, not a hard ring.
        float fres = pow(1.0 - ndv, 2.0);
        if (nz.g > fres * uFuzz * 1.7) discard;
      }
      float diff = max(dot(N, uLightDirW), 0.0);
      vec3 col = mix(uRootColor, uTipColor, t);
      col *= 0.30 + 0.70 * diff;                 // cheap lambert vs key light
      col *= 0.55 + 0.45 * t;                    // fake AO: roots in shadow
      col *= 0.85 + 0.30 * nz.g;                 // per-strand shade jitter
      col += uTipColor * pow(1.0 - ndv, 3.0) * 0.22;  // rim sheen
      gl_FragColor = vec4(col, 1.0);
    }`;

  /** Shared tiling RGBA noise texture (per-strand randomness source). */
  function getNoiseTexture(scene) {
    const key = '__shellfurNoise';
    if (scene[key]) return scene[key];
    const data = new Uint8Array(NOISE_SIZE * NOISE_SIZE * 4);
    // Deterministic LCG so screenshots are reproducible run to run.
    let s = 0x2f6e2b1;
    for (let i = 0; i < data.length; i++) {
      s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
      data[i] = (s >>> 16) & 0xff;
    }
    const tex = new BABYLON.RawTexture(
      data, NOISE_SIZE, NOISE_SIZE,
      BABYLON.Engine.TEXTUREFORMAT_RGBA, scene,
      false /* no mipmaps: cells must stay crisp */,
      false, BABYLON.Texture.NEAREST_SAMPLINGMODE);
    tex.wrapU = tex.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE;
    scene[key] = tex;
    return tex;
  }

  const DEFAULTS = {
    shells: 16,
    furLength: 0.04,
    density: 0.6,
    patternScale: 200,
    bend: 0.3,                    // 0 = straight out, 1 = strong droop
    bendDir: new BABYLON.Vector3(0, -1, 0),  // local space
    fuzz: 0.7,                    // 0 disables the fuzz shell
    rootColor: new BABYLON.Color3(0.13, 0.08, 0.045),
    tipColor: new BABYLON.Color3(0.55, 0.38, 0.22),
    lightDir: new BABYLON.Vector3(0.4, 0.8, 0.45).normalize() // toward light, world
  };

  /**
   * Attach shell fur to a mesh. The source mesh stays as the "skin" base;
   * shells are added as sibling clones sharing its geometry.
   * Returns a handle { setParam, setShellCount, dispose, meshes, params }.
   */
  function attach(scene, source, options) {
    const params = Object.assign({}, DEFAULTS, options || {});
    const noise = getNoiseTexture(scene);
    const hasUV = source.isVerticesDataPresent(BABYLON.VertexBuffer.UVKind);
    const patternSpace = hasUV ? 'uv' : 'object';

    // Darken the skin under the fur toward the root colour: at grazing
    // angles you see between strands down to the base, and bright skin
    // showing through reads as bald patches.
    let baseMaterial = null;
    if (source.material &&
        (source.material instanceof BABYLON.StandardMaterial ||
         source.material instanceof BABYLON.PBRMaterial)) {
      baseMaterial = source.material.clone(source.name + '_furbase');
      const dk = params.rootColor.scale(1.6);
      if (baseMaterial instanceof BABYLON.PBRMaterial) {
        baseMaterial.albedoColor = baseMaterial.albedoColor.scale(0.45).add(dk.scale(0.4));
      } else {
        baseMaterial.diffuseColor = baseMaterial.diffuseColor.scale(0.45).add(dk.scale(0.4));
      }
      source.material = baseMaterial;
    }

    const group = { meshes: [], materials: [] };
    let disposed = false;

    function makeShellMaterial(t, isFuzz) {
      const mat = new BABYLON.ShaderMaterial(
        source.name + '_shell_' + (isFuzz ? 'fuzz' : t.toFixed(3)), scene,
        { vertex: 'shellfur', fragment: 'shellfur' },
        {
          attributes: hasUV ? ['position', 'normal', 'uv'] : ['position', 'normal'],
          uniforms: ['world', 'worldViewProjection', 'uShellT', 'uFurLength',
                     'uBendDir', 'uDensity', 'uPatternScale', 'uFuzz',
                     'uRootColor', 'uTipColor', 'uLightDirW', 'uCamPos'],
          samplers: ['uNoise'],
          defines: hasUV ? ['#define PATTERN_UV'] : []
        });
      mat.setTexture('uNoise', noise);
      mat.setFloat('uShellT', t);
      mat.backFaceCulling = true;
      applyUniforms(mat, isFuzz ? 1 : 0);
      return mat;
    }

    function applyUniforms(mat, fuzzFlag) {
      mat.setFloat('uFurLength', params.furLength * (fuzzFlag ? 1.3 : 1.0));
      mat.setFloat('uDensity', params.density);
      mat.setFloat('uPatternScale', params.patternScale);
      mat.setFloat('uFuzz', fuzzFlag ? params.fuzz : 0.0);
      mat.setColor3('uRootColor', params.rootColor);
      mat.setColor3('uTipColor', params.tipColor);
      mat.setVector3('uBendDir', params.bendDir.scale(params.bend * 0.6));
      mat.setVector3('uLightDirW', params.lightDir);
    }

    function buildShells() {
      // remove old
      for (const m of group.meshes) m.dispose(false, false);
      for (const mt of group.materials) mt.dispose();
      group.meshes.length = 0; group.materials.length = 0;

      const bb = source.getBoundingInfo().boundingBox;
      const grow = params.furLength * 1.4 + 0.01;
      const bmin = bb.minimum.subtract(new BABYLON.Vector3(grow, grow, grow));
      const bmax = bb.maximum.add(new BABYLON.Vector3(grow, grow, grow));

      function addShell(t, isFuzz) {
        const shell = source.clone(source.name + (isFuzz ? '_fuzz' : '_shell' + Math.round(t * 1000)));
        shell.parent = source.parent;
        shell.position.copyFrom(source.position);
        shell.rotation.copyFrom(source.rotation);
        if (source.rotationQuaternion) shell.rotationQuaternion = source.rotationQuaternion.clone();
        shell.scaling.copyFrom(source.scaling);
        const mat = makeShellMaterial(t, isFuzz);
        shell.material = mat;
        shell.isPickable = false;
        // Bounds must include the extrusion or fur clips at screen edges.
        shell.setBoundingInfo(new BABYLON.BoundingInfo(bmin, bmax));
        shell.freezeWorldMatrix();
        group.meshes.push(shell); group.materials.push(mat);
      }

      for (let i = 1; i <= params.shells; i++) addShell(i / params.shells, false);
      if (params.fuzz > 0) addShell(1.0, true);
    }

    buildShells();

    // Keep the shader's camera position current (one hook per fur group).
    const camObserver = scene.onBeforeRenderObservable.add(() => {
      const cam = scene.activeCamera;
      if (!cam) return;
      for (const mt of group.materials) mt.setVector3('uCamPos', cam.globalPosition);
    });

    return {
      params,
      patternSpace,
      get meshes() { return group.meshes; },
      setParam(name, value) {
        params[name] = value;
        if (name === 'fuzz' || name === 'shells') { buildShells(); return; }
        group.materials.forEach((mt, idx) =>
          applyUniforms(mt, idx === group.materials.length - 1 && params.fuzz > 0 ? 1 : 0));
      },
      setShellCount(n) { params.shells = n; buildShells(); },
      dispose() {
        if (disposed) return; disposed = true;
        scene.onBeforeRenderObservable.remove(camObserver);
        for (const m of group.meshes) m.dispose(false, false);
        for (const mt of group.materials) mt.dispose();
        if (baseMaterial) baseMaterial.dispose();
      }
    };
  }

  global.ShellFur = { attach, getNoiseTexture, DEFAULTS };
})(window);
