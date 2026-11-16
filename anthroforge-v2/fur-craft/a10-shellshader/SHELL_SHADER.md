# A10 — Shell-Texturing Fur Shader (Realtime, Babylon)

**Status: code-complete prototype, NEVER RUN.** Reconstructed by the A10
finisher pass (Nov 12, 2026) from the surviving source after the original
agent died silently. `shellfur.js` and `shots.js` both pass `node --check`
(verified by the finisher). There is **no test page, no screenshot, and no
timing anywhere** — every performance statement below is labelled
**[UNMEASURED]** unless it follows from the code by construction.

Deliverables in this folder:

| File | What it is |
|---|---|
| `shellfur.js` (11.5 KB) | The shader + attach API — the actual A10 deliverable |
| `shots.js` (4.3 KB) | Headless-Chrome (CDP + SwiftShader) screenshot driver, written for a fur test page that **does not exist** |
| `probe.html` (1.8 KB) | Babylon engine smoke test only (green sphere + red ShaderMaterial sphere, sets `ENGINE_OK`). It does **not** load `shellfur.js` |

---

## 1. Technique in one paragraph

Classic Lengyel shell texturing adapted for meshes that may have no UVs,
targeting Babylon.js 7.x. The source mesh is cloned N times; shell *i* is
extruded along its vertex normals by `t_i · furLength` in the vertex shader.
Each fragment tests a per-strand random value fetched from a tiling noise
texture, keyed by a pattern coordinate anchored to the **un-extruded**
surface — so the same strand column is tested identically on every shell.
A fragment survives only if its strand exists (density test) and the shell
lies within that strand's own length, so strands taper out individually
instead of all ending on one shell. One extra **fuzz shell** sits just past
the tips and keeps only fresnel/dither-gated silhouette fragments — a soft
rim halo with no alpha blending. Everything is **opaque + discard**:
depth-write on, no transparency pass, no sort order. That is the
mobile/webview-friendly way to do shells.

## 2. How it works

### 2.1 Shell construction (`ShellFur.attach`)

- `attach(scene, source, options)` returns a handle
  `{ setParam, setShellCount, dispose, meshes, params, patternSpace }`.
- Shells are Babylon clones of the source — they **share its geometry**, so
  extra geometry memory is ~zero by construction; the cost is draw calls
  and fragment overdraw (see §6).
- Shells are built at `t = i/N` for `i = 1..N` (no t=0 shell — the source
  mesh itself is the root layer). If `fuzz > 0`, one fuzz shell is added at
  t = 1.0 with `furLength × 1.3`.
- Each shell gets its own `ShaderMaterial` (registered shaders `shellfur`
  vertex/fragment in `BABYLON.Effect.ShadersStore`), `backFaceCulling =
  true`, `isPickable = false`. Bounding info is expanded by
  `furLength · 1.4 + 0.01` so fur doesn't clip at screen edges, and world
  matrices are **frozen** (see limit L5).
- The source mesh's transform (position/rotation/scaling, parent) is copied
  to each shell once, at build time.
- **Base darkening:** if the source material is Standard/PBR, it is cloned
  and darkened toward the root colour (`albedo × 0.45 + rootColour × 0.64`)
  so skin showing between strands at grazing angles doesn't read as bald
  bright patches.

### 2.2 Vertex shader

```
p = position + normal · (t · furLength)        // shell extrusion
p += bendDir · bend · 0.6 · t² · furLength     // quadratic droop
```

Droop is zero at the root and full at the tip; `bendDir` is in the mesh's
local space (default straight down, (0,−1,0)).

### 2.3 Pattern coordinate & the noise texture

- **UV mode** (`PATTERN_UV` define, chosen automatically when the mesh has
  UVs): `pat = uv · patternScale`.
- **Object mode** (no UVs): dominant-axis projection of the **base**
  (un-extruded) position, `pat = proj · patternScale`.
- `cell = floor(pat)`; one fetch per fragment from a shared 256×256 RGBA
  `RawTexture`, NEAREST sampling, **no mipmaps** (cells must stay crisp),
  wrap-addressed, filled by a deterministic LCG (seed `0x2f6e2b1`) so
  screenshots are reproducible. The texture is cached on the scene under a
  magic key and shared by all fur groups.
- The three channels are the entire per-strand random model:
  - **R — existence:** `if (nz.r > density) discard;`
  - **B — strand length:** `if (t > 0.35 + 0.65 · nz.b) discard;` — every
    strand reaches at least 35 % of `furLength`; lengths stagger to 100 %.
  - **G — shade jitter** (colour) and **fuzz dither** (fuzz shell).

### 2.4 Fragment shading (per shell fragment)

- Colour = `mix(rootColor, tipColor, t)`.
- Cheap Lambert against **one fixed world-space key-light direction
  uniform** (`0.30 + 0.70 · max(N·L, 0)`). Scene lights are ignored.
- Fake AO: `× (0.55 + 0.45 · t)` — roots in shadow.
- Per-strand jitter: `× (0.85 + 0.30 · nz.g)`.
- Rim sheen: `+ tipColor · (1 − N·V)³ · 0.22` — additive (see §5).
- Shading normal is the base mesh's vertex normal everywhere; there is no
  per-strand direction or flow (see limit L6).

### 2.5 Fuzz shell

`t = 1.0`, length × 1.3, `uFuzz > 0`: a fragment survives only if
`nz.g ≤ (1 − N·V)² · fuzz · 1.7` — near the silhouette, dithered by the
green channel so the halo is soft rather than a hard ring.

### 2.6 Live control

- `setParam(name, value)` — uniform-only update for everything except
  `shells`/`fuzz`, which rebuild the clone set.
- `setShellCount(n)` — rebuild. `dispose()` — removes shells, materials,
  the camera observer, and the cloned base material (not the shared noise
  texture).
- Camera position is pushed to all shell materials per frame via
  `scene.onBeforeRenderObservable` (the rim/fuzz terms need it).

## 3. Parameters

Defaults from `ShellFur.DEFAULTS`:

| Parameter | Default | Meaning | Live? |
|---|---|---|---|
| `shells` | 16 | Shell layers (t = 1/N … 1) | rebuild |
| `furLength` | 0.04 | Strand length, scene units (≈ m at our scale) | yes |
| `density` | 0.6 | Fraction of pattern cells that grow a strand | yes |
| `patternScale` | 200 | Pattern cells per UV unit (UV mode) or per metre (object mode) → ≈ 5 mm cell pitch in object mode | yes |
| `bend` | 0.3 | Droop strength, 0 = straight out, 1 = strong (scaled ×0.6 in-shader) | yes |
| `bendDir` | (0,−1,0) | Droop direction, local space | yes |
| `fuzz` | 0.7 | Fuzz-shell strength; 0 disables the fuzz shell | rebuild |
| `rootColor` | (0.13, 0.08, 0.045) | Strand root colour (dark warm brown) | yes |
| `tipColor` | (0.55, 0.38, 0.22) | Strand tip colour (tan) | yes |
| `lightDir` | normalize(0.4, 0.8, 0.45) | Fixed key-light direction, world space, *toward* the light | yes |

Parameters are per-`attach()` call, i.e. per mesh. Per-zone variation
(density/length/colour by body region) means one attach per zone mesh —
there are no paintmap inputs (see L7).

## 4. The supporting files, honestly

- **`probe.html`** proves only that the workspace Babylon build
  (`../../lib/babylon.js` → `anthroforge-v2/lib/babylon.js`, present) can
  create an engine and compile a trivial ShaderMaterial. It never touches
  `shellfur.js`. Whether it was ever run is unknown — no output survives.
- **`shots.js`** is a competent CDP driver: launches the workspace Chrome
  headless with SwiftShader WebGL, waits for `window.__AF_READY`, evaluates
  per-shot expressions (it expects a page API `AF.setSubject(...)`), and
  captures PNGs. **That page was never written or never saved** — a
  tree-wide search finds no other reference to `ShellFur`. The screenshot
  pipeline therefore dead-ends at the missing page, and no PNG evidence
  exists.
- Even if run, SwiftShader is CPU rendering: screenshots would verify
  *correctness only*, never GPU frame cost.

## 5. Connection to A12 (fur shading models)

A12's shipped model — anisotropic GGX + Charlie sheen on cards via PBR
materials and ratified glTF extensions — is a **different path** from A10.
A10 is a custom Babylon `ShaderMaterial`: no PBR, no sheen, no anisotropy,
nothing exportable to glTF. The two meet only at the rim/fuzz question:

- **Agreement:** A12's hard rule is *"rim is additive or it is wrong"*
  (a Mix-style rim collapsed silhouette p95 186 → 160 in its testbed).
  A10's in-shell rim term is purely **additive** and its coefficient 0.22
  sits **inside A12's ≤ 0.25 bound**. The fuzz shell is the same garnish
  in shell form: fresnel-gated, silhouette-only.
- **Conflict:** A12 mandates rim **default OFF**, engine-only, never baked.
  A10's rim term is **always on** with no switch, and the fuzz shell
  defaults on (`fuzz: 0.7`). Adopting A10 as-is would violate the A12
  default; conforming it is a small change (a `rim` parameter, default 0;
  `fuzz` default stays a product call).
- A12's LOD guidance (sheen+aniso → sheen → sheen) applies to cards, not
  shells; for shells the A5 ladder governs (§6).

## 6. Connection to A5 (fur budgets)

A5 places shells at **tier 2** of the technique ladder: zone tris × shell
count, a practical interactive cap of **≈ 8 shells**, spent on short-fur
zones only (belly ×6 desktop/WebGL-high, body hair ×4 max), with the
Mini App budget at **1 fur draw call, shells off on the low tier** and
scene guidance of ≤ ~80 draw calls in a phone webview. Against that:

- **A10's defaults do not fit A5.** 16 shells + fuzz = **17 draw calls per
  furred mesh** (18 counting the base) and 17× the mesh's triangles
  rasterised, applied to a *whole mesh* rather than a zone. [Cost figures
  are by construction from the code; frame-time impact UNMEASURED.]
- **Where A10 does agree with A5:** A5 §6 makes alpha-test/cutout the
  mandatory core (blended overdraw is the mobile frame-killer). A10 is
  discard-only with depth-write on and no blending or sorting at all —
  exactly the safe side of that rule. Its discard happens immediately
  after the single noise fetch, before any lighting math, which limits
  (does not eliminate) wasted fragment work: discarded fragments still
  cost rasterisation + one texture fetch.
- **A conforming configuration exists:** attach per short-fur *zone* at
  4–6 shells, desktop/WebGL-high tier only; cards remain the primary
  technique everywhere else, per A5 and the D4 direction. A10 as shipped
  is a whole-mesh desktop demo, not a budget-compliant zone system.

## 7. Honest limits

- **L1 — Never executed.** Syntax-valid only. Shader compile errors,
  Babylon API drift (7.x assumed), and visual quality are all unverified.
- **L2 — Lighting is a toy.** One fixed-direction Lambert, 0.30 ambient
  floor, fake root AO. It ignores scene lights, shadows, and environment;
  relighting a scene does not relight the fur.
- **L3 — No export path.** Runtime Babylon only; nothing reaches glTF,
  the Mini App's exported characters, or SL. (Same wall A12 found for
  Marschner, one level down.)
- **L4 — Draw calls scale with zones.** Every `attach()` is N+2 draws;
  a zoned character multiplies that per zone. See §6.
- **L5 — Fur does not follow the character.** World matrices are frozen
  and transforms copied once at build. No skinning, no morph targets, no
  animation — re-pose the source and the shells stay behind. For skinned
  avatars this is the structural blocker: real shell fur here needs the
  extrusion inside a bone-aware vertex shader.
- **L6 — No strand direction.** Strands grow along vertex normals plus a
  single global bend vector. No flow field (A7's `FURP_direction`), no
  combing, no whorls.
- **L7 — No authoring inputs.** Uniform density/length/colour per attach.
  No connection to A7 paintmaps (`FURP_density/length/zone_*`), A11's
  banded shaft profiles (colour is a two-stop root→tip mix — no agouti
  banding), or A19 species profiles. Colours are raw Color3 uniforms.
- **L8 — Pattern anchoring caveats.** Object-mode dominant-axis projection
  can flip cells where the dominant axis changes; the header comment
  claims seams are invisible in random noise — plausible, **unverified**.
  Strand pitch also differs between UV mode (per UV unit) and object
  mode (per metre) at the same `patternScale`.
- **L9 — Coverage is cell-bound.** One strand column per pattern cell;
  at ≈ 5 mm pitch (object mode, default scale) this is a short-fur
  technique only — long fur would read as stacked cards of noise, which
  is what A5's ladder already says (shells = short zones).

## 8. What finishing A10 takes

1. A test page in the `shots.js` contract (`AF.setSubject`,
   `window.__AF_READY`) on a UV'd and a UV-less mesh; run the existing
   driver for correctness screenshots (SwiftShader is fine for this).
2. Conformance edits: `rim` parameter defaulting to 0 (A12), shell-count
   presets per A5 zone (4–6), attach-per-zone instead of whole-mesh.
3. Real-GPU timing on a phone-class device before any Mini App claim —
   nothing in this folder measures that, and SwiftShader numbers must
   never be quoted as performance.
4. Skinning support (bone-aware extrusion) before it can touch an actual
   AnthroForge character — until then A10 is a static-mesh demo.
5. Optional, later: sample A7 `FURP_*` maps in place of the uniform
   density/length/colour parameters.

---

*Evidence base: `shellfur.js`, `shots.js`, `probe.html` (this folder,
read in full); `../a12-shading/FUR_SHADING.md` §2.4/§4.3/§5;
`../a5-budgets/FUR_BUDGETS.md` §2/§3b/§4/§6. Syntax verified with
`node --check` by the finisher. No browser was run for this document.*
