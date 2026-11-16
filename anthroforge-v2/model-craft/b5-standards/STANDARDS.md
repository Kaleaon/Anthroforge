# Game-Ready Model Standards — AnthroForge Export-Profile Budgets

*Learning agent B5, model-craft wave — Nov 12, 2026. Text study; no assets built.*

**Purpose.** APP_BLUEPRINT §11 defines the export pipeline and per-format
profiles in prose; HEROFORGE HF7 adds the print-profile doctrine ("the
export profile is a product"). What neither carries is a single table of
*numbers*: how many triangles, materials, texture pixels, bones, and
morphs a character may spend per target before the target pushes back.
This document supplies those numbers — first as published by the
platforms themselves, then as AnthroForge budget tables that our QA
gauntlet and export profiles can enforce.

**Labels.** `[S]` = sourced from a published platform document or a
cited production guide. `[E]` = AnthroForge estimate: our own budget,
derived from the sourced numbers and stated reasoning, not a platform
rule. A third class appears throughout and matters most:

- **Hard limit** — the platform refuses, splits, blocks, or silently
  breaks the asset past this line. Non-negotiable at export.
- **Rank / cost threshold** — the asset uploads, but pays: a worse
  performance rank, more Land Impact, more L$, or default-hidden
  visibility.
- **Budget** — our chosen target inside the thresholds. Budgets are
  AnthroForge policy `[E]` even when the threshold they sit under is
  `[S]`.

**Counting rules (apply to every table below).** Triangles are counted
after triangulation, summed over all meshes of the assembled character
at LOD0 unless a row says per-mesh. "Materials" means material *slots*
(each slot is at least one draw call — Unity/VRChat count slots, SL
counts faces per mesh object). Texture memory is GPU memory including
mipmaps, not file size: a 2048×2048 RGBA texture is ≈22 MB in VRAM
regardless of how small its PNG/WebP file is `[S — web GLB guide]`;
only GPU-compressed formats (KTX2/Basis, BC/ASTC) reduce VRAM itself.
Bones are counted as joints actually weighted by the export, not joints
present in the authoring rig.

---

## 1. The sourced evidence

### 1.1 VRChat — official performance ranks `[S]`

VRChat's Avatar Performance Ranking System is the most completely
published budget scheme in the avatar world: every stat has four
thresholds (Excellent / Good / Medium / Poor); exceeding Poor on any
stat makes the avatar Very Poor on that stat. VRChat's own guidance:
"**Aim for Good ranking.** If you can't hit that, Medium is perfectly
fine." On PC the default minimum displayed rank is Very Poor (nothing
hidden by default); **on mobile the default block level is Medium —
Poor and Very Poor avatars are not shown** unless a user opts in, and
Very Poor mobile avatars may lose that override entirely in future.

**PC thresholds** (maximums per rank) `[S]`:

| Stat | Excellent | Good | Medium | Poor |
|---|---:|---:|---:|---:|
| Triangles | 32,000 | 70,000 | 70,000 | 70,000 |
| Texture memory | 40 MB | 75 MB | 110 MB | 150 MB |
| Skinned meshes | 1 | 2 | 8 | 16 |
| Basic meshes | 4 | 8 | 16 | 24 |
| Material slots | 4 | 8 | 16 | 32 |
| Bones | 75 | 150 | 256 | 400 |
| PhysBone components | 4 | 8 | 16 | 32 |
| PhysBone affected transforms | 16 | 64 | 128 | 256 |
| Animators | 1 | 4 | 16 | 32 |
| Lights | 0 | 0 | 0 | 1 |
| Face-tracking operations | 2,000 | 4,000 | 8,000 | 16,000 |
| Forwarded parameters | 10 | 20 | 30 | 40 |

**Mobile (Android / iOS / Quest) thresholds** `[S]`:

| Stat | Excellent | Good | Medium | Poor |
|---|---:|---:|---:|---:|
| Triangles | 7,500 | 10,000 | 15,000 | 20,000 |
| Texture memory | 10 MB | 18 MB | 25 MB | 40 MB |
| Skinned meshes | 1 | 1 | 2 | 2 |
| Basic meshes | 1 | 1 | 2 | 2 |
| Material slots | 1 | 1 | 2 | 4 |
| Bones | 75 | 90 | 150 | 150 |
| Animators | 1 | 1 | 1 | 2 |
| PhysBone components | 0 | 4 | 6 | 8 (hard cap) |
| Contacts | 2 | 4 | 8 | 16 (hard cap) |
| Constraints | 30 | 60 | 120 | 150 (hard cap) |

Mobile also carries *hard component caps* (PhysBones ≤8, affected
transforms ≤64, colliders ≤16, contacts ≤16, constraints ≤150, depth
≤50) that cannot be bypassed even with "Show Avatar" `[S]`, and the
Android build itself must be **≤10 MB after compression** (aim 5–8 MB)
`[S — VRChat Android content optimisation]`. Two traps worth naming:
disabling Mesh Read/Write on any mesh forces an instant Very Poor
regardless of counts `[S]`, and **all components count, including
disabled ones** `[S]`.

Morphs/blendshapes are *not* a ranked stat in themselves. They enter
the ranks through texture/geometry memory and, when face-tracked,
through Face Tracking Operations (each tracking→blendshape mapping
counts once per mesh containing the target shape) `[S]`. VRChat's
authoring guidance recommends one skinned mesh renderer at maximum
(three static), splitting head from body so blendshape cost is paid
only on the head mesh, and baking detail into normal maps rather than
triangles `[S — VRChat optimisation tips / first-avatar guide]`.

### 1.2 Second Life — hard limits and upload economics `[S]`

SL's constraints are architectural, not advisory. From the Second Life
wiki limits page and the Project Bento knowledge base:

| Limit | Value | Class |
|---|---:|---|
| Joints weighted per mesh | **≤110** | hard `[S]` |
| Bone influences per vertex | **≤4** | hard `[S]` |
| Materials (faces) per mesh object | **≤8** | hard `[S]` |
| Vertices per mesh per LOD | **≤65,536** | hard `[S]` |
| Triangles per material face | **≈21,844** (importer quirk, BUG-1001) | hard-in-practice `[S]` |
| Triangles per single uploaded object | **≈174,752** (8 × 21,844); beyond this the uploader splits the mesh into linked objects | hard-in-practice `[S]` |
| Compressed mesh asset size | **≤8 MB** (≈256 MB raw Collada) | hard `[S]` |
| Largest single dimension | **64 m** | hard `[S]` |
| Clothing / baked textures | **≤1024×1024** (eyes 128×128); larger is downsized server-side; 2K BoM in development, not supported | hard `[S]` |
| LOD levels per mesh | **4** (High / Medium / Low / Lowest), each ≤65,536 verts | structural `[S]` |
| Mesh / texture upload fee | **L$10 per file** (mesh fee scales with calculated cost above the base) | cost `[S]` |

**Bento.** Project Bento extended the avatar skeleton by 106 bones
(the full skeleton totals ~159 bones in community tooling counts) —
face, fingers, wings (11 joints incl. `mWingsRoot` + `mWing4Fan` per
side), tail, hind limbs `[S — Bento KB; BODY_PLANS §1]`. The 110-joint
per-mesh cap sits *below* the skeleton total, so a full-body-plus-face
export must be split across meshes or drop unused joints — partial
skeletons are allowed and expected `[S]`. Bento joint positions are
negotiated with the wearer's shape sliders and translation animations
`[S — BODY_PLANS §1]`; a mesh's uploaded joint positions can override
the wearer's skeleton, which is why stray ancestors in a part export
are a correctness bug, not clutter.

**Land Impact.** For rezzed objects, LI = **max(download weight,
physics weight, server weight)** `[S]`, driven mainly by LOD triangle
counts and object size; the lowest LOD dominates the download-weight
calculation in practice. **Worn attachments do not consume parcel LI**
`[S]`, so for avatar exports LI is not the binding constraint — the
binding constraints are the hard caps above plus the social cost of
download weight (every nearby viewer streams your LOD chain). Upload
fees still apply per mesh and per texture, so part count is a real
L$ cost driver for a modular character: a 12-part character with
4 LODs is one DAE per part, plus one upload per texture.

**Morphs in SL: none.** Collada mesh upload carries no morph-target
channel usable by the viewer; SL "shape" is bone positions (system
shape sliders + uploaded joint overrides) and Bakes on Mesh textures.
Every AnthroForge slider must therefore be **baked** for SL, or
re-expressed as joint positions where the slider is genuinely a
proportion change (BODY_PLANS §5 mapping) `[S + blueprint §11.3]`.

### 1.3 Indie / engine practice — Unity, Unreal, mobile `[S]`

No engine imposes a character budget; production guides converge on
ranges that reflect draw calls, skinning cost, and texture memory:

| Target | Triangles / character | Materials | Textures | Bones | Influences |
|---|---:|---:|---:|---:|---:|
| PC/console hero | 30,000–100,000+ `[S]` | ≤4 typical, up to 8 | 2048–4096 | 30–60 typical main rig; more with attachments | 4 (Unity default max) `[S]` |
| PC/console NPC | 5,000–20,000 `[S]` | 1–2, shared atlases | 1024–2048 | simplified, no fingers | 4 |
| Mobile hero | 5,000–15,000 (mid-range); 20,000–30,000 flagship `[S]` | 1–2 | 1024 (2048 face close-ups) | ~30–60 | 4 `[S]` |
| Mobile NPC / crowd | 300–6,000 `[S]` | 1 | 512–1024 | minimal | 1–2 |
| Low-poly stylised (any) | 500–5,000 `[S]` | vertex colour or 1 | ≤1024 or none | simple | ≤4 |

Engine facts that shape budgets `[S — Unity docs]`: linear blend
skinning defaults to **4 influences per vertex** in Unity, and mobile
skinning cost scales with bone count (Unity's own example: +15 bones
on a 30-bone rig = ~50% more solve operations in Generic mode);
Unity's optimisation guidance is literally "use a single Skinned Mesh
Renderer" and "use as few bones as possible." Every extra material is
an extra draw call, and on mobile a shader *switch* (setpass) costs
3–4× a draw call — materials discipline beats triangle discipline on
phones `[S — mobile optimisation guides]`.

Morphs in engines: blendshapes are stored as full per-vertex delta
buffers (position, usually normal/tangent too), so **morph memory ≈
one extra copy of the mesh's vertex data per morph**, and Unity
applies them on CPU by default `[S]`. There is no standard count cap;
the budget is memory and the number of *simultaneously evaluated*
shapes. Production practice keeps runtime morph sets small (visemes +
expressions on a head mesh) and bakes customisation sliders at spawn
or export `[E — synthesis of the above]`.

### 1.4 Web / WebGL (the Mini App's world) `[S + E]`

glTF/GLB is the delivery format; the optimisation literature is
consistent: textures dominate both file size and VRAM (often ≥80% of
file bytes) `[S]`; meshopt compression is preferred over Draco for
animated/morph content because it compresses morph targets and
animation too, while Draco leaves them untouched `[S]`; KTX2/Basis is
the only step that reduces *GPU* memory (4–8× vs raw RGBA) rather than
just download size `[S]`. Published starting points for a single hero
avatar in a phone browser: **<10 MB total file (aim ~5 MB)**, draw
calls **<12 for the character**, textures capped at 1024–2048, and
budgets set for *sustained* (thermally throttled) phone GPUs, not
burst clocks `[S — web avatar guides]`. Telegram Mini Apps add no
published 3D limits of their own; the constraint is the phone browser
itself, plus first-load patience on mobile data `[E]`.

### 1.5 Print `[S]`

Print inverts every real-time rule: triangle count is not a budget,
*resolution and wall thickness* are. STL carries no units — export in
millimetres `[S]`. The mesh must be watertight/manifold (every edge
shared by exactly two faces, no holes, no flipped normals) `[S]`.
Export tessellation: chord deviation 0.01–0.05 mm `[S]`. Walls:

| Rule | Resin (SLA/DLP) | FDM |
|---|---:|---:|
| Absolute minimum wall | 0.4 mm supported | 0.8 mm (= 2 × 0.4 mm nozzle) `[S]` |
| Recommended minimum wall | 0.6–1.0 mm | 1.2 mm structural `[S]` |
| Handled / load-bearing parts | 2.0 mm | 2.0 mm `[S]` |
| Hollow shell (if hollowed) | 1.5–2.0 mm + ≥2 drain holes | n/a (infill) `[S]` |
| Minimum feature / pin | ~0.15–0.5 mm detail | pins <2 mm shear; gaps <0.4 mm fuse `[S]` |

Materials, bones, morphs, and textures do not exist in an STL print
export (single fused solid, one colour; 3MF can carry colour). Print
profiles instead budget **scale** (figurine 32 mm / 75 mm, bust,
life-size fursuit head) and a **strength pass** that thickens sub-minimum
features *with a report*, per HF7 `[S — HEROFORGE HF7]`.

---

## 2. AnthroForge export-profile budgets

Six profiles. Each row is a **budget** (what the exporter targets and
the QA gauntlet checks) with the governing hard limit or threshold
named beside it. All budgets `[E]` — AnthroForge policy derived from
§1 — except where a cell repeats a platform hard limit, marked `[S]`.
The 128-point parts pool (PARTS_STANDARD) is a *character-design*
budget and still applies at authoring time; these tables govern what
survives export.

### 2.1 `dae-sl` / `dae-sl-bento` — Second Life

Unit of budgeting is **per uploaded mesh object**, because SL's caps
are per mesh; a character is a set of part meshes (BODY_PLANS §5:
partial skeletons, parts exported separately).

| Axis | Budget | Governing limit |
|---|---|---|
| Triangles per mesh, LOD0 (High) | ≤20,000 design target; split the part before exceeding it | ≤21,844 per material face `[S]`; ≤174,752 per object `[S]` |
| Triangles, whole character (all worn parts, LOD0) | ≤80,000 | none (social/download cost only) `[E]` |
| LOD chain per mesh | High 100% → Medium ~50% → Low ~25% → Lowest ≤300 tris and ≥1 tri (never auto-decimated garbage) | 4 LODs, each ≤65,536 verts `[S]`; blueprint §11.3 ratios |
| Materials per mesh | ≤6 design target | **≤8 hard** `[S]` |
| Textures | ≤1024×1024 per face, atlased per part; eyes 128–256 | 1024 clothing/bake cap `[S]` |
| Texture uploads per character | ≤12 (atlas aggressively — L$10 each) | fee per file `[S]` |
| Bones per mesh | ≤100 design target | **≤110 hard** `[S]` |
| Influences per vertex | ≤4, normalised | **≤4 hard** `[S]` |
| Morphs | **0 — all sliders baked**; proportion sliders may re-express as joint-position overrides (reported) | no morph channel `[S]` |
| Fur | Cards only, counted inside the part's tri budget; shell/strand fur dropped with a report line | — |
| Scale | Total avatar extent ≤64 m per mesh; realistic characters 0.5–3.5 m (Titan-scale exports are legal but pay download weight) | 64 m hard `[S]` |
| File | DAE per part; physics = lowest-LOD reuse or convex low mesh | ≤8 MB compressed asset `[S]` |

**Profile-specific gates:** joint count computed *after* Bento name
mapping (BODY_PLANS §5.4); partial exports contain no unintended
ancestor joints; every joint-position override listed in the report;
each mesh ≤8 materials *after* atlasing; LOD0 silhouette checked
against the Lowest LOD at 75 m+ viewing distance (impostor honesty).

### 2.2 `vrchat-pc` — VRChat-style, PC

Target rank **Good** (VRChat's own recommended aim), Excellent as the
stretch column. Whole-character counting.

| Axis | Budget (Good) | Stretch (Excellent) | Governing threshold `[S]` |
|---|---|---|---|
| Triangles | ≤70,000 | ≤32,000 | rank table §1.1 |
| Material slots | ≤8 | ≤4 | rank |
| Skinned meshes | ≤2 (body + head) | 1 | rank |
| Basic meshes | ≤8 | ≤4 | rank |
| Texture memory | ≤75 MB VRAM | ≤40 MB | rank |
| Texture size | ≤2048 body/head, ≤1024 parts | ≤1024 | derived from memory budget `[E]` |
| Bones | ≤150 | ≤75 | rank |
| Influences per vertex | ≤4 | ≤4 | Unity default `[S]` |
| Morphs | ≤64 exported, head mesh only (visemes + expression set); body sliders baked | ≤32 | face-tracking ops ≤4,000 at Good `[S]`; memory `[E]` |
| PhysBones | ≤8 components / ≤64 transforms | ≤4 / ≤16 | rank |
| Fur | Cards LOD0–2 inside tri budget; strand groom never exported | cards, fewer | `[E]` |
| File size | ≤25 MB `[E]` | ≤10 MB | no PC hard cap published |

### 2.3 `vrchat-mobile` — VRChat-style, Android / Quest / iOS

Target rank **Medium or better** — not politeness: mobile's default
block level is Medium, so a Poor avatar is invisible by default `[S]`.
Good is the design target where the character allows it.

| Axis | Budget (design: Good) | Ceiling (Medium) | Governing threshold `[S]` |
|---|---|---|---|
| Triangles | ≤10,000 | ≤15,000 | rank table §1.1 |
| Material slots | **1** | ≤2 | rank |
| Skinned meshes | **1** | ≤2 | rank |
| Texture memory | ≤18 MB VRAM | ≤25 MB | rank |
| Texture size | ≤1024 total atlas | ≤1024 | Android guidance: avoid >1k `[S]` |
| Bones | ≤90 | ≤150 | rank |
| Influences per vertex | ≤4 (2 preferred on body) | ≤4 | Unity mobile practice `[S]` |
| Morphs | ≤16, head-and-body merged mesh pays for them in memory; visemes only + core expressions | ≤24 | memory `[E]` |
| PhysBones | ≤4 components | ≤6 | rank; hard cap 8 `[S]` |
| Fur | **No cards at Good** (1 material slot); baked fur shading in the atlas + fresnel fuzz in shader. Cards permitted only at Medium, ≤2,000 tris | cards ≤3,000 tris | `[E]` from slot/tri budgets |
| File size | ≤8 MB compressed | **≤10 MB hard** `[S]` | Android avatar cap |

This is the most destructive profile: most AnthroForge characters
will need a *derived* mobile variant (merged mesh, merged materials,
baked sliders, fur painted not geometric). The profile must say so in
its report rather than pretend the PC asset squeezes down `[E]`.

### 2.4 `webgl-miniapp` — Telegram Mini App / browser (Babylon.js, GLB)

The Mini App is mobile-first (375 px-class phone screens, phone GPUs,
mobile data). No platform publishes limits; budgets are `[E]`,
anchored to §1.4's web practice and §1.1's mobile ranks.

| Axis | Budget | Notes |
|---|---|---|
| Triangles (LOD0, whole character) | ≤20,000 | One hero character on screen; LOD1 ~50%, LOD2 ~25% shipped in the same GLB |
| Draw calls (character) | ≤12 | Merge meshes sharing a material `[S-anchored]` |
| Material slots | ≤4 | body / head / eyes / fur-cards |
| Texture size | ≤1024 body, ≤1024 head, ≤512 parts | KTX2 required for shipped assets (VRAM 4–8× saving `[S]`) |
| Texture memory | ≤25 MB VRAM | mobile-rank-consistent `[E]` |
| Bones | ≤90 total; our 36-bone core + part modules fits by design | skinning cost on phone GPUs |
| Influences per vertex | ≤4 | glTF standard practice |
| Morphs | ≤24 exported unbaked (the creator's live slider subset); the full slider stack bakes | each morph ≈ a full vertex-delta buffer `[S]`; Babylon morph-target cost is per-target memory |
| Fur | Cards LOD set from the fur prototype (LOD0 ≈13.6k tris is *over* this profile's whole budget — Mini App fur uses LOD1/LOD2 card sets, ≈5.4k / ≈2.0k tris) | measured, fur-prototype QA |
| File size | ≤5 MB GLB (meshopt + KTX2) | first-load on mobile data `[E]` |
| Load behaviour | Preview LOD2 renders before full asset streams | `[E]` |

### 2.5 `indie-pc` — generic Unity/Unreal character (FBX/GLB)

For characters leaving the avatar ecosystems into a game project.

| Axis | Budget (hero) | Budget (NPC) | Source |
|---|---|---|---|
| Triangles | ≤80,000 | ≤20,000 | §1.3 ranges `[S]` |
| Materials | ≤4 | ≤2, shared atlas | `[S]` |
| Textures | 2048 body / 2048 head / 1024 parts; 4096 hero option | 1024 | `[S]` |
| Bones | ≤150 incl. part modules; 30–60 core preferred | ≤40, no fingers | `[S + E]` |
| Influences | ≤4 | ≤4 | Unity default `[S]` |
| Morphs | ≤32 runtime (expressions/visemes); customisation baked at spawn | ≤8 | memory practice `[E]` |
| LODs | 3–4, ~50% steps | 3 | engine practice `[S]` |
| Fur | Cards; strands only as cinematic variant | baked shading | `[E]` |

### 2.6 `print` — STL/3MF (figurine + fursuit)

No tri/material/bone budgets exist; the budget axes are physical.

| Axis | Figurine (resin) | Figurine (FDM) | Fursuit head (life-size) |
|---|---|---|---|
| Triangles | resolution-driven; chord deviation 0.01–0.05 mm `[S]` | same, detail below 0.4 mm is wasted | same |
| Watertight / manifold | **required** `[S]` | **required** `[S]` | **required**; jaw as separate shell |
| Min wall after strength pass | ≥0.6 mm; ≥2.0 mm handled features `[S]` | ≥1.2 mm; ≥2.0 mm handled `[S]` | ≥2.0 mm shell; hinge/pin features ≥3 mm `[E]` |
| Scale presets | 32 mm, 75 mm, 120 mm `[E]` | 75 mm+ recommended (thin features fail at 32 mm `[S]`) | real size (~1:1 head); teeth plates as separate STLs (blueprint §11.5) |
| Materials / textures | none (single colour); 3MF colour optional | none | none; coat region map exported as pattern-guide PNG |
| Bones / morphs | n/a — posed, fused, sliders baked at export pose | n/a | jaw separated + hinge pin holes option (blueprint §11.5) |
| Strength pass | auto-thicken sub-minimum features, **reported, never silent** (HF7) | same | same |
| Fur | n/a (surface texture only) | n/a | n/a — fabric step |

---

## 3. Cross-profile rules (all targets)

1. **Influences ≤4 everywhere real-time.** SL hard-caps it, Unity
   defaults to it, glTF practice assumes it. The authoring rig may
   use more; every real-time profile prunes + renormalises at export
   and reports the prune `[S-grounded]`.
2. **Morphs are memory, not a count.** One morph ≈ one full set of
   per-vertex deltas. Profiles therefore cap *exported unbaked*
   morphs and bake the rest — the blueprint's default (baked shape,
   targets on request) is the budget-compliant behaviour, not a
   limitation. SL is the extreme case: zero survive.
3. **LOD ratios are shared.** ~100 / 50 / 25 / impostor across SL,
   indie, and WebGL profiles; only the LOD0 ceiling and the impostor
   floor differ (SL Lowest ≤300 tris `[blueprint]`, WebGL LOD2 ≈25%).
4. **Texture memory is the silent budget-breaker.** A single 4096
   texture ≈ 89 MB VRAM with mips — over the *entire* VRChat PC Good
   texture budget by itself. Texture-size cells in §2 are derived
   from the memory rows, and the gauntlet should check memory, not
   just dimensions `[E, arithmetic from §1.4's 2048 ≈ 22 MB]`.
5. **Materials before triangles on mobile.** Draw calls and shader
   switches dominate phone cost (§1.3); every mobile profile spends
   its discipline on slots first.
6. **Fur is a profile decision, never a default.** Strands exist only
   in BLEND interchange; cards are budgeted inside the tri rows;
   mobile-Good and print get baked/pattern representations instead.
7. **Conformance flags ride along.** A character that only fits a
   profile after extreme-slider baking keeps the blueprint's
   `extreme` flag; a profile report must state what was baked,
   merged, or dropped (blueprint §11.0 step 5) — a budget met by
   silently deleting the tail is a failed export, not a pass.
8. **Titan scale is legal but not free.** Oversize characters pass
   SL's 64 m hard cap easily and VRChat's bounds thresholds poorly
   (Poor at >5×6×5 m bounds `[S]`); scale is a character decision the
   report must surface, not an exporter surprise.

## 4. What the QA gauntlet should check per profile `[E]`

Extends the existing whole-library gauntlet (parse / NaN / skin /
contract / scale) with profile gates:

- **All real-time:** tri count per profile row; influences ≤4 after
  prune; texture *memory* total; morph count exported vs baked list.
- **SL:** per-mesh joints ≤110 post-mapping; materials ≤8 per mesh
  post-atlas; tris per material face ≤21,844; 4 LODs present, Lowest
  ≤300 tris; no stray ancestor joints in part exports.
- **VRChat-style:** predicted rank computed from the §1.1 tables and
  printed in the report (the exporter knows the rank before Unity
  does); mobile profile additionally checks the hard component caps
  and the ≤10 MB compressed size.
- **WebGL:** GLB ≤5 MB; KTX2 present; LOD set present; draw-call
  estimate ≤12.
- **Print:** manifold check; minimum-wall scan after the strength
  pass; scale in mm verified against the chosen preset (the library
  already owns a 30,571 m toriel head — unit discipline is not
  theoretical).

## 5. Sources

- VRChat, *Performance Ranks* (official creator docs; PC + mobile
  threshold tables, face-tracking stats, blocking behaviour) —
  https://creators.vrchat.com/avatars/avatar-performance-ranking-system/
- VRChat, *Avatar Optimization Tips* —
  https://creators.vrchat.com/avatars/avatar-optimizing-tips/
- VRChat, *Android / Quest Content Optimization* (10 MB avatar cap,
  ≤1k texture guidance, 10k-tri avatar aim) —
  https://creators.vrchat.com/platforms/android/quest-content-optimization/
- Second Life Wiki, *Limits* (mesh caps: 65,536 verts/LOD, 110 bone
  weights per mesh, 8 materials, 1024 clothing textures, 174,752-tri
  importer behaviour) —
  https://wiki.secondlife.com/wiki/Numerical_limits_within_the_Second_Life_world
- Second Life Knowledge Base, *Enhanced Skeleton (Project Bento)*
  (110-joint rigging cap, partial skeletons, Collada requirement) —
  https://community.secondlife.com/knowledgebase/english/enhanced-skeleton-project-bento-r773/
- Second Life mesh economics (LI = max of download/physics/server
  weights; L$10 base upload fee; worn attachments exempt from parcel
  LI) — SL Wiki *Mesh* cost pages via community documentation, plus
  fee reporting in §1.2's cited coverage.
- Unity Manual, *Modeling characters for optimal performance* and
  *Importing skinned Meshes* (single skinned renderer, 4-influence
  default, bone-count solve cost) —
  https://docs.unity3d.com/2020.1/Documentation/Manual/ModelingOptimizedCharacters.html
- Mobile/indie production ranges — GameAssetly, *Optimize 3D Assets
  for Mobile Games* (hero 5–15k tris, 1–2 materials, 30–60 bones);
  Oxodi, *Polygon Budgets for Mobile Games* (characters 3–15k,
  ~30–60 bones, 4 influences) —
  https://gameassetly.com/optimize-3d-assets-for-mobile-games/ ·
  https://www.oxodi.com/blog/polycount-budgets-for-mobile-games.html
- Web GLB practice — *How to Optimize GLB Files for the Web* (texture
  VRAM ≈22 MB at 2048 RGBA, meshopt-vs-Draco morph behaviour, KTX2
  VRAM savings) — https://app.cinevva.com/guides/optimize-glb-for-web
- Print rules — Additive Inn, *3D Printing Design Rules* (wall
  thickness by process, hollow shells, drain holes) —
  https://www.additiveinn.com/blog/how-to-prepare-3d-files-for-3d-printing ·
  Pookie Prints, *Prepare Your STL File* (watertight definition,
  1.2 mm structural FDM rule) — https://pookieprints.com/prepare-stl-file
- Internal: APP_BLUEPRINT §10.5, §11.0–11.5; HEROFORGE HF7;
  BODY_PLANS §1, §5 (Bento facts + SL profile rules); PARTS_STANDARD
  (128-point authoring pool); fur-prototype QA (card LOD tri counts).
