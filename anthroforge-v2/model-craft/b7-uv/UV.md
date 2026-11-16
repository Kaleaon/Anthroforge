# B7 — UV Unwrapping Strategy for Anthro Bodies

*Model-craft wave, brief B7: seam placement, texel density, UDIM vs single
atlas, mirror symmetry. The original agent died after the measurement pass;
this doc is the finisher's reconstruction from its surviving artifacts.*

**Provenance — what is whose work**

| Artifact | Author | State |
|---|---|---|
| `work/measure.py`, `work/metrics.json` | original B7 agent | ran; all §2 numbers come from `metrics.json` |
| `work/reunwrap.py` | original B7 agent | **written but never run** — no outputs existed. Finisher ran it 2026-11-13 (Blender 5.2.3, ~3 s); results in `work/reunwrap.json`, mesh in `work/head_reunwrap.blend` (§4) |
| `work/symcheck.py`, `work/symcheck.json` | finisher | tests the *second* mirror convention the original symmetry test missed; it changes a headline conclusion (§3.3) |

All work was read-only against source assets; re-unwrap outputs are new files
in `work/`. Disk held at 56 GB free throughout.

---

## 1. Method (from `measure.py`)

Per-face UV quality is computed from the singular values (s1 ≥ s2) of the
per-face 3D→UV Jacobian:

- **density** = s1·s2 per face, normalised by the object's median (so 1.0 =
  typical for that object; this is *relative* density, texture-free — the
  absolute texels/m version is B3's metric, §3.2);
- **density CV** = std/mean of relative density; **outside-band %** = faces
  below 0.5× or above 2× median density;
- **L2 stretch** = sqrt((s1²+s2²)/2) / sqrt(median density) — 1.0 is perfect;
- **conformality** = s1/s2 — 1.0 is angle-preserving;
- **islands** = connected components under shared UV edges;
- **symmetry** = for up to 4,000 sampled vertices, find the sagittal mirror
  partner by KD-tree (partner within 1% of model scale) and compare UVs.

Sample (chosen by the original agent): the lineup **border collie**
(3 sub-objects, literally named `0`/`1`/`2` in the GLB), the Codaj
**anthro fennec** rig (single measured object `Object_113`), and **our own
base head v3** (`neutral_base_head_v3.glb`, 5 named parts).

## 2. Findings per model

### 2.1 Purchased/study models — nobody is texel-uniform, big bodies are worst

| Object | Tris | Islands | Tile share (Σ UV area) | Density CV | p10–p90 | Faces outside 0.5–2× | L2 RMS / p95 | Conformal p95 | Conf. >2 |
|---|---|---|---|---|---|---|---|---|---|
| collie `0` | 7,084 | 13 | 0.500 | 0.754 | 0.45–2.02 | 23.2% | 1.113 / 1.725 | 1.76 | 2.5% |
| collie `1` | 1,411 | 11 | 0.437 | 0.596 | 0.64–1.35 | 10.5% | 1.077 / 1.324 | 2.04 | 5.0% |
| collie `2` | 634 | 6 | **0.000** | — | — | 100% | — | — | — |
| fennec `Object_113` | 78,860 | **70** | 0.297 | 0.764 | 0.51–4.16 | **50.7%** | 1.600 / 2.473 | 3.29 | **54.7%** |

- Collie object `2` (360 verts) ships with **no UVs at all** — 100% zero-area
  UV faces. (Its identity isn't recoverable from the data; the GLB names are
  numeric.) Even in a finished commercial asset, a sub-part can be silently
  un-unwrapped.
- The fennec is the cautionary tale: **half its surface sits outside a
  0.5–2× density band** and over half its faces have conformal ratio > 2.
  This is what an un-gated auto-atlas looks like — fine for a study rip,
  unusable as a texturing base.
- Every UV in the sample lies inside the 0–1 tile (`outside_tile_frac` =
  0.0 everywhere). **Nobody in the sample uses UDIMs or tiling.**

### 2.2 Our own base head v3 — good small parts, two real defects

| Part | Tris | Islands | Tile share | Density CV | Faces outside band | L2 RMS | Conf. p95 |
|---|---|---|---|---|---|---|---|
| TissueHead | 1,828 | 4 | 0.083 | 0.443 | 9.7% | 1.074 | 2.07 |
| TeethArcade | 1,368 | 10 | 0.730 | **0.293** | 3.4% | 1.016 | 1.50 |
| Tongue | 880 | 2 | 0.184 | **0.297** | 7.0% | 0.982 | 1.60 |
| Jaw | — | — | — | — | — | — | — |
| Ear_L | — | — | — | — | — | — | — |

- **Defect 1: `Jaw` and `Ear_L` have no UV layer at all** (`uv: null` —
  `measure.py` found no active UV layer on import). The jaw and ears of our
  flagship base head cannot be textured, full stop. (Ear_R was not in the
  measurement job list; same risk, unverified.)
- **Defect 2: the parts are not a packed atlas.** Each part lives in its own
  0–1 space with wildly disproportionate tile share: TeethArcade (984 verts)
  claims 0.730 of a tile while TissueHead (1,023 verts) claims 0.083 — an
  ~8.8× share skew between similar-sized parts of the same head. Give each
  part an equal texture and the teeth get nearly an order of magnitude more
  texel share than the face. This is B3's library-wide disease (§3.2) at
  intra-head scale.
- The small parts are otherwise the best-measured surfaces in the whole
  sample (CV ≈ 0.29, L2 ≈ 1.0). TissueHead is middling: CV 0.443, and only
  8.3% tile occupancy — most of its texture budget is empty space.

## 3. Cross-cutting findings

### 3.1 Texel density: two different CVs, both bad news

B7's density CV is *within one object, relative to its own median*. B3's
texel CV (`b3-qa/QA2.md` §4) is *across primitives within a file, in absolute
texels/m* (from embedded texture dimensions). They measure different failure
modes and both fire across the library:

- **B3: 21 of 33 measurable files have cross-primitive texel CV > 0.5** —
  face textures resolving several times finer or coarser than body textures
  on the same model. Worst: persipia 1.65, otter-chan 1.21, Pyn_v3 1.04.
  House styles differ by two orders of magnitude (Kaleaon family ≈ 12–16k
  texels/m per primitive vs the collie's ≈ 650), which silently breaks any
  part mixed across models.
- **B7: within-object CV runs 0.44–0.76 on every body-sized surface
  measured**; only our teeth/tongue (≈0.29) are tight.

A standard has to gate both levels (§5, U5/U6); gating only one leaves the
other free to drift.

### 3.2 Mirror symmetry — the convention matters, and ours is shared-texel

MARKINGS.md (line 127) makes a load-bearing assumption:

> "`mirror: true` mirrors the layer across the sagittal plane *in UV space*
> — valid only because our bases' UV layouts are symmetric by authoring
> rule (add to base-mesh checklist: **head/body UVs must be
> mirror-symmetric** or mirrored decals land wrong…)"

"Mirror-symmetric" has **two different concrete meanings**, and the original
agent's `symmetry()` tested only one of them:

- **(S) shared-texel:** mirror partners have *identical* UVs (u_j = u_i).
  Overlapping islands; a mirrored marking is automatic.
- **(P) centre-mirrored pairs:** partners sit at u_j = 1 − u_i, same v.
  Separate islands; mirroring a marking = reflect u → 1 − u in UV space.

The original test (convention P only, from `metrics.json`) reads like a
disaster: collie 0.0%, fennec 0.1%, **our TissueHead 3.8%** of pairs within
0.02. The finisher's `symcheck.py` tested both conventions on the same
meshes (`work/symcheck.json`):

| Mesh | (S) shared-texel within 0.02 | mean Δu / Δv (S) | (P) centre-mirror within 0.02 |
|---|---|---|---|
| collie `0` | 2.0% | 0.280 / 0.126 | 0.0% |
| fennec `Object_113` | 13.3% | 0.076 / 0.118 | 0.1% |
| **head v3 TissueHead** | **94.0%** | **0.024 / 0.008** | 3.8% |
| head v3 after house re-unwrap (§4) | 5.9% | 0.212 / 0.182 | 0.4% |

Conclusions:

1. **Our head v3 IS mirror-symmetric — under convention S.** 94.0% of
   mirrored vertex pairs share UVs within 0.02, consistent with QA2 §5's
   finding that the Kaleaon/Pyn bodies double-claim 0.87–0.98 of UV area
   (the shared-texel strategy). The house convention is shared-texel
   everywhere we've measured our own work. MARKINGS' assumption **holds**
   for the head — but only because the convention is S; read with the wrong
   test, it looks broken. Any future checker must test the *declared*
   convention.
2. **Neither purchased model offers a usable mirror layout** (collie:
   neither convention; fennec: 13.3% shared — some parts mirrored, most
   not). Mirror-dependent features (markings `mirror: true`, symmetric fur
   colour zones) cannot be assumed on third-party bases; they need the
   §5 gate per base.
3. **A naive re-unwrap destroys the property** — see §4. This is now the
   strongest constraint on the whole UV pipeline.

(Caveat: centreline vertices pair with themselves and count as passes under
S, so 94.0% is an upper bound by a few points. The conclusion is not close
enough for that to matter.)

### 3.3 UDIM vs single atlas — settled by the sample and the target

Zero of three sample files use UDIMs or any out-of-tile UVs; our delivery
target is glTF/Babylon (single texture set per material) and the fur atlas
work (A13) is already a single 2048 atlas. UDIM is a film-pipeline
convention glTF doesn't carry. **Single 0–1 tile per part set at delivery;
no UDIM.** (Untested rather than measured: no UDIM asset existed in the
library to measure — the recommendation rests on the delivery format, and
says so.)

## 4. The re-unwrap experiment (prototype run by the finisher)

`reunwrap.py` compares three unwraps of head v3's TissueHead:
**(a)** original, **(b)** Blender Smart UV Project (66°), **(c)** the
"house method": hand-marked low-visibility seams (sagittal back-of-skull
strip, under-jaw band, crown-to-back ring — 19 seam edges marked) →
angle-based unwrap → pack. Stretch stats use the same Jacobian code as
`measure.py` (its `original` row reproduces the `metrics.json` TissueHead
row exactly — a useful cross-validation of both scripts).

| Method | L2 RMS | L2 p95 | Conf. p95 | Conf. >2 | Density CV | Density p10–p90 |
|---|---|---|---|---|---|---|
| (a) original | 1.074 | 1.448 | 2.068 | 5.9% | 0.443 | 0.55–1.77 |
| (b) smart project | **1.007** | **1.083** | **1.547** | **0.0%** | **0.130** | 0.81–1.16 |
| (c) house seams + ABF | 1.006 | 1.248 | 1.726 | 3.3% | 0.653 | 0.46–1.33 |

Reading this honestly:

- **On stretch and density numbers alone, Smart Project wins outright** —
  its density CV (0.130) is better than anything measured in §2. The house
  method ties it on L2 RMS but its **density CV got worse than the
  original** (0.653 vs 0.443): the prototype's pack step did not normalise
  island scale to uniform texel density, so ABF's area variance survived
  into the atlas. That is a missing pipeline step, not a verdict on seam
  placement.
- **But the comparison is blind to what the house method exists for.** The
  stats function records no island count and no seam length/placement, so
  Smart Project's fragmentation (a 66° projection of a smooth head —
  many islands, seams across the muzzle and cheeks by construction) is
  invisible in its own winning row. Neither is seam *visibility* measured.
- **And both re-unwraps fail the mirror gate**: the house output drops
  shared-texel compliance from 94.0% to **5.9%** (§3.2). Shipping either
  output as-is would silently break MARKINGS `mirror: true` on the head.
  Smart Project was not symmetry-tested (its asymmetric projection islands
  cannot pass by construction; stated as reasoning, not measurement).

**Verdict:** the numbers say the *stretch* problem is easy; the production
problem is doing it while preserving shared-texel symmetry and seam
placement. The pipeline in §5 (U10) is the synthesis: house seam placement,
angle-based unwrap **of one half**, mirror-copy the UVs to the other half
(the sagittal seam set is exactly what makes this legal), then a
density-normalised pack, then the gates.

## 5. Recommended AnthroForge UV standard

Proposed gates are marked †; values are chosen from this sample's measured
pass/fail spread, for ratification — they are not yet canon.

- **U1 — Single tile at delivery.** Shipped assets: one 0–1 UV space per
  texture set, no UDIM, no tiling-dependent materials. (Sample: 3/3 files
  single-tile; glTF target.)
- **U2 — No UV-less parts.** Every visible or skinned part ships an active
  UV layer; a null UV layer is a QA **fail** for our own exports (the
  Jaw/Ear_L defect class; cf. QA2's graduated checks). Add Ear_R and Jaw
  re-authoring to the head v3/v4 fix list.
- **U3 — One declared mirror convention per base.** House default is
  **(S) shared-texel** — it is what head v3 (94.0%) and the Kaleaon/Pyn
  bodies (0.87–0.98 overlap) already do, and it makes MARKINGS
  `mirror: true` a no-op rather than a transform. Convention (P) is legal
  only if declared in the base record, because the markings mirror op
  differs per convention. **Gate†: ≥90% of mirrored vertex pairs within
  0.02 under the declared convention** (`work/symcheck.py` is the gate
  tool). This discharges MARKINGS.md line 127's checklist item with a
  number instead of an intention.
- **U4 — Pack parts as one atlas, density-normalised.** A character's
  parts pack into a shared atlas with island scaling normalised to the
  character's target density — tile share proportional to surface area,
  not per-part 0–1 spaces (the teeth-vs-tissue 8.8× skew is the
  anti-example). Packing without the normalisation step is the §4 house
  prototype's failure (CV 0.653); the step is mandatory.
- **U5 — Within-object density gate†:** CV ≤ 0.35 and ≤10% of faces
  outside the 0.5–2× band. (Teeth 0.293 / tongue 0.297 pass today;
  TissueHead 0.443 and every purchased body fail → re-unwrap queue.)
- **U6 — Cross-part absolute density gate†:** each delivery class (hero /
  lineup / mini-app) declares a texels/m target; cross-primitive texel CV
  ≤ 0.5 across a character's parts (B3's metric — advisory library-wide
  today, proposed as a fail for our own exports once class targets exist).
- **U7 — Stretch gate†:** L2 RMS ≤ 1.10, conformal p95 ≤ 2.0, conformal
  >2 fraction ≤ 5%. (Both §4 re-unwraps pass; the fennec fails all three.)
- **U8 — Seam canon (anthro).** Seams belong: along the sagittal line at
  the *back* of the skull; under the jaw/chin; in the crown-to-back ring
  behind the ears; down the spine; on inner arm / inner leg; under the
  tail base; and on existing material boundaries wherever they exist
  (paw-pad rims, nose-leather edge, inner-ear boundary, lip line). Seams
  never cross: muzzle front, cheek planes, brow, chest front, or any
  region a markings generator draws continuous pattern across. On
  short-fur zones (<~10 mm coats, A14) texture seams stay visible — seam
  discipline matters most exactly there; under long fur, flow direction
  matters more than the seam itself.
- **U9 — Islands upright.** Keep island V ≈ anatomical up (head v3
  already behaves: mirror-pair Δv = 0.008). Fur-flow fields (A7
  `FURP_direction`, A11 shaft banding) and markings generators read V as
  "up the body"; a rotated island silently corrupts them.
- **U10 — Re-unwrap pipeline (the §4 synthesis).** House seam set →
  angle-based unwrap of one sagittal half → mirror-copy UVs to the other
  half → density-normalised pack (U4) → gates U3/U5/U7 before the asset
  may replace the old UVs. No re-unwrap ships on stretch numbers alone.

## 6. Honest limits

- **Sample size is three files**, one symmetry object per file, chosen by
  the original agent before it died. Purchased-model conclusions are
  indicative, not library-wide (B3's 68-file sweep is the library-wide
  instrument; where the two overlap, they agree).
- The collie's sub-object identities are unrecoverable (numeric GLB names);
  object `2`'s missing UVs are a fact, its role is not.
- "No UV layer" for Jaw/Ear_L means no *active* UV layer in the glTF
  import; Ear_R was never in the job list and remains unmeasured.
- §4's comparison covers stretch/density only — the prototype never
  counted islands or seam length, so seam-visibility claims for either
  method are argued from construction, not measured. Smart Project's
  symmetry was not run (see §4).
- The house seam set is a heuristic sketch (19 edges from coordinate
  bands), not an edge-loop-aware production seam set; U8 is the canon it
  was sketching toward.
- B7 density is median-relative per object; absolute texels/m needs
  textures (B3). The two CVs must not be conflated or averaged.
- The 94.0% shared-texel figure is an upper bound by a few points
  (centreline self-pairs, §3.2 caveat).
- UDIM was recommended against on delivery-format grounds; no UDIM asset
  existed to measure.

## 7. Artifact index

- `work/measure.py` + `work/metrics.json` — original agent's measurement
  pass (source of all §2/§3.1 numbers and the convention-P symmetry rows).
- `work/reunwrap.py` — original agent's prototype, unrun until this pass.
- `work/reunwrap.json` + `work/head_reunwrap.blend` — its outputs
  (finisher-run, 2026-11-13).
- `work/symcheck.py` + `work/symcheck.json` — finisher's two-convention
  symmetry check (source of §3.2's table).
- Cross-refs: `../b3-qa/QA2.md` §4–§5 (absolute texel CV, overlap);
  `../../MARKINGS.md` line 127 (the mirror assumption this doc gates);
  `../b8-baking/` (baking inherits whatever UV standard lands here).
