# Hyper Animation — Technical Implementation Techniques

**Study date:** Nov 12, 2026 (Joe's directive: "check out hyper animations different artists have done" — this document is the *implementation* half: how hyper animation is actually **built** in avatar/engine contexts, with concrete parameter values where creators publish them.)

**Companion documents:** `dynamics/SOFT_DYNAMICS.md` (sibling study — spring-chain format + paintable softness field; this doc specifies what that format must support, §9), `hyper/HYPER_RANGES.md` (sibling study — static geometry failure map at 2–4×), `parts-lab/kaleaon-anatomy/KALEAON_ANATOMY.md` (the canon build these techniques animate), `first-proof/GRAVITY_V5.md` (belly v5.1 system), `bara-proof/BARA_PROOF.md`, `MUSCLE_TISSUE_MODEL.md`.

**Provenance discipline:** [S] = sourced from a cited public document/store page/spec · [D] = derived from data we hold on disk · [E] = estimate/fit by this study, labelled so first builds can tighten it. Where a creator does **not** publish numbers, this doc says so plainly rather than inventing them — most commercial hyper creators publish *feature lists*, not parameter tables; the hard numbers below come from the open specs (VRChat PhysBones, VRM SpringBone) and from the one fully open implementation we own (naelstrof's ChurnVectorSDK, GPL-3.0).

---

## 0. The one-paragraph answer

Nobody animates hyper with one system. Every production hyper avatar found in this study is a **stack of four independent channels driven by a small set of master parameters**:

1. **Size channel** — blendshapes (girth/volume) + bone-scale (length) driven together by one growth/arousal slider through an Animator blend tree or FX-layer clip. Girth is *never* bone-scale; length is *rarely* a morph (body-diversity verdict, confirmed again here).
2. **State channel** — a single master float (arousal 0–1 in Z Arousal / ChurnVector; muscle-flex 0–1 in Hypermancer) that sequences staged shape keys (flaccid → erect; Cum0→Cum4 traveling bulge; flex correctives) via **non-linear remap curves**, not linear crossfades.
3. **Secondary-motion channel** — PhysBone (VRChat) or SpringBone (VRM) chains on the oversized parts, with per-chain curves so stiffness/pull vary along the chain, plus **SquishyBones stretch/squish** (PhysBone 1.1) for volume-ish deformation. Force parameters are set at build time and **cannot be animated** in VRChat — growth changes how a chain *looks* (longer bones, bigger colliders), never its tuned constants. This is the single most consequential platform fact for hyper: **you tune physics for the biggest state, or you ship multiple pre-tuned chains and toggle between them.**
4. **Locomotion channel** — stock walk/run cycles are *not* re-authored for hyper. The industry answer is: accept clipping past a stated size, cap sway with angle limits + Immobile damping, add colliders so parts ride *over* thighs/floor instead of through them, and — for the parts that matter — drive **corrective blendshapes from joint angles / PhysBone feedback parameters** (`{param}_Angle/_Stretch/_Squish`) so the mesh responds to contact instead of interpenetrating silently.

Sections 1–7 document each channel from sources. Section 8 is the locomotion/clipping evidence. Section 9 is the normative part: **what our SOFT_DYNAMICS format must support** to reproduce all of it.

---

## 1. The size channel: growth toggles (bone-scale × blendshape, driven together)

### 1.1 How VRChat growth toggles are actually wired [S]

A VRChat "growth toggle" is not an engine feature; it is an Animator pattern:

- One synced float parameter (e.g. `Size`, `Belly`, `Arousal`) in the avatar's expression parameters.
- An **FX-layer** 1D blend tree (or a set of animation clips on a dedicated layer) keyed by that float. FX is the only layer whose blendshape/material curves replicate to the mirror clone and remote instances — transform/bone-scale curves can live on FX too, which is why size systems put **both** curve types in the same clips.
- Each clip animates, simultaneously:
  - `SkinnedMeshRenderer.blendShape.*` weights (0–100 in Unity) — the girth/volume channel;
  - `Transform.localScale` on dedicated size bones — the length channel;
  - optionally `VRCPhysBone` collider radii are **not** animatable (component properties initialise once), so creators who need collision to grow either scale a *collider parent bone* (colliders are transforms — their scale *is* animatable) or attach `VRCPhysBoneCollider` objects under a scaled bone.
- Non-destructive tooling has standardised the plumbing: **Modular Avatar** ships a `Scale Adjuster` (humanoid bone-length adjustment), `Shape Changer` (blendshape state driven by animations), and `Blendshape Sync` (propagates a base-body blendshape value to clothing/other meshes so outfits follow size) [S — VRChat wiki, Modular Avatar]. **VRCFury** (required by ZealotDKD, Wolke SPS setups, and most current NSFW/hyper addons) provides the toggle/slider scaffolding, SPS plug/socket deformation, and parameter compression so a multi-slider size system fits VRChat's synced-parameter budget.

**Design consequence for us:** the blendshape-sync pattern (one master value fanned out to every mesh that shares the region — body, clothing, fur cards) is exactly our coupling evaluator's job at the vector layer. The app already does this for tissue/definition (`core/sliders.py` evaluation → effective vector); hyper animation needs the same fan-out at *runtime*, per frame, for the animated masters (§9, R1).

### 1.2 Wolke's line (WLK_MEAT + the Wolke avatar bases) [S/D]

Wolke (Wolkehond) is the scene's hyper-anatomy hub. What is published:

- **WLK_MEAT | Hyper** ($10, study-tier, in our body-diversity manifest): a hyper genital add-on "made for all the size difference scenarios", two shaft styles, attaches to any avatar, ships an **SPS** (VRCFury Super Plug Shader) setup and **PhysBones**, with sliders for **shaft thickness, sagginess, and erection** [D — `character_assets/body-diversity/MANIFEST.md` H1, page-checked]. The three-slider split is the two-channel rule made literal: *thickness* = blendshape girth, *sagginess* = a droop morph/pose channel (gravity-shaped rest pose), *erection* = the state master (§2).
- Wolke's avatar bases expose the same philosophy body-wide as **"scale sliders"** in the expression menu [S — itch.io store pages]:
  - *Ample Anaconda*: arm width "Twig to Thick", chest "Small to Hyper", booty "Flat to Hyper", thighs "Thin to Fat", belly "Flat to Hyper", plus a breast↔pectoral shape toggle.
  - *Caked-Up Kobold*: arm width, chest "Flat to Busty", booty "Flat to Hyper", belly "Flat to Round", and a booty shape that is explicitly a **mix between ROUND, FATTY and MUSCULAR** — i.e. one size value crossfading *three* authored shape endpoints, the direct commercial analogue of our Muscle × Tissue grid.
  - *Strong Shark / Pudgy Pig / Cult Caprine*: per-region scale sliders (thigh, torso, chest, arm; belly + hip wideness) with full PhysBone setups.
- Wolke does **not** publish the numeric PhysBone values or blend weights used — the Unity packages are the documentation. Treat any specific numbers attributed to WLK_MEAT online as unverified unless extracted from an owned package. (We do not own it; $10, no-funds rule applies. Study-tier lead stands.)

### 1.3 Hypermancer Rev (Sombreve) — per-muscle blendshape animation [S/D]

- **15 Muscle Size Controls**: "Direct controls… to shrink and grow individual muscle groups… Unique blendshapes in Unity allow you to change his proportions separately from the in-game sliders" [S — sombreve.itch.io / vrc.sombreve.com]. Hyper muscle is therefore **15 independent girth channels**, not one "muscle" morph — matching our bara finding that HIMBO sculpts with 126 granular sliders while Atomic Muscle switches with macro morphs; Hypermancer is the granular school, productised.
- **Dynamic pectoral deformations**: pecs "stretch, compress, and squeeze in real time" as arms lift/cross/pull inward [S]. This is a **joint-angle-driven corrective**: arm elevation/adduction parameters feed corrective blendshapes — the same family as our definition sliders, but driven by *pose*, not by a user slider.
- **Automatic bicep flexing**: biceps flex correctives fire from elbow flexion automatically [S]. Again pose-driven, thresholded, no user input.
- Also shipped: 3 horn shape controls, 4 face shape controls, 2 nipple shape controls, ARKit shape keys — i.e. even decorative parts get the same slider treatment; nothing is a mesh swap at this quality tier.
- No parameter values are published (closed $54.49 package, all rights reserved — study-tier). The *architecture* is the harvest: per-group channels + pose-driven correctives layered over user size channels.

### 1.4 The mesh-swap ceiling [D]

Our body-diversity sweep's verdict stands and bounds all of the above: past the hyper threshold, several artists stop morphing and **swap meshes** (Mal-0 Hyper is a different body mesh; Nexa'vali ships anatomy as separate add-on objects). Blend trees make this cheap in VRChat (toggle the hyper mesh on, base mesh off, at a parameter threshold), and it dodges the fold/stretch failure modes the HYPER_RANGES study maps. Our format must therefore treat "mesh variant at threshold" as a first-class size-channel endpoint, not a hack (§9, R2).

---

## 2. The state channel: arousal as a master float with staged keys

### 2.1 Z Arousal Framework (ZealotDKD) [S/D]

The framework is **free**; every ZealotDKD anatomy product (canine/equine/dracanine/gryphon/werewolf/sergal sheaths, prehensile, slits, donuts — 12+ SKUs) requires it plus VRCFury [S — itch.io store pages; D — genitalia-blender manifest]. Published behaviour, consistent across all product pages:

- **Contact-driven accumulation**: "touch your sheath, balls, or peen with any other player object and increase arousal, going from flaccid to erect and cumming." The input is VRChat **Contact Receivers** on the anatomy (proximity float from any matching Contact Sender), integrated over time into one master **arousal** value; arousal decays when stimulation stops.
- The master drives, in sequence along its range: sheath emergence → flaccid→erect blend (blendshapes + bone pose) → knot/taper feature keys where the species part has them → **orgasm event** at the top of the range, which fires the effects package: in-house **cum, precum, piss, musk**, and a **proximity-based arousal blush/colour effect** ("pink"/"red" proximity arousal on the shader) [S].
- **SPS integration**: parts carry SPS plug/socket configuration "for dynamically penetrating others" — SPS deforms the plug along the socket's guided path in the shader and generates a **depth-driven traveling bulge** on the receiving body (the SPS Tools package literally ships a "Bulge Configurator — generates a depth-driven traveling bulge effect from blendshapes") [S — VPM catalog, SPS Tools]. The bulge is positional: each point on the path peaks when the plug tip reaches it.
- **PhysBones everywhere**: "Physbone dynamics for sheath, balls, and peen" is a headline feature of every SKU; rigging/dynamics are credited to a dedicated rigger (CFrostfoe) across the line — dynamics are authored per part, not auto-generated.
- Prehensile variant adds a **puppet** (manual 2D puppet control of the shaft's bend) and frotting functions — i.e. the state channel accepts *manual pose override* as an input alongside contact accumulation.
- The framework's internal numeric tuning (accumulation rates, thresholds) is **not published**; it ships as a VRCFury prefab. Our own values in §9 are therefore [E] fits to the *described* behaviour.

**Pattern to steal, precisely:** one master float; inputs are (a) contact proximity integrated with attack/decay, (b) manual slider/puppet override; outputs are staged, curve-remapped channels; the top of the range is an **event**, not just a pose. This is a state machine, and it belongs in the dynamics format as data (§9, R5).

### 2.2 ChurnVectorSDK (naelstrof) — the open reference implementation [S/D]

The only fully open implementation we hold (GPL-3.0; source + .blend files verified headless in the genitalia hunt). Its wiki ("Giving your character a working wang") is the most concrete hyper-animation spec publicly written down:

**Staged shape-key vocabulary** (the standard keys, verified in the shipped meshes):

| Key | Role |
|---|---|
| `Flaccid` / `Flaccid2` | smaller+thinner / fully soft-or-sheathed endpoint |
| `TipOpen` / `TipOpenMore` (+ staged variants ×3 on BigDragonCock_2) | tip opening, small → large |
| `Cum0`…`Cum4` | **traveling bulge**: five keys, each inflating a successive segment base→tip; `Cum4` ends at the open tip |
| extras per part | `Stubby`, `Seathed1/2`, `SheathClosed`, `Explode`, `Limp` |

BigDragonCock_2 carries **14 keys on a 214-vert mesh**; SpikeyDick and HumanoidDick carry the same vocabulary at 1,263 / 327 verts [D]. Lesson: these parts are **low-poly deformable primitives; the keys do the work** — vertex count is spent on smooth key interpolation, not sculpt detail.

**The "Boner" remap curve** [S — wiki]: the animator controller maps the master arousal value through **explicit non-linear curves per channel**, e.g. one channel keyed `1:0 → 0:1` against another keyed `0:0 → 0.5:0.5 → 0.2:1`. Channels deliberately *cross over* mid-range (one key fades out as another overshoots), which is how a two-key flaccid/erect pair reads as organic growth instead of a linear morph. A second curve set ("Cock Vore Size Change") "doesn't start at 0" — size channels hold a floor offset so the part never collapses to a degenerate zero (the wiki's FAQ: a flaccid state at exactly 0 with coincident verts produces NaN in the deform solver; start at **0.95** instead of 1.0 on the inverse curve).

**Rig convention** [S/D]: the shaft is **one bone weighted to the whole shaft** (multi-bone shafts are merged down — `Alt+M`); deformation shape comes from keys + shader, not from bone bending. Balls are a separate two-bone vertical chain with a designated **centre bone** the inflator uses as its spherisation origin. The SDK has "custom packages for jiggle physics which expects certain bone chain lengths" — chain topology is a contract, not a preference.

**Vertex-colour deform masks** [S]: red channel = spherise/shaft-control mask (balls spherise when full; shaft fully red), green channel = bulge-deform mask (shaft region the traveling bulge may expand). Painted masks, baked into vertex colours, read by the shader — the direct ancestor of our paintable-field pattern, and the reason §9 requires dynamics data to support **per-vertex scalar fields beyond softness** (R7).

**Jiggle** [S]: balls get an entry in the **Jiggle Rig builder** with a dedicated `BallsBlend` preset, separate from the shaft's Penetrator Jiggle Deform component (which deforms the shaft along a spline and has its own curvature settings). Two different secondary-motion models for two different part shapes: **volume jiggle for blobs, spline jiggle for shafts**.

### 2.3 Two erection styles [D]

From the genitalia hunt's design notes: implementations split into **morph-erection** (flaccid/erect are shape keys; pose follows) and **bone-erection** (the part is posed erect by its bone chain; keys only adjust girth/skin). Kaleaon's canon is bone-articulated (89-bone r3 rig, no erection morphs) [standing canon]. The state channel must drive *both* styles from the same master — Z Arousal products do exactly this across their line (some parts morph-led, prehensile puppet bone-led) — so the format stores per-part `erection_style: morph | bone | hybrid` (§9, R5).

---

## 3. The secondary-motion channel I: VRChat PhysBones

### 3.1 The parameter set (Version 1.1, current) [S — creators.vrchat.com/common-components/physbones; wiki.vrchat.com/PhysBones]

| Parameter | Range | Meaning |
|---|---|---|
| Integration Type | Simplified / Advanced | Simplified: stable, less reactive. Advanced: reactive, less stable, unlocks Momentum+Stiffness |
| Pull | 0–1 | Force returning bones to rest position |
| Spring (Simplified) | 0–1 | Wobble carried while returning |
| Momentum (Advanced) | 0–1 | Wobble under Advanced integration (not identical to Spring) |
| Stiffness (Advanced) | 0–1 | In 1.1: **absolute blend** — final orientation = lerp(current, target, Stiffness); 1.0 = never moves |
| Gravity | −1…1 (0–1 typical) | In 1.1: **absolute ratio** of how far bones rotate toward down at rest; requires Pull > 0 to act |
| Gravity Falloff | 0–1 | Gravity removed at rest pose (1.0 = no gravity effect at rest; docs suggest 0.5–0.8 for parts modelled part-way) |
| Immobile | 0–1 (+ Type: All Motion / World) | Damps motion inherited from root movement — the locomotion-isolation knob (§8) |
| Limit Type | None / Angle / Hinge / Polar | Cone / plane-slice / spherical-segment rotation caps (Max Angle 0–180°; Polar: Max Pitch/Yaw) — "far more performant than a collider" per docs |
| Radius | metres | Per-bone collision + grab radius |
| Stretch Motion | 0–1 | How much ordinary motion (vs grab/collision) feeds stretch/squish |
| Max Stretch | multiple of bone length (unbounded field) | SquishyBones elongation cap |
| Max Squish | 0–1 (multiple) | SquishyBones shortening cap |
| Grab Movement | 0–1 | 0 = spring to grabbed pose, 1 = snap |
| Endpoint Position | vector | Required fake end-bone for single-bone / single-generation chains |

**Curves:** nearly every force/limit value accepts a **per-chain curve** (the "C" button) — the value varies along the chain's length. This is how a tail/belly/sac chain is stiff at the root and loose at the tip *within one component*. Any format that stores one scalar per chain is already below the platform's expressiveness (§9, R3).

**Hard platform facts** [S]:

- **Force properties are set at initialisation and cannot be animated.** No growth-driven retuning. (Workarounds in §3.3.)
- One component ≤ **256 transforms**; Quest has a hard PhysBone budget far below PC.
- **Never root a PhysBone on a Humanoid bone** (Hips/Spine/Chest/limbs) — breaks locomotion; chains branch from dedicated non-Humanoid bones.
- Multi-Child Type (Ignore/First/Average) decides root behaviour for fan-out chains (hair, skirt, multi-teat/multi-shaft roots).
- Setting `Parameter = "X"` exposes feedback floats `X_Angle` (0–1, normalised 180°), `X_Stretch`, `X_Squish`, and bools `X_IsGrabbed`, `X_IsPosed` to the Animator — the sanctioned way to make *other* systems (correctives, sounds, blush) react to physics (§7).
- `Is Animated` lets animation move the chain's rest pose each frame (required if a growth clip re-poses a physics chain's bones).

### 3.2 SquishyBones (PhysBone 1.1, shipped 2023-05-03, build 2023.2.289) [S]

1.1's headline: bone **length** becomes dynamic. Stretch/squish are driven by motion (scaled by Stretch Motion), grabs, and collisions, capped by Max Stretch / Max Squish, and reported via the `_Stretch`/`_Squish` feedback parameters. For soft masses this is the volume-preservation illusion: a belly/sac/breast chain that *squishes* on contact and *stretches* in a stride reads as soft tissue rather than a swinging rigid pendulum. Note the 1.1 semantic changes that bite tuners: Gravity and Stiffness became **absolute ratios** (a 1.0 Gravity chain points fully down regardless of Pull size, gated by Stiffness), so 1.0-era presets do not transfer numerically.

### 3.3 What hyper creators actually do about "physics can't be animated" [S/D/E]

No creator publishes a full PhysBone preset table for hyper parts (checked: Wolke, ZealotDKD/CFrostfoe, Sombreve — feature lists only). The *patterns* are documented in platform tooling and conversion work:

1. **Tune for the largest state.** Bones are longest and colliders biggest at max size; a chain tuned stable there is merely *stiffer-feeling* at small sizes. The common failure (tuned small, explodes/flails at hyper) is why hyper avatars' small states often look over-damped. [E — inference from the init-only constraint + observed avatar behaviour; labelled as such.]
2. **Scale the collider, not the component.** PhysBone *colliders* live on transforms; parenting colliders under a size-scaled bone makes collision volume track growth while forces stay constant. AvatarBridge's conversion notes make the adjacent point for export: a breast/belly is best modelled as an **anchored volume** ("Bone Spring" in MagicaCloth2 terms — held near rest position), *not* as a hanging chain; converting anchored masses as chains "is what made them swing like a pendulum" [S — AvatarBridge docs]. **Anchored vs hanging is a per-part type decision**, and hyper masses (belly apron, sac, chest) are anchored; only truly pendant geometry (tails, ears, teat tips, foreskin, hair) is a hanging chain.
3. **Duplicate-chain toggling.** For parts whose feel changes categorically with size (flaccid vs erect dynamics), ship two pre-tuned PhysBone components on parallel chains and toggle component enabled state from the same master parameter. Costs a second chain against the transform budget; used sparingly. [E — pattern consistent with VRCFury toggle practice; no vendor doc states it outright.]
4. **Feedback-driven squash.** `_Squish`/`_Stretch`/`_Angle` floats drive corrective blendshapes (§7), faking volume response the bone solver can't do.

### 3.4 Working value bands [S/E]

Published anchors are scarce; the table separates what is documented from this study's starting bands for *our* Babylon runtime (to be calibrated against the SOFT_DYNAMICS prototype's measured lag/settle):

| Part class | Pull | Spring/Momentum | Gravity | Falloff | Immobile | Limits | Source |
|---|---|---|---|---|---|---|---|
| Hair / ears (reference) | 0.2–0.5 | 0.2–0.9 shown in VRC School A/B demos (0.2 vs 0.9 spring visibly separates) | 0–0.5 | 0.5–1.0 if modelled posed | 0–0.3 | Angle 30–60° | [S] demos/docs |
| Anchored soft mass (breast/belly/sac body) | 0.35–0.6 [E] | 0.3–0.55 [E] | 0.15–0.4 [E] | 0.6–0.9 [E] | 0.4–0.7 [E] | Angle 15–35°, Max Squish 0.25–0.45, Max Stretch 1.15–1.35, Stretch Motion 0.4–0.8 [E] | bands fitted to §3.2 semantics |
| Pendant chain (tail/teat/shaft tip) | 0.1–0.3 [E] | 0.5–0.85 [E] | 0.4–0.9 [E] | 0–0.4 [E] | 0–0.25 [E] | Angle 45–90° [E] | " |
| Erect shaft (state-dependent) | higher Pull + Stiffness than flaccid state; commonly a second component (§3.3.3) | — | low | high | mid | tight Angle | [E] |

Gravity Falloff guidance *is* documented: parts modelled already-drooped take Falloff ≈ 1.0; parts modelled at 45° take 0.5–0.8 for a partial droop [S — creators.vrchat.com]. For hyper parts modelled at their *hyper* rest shape, the same rule says: model the drape in, keep Falloff high, let gravity act on *deviation* — which is precisely our v4/v5 approach of authoring the sag into the field and animating around it.

---

## 4. The secondary-motion channel II: VRM SpringBone + Unity spring systems

### 4.1 The VRM spec parameter set [S — vrm.dev spec / UniVRM; three-vrm]

VRM SpringBone is a **Verlet chain solver**, specified exactly enough that independent runtimes (UniVRM, three-vrm, VSeeFace, and even a native reimplementation measured at 0.13–0.18 ms per 60 Hz tick for 112 joints) reproduce authored motion bit-comparably:

| Parameter | Range (spec/implementations) | Meaning |
|---|---|---|
| `stiffness` | 0–4.0 in spec tables (0–1 in most editor UIs; default ≈ 0.5–1.0) | Pull toward the *animated* rest direction, as a fixed distance per second |
| `gravityPower` | 0–2.0 (default ≈ 0–0.1 for hair — "most VRoid hair has gravityPower 0") | Gravity magnitude along `gravityDir` (usually (0,−1,0)) |
| `dragForce` | 0–1 (default ≈ 0.4) | Fraction of velocity lost per step — the damping/settle knob |
| `hitRadius` | metres (≈ 0.02 typical for hair) | Per-joint collision sphere vs sphere/capsule colliders on body bones |

Per-joint settings (each joint carries its own stiffness/gravityPower/dragForce/hitRadius), collider groups push chain *tails* out; chains never collide with each other. Leaf joints get a virtual tail (7 cm in VRM 0.x rules).

**Crosswalk that already exists** [S — Orbiters My Avatar conversion notes]: VRM stiffness maps *jointly* onto PhysBone Pull and Stiffness (VRM stiffness 1.0 → ≈ 0.17 each), Spring/Momentum derives from drag as its complement (VRoid drag 0.4 → Spring ≈ 0.67), gravity carries over directly. Our format should store **one canonical parameterisation and emit both** (§9, R4) rather than storing platform values.

### 4.2 Tuning very large soft masses in spring systems [S/E]

What changes when the mass is hyper-scale, from the spring literature + the VRM/Unity practice above:

- **Chain length discipline**: keep chains to **4–6 segments** (Unity spring-bone best practice; mobile fewer). A hyper sac/belly does not get a 15-bone chain — it gets a short anchored chain with big radii. Long chains at large amplitude are the jitter/explosion source.
- **Stiffness low, drag high**: large masses read correctly with *low* stiffness (0.5–1.5 on the UnityChan 0–4 scale; start low, raise iteratively to avoid jitter) and drag in the upper band (0.4–0.7) so sway settles in 1–2 oscillations instead of ringing. Small parts (teats, ear tips) invert this: stiffer, lighter drag, faster settle.
- **Colliders are few and big**: 3–5 body colliders suffice for an avatar; oversized colliders are the #1 VRM defect in the wild (a known UniVRM export quirk inflates them; a 50% reduction empirically fixes tested models). For hyper, collider radius must be a *function of the size channel* (§3.3.2) — a belly collider authored at base size is inside the mesh at hyper size and does nothing, or outside it at small size and floats the chain.
- **Scaling warning** [S]: UniVRM officially discourages combining SpringBone with node scaling — the solver assumes authored bone lengths. This is the VRM-side statement of the same law as §3.3: **bone-scale growth and spring physics fight**; the working compromise is scaling *colliders and mesh*, keeping physics bone lengths near-authored, or re-deriving chain rest lengths at state thresholds (mesh-swap points, §1.4) rather than continuously.

### 4.3 Beyond PhysBone/SpringBone: MagicaCloth2 & Dynamic Bone conversions [S]

AvatarBridge's published conversion derivations are useful as *semantic* evidence for our canonical model:

- PhysBone → DynamicBone maps field-for-field with rescalings: **Pull → Elasticity × 0.2**, **Gravity → Force × 0.2** (the pair rescaled together so the resting equilibrium matches), **Spring → inverted Damping**. The equilibrium-matching principle — *preserve where the chain settles, then preserve how it rings* — is the correct crosswalk doctrine for any platform pair.
- PhysBone → MagicaCloth2 splits by part type: hanging chains → Bone Cloth; **anchored volumes (breast/butt/belly/thigh) → Bone Spring** with collision offered on **one bone per side** (the bone whose pivot sits nearest the mesh centroid of that side) so touches land where the mass actually is. Stretch & squish have **no MagicaCloth2 equivalent** and are reported as losses — a reminder that squish is a PhysBone-1.1-only channel our format should keep as optional capability, not a core assumption.

---

## 5. Per-muscle blendshape animation (the Hypermancer pattern, generalised)

Hypermancer's two dynamic systems generalise to a pattern our stack lacks today:

1. **Pose-driven correctives**: a corrective blendshape set whose weights are *computed from joint state* each frame — pec deformation from arm elevation/adduction; bicep flex from elbow angle (with a threshold + smoothing so it reads as a flex, not a linear bulge). In VRChat these live on the FX layer as clips sampled by blend trees whose inputs are the avatar's tracked joint proxies; in our Babylon runtime they are a per-frame function `correctives = f(jointAngles)` evaluated before skinning.
2. **User size channels are separate from pose channels** and the two multiply: the flex corrective is authored at a reference size and scaled by the muscle-size channel's local value (a flex on a 0.3-size arm is a small flex). Our coupling evaluator already has this shape (authored value × attenuation/show-through factors); §9 R6 asks the dynamics format to store the *joint→corrective bindings* with their gain curves.
3. **Interaction with tissue**: at high tissue, flex correctives must attenuate (a buried biceps doesn't ripple the surface) — our definition-attenuation coupling (MUSCLE_TISSUE_MODEL §2) already computes exactly this factor; the dynamics layer should consume the same A(region) value rather than re-deriving it.

The bara proof's static composition (muscle field → tissue over it → definition attenuated) is the *rest-pose* half of this; Hypermancer proves the *posed* half is the same fields re-evaluated per joint state.

---

## 6. Traveling and staged deformations (bulge, inflation, spherisation)

Three distinct traveling-deformation implementations were found — worth separating because they need different data:

| Pattern | Implementation | Data needed |
|---|---|---|
| **Discrete staged keys** (ChurnVector `Cum0–4`) | 5 authored keys, successive shaft segments; animator crossfades key *n* → *n+1* as the event parameter advances; tip key doubles as `TipOpenMore` | Ordered key list + per-key segment mask (the key itself carries it) + event parameter mapping |
| **Path bulge** (SPS Bulge Configurator) | Plug bends along a socket's guided path *in the shader*; bulge on the receiver peaks at the path point nearest the plug tip, continuously | A **path** (bone chain or curve) on the receiving part + bulge blendshape + depth parameter in plug units |
| **Shader spherisation** (ChurnVector `BallsSpherize`) | Vertex-colour red mask defines the region; shader spherises around the centre bone by a fullness uniform; shaft uses a sibling spline-deform shader | Per-vertex mask field + centre bone + fullness parameter + spline for the shaft |

Common structure: **a scalar event parameter + a spatial guide (staged masks, a path, or a mask+centre) + authored endpoint shapes**. None of them is a spring system; they are *kinematic* deformations slaved to a state variable. Our format must keep them in the state channel (§2), not the physics channel — but note the interplay: a traveling bulge that changes a part's girth mid-animation changes its collision radius and its jiggle inertia, which loops back to §3.3's "physics can't follow growth" problem; production answer is that bulge-scale effects are small/fast enough that constant physics tuning survives them, while *growth*-scale effects use thresholds (§9, R2/R8).

---

## 7. Feedback loops: physics → animation parameters

PhysBone's `{parameter}_Angle/_Stretch/_Squish/_IsGrabbed/_IsPosed` outputs [S] enable the pattern that makes hyper parts feel *reactive* rather than merely *loose*:

- **Squash correctives**: `_Squish` drives a widen-when-squashed blendshape (volume illusion) on breasts/belly/sac; `_Stretch` drives a narrow-when-stretched shape. This pair is the cheapest volume preservation in the whole study — two blendshapes + two feedback floats.
- **Contact blush / arousal feed**: Z Arousal's proximity colour effect and its contact→arousal accumulation are the same loop at a slower time constant (contacts are also VRChat-native: Contact Receiver proximity floats).
- **Sound/gesture triggers**: `_IsGrabbed`/`_IsPosed` gate emotes and audio in shipped avatars.

For our runtime: the spring solver must **publish** per-chain normalised angle/stretch/squish every frame as named signals, and the character record must allow binding those signals to blendshape weights, material uniforms, and state-channel inputs (§9, R8). Without published signals, every reactive trick in this section is unimplementable.

---

## 8. Locomotion with massive anatomy: contact, sway caps, clipping policy

### 8.1 What actually breaks [S]

- VRChat FBT assumes a roughly human-proportioned avatar ("works best when the avatar is proportional to a typical human being in regards to limb and torso length; the spine should not have sudden bends; no full-body hacks") [S — docs.vrchat.com Full-Body Tracking]. Hyper proportions violate the assumption at the *mesh* level, not the skeleton level — the skeleton stays humanoid (all systems in this study keep a stock humanoid rig), so tracking itself survives; what breaks is **self-intersection**: thighs vs belly apron, arms vs chest mass, sac vs floor in sits, shaft vs thigh in strides.
- GoGoLoco (the near-universal locomotion/pose package) + avatar scaling is the standard locomotion answer; posed sets (sit/lay/kneel) are where hyper clipping concentrates, and creators handle it by authoring **pose-specific correctives** or accepting it in poses. V-Roo (Voxian, kangaroo base with custom locomotion) and AvaTAUR (taur base, 310 blendshapes, custom locomotion with grounders) show the high-effort end: when the *body plan* is non-human, locomotion is re-authored wholesale — but for hyper *humanoids*, nobody in this study re-authors walk cycles. [S — Jinxxy product pages]
- Spectrum Redux (modular base) documents the mainstream soft-mass setup: PhysBones on "Breasts, Head fluff, Thighs, Butt, Toes, and **Belly (at larger body sizes)**" plus helper/constraint bones for FBT [S] — note the belly chain is *conditional on size state*, a shipped example of §3.3's size-gated physics.

### 8.2 The coping toolkit (in order of preference) [S/E]

1. **Angle limits before colliders.** PhysBone Limits (Angle/Hinge/Polar) are cheaper than colliders and deterministic: cap a belly/sac chain's pitch so it cannot swing *into* the thighs; cap shaft chains so stride motion can't fold them through a leg. Docs explicitly recommend limits over colliders for clip avoidance.
2. **Immobile as the stride isolator.** Immobile (All Motion) damps root-translation forcing — at 0.4–0.7 on anchored masses [E band, §3.4], walk bob stops driving belly bounce while *rotation* (turns, leans) still reads. Pendant chains keep Immobile low so they can lag honestly.
3. **Colliders as deflectors.** A thigh collider + a belly/sac chain radius makes the mass ride *over* the thigh in a stride instead of through it. Collider count stays tiny (§4.2); on avatars, hand/global colliders also give the grab/pose interactivity hyper parts are expected to have.
4. **Squish as the contact absorber.** Where contact is unavoidable (sitting on a sac/belly, thighs meeting at hyper thigh size), SquishyBones Max Squish + the §7 squash correctives convert interpenetration into *deformation* — the visual difference between "clipping" and "squishing" is whether the surface moves. Our thigh-contact solver (v5.2 study) is the static version of this; the dynamic version is a squish channel.
5. **Breathing/idle layering.** Shipped bases include toggleable breathing animations; at hyper sizes the breath cycle is a *belly/chest* animation, and it must be authored on the size-driven mesh (an additive clip over the FX size layer), or the belly visibly detaches from the breath.
6. **Stated clipping policy.** Production avatars document the line rather than pretending it doesn't exist — e.g. Mirage (Payhip): "made using the low poly variation of this outfit, so there may be clipping in extreme positions" with showcase GIFs filmed in FBT [S]. Our export profiles should carry the same honesty as data: per-part, per-pose-class, the size at which clipping is *accepted* (§9, R9) — a QA gate, not an apology.

### 8.3 Sway amplitude: the numbers that exist

No creator publishes sway amplitudes. The measurable proxies from the specs: PhysBone `_Angle` normalises 180° of end-bone deviation to 1.0, and limit cones for soft masses in tutorials sit at 15–35° [E from §3.4 bands]; VRM practice keeps big-mass chains short (§4.2), which caps tip excursion geometrically (excursion ≈ chain length × sin(limit)). Our SOFT_DYNAMICS prototype's measured lag angle + settle time at two stiffnesses is the right primary source for our own bands — §9 R10 requires the format to store **measured** sway/settle per reference chain so future parts calibrate against data, not vibes.

---

## 9. What our SOFT_DYNAMICS format must support (normative)

Requirements for the sibling `SOFT_DYNAMICS.md` format, each traced to the section that forces it. "Must" = a technique in this study is unimplementable without it.

- **R1 — Master parameters with fan-out (§1.1, §2).** Named master floats (size masters per region; `arousal`; future `fullness`, `flex`) stored once, with per-target **remap curves** (piecewise, crossovers allowed, floor offsets allowed — the ChurnVector 0.95 lesson) fanning out to blendshape weights, bone scales, bone poses, material uniforms, and component toggles. Linear-only mapping is insufficient (§2.2).
- **R2 — Threshold events & mesh variants (§1.4, §2.1).** A master crossing a threshold may fire one-shot events (orgasm package, sound, particle/uniform burst) and swap mesh variants / physics-chain sets. Events are data (threshold, direction, payload list), not code.
- **R3 — Per-joint curves on every chain parameter (§3.1).** Stiffness/pull/gravity/drag stored as **curves over chain parameter t∈[0,1]**, scalar as degenerate case. Root-stiff/tip-loose is the default shape for pendant chains; anchored masses want the inverse on radius.
- **R4 — One canonical solver parameterisation + platform crosswalks (§4.1, §4.3).** Store canonical (stiffness, damping, gravity, radius) per joint; emit VRM SpringBone (stiffness 0–4 scale, dragForce, gravityPower) and PhysBone (Pull/Spring-Momentum/Stiffness/Gravity/Falloff) via documented crosswalks that **preserve rest equilibrium first, ringing second**. Include Immobile/limits as PhysBone-only extras, hitRadius/colliders as shared.
- **R5 — State machines for anatomy (§2).** A state-channel record per part: master input(s) (contact-integrated with attack/decay rates, manual override, puppet), staged key list in canonical vocabulary (`Flaccid`, `Flaccid2`, `TipOpen`…, `Cum0…N`), per-stage curves, `erection_style: morph|bone|hybrid`, and threshold events (R2). Accumulation/decay rates are fields with [E] defaults (attack ≈ +0.25/s at full contact proximity, decay ≈ −0.05/s [E]) for first builds to calibrate.
- **R6 — Pose-driven corrective bindings (§5).** Records binding a joint-angle signal (source bone, axis, angle range) through a gain curve to corrective blendshape weights, with a tissue-attenuation input that consumes the coupling evaluator's A(region) so posed correctives and static definition share one attenuation truth.
- **R7 — Paintable fields beyond softness (§2.2, §4).** The softness field generalises to named per-vertex scalar fields: `softness` (solver gain), `spherise_mask`, `bulge_mask`, plus per-vertex **radius scale** for colliders. ChurnVector proves two masks minimum; our teat/sac/belly case needs all four.
- **R8 — Published feedback signals (§7, §6).** Every chain publishes `{chain}_angle`, `{chain}_stretch`, `{chain}_squish` (normalised, PhysBone-compatible semantics) each frame; bindings may route them to blendshapes (squash correctives), uniforms, and state inputs. Squish/stretch capability is flagged per export profile (PhysBone 1.1 yes; MagicaCloth2 no; VRM no) so exports degrade honestly.
- **R9 — Size-conditioned physics & clipping policy (§3.3, §8).** Per part: physics parameter *sets* keyed by size-state (with the active set switched at R2 thresholds, since continuous retuning is impossible on the target platforms), collider radius as a function of the size master, and a `clip_policy` record (pose classes × max clean size; beyond it, squish-absorb or accept). Anchored vs hanging is a required per-chain `type` field.
- **R10 — Measured calibration data (§8.3).** Chain records carry an optional `measured` block (lag angle, settle time, test motion, solver, date) so the library accumulates real tuning data per part class — starting with the SOFT_DYNAMICS prototype's sac/belly numbers.
- **R11 — Babylon runtime mapping.** Our own runtime is the fourth platform: canonical chains compile to (a) Babylon bone-level spring integration using the same Verlet step as VRM (bit-comparable tuning with VRM exports), (b) baked bone animation for static exports (GLB ships nothing dynamic — the bake is per locomotion clip × size state, generated, not authored). The format must therefore also store `bake` hints: which chains bake, at what sample rate, for which clips.

### Worked example — Kaleaon's sac-udder under this format [D/E]

- **Size channel**: sac volume master → girth blendshapes on the sac mesh + teat length via teat-bone scale; collider (one anchored sphere at the sac centroid bone, per §4.3's one-bone-per-mass rule) radius = f(master).
- **Chains**: one **anchored** chain (sac body; 3 joints; stiff root curve, high Falloff — drape is modelled in per canon) + four short **pendant** teat chains (2 joints each; softness field peaks at teat tips — teats softer than sac body, sac softer than belly core, per Joe's specification and the paintable-field design).
- **Locomotion**: Immobile mid (stride isolation), Angle limit ≈ 25° pitch [E], squish on with Max Squish ≈ 0.35 [E] + `_Squish`→widen corrective so floor/thigh contact reads as squash; clip policy: clean to canon size in walk/run, squish-absorb in sits, accept in extreme GoGoLoco poses.
- **Quad shafts**: per shaft, state channel (R5) with bone-style erection (canon: bone-articulated), ChurnVector key vocabulary for girth/tip stages, one-bone shaft convention *per shaft* with its own short pendant PhysBone-equivalent chain for flaccid sway, switched to the stiff set at the erect threshold (R9/R2).

---

## 10. Source list

Platform specs & docs (all retrieved Nov 12, 2026):
- VRChat Creator Docs — PhysBones (component reference, v1.1 semantics, feedback parameters): https://creators.vrchat.com/common-components/physbones/
- VRChat Wiki — PhysBones (version history, SquishyBones 2023-05-03, parameter ranges): https://wiki.vrchat.com/wiki/Physbones
- VRC School — Phys Bones (A/B parameter demos: Pull 0.2 vs 0.4, Spring 0.2 vs 0.9, Stiffness 0.2 vs 0.8, Gravity 0.2 vs 0.5): http://vrc.school/docs/Avatars/PhysBones/
- VRChat Docs — Full-Body Tracking (proportionality assumptions): https://docs.vrchat.com/docs/full-body-tracking
- VRM specification / UniVRM SpringBone parameter tables (stiffness, gravityPower, dragForce, hitRadius; Verlet step; collider model) via vrm.dev documentation summaries; three-vrm joint settings.
- Orbiters My Avatar / Toolkit (VRM↔PhysBone conversion crosswalk values): https://vpm-catalog.vercel.app/packages/orbiters.myavatar/
- AvatarBridge (PhysBone→MagicaCloth2/DynamicBone derivations; anchored-volume "Bone Spring" doctrine): https://github.com/MrTactical/AvatarBridge
- Modular Avatar (Scale Adjuster, Shape Changer, Blendshape Sync): https://wiki.vrchat.com/wiki/Community:Modular_Avatar
- SPS Tools (Bulge Configurator — depth-driven traveling bulge from blendshapes): https://vpm-catalog.vercel.app/packages/com.aurorakai.sps-tools/

Creator implementations:
- ZealotDKD itch.io line (Z Arousal behaviour, SPS, PhysBone dynamics per part; bundle: https://itch.io/b/2416/z-arousal-framework-bundle) — product pages for Canine/Equine/Dracanine/Gryphon/Werewolf/Sergal/Prehensile/Humanoid SKUs.
- naelstrof, ChurnVectorSDK wiki — "Giving your character a working wang" (shape-key vocabulary, Boner curves, vertex-colour masks, jiggle rig): https://github-wiki-see.page/m/naelstrof/ChurnVectorSDK/wiki/Giving-your-character-a-working-wang — plus the SDK meshes verified on disk (`character_assets/genitalia-blender/`).
- Wolke itch.io line (scale-slider anatomy; WLK_MEAT sliders per our page-checked manifest): Ample Anaconda https://wolkehond.itch.io/anaconda · Caked-Up Kobold https://wolkehond.itch.io/kobold · Strong Shark, Pudgy Pig, Cult Caprine store pages.
- Sombreve — Hypermancer Rev (15 muscle controls, dynamic pecs, auto-flex): https://sombreve.itch.io/hypermancer-rev-vrc · https://vrc.sombreve.com
- Spectrum Redux (size-conditional belly PhysBones, Blendshape-Sync-class body system): https://arkorenart.itch.io/spectrumredux
- Voxian V-Roo & AvaTAUR (custom locomotion at non-human plans; belly jiggle/touch cleanup): https://jinxxy.com/Voxian/VRoo · https://jinxxy.com/Voxian/AvaTAUR
- Mirage (published clipping disclaimer as shipped practice): https://payhip.com/b/OC4Tu

**Honesty box.** No commercial hyper creator in this study publishes numeric PhysBone/SpringBone presets; §3.4's soft-mass bands are [E] fits anchored to the documented semantics and demo values, and §9's [E] defaults are starting points for calibration against our own measured prototype — not recovered vendor numbers. Video evidence was not required for any load-bearing claim above (all rest on text specs/store pages/open source), so no frame-extraction was needed this pass.
