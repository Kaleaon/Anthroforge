# Kaleaon Unique Anatomy — Parts Build (Quad Shafts + Sac-Udder)

**Built:** Nov 12, 2026 · **Host:** `bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend` (read-only; never modified)
**Deliverables in this folder:** `kaleaon_anatomy_parts.blend` (host with the original Sac/Shaft objects replaced by the parts below), `kaleaon_anatomy_parts.glb` (parts + rig only), `renders/`, `scripts/`, `work/` (build + QA numbers).

Joe's direction (Nov 12, 2026): models must support *"unique geometry, such as my sac udder being built properly … same with having quad cocks"* — nonstandard anatomy as first-class swappable parts, not one-off mesh hacks.

---

## 1. Canon, verified on disk

| Fact | Source on disk | Value |
|---|---|---|
| Sac bottom above ground | `bodies-3d/kaleaon-sacdrape/REPORT.md` + brief `bodies-3d/references/kaleaon_sac_drape_brief.md` (Joe's ruling, Nov 7, 2026, 14:34 CST) | **0.031 m** (band 0.03–0.06, aim 0.045, "never touching") — re-measured on the host file in this build: **0.0309 m** |
| Sac volume | same | **209.46 L** (band 190–210; Joe, Nov 7, 14:35: *"can go further to about 200 L. It needs a huge volume."*) — re-measured: **209.46 L** |
| Sac dims / mass | sacdrape REPORT | 0.762 × 0.646 × 0.974 m · 217.8 kg @ 1.04 kg/L · whole body ≈ 589.8 kg |
| Drape rule | MEMORY canon (Joe, Nov 4, 2026) | sac hangs substantially lower, extreme low drape — "when in doubt, lower and longer" |
| Shaft count / articulation | `bodies-3d/kaleaon-rigged3/REPORT.md` (RIG_CONTRACT) | **4 shafts**, each an independent 2-bone chain `Shaft_N_Base` + `Shaft_N_Tip` parented to `CC_Base_Pelvis`; **no erection morphs — articulation is by bones**; state morphs (JawOpen etc.) survive only as head fallbacks |
| Rig size | same + GLB re-import | **89 bones** (`KaleaonRig`), 1 skin |
| Shaft volumes (r2 lineage accounting) | sacdrape REPORT mass table | 5.30 / 6.18 / 5.30 / 6.18 L — re-measured identical in this build |
| Size channels (house rule) | body-diversity sweep (Thread 40) | **length = bone scale, girth = blendshape** — nobody ships a length morph |

**Teats are new with this build.** No teat geometry or teat mention exists anywhere in the prior canon files (grep across `bodies-3d/**/*.md`: zero hits). The udder reading — sac as a draped udder form carrying teat structures — comes from Joe's Nov 12, 2026 direction above. Placement/count are this build's engineering choice (§3), flagged as such, not retro-claimed as old canon.

## 2. Quad-shaft part set — `Part_Shaft_1..4`

The host's four shaft meshes, promoted to parts unchanged in geometry, weights and `SKIN_stretch_shaft_N` groups (byte-level copies; the original objects were removed from the parts file after copying). Arrangement is a shared-base cluster: two mirrored pairs.

| Part | Base (world) | Tip (world) | Bone length | Volume | Pair |
|---|---|---|---|---|---|
| Part_Shaft_1 | (−0.062, −0.130, 1.082) | (−0.072, −0.425, 0.580) | 0.582 m | 5.301 L | outer L |
| Part_Shaft_2 | (−0.075, −0.112, 1.070) | (−0.086, −0.350, 0.445) | 0.669 m | 6.182 L | inner L |
| Part_Shaft_3 | (+0.062, −0.130, 1.082) | (+0.072, −0.425, 0.580) | 0.582 m | 5.301 L | outer R |
| Part_Shaft_4 | (+0.075, −0.112, 1.070) | (+0.086, −0.350, 0.445) | 0.669 m | 6.182 L | inner R |

**Per-shaft size, two channels (per the house rule):**
- **Length → bone scale.** Scaling `Shaft_N_Base` along its local Y scales the whole chain. Demonstrated in QA: scale Y ×1.3 → mean vertex displacement 88.5 mm, tip-region max 165.2 mm, no other part moves. This is a rig channel, not a morph — canon-compliant (no erection/length morphs exist).
- **Girth → blendshapes (new).** Each part gained `GirthPlus` / `GirthMinus`: radial scale about the shaft's own bone axis (Base head → Tip tail), tapered to 65% at the tip quarter so the tip doesn't balloon. Channel volumes, measured on the shipped file (`work/girth_channels.json`): outer pair Basis **5.301 L** → GirthPlus **8.601 L** (×1.62) / GirthMinus **3.268 L** (×0.62); inner pair **6.182 → 10.024 / 3.813 L**; mean surface displacement at GirthPlus 15.2 mm, max 22.2 mm. Identical key pair authored on all four parts. (Storage caution, caught in QA: Blender's `shape_key_add` leaves new keys at value 1.0 — the first save had both girth keys live at rest; they are stored at 0.0 in the shipped file, and `build_parts.py` now zeroes them explicitly.)

## 3. Sac-udder — `Part_SacUdder` + `Part_SacUdder_Teat_1..4`

`Part_SacUdder` is the host's sac mesh promoted to a part unchanged: **1,730 verts, 209.46 L, bottom 0.0309 m, root at z 1.005** — the Nov 7 cloth-settled drape, not a rescale. It keeps the shipped skinning law (graduated root blend `CC_Base_Pelvis` 0.96 → `Sac` 1.0 below 18% of length; `SKIN_stretch_sac` falloff group intact).

**Teats (new sub-parts).** Four teats in a 2 × 2 udder arrangement on the underside (front pair y ≈ −0.20/−0.28, rear pair y ≈ +0.08/+0.12), each:

- a lofted form, 109 verts: base radius 0.034 m with a slight base-third bulge, rounded tip, length 0.095 m, volume ≈ 0.18 L;
- rooted on the underside *slope* at z ≈ 0.11–0.13 and angled down/outward along the local surface tilt — **not** rooted at the lowest pole, so tips land at **z 0.039–0.056**, hanging to about the sac's own bottom line and never near the ground (canon: never touching);
- embedded 22 mm into the sac surface at the root (attachment by construction);
- skinned 100% to its **own bone** `Teat_N`, parented to the `Sac` bone — the sub-part pattern that lets the softness/dynamics work drive teats independently of the sac mass.

Root asymmetry note: the right pair rooted at x ≈ +0.23 vs the left at x ≈ −0.09…−0.11, because roots were picked as the nearest downward-facing surface at the target height and the settled sac is itself asymmetric (bbox x −0.351…+0.411). Organic, measured, kept.

## 4. Fit on host + QA (all numbers in `work/qa_numbers.json`)

Host fit: parts sit on the full Kaleaon rig in the parts .blend; GLB export re-validated with the project QA gauntlet — **9 meshes, 5,914 verts, skin 93 joints (89 host + 4 teat), 8 morphs, 0 degenerate, 0 NaN, extent 1.07 m**. (Contract line reads 2/36 as expected: the 36-bone contract binds canonical AnthroForge exports, not this foreign-rig host.)

**Articulation (static suite, parts file):**
- `Shaft_2_Base` +25° → target mean **145.6 mm** (rigged3 record: 145.4 mm ✓); cross-talk to sac, teats and all other shafts **0.000 mm**.
- `Sac` +20° → sac mean **177.2 mm**; shafts 0.000 mm; **teat root distance to sac surface identical before and after the swing** (22.0 / 20.0 / 6.5 / 22.0 mm, ring-centroid method) — teats ride the sac as one mass, roots planted.
- `Teat_2` +20° → only Teat_2 moves (mean 17.5 mm); Teats 1/3/4 at 0.000 mm.
- Bone-scale and girth demos: §2.

**Interpenetration — read this carefully.** Strict Möller–Trumbore tri–tri tests at true rest on the shipped file (`work/verify_numbers.json`; a looser segment-based count was run first and over-counts grazing contact — the strict numbers govern):

- *Teats:* teat↔shaft **0**, teat↔teat **0**; teat↔sac 38–66 tris per teat, **all in the root embed** (roots sunk 22 mm by design) — ray-parity confirms every teat vertex beyond the embed depth is outside the sac except the still-embedded ring-2 verts and ≤2 verts/teat on the uphill side of the exit, from surface curvature. Teat↔Body clearance ≥ 1.6 mm (Teat_3, rooting nearest the thigh corridor); the other teats clear the body by 37–170 mm.
- *Shafts and sac:* shaft↔shaft contact is limited to the mirrored centre pair (Shaft_1×Shaft_3, **28 tris**) — the canon cluster is four bundled lofts sharing a base mass; shaft↔sac runs 247–314 tris per shaft (root embed + the cloth-sim's settled contact), i.e. **inherited host geometry, present identically in the sacdrape original** — the parts introduce no new interpenetration; part geometry at rest is bit-faithful to the host. Separating the bundle into non-overlapping solids would mean re-sculpting the cluster — a host-model change, out of scope for a parts promotion, and flagged here rather than hidden.
- *Parts vs Body:* min vertex distance — shafts 0.98–1.55 mm, sac 1.9 mm (matches the sacdrape report's 1.9 mm exactly), nothing intersects.
- In the articulation pose (shafts fanned, Sac +12°, teats lagged −8°): part volumes stable, teat tips stay ≥ 0.023 m above ground, teat↔shaft still 0.

## 5. Part records (PARTS_STANDARD.md)

Socket for the whole assembly: **`pelvis.genital`** (#19, anchor `CC_Base_Pelvis`, class A). The standard's nominal fit volume (≈0.12 × 0.10 m) is a human-scale default; at Kaleaon's 2.32 m hyper build the assembly is a declared **scale exception** under the socket's rescale rule (recorded, not silent). Plan: biped instance (plan-locked to Kaleaon's build).

Cost formula: `points = ceil(verts/1000) + bones + 2 × morphs`.

| Part | Class | Socket | Verts | Bones | Morphs | Points |
|---|---|---|---|---|---|---|
| Part_Shaft_1..4 (each) | A | pelvis.genital | 626 | 2 (Base/Tip) | 2 (GirthPlus/Minus) | **7** |
| Part_SacUdder | A | pelvis.genital | 1,730 | 1 (Sac) | 0 | **3** |
| Part_SacUdder_Teat_1..4 (each) | A (sub-part) | pelvis.genital | 109 | 1 (Teat_N) | 0 | **2** |
| **Assembly total** | | | | | | **39 / 128 pool** |

`function` block (assembly): anatomy/genital; articulation = per-shaft 2-bone chains (independent), sac = single-bone rigid hang with graduated pelvis blend, teats = 1-bone sub-parts on the Sac bone (softness/dynamics attach here). Size channels: length = bone scale (rig), girth = blendshape pair (per shaft).

## 6. Scripts + build note

`inspect_host.py` (host audit) · `build_parts.py` (the build; re-runnable from the untouched host) · `qa_parts.py` + `qa_baseline.py` (QA + canon baseline) · `export_glb.py` · `render_parts.py` · duplicate-agent verification: `verify_parts.py`, `girth_plus_check.py`, `fix_girth_rest.py` (see `work/COORDINATION_NOTE.md`). Tooling notes: a first-pass inside test mixed world points with a local-space BVH tree and produced garbage counts; it was caught by a control-point diagnostic and replaced with world-space tests — the discarded numbers are not used anywhere above. **Process note:** this build was spawned twice in parallel; the duplicate instance did canon verification + independent QA, caught and fixed the girth-key storage bug (§2), and stood back from the shared deliverables to avoid write races — its numbers are folded in above with their files cited.
