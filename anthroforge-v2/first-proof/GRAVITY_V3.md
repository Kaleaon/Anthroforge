# Belly v3 — realistic gravity

*AnthroForge first-proof follow-up #2 — Nov 12, 2026. Companion to `PROOF.md` (v1) and `GRAVITY_WEIGHTS.md` (v2). Joe's verdict on v2, over the v1-vs-v2 side-by-side: **"needs realistic gravity, this floats too much."***

**Verdict up front: v3 hangs like a pendant mass, because it now is one in the model.** The navel is dragged **7.28 cm down** at +1 (v2: 2.95 cm; v1: it *rose* 0.21 cm). The added mass centres **9.26 cm below the navel line** (v1: 3.15, v2: 5.45). The top of the belly is **drained** — upper-belly protrusion falls from 5.68 cm (v1/v2) to **4.30 cm** — and the spatial profile shows the extent peak living at **+9 to +13 cm below the navel line**, with 10.6 cm of added extent still present at +16 cm where v1 had 5.7 and was dead by +19. The price, reported plainly in §3: the navel gives up 1.30 cm of its forward anchor, and the shipped field carries 87.5% of v1's added volume (the fold repair is the leak). Fold gate: **0 flips at +1 on both bases**, full drape factor 1.0 shipped — no bisection needed. See `renders/belly_v1_v2_v3_+1_profile.png`.

---

## 1. What changed in the model (v2 → v3)

`shape(w) = base + w·Δ_protrusion + f(w)·Δ_sag` — same decomposition, new sag field with three terms instead of one:

| term | v2 | v3 |
|---|---|---|
| **Descent** | `−m·p·(0.40 + 0.12·umbilical)` straight down | `−gain · m·p·(1 + 0.25·umbilical)`, **gain solved** (1.44) so the navel drop lands in the 7–9 cm band after repair |
| **Drain** | — (the dome kept its mass) | upper-belly rows (`h > h* − 0.02`) surrender **45%** of their outward delta, weighted mask × angular × height ramp. Mass leaves the top *because it went down* |
| **Drape** | inward tuck `0.35·m·p` below a crease at `h* − 0.13`, down-component unchanged | crease deepened to **`h* − 0.16`**; below it a ramp `t = clip((h_c − h)/0.22)^1.3` adds **0.85·m·p downward + 1.05·m·p inward** on top of a 0.30 base tuck — the motion is a hanging curve (down-dominant at the crease, tuck-dominant at the bottom), soft-floored so tissue never passes through the body surface |
| **Mobility** | peak at `h* − 0.06`, σ 0.15, floor 0.25, cap ~0.90, pelvis anchor at h 0.22–0.30 | peak **lower** (`h* − 0.10`), σ 0.16, floor **0.35**, mass factor 0.45 + 0.55·\|Δ\|, pelvis anchor lowered to **h 0.16–0.26** (tissue hangs lower than v2 allowed it to), cap 0.917, coverage 390 verts > 0.05 (v2: 266) |
| **Coupling** | γ = 1.7, f(0.5) = 0.31 | **γ = 2.0, f(0.5) = 0.25** — a drape engages late; at half size the belly mostly protrudes, the hang arrives with real mass |
| **Navel pin** | guarded micro-pin restored the forward anchor | **no pin.** The forward anchor is reported as the true vector (see §3) |

**Gain iteration (the honest knob):** attenuation repair taxes the navel drop, and the tax grows with field strength — solve targets 8.0 / 9.8 / 11.5 cm shipped 6.2 / 6.6 / **7.28 cm**. The shipped solve aims at 11.5 pre-repair on purpose. If Joe wants more (or less) hang, this one number is the dial; everything else follows.

## 2. The numbers (numpy canonical frame; Blender cross-checks agree)

**Navel anchor — now a trade, not a point:**

| state | forward | down |
|---|---|---|
| v1 at +1 | 11.90 cm | **−0.21 cm (rises)** |
| v2 at +1 | 11.84 cm | +2.95 cm |
| **v3 at +1 (numpy / Blender)** | **10.67 / 10.80 cm** | **+7.28 / +7.28 cm** |
| v3 at +0.5 coupled (numpy / Blender) | 5.64 / 5.71 cm | +1.77 / +1.77 cm |

**Profile metrics** (per-vertex band statistics, deformed heights; method in `build_belly_v3.py`):

| metric | v1 | v2 | v3 | reading |
|---|---|---|---|---|
| mass centroid below base navel line | 3.15 cm | 5.45 cm | **9.26 cm** | where the added mass *lives* |
| mass centroid below deformed navel | 3.36 | 2.50 | 1.99 | small because the navel itself fell into the mass |
| upper-belly protrusion (drain readout) | 5.68 cm | 5.63 cm | **4.30 cm (−24%)** | the dome gave up its mass |
| crease-band pinch ratio (material) | 0.695 | 0.679 | 0.697 | inherited from the source sculpt — see §4 |
| apron bottom rows' extent (material) | 3.05 cm | 2.87 cm | 2.89 cm | bottom rows sit near the body in all versions |

**Band profile** — mean added extent (cm) by deformed height, cm below the *base* navel line:

| height | −6 | −3 | +0 | +3 | +6 | +9 | +13 | +16 | +19 |
|---|---|---|---|---|---|---|---|---|---|
| v1 | 7.8 | 11.6 | **13.8** | **14.0** | 13.5 | 11.8 | 9.5 | 5.7 | 1.4 |
| v2 | 7.0 | 8.7 | 11.6 | 13.4 | 13.7 | **13.8** | 11.7 | 7.0 | 2.3 |
| v3 | **3.7** | **5.1** | 7.3 | — | 10.3 | **13.3** | **12.3** | **10.6** | **5.6** |

v1's mass is a dome centred on the navel and gone by +19. v3's top is drained (3.7 at −6, where v1 had 7.8), its peak sits at +9…+13, and it is still carrying 10.6 cm of extent at +16 cm below the navel line. That is the difference between a balloon and an apron, in one table.

**Folds** (belly faces, normal-dot vs rest): +1 combined **0 / 0** (raw min_dot 0.0034, macro 0.046); coupled +0.5 **0 / 0**; Blender evaluated belly region **0 / 918 faces** (min_dot 0.042). +1.05 flips (15 raw / 2 macro) — outside the shipped range, as with v1/v2. −1 linear: 162 / 154 — the inherited negative-pole problem, unchanged; the decrease pole still needs its own authored target.

**Zone-split residuals** (triangle-exact, vs the gravity-free source surface — departure *is* the sag; v1 aggregate recomputed as control in v2's run): all-zone p95 v1 1.39 → v2 2.37 → **v3 3.77 cm**; pin-patch mean sag3 7.00 cm down, crease zone 3.37, core 2.07. The departure is largest exactly where flesh travels.

## 3. Cross-check against the learned fields (`scripts/crosscheck_fields.py`)

One metric set on each field's own base (belly band anchored to the field's own forward peak; AM is field-level only — its FO4 BSTriShape vertex buffer defeated the stream scanner in both float32 and float16, so no band metrics exist for it; stated, not papered over):

| field | mean downward push in band | share of band mass moving down | centroid vs own peak |
|---|---|---|---|
| **ours v3** | **−4.65 cm** | **100.0%** | +2.43 cm |
| Atomic Muscle "Nuka Bull" | −2.55 cm *(field-level)* | 84.0% | — |
| ours v2 | −2.63 cm | 97.4% | +3.60 cm |
| Fat Males (source sculpt) | −1.25 cm | 59.9% | **−2.58 cm** |
| ours v1 | −0.94 cm | 78.8% | +3.79 cm |
| HIMBO "BodyChubby" | −0.33 cm | 59.8% | +2.10 cm |

**Which real field hangs most? Fat Males** — it is the only band-measured field whose displacement centroid sits *below* its own forward peak (−2.58 cm), and its mass centroid sits 5.35 cm below its own navel line (measured per-vertex; its navel itself barely drops, 0.87 cm — the sculpt hangs the mass *around* a stable navel). HIMBO BodyChubby barely hangs at all: −0.33 cm mean push and a centroid *above* its peak — it rounds upward, a dome-builder, the same disease Joe called out in v2. Nuka Bull pushes down hard (−2.55) but as a whole-body transformation, not a belly-local one.

**How v3 compares:** by downward push and by share-of-mass-moving-down, v3 exceeds every learned field. By mass-centroid-below-navel, **v3 (9.26 cm) now hangs past the Fat Males sculpt itself (5.35)** — v2 (5.45) had matched it almost exactly. That is deliberate (Joe asked for *more* gravity than the source shows), but it means v3 is no longer "the source, corrected" — it is a stronger-gravity variant of it, and the gain is the dial if it overshoots on the body Joe has in mind. By centroid-vs-own-peak ours stays positive (+2.43) even in v3: the v1 navel pin made the navel row the peak, and the mask's drained-but-present upper rows still anchor the centroid high. Both readings are in the record; neither is hidden.

## 4. Honest self-critique

- **The forward anchor trade is real.** The navel keeps 10.67 of 11.97 cm (shortfall 1.30 cm) — the drain pulls the umbilical region in as it drops it. I judge this correct physics (a navel buried in a falling fold does not keep its full forward travel), and the brief authorised the trade explicitly — but it *is* a regression against the v1/v2 acceptance criterion, and it is a choice, not a necessity: a host that wants the old anchor can blend the v2 and v3 sag components.
- **Volume leaks through the repair.** Pre-repair, the compensation solve is exact (ratio 1.000). Attenuation then spends the field down to **0.875** of v1's added patch volume; a post-repair re-solve (+1.52 cm) was computed and **rejected by the flip guard**. So: gravity redistributes ~7/8 of the mass and quietly deletes ~1/8. A bigger belly class would hide this; at this size it is a known, bounded inaccuracy.
- **The crease pinch is inherited, not built.** The material pinch ratio at the crease line is ~0.69 in v1, v2 *and* v3 — the Fat Males sculpt already pinches there. What v3 changes is where that material *sits* (the band profile, §2) and how deep the shadow reads in the render, not the pinch itself. Three earlier metric designs (binned silhouettes in three variants) proved too jittery at hm08's row density to measure a crease depth in cm; rather than ship a fragile number, the crease claim rests on the band profile + the render. A denser base would support a true silhouette-valley measurement.
- **Fold margin at +1 is thin on the raw base** (min_dot 0.0034, thinner than v2's raw 0.005 — though the macro base improved to 0.046 from 0.003, and Blender's evaluated check sits at 0.042). The slope limiter also never fully converged in its 80 iterations; the attenuation repair absorbed the residue. The shipped range [0, 1] is clean on both bases and in Blender — do not extend it without re-running repair.
- **Attenuation footprint is broad** (509 of 535 moved verts touched, min 0.10). The repair is no longer a local touch-up at this field strength; it is a global softening of ~35% at the navel. The shape survives because the field was over-solved to compensate — effective, but it means the *analytic* model and the *shipped* field differ by that softening layer, and the record says so.
- **The apex question, answered carefully.** "Apex ≥ 4 cm below the navel": against the anatomical (base) navel line, the mass centroid sits 9.26 cm below and the extent peak lives at +9…+13 — pass, decisively. Against the *deformed* navel vertex, the centroid is only 1.99 cm below — because the navel was dragged 7.28 cm down into the mass it used to sit on top of. Both numbers are reported; the first is the meaningful one for a silhouette judgement.
- **γ = 2.0 makes small values subtle.** At w = +0.3 the drape is at 9% — a small belly now shows almost no hang until ~+0.6. That matches the physics (light tissue doesn't drape) but changes the slider's feel versus v2; noted for whoever tunes the production range.

## Files

| file | what |
|---|---|
| `body.belly.protrusion_v3.target` | combined +1 field (protrusion + sag3), hm08 |
| `body.belly.protrusion_sag_v3.target` | sag3 component alone (pair with coupling γ = 2.0) |
| `body.belly.protrusion.slider_v3.json` | canonical slider record v3 (gravity section, QA, cross-check) |
| `scripts/build_belly_v3.py` | v3 builder + full QA (gain solve, drain/drape, repair, metrics) |
| `scripts/test_belly_v3.py` | Blender/MPFB verification + renders |
| `scripts/crosscheck_fields.py` | learned-field vertical-distribution cross-check (+ `work/crosscheck_fields.json`) |
| `renders/belly_v3_w+0.5_profile.png`, `belly_v3_w+1.0_profile.png` | v3 profiles, v1/v2 camera |
| `renders/belly_v1_v2_v3_+1_profile.png` | three-way side-by-side at +1 |
| `work/qa_numbers_v3.json`, `work/blender_v3_numbers.json`, `work/belly_v3.npz`, `work/target_coupled_v3_w0.5.target` | QA data + coupling fixture |

v1 and v2 files are untouched.

*Licence: study-only, internal — same as v1/v2. The gravity pass is AnthroForge-authored analytic work, inseparable from the v1 transfer it modifies, so the v3 files inherit study-only status.*
