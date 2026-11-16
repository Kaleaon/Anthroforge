# Gravity, sag, and paintable body weights

*AnthroForge first-proof follow-up — Nov 12, 2026. Companion to `PROOF.md` (v1). Joe's direction, reacting to the v1 render: "a belly doesn't go straight out, it sags, so shape weight/skin weight needs done right. Look into paintable body weights."*

**Verdict up front: belly v2 hangs.** Same forward anchor as v1 (error ≤1.3 mm), but the navel now also migrates **2.95 cm down** at +1, the profile apex sits below the navel, the top slope flattens, and the lower rows drop and tuck into an under-belly crease — see `renders/belly_v1_vs_v2_+1_profile.png`. The hang is moderate, not theatrical, which is correct for a 12 cm belly: this is the source morph's size class, not an apron belly. v2 is fold-free at +1 on both bases and at the coupled +0.5 state.

---

## Part 1 — Paintable body weights as a discipline

### Two different things are both called "weight"

| | **Skin weights** (skinning / envelope weights) | **Shape weights** (mobility / influence fields) |
|---|---|---|
| Question answered | *Which bone moves this vertex, and how much?* | *How much does this flesh behaviour apply at this vertex?* |
| Lives on | rig + mesh (per-bone vertex groups) | morph / slider record (per-effect field) |
| Painted in | Blender Weight Paint per bone group | Weight Paint on effect groups (dForce influence, Chaos masks, our mobility) |
| Failure mode if wrong | rigid candy-wrapper bends, creases at joints | uniform rubber deformation; protrusions that ignore gravity |

They **interact**: a sagging belly needs both. The mobility field makes the *shape* hang; the skin weights must then let the hanging mass *follow* pose — a belly weighted rigidly to the pelvis bone will swing like a board when the spine bends, and one weighted wholly to the spine will shear at the waistband crease. Production practice splits the hanging region's skin weights across pelvis/spine in proportion to how far the tissue hangs — which is exactly the mobility field reused as a blending prior. AnthroForge rule: **derive initial skin weights in mobile regions from the mobility field; never let the two fields contradict each other.**

### Painted mobility maps are the industry pattern

Every serious soft-tissue pipeline converges on the same object: a **per-vertex painted scalar field** that says how free the flesh is at each point, used to modulate a deformation.

- **Framestore's fcJiggle** (built for *The Golden Compass*, still the canonical write-up): TDs **painted parameter maps** per character region — where soft tissue is, how deep it is, spring and damping values per tissue type (fat vs muscle vs skin). The simulated layer is then blended back over the skinned mesh. The lesson that survives every implementation since: *uniform softness looks wrong; painted, region-varying parameters are what read as flesh.*
- **The jiggle-map blend** (Sébastien Vaillant's widely-copied formulation): `final = p·(1−w) + jiggled·w`, where `w` is a painted jiggle weight per vertex. The deformation can be simulated, sculpted, or — our case — analytic; the *field* is the authoring surface.
- **DAZ dForce**: cloth/hair simulation driven by painted **Influence Weights** and surface **Dynamic Strength** maps (Node Weight Map Brush; red = 100% simulated, blue = 0%). Their own docs warn "a little goes a long way" — the field's dynamic range matters more than its resolution.
- **Unreal Chaos Cloth**: artists paint **Max Distance** (0 = glued to the skinned mesh — the anchor), stiffness masks, and collision masks. Same pattern, game-side.
- **Blender**: cloth and soft-body **pin groups are vertex groups**; goal/pin weights are paintable per vertex. Simulations are baked through the point cache, and a sim becomes a slider only via an MDD/PC2 round-trip or per-frame shape-key sampling — FBX cannot carry per-frame cloth deformation into a target-based pipeline.

**What transfers to a slider pipeline cheaply, and what doesn't:**

- ✅ *Painted field × analytic deformation* (what v2 does): the field is data, the deformation is a formula, the result is an ordinary `.target`. Zero runtime cost, fully slider-native, repaintable by a human.
- ✅ *Field-driven post-corrections*: fold repair by turning the field's effect down locally ("attenuation", §2.4) is literally the dForce/Chaos artist workflow, automated.
- ⚠️ *Sim-bake to shape keys*: gives one true simulated pose per slider stop, but the bake is state-dependent (a belly sim at +1 doesn't interpolate to +0.5), expensive per slider, and doesn't survive base changes. Keep as a future *authoring* aid for hero sliders, not the pipeline.
- ❌ *Full FEM tissue (Weta Tissue et al.)*: muscle+fat finite elements are the quality ceiling and completely out of scope for a morph tool.

### The mobility field, defined

For AnthroForge a **mobility field** is a per-vertex scalar `m(v) ∈ [0,1]` attached to a morph (or morph family):

- **Anchors (`m → 0`)**: ribcage brim, sternum, spine line, pelvis brim, anywhere tissue is bound to bone or fascia.
- **Free tissue (`m → 1`)**: lower belly apron, chest mass, jowls, upper arms — wherever flesh actually travels.
- The field modulates any gravity-aware deformation: downward translation, sub-crease tuck, jiggle amplitude, and (per above) skin-weight blending priors.

It is authored three ways, in increasing order of authority: **procedural seed** (anatomy rules, this proof) → **human repaint** (the paintable blend, §3) → **learned** (fields fitted from studied sources, future).

---

## Part 2 — Belly v2: the gravity pass

### 2.1 Model (3 lines)

`shape(w) = base + w·Δ_protrusion + f(w)·Δ_sag`, with nonlinear coupling `f(w) = sign(w)·|w|^1.7` (so `f(0.5) ≈ 0.31`, `f(0) = 0`). `Δ_sag` displaces the v1 field's own protrusion **downward** in proportion to a painted mobility field and to each vertex's outward travel (`Δ_z = −m·p·(0.40 + 0.12·umbilical)`), and **tucks the rows below the crease line inward** (`Δ_radial = −m·0.35·p·gate`), the crease sitting 0.13 torso-units below the navel. Hosts without coupling support load the pre-combined `body.belly.protrusion_v2.target`, which is exactly the +1 shape.

### 2.2 The mobility seed (procedural, before any repaint)

`m = morph_mask × angular × vertical × mass`, then 6 graph-Laplacian smoothing passes:

- **angular**: `clip((cosθ + 0.35)/1.35)` — front-weighted, fading around the flanks, zero at the back.
- **vertical**: peak on a Gaussian centred just *below* the navel (`h* − 0.06`, σ = 0.15 torso units), cut by a ribcage taper (full below `h = 0.62`, zero above 0.70) and a pelvis taper (zero below `h = 0.22`, full above 0.30) — tissue is anchored where the skeleton cages it.
- **mass**: `0.30 + 0.70·|Δv1|/max|Δv1|` over the mask core — where the morph itself says the tissue is, it can move more.

Result on hm08: max 0.896, navel 0.590, 266 verts above 0.05. The field ships as data (§3), not just as an ingredient.

### 2.3 Slope limiting and volume

- **Slope limiter**: `|Δ_sag(u) − Δ_sag(v)| ≤ 0.55 × |edge(u,v)|` on all belly edges, enforced by iterative relaxation. Diagnosed necessity: an early build put a −1.23 cm sag step across a 0.82 cm edge at the crease and sheared 11 faces inside-out — a real crease is a smooth inflection, never a vertex-scale kink.
- **Volume**: signed-tetrahedral volume proxy over the mask patch, matched between v1 and v2 by solving a radial compensation term. The solver's answer was **−0.06 cm — nil**: dropping and tucking redistributes the same tissue, so v2's patch volume equals v1's to the proxy's precision (ratio 1.000). Gravity moves mass; it doesn't create it.

### 2.4 Fold repair by attenuation (a finding worth keeping)

v1's field sits at min_dot ≈ 0.055–0.089 — almost no margin — so *any* added gradient flips marginal faces somewhere (pre-repair v2: 2 raw / 11 macro). v1's remedy, Laplacian smoothing of the combined field, **fails here**: its grow-set boundary cuts across the sag gradient and the smoothing drags boundary verts *along* the gradient, manufacturing a new −1.23 cm step at the crease (measured). The fix that converges (7 rounds): an **attenuation field** `a(v)` that turns the sag *down* locally (×0.82 on bad-face verts, ×0.94 on their ring, smoothed, floor 0.10) while preserving its direction everywhere. Final: att min 0.54, 197 verts touched. This is the dForce move — paint influence down where the surface can't take it — and it is the correct general repair for field-modulated morphs.

### 2.5 QA (all numbers from `work/qa_numbers_v2.json`, `work/blender_v2_numbers.json`)

**Anchor — now a vector.** The v1 anchor criterion was forward-only; v2's navel keeps it *and* drops:

| state | forward | down | forward error vs 0.11969 m anchor |
|---|---|---|---|
| v1 at +1 (numpy / Blender) | 11.90 cm / 12.06 cm | −0.21 cm (rises slightly) | 0.9 mm (PROOF.md) |
| **v2 at +1 (numpy)** | **11.84 cm** | **+2.95 cm** | **1.3 mm** |
| **v2 at +1 (Blender evaluated)** | **11.99 cm** | **+2.95 cm** | **0.2 mm** |
| v2 at +0.5 coupled (numpy / Blender) | 5.93 / 6.00 cm | +0.87 cm | — (31% of full sag at 50% protrusion, per γ = 1.7) |

**Folds** (belly faces, normal-dot test vs rest, v1 method):

| state | raw base | MPFB macro base | Blender evaluated |
|---|---|---|---|
| +0.5 coupled | **0** (min_dot 0.366) | **0** (0.557) | — |
| +1 combined | **0** (0.005) | **0** (0.003) | **0** / 918 belly-region faces (0.020) |
| +1.05 | 10 flips | 8 flips | outside shipped range |
| −1 (linear) | 157 flips | 142 flips | inherited v1 negative-pole problem, unchanged |

Honest margin note: v2 at +1 is fold-free but with **thinner margin** than v1 (min_dot 0.005/0.003 vs 0.055/0.089) — the sag spends most of the geometric headroom the transfer had. Fine at the shipped range [0, 1]; do not extend the range without re-running attenuation.

**Zone-split residuals** (triangle-exact, torso-param space, mask core; method identical to PROOF.md — its aggregate was recomputed as a control and reproduces: v1 p50 0.039 / p95 1.394 cm):

| zone | n | v1 p95 | v2 p95 | mean sag in zone |
|---|---|---|---|---|
| pin patch | 18 | 3.55 | 3.63 | 3.92 cm (the navel drop itself) |
| crease | 63 | 1.37 | 2.49 | 1.71 cm |
| flank | 66 | 1.51 | 1.74 | 0.68 cm |
| core | 244 | 0.25 | 1.03 | 0.43 cm |
| **all** | 391 | **1.394** | **2.375** | — (p50 0.039 → 0.117) |

Read these correctly: the residual measures distance **from the gravity-free source surface**, and v2 departs from that surface *on purpose*. The zone means show the departure is the sag itself, largest exactly where flesh should travel (pin patch / crease) and smallest in the core. This is the metric working as intended — it localises *what changed*, and what changed is gravity.

**Load test**: combined v2 target and the coupled-+0.5 field load as shape keys through stock MPFB 2.0.18 `TargetService.load_target`; measurements above are from the evaluated mesh. (Environment note for future runs: this VM's shared Blender config had its MPFB silently replaced by a newer-API build mid-session, and Workbench rendering needs a display — `scripts/test_belly_v2.py` therefore installs the zip's 2.0.18 into an isolated `HOME=/tmp/af_home` and runs under `xvfb-run`. v1's `test_mpfb.py` targets an older MPFB API and will not run as-is against either installed build.)

### 2.6 Renders

- `renders/belly_v2_w+0.0_profile.png`, `belly_v2_w+0.5_profile.png`, `belly_v2_w+1.0_profile.png` — v1's camera/lighting, helpers masked.
- `renders/belly_v1_vs_v2_+1_profile.png` — side-by-side.

**Does it visibly hang? Yes.** Against v1's high round dome (apex at the navel, underside curving back up early), v2's mass is elongated downward: longer flatter top slope, apex below the navel, underside drooping over the pelvis to roughly hand level, with a shallow crease where the tuck bites. It reads as a belly that *sits* on the body instead of a balloon glued to it. It is not a dramatic apron — at 12 cm of protrusion it shouldn't be; pushing α higher starts to look like a bigger belly class, not a saggier one. If Joe wants more hang at this size, the honest lever is the mobility repaint (raise `m` in the apron, deepen the crease gate) — the tooling for exactly that is §3.

---

## Part 3 — Paintable weights in the app (design)

### 3.1 Deliverable shipped with this proof

`body.belly.protrusion_paintable.blend` — the hm08 base carrying:

- vertex groups **`AF_mobility`** and **`AF_anchor`** (= 1 − mobility in the mask): paint targets, Blender Weight Paint semantics;
- colour layer **`mobility_viz`**: heat ramp of the same field for a fast read;
- shape keys **protrusion_v1 / sag_component / protrusion_v2** so a painter sees the effect of the field live at +1;
- text block **MOBILITY_NOTES** documenting the semantics in-file.

### 3.2 Brush semantics (app)

| brush | action on field | notes |
|---|---|---|
| **Paint Mobility** | raise `m(v)` (add, strength-scaled) | tissue here travels more: more drop, deeper crease response |
| **Paint Anchor** | lower `m(v)` toward 0 | pin tissue to skeleton; writes the complement into AF_anchor |
| **Smooth** | graph-Laplacian relaxation pass | kills vertex-scale kinks (the fold-makers of §2.3) |
| **Flood Fill** | set region (mask / selection / flood by angle) to a value | fast blocking-in of anchor zones (ribcage, pelvis brim) |
| **Attenuate** (auto) | local amplitude reduction where QA reports flips | §2.4 as a one-click repair, human-overridable |

Invariants the editor enforces: field stays in [0,1]; slope limit re-checked after every stroke batch (warn, don't block); every repaint bumps the field's revision in the slider record.

### 3.3 Storage in the canonical slider record

The record (`body.belly.protrusion.slider_v2.json`, `gravity` section) carries:

- `gravity.model` — the analytic deformation + its constants (α, β, umbilical, crease offset);
- `gravity.coupling` — `{gamma, f}` so every host applies the same nonlinear curve;
- `gravity.mobility_field` — definition, procedural seed (so any base can re-seed), stats, and the **paintable file reference**; per-base instances store the field as a **sparse vertex-weight list** (only verts with m > 0 — 266–535 entries here, kilobytes), versioned with a revision counter and author tag (`procedural-seed` / `hand-painted` / `learned`);
- components stay separate files (protrusion / sag / combined-at-+1) so hosts pick their capability tier: full coupling > two-target blend > single combined target.

### 3.4 Roadmap implied by this proof

1. **Chest, jowls, upper arm** get their own mobility fields on the same pattern (anchors differ; the machinery doesn't).
2. **Authored decrease target** for the negative pole (already owed from v1); its shape should be authored *with* the mobility field — decreasing bellies lift toward the anchors.
3. **Skin-weight derivation** for posed characters: blend pelvis/spine weights by mobility in the hang region (§1).
4. **Sim-bake as authoring aid** for hero sliders only: simulate at +1, sample to a target, keep the analytic field as the shipping form.

---

## Files

| file | what |
|---|---|
| `body.belly.protrusion_v2.target` | combined +1 field (protrusion + sag), hm08 |
| `body.belly.protrusion_sag.target` | sag component alone (pair with coupling) |
| `body.belly.protrusion.slider_v2.json` | canonical slider record v2 (gravity section) |
| `body.belly.protrusion_paintable.blend` | paintable mobility deliverable (§3.1) |
| `scripts/build_belly_v2.py` | gravity pass + full QA |
| `scripts/test_belly_v2.py` | Blender/MPFB verification + renders |
| `scripts/build_paintable_blend.py` | paintable blend builder |
| `work/qa_numbers_v2.json`, `work/blender_v2_numbers.json`, `work/belly_v2.npz`, `work/target_coupled_w0.5.target` | QA data + coupling fixture |

v1 files (`PROOF.md`, `body.belly.protrusion.target`, `body.belly.protrusion.slider.json`, v1 renders) are untouched.

*Licence: study-only, internal — same as v1. The sag pass is AnthroForge-authored analytic work (no external asset), but it is inseparable from the v1 transfer it modifies, so the v2 files inherit v1's study-only status.*
