# Fur States — FUR_STATES.md

**Learning Agent A17 + finisher pass, AnthroForge fur-craft wave, Nov 12–13, 2026.**
Coat *condition* — wet, wind-blown, matted, dirty/aged — expressed the same way
A19 expresses coat *season*: as parameter deltas over one groom, never as a
second groom. Two of the four states are built and rendered (§3); two are
specified in the same grammar and honestly marked unbuilt (§5).

Companion docs: A19 `SPECIES_FUR.md` (the §9.5 `fur_region` parameter
vocabulary + the seasonal model this generalises), A7 `PAINTMAPS.md` (the
`FURP_` groom-mechanics fields states modulate, and the record discipline
states inherit), A11 `FUR_COLOUR.md` (the colour-population model that owns
greying, §5.2), A12 `FUR_SHADING.md` (the shippable shader carriers for state
sheen), APP_BLUEPRINT §9.5/§10.1 (the record shape; the wetness ruling).

---

## 0. What a fur state is

**A fur state is a parameter morph over ONE groom.** The blueprint already
rules the core case (§10.1): wetness is a *material state*, not a new model —
the Fat Males Dry/Wet pairs are the cited reference. This doc generalises
that ruling from wetness to all coat conditions:

> A state = per-region **groom deltas** + one **material delta set** + an
> optional **spatial mask** + a **blend weight**. Applying a state changes
> settings and material values only. It never re-grooms, never re-simulates,
> never edits hair keys, and never adds or removes a strand.

States blend by lerping every numeric field against the dry groom at the
record's weight. (One non-numeric field exists — kink *type* — and needs a
switch rule; proposed: enum fields take the state's value at weight ≥ 0.5,
the dry value below. **Proposed, untested** — no two-state or partial-weight
render exists yet.)

The format already contains one state, unnamed: A19's **seasonal model**.
Summer is not a second profile; it is per-region length overrides + two
global scalars (`density_scale`, `undercoat_scale`). Fur states are that
exact mechanism generalised from *season* to *condition*, and §4 proposes
re-expressing season as a state (`season.summer`) rather than leaving it a
special case bolted onto the profile.

What a state is **not**: identity. A wet dog saved and reloaded is the same
character — weights are presentation data in the record (§4), and a state
definition is library data shared by every character, like a species profile.

---

## 1. The state catalogue

| State | Physical story | Primary channels | Status |
|---|---|---|---|
| `dry_neutral` | The groom as authored; the reference every delta is measured against | — | baseline |
| `wet_clumped` | Water films bridge neighbouring strands → they collapse into separated spikes; added mass + lost loft lay the coat down; the water film darkens colour (less air–hair scattering) and adds clearcoat-like sheen | clump ↑↑, kink order ↓, length/thickness ↓, colour ×0.45, roughness ↓, coat ↑ | **built + rendered** (§3) |
| `wind_swept` | Moving air bends every strand coherently root→tip and splays the tips; separation *reduces* clumping | directional bend (reserved field), tip splay ↑, clump ↓, roughness ↑ slight | **record built; bend approximated** (§3.3) |
| `matted` | Felted tangles at skin level: strands lock into lumps that no longer lie in the flow field; patchy by nature — mats form where fur is long and friction is high | clump → ~max through a **mask**, coarse clump noise, kink flattened + disordered, roughness ↑ | specified, **not built** (§5.1) |
| `dirty_aged` | Two mechanisms sharing one slot: *soiling* (surface grime — tip-weighted darkening, dullness, tack) and *greying* (follicle pigment loss — a per-strand colour-population change) | zone colour fields + roughness (soiling); colour population fraction (greying) | specified, **not built** (§5.2) |

A note on density: **no state changes authored strand count.** Wet fur does
not have fewer hairs; it has the same hairs in fewer, fatter groups. The
built states honour this — `count` is byte-identical across all three
resolved records — and §5's specifications keep it.

---

## 2. The delta grammar

States are written in the op forms `fur_states.json` v1 already uses, and no
others:

| Op | Form | Example (wet) |
|---|---|---|
| multiply | `"x0.92"` | `hair_length: x0.92` |
| set | bare value | `clump_shape: -0.85` |
| clamped affine | `"min(1, 1.45x + 0.25)"` | `clump_factor` (clump saturates; the clamp *is* the physics) |
| per-region table | `{region: value}` | wind `kink_amplitude` by groom region |

**Vocabulary mapping.** The normative field names are the §9.5 / A19
`fur_region` fields; each binds to groom parameters (this prototype: Blender
particle properties) and to A7 paintmap fields as follows:

| `fur_region` field | Groom binding (particles) | Paintmap interaction |
|---|---|---|
| `clump` | `clump_factor`, `clump_shape`, clump noise | state scales the system scalar; `FURP_clump` remains the spatial authority (A7: the map is absolute, the scalar a pass-through — a state therefore multiplies the *pass-through*, not the painting) |
| `length_m` | `hair_length` (per region system) | `FURP_length` × profile `length_ref_m` sets the dry value; the state multiplies the result |
| `curl` | kink type/amplitude/frequency family | `FURP_curl` arms CURL regions; wet's kink damping applies to whichever kink a region runs |
| `frizz` | `roughness_endpoint`, kink randomness | — |
| `colour` root/tip | hair material Color (+ pattern function per A11) | `FURP_zone_root/tip` are the spatial fields; a state applies a global multiplier/set over the field result |
| `density` | `count`, child counts | `FURP_density`; states leave it alone (§1) except thinning-by-age, flagged as a boundary question in §5.2 |

**Material deltas are written in Principled-Hair-BSDF terms** — `Color`,
`Roughness`, `Radial Roughness`, `Coat` — because that is the groom-side
normative shader (A7 §6's melanin discipline applies to how colour is set).
The shippable carriers differ by representation, and the state record does
not pretend otherwise: on the §10.1 PBR stack and A12's card material, wet
sheen lands as **clearcoat + sheen**, colour darkening as a base-colour
multiplier; `Radial Roughness` is strand-only and simply has no card analog
(the export report should say so, per §9.8's never-silently-dropped rule).

**Region naming.** The prototype's groom regions (`ruff`, `back`, `belly`,
`coat`, `bodyhair`) are the fur prototype's system names, not the canonical
§9.5/A19 region vocabulary (`ruff`, `torso.back`, `torso.front`, …). State
*definitions* in the library use canonical regions; the prototype's
`fur_states.json` is a groom-local draft and its region keys need the
rename when the defs are promoted (§4). Flagged, not hidden.

---

## 3. The prototype — what was actually built and run

### 3.1 Provenance, stated plainly

The original A17 agent died mid-investigation. It left no outputs — only
`work/probe_keys.py`, `probe_keys2.py`, `probe_keys3.py` and
`work/build_states.py`. The probes test whether baked hair keys can be
written directly (outside and inside particle-edit mode); **no probe logs
survive**, so their verdicts can't be quoted — but the design they fed is
legible in `build_states.py` itself: states as pure setting/material
deltas, keys never touched. That design is what the finisher ran.

### 3.2 The run, and the two defects it surfaced

`build_states.py` as left **does not run against the real groom**. First
finisher run died at the baseline snapshot:

```
IndexError: list index out of range
  hair = [n for n in bpy.data.materials["FurHair"].node_tree.nodes
          if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
```

The script assumes the stage-2 groom's `FurHair` material contains a
Principled Hair BSDF. It does not: `fur_stage2.blend`'s hair slot holds a
plain **Principled BSDF** (Base Color 0.072/0.054/0.041 linear, Roughness
0.62, Coat Weight 0). Every probe script ends with the same hair-node
lookup, so it is plausible — stated as plausible, not proven — that this
is also where the original agent's line of work stopped.

The finisher therefore ran a patched copy, `work/build_states_run.py`
(original untouched), with three documented patches, all confined to
material access and provenance:

1. **Node resolution** — prefer a hair BSDF, fall back to the BSDF actually
   in the slot; deltas map by input-name candidates (`Color`→`Base Color`,
   `Coat`→`Coat Weight`). A delta with no analog input (`Radial Roughness`)
   is recorded in the JSON under `material_unapplied`, never silently
   dropped.
2. **Per-object snapshot** — the original `snapshot()` read the *shared*
   `FurHair` material for every object, so the wet/wind "resolved" records
   would have shown the dry material. The run copy resolves each object's
   own material via its particle-settings slot.
3. **Provenance** — the JSON states what the deltas were applied to
   (`"material_applied_to": "BSDF_PRINCIPLED"` + a `material_note`).

Everything else — state construction, particle deltas, record shape,
studio, renders — is the original script byte-for-byte in behaviour.

### 3.3 Verified results

The run completed clean (exit 0): `fur_states.json` + `fur_states.blend`
(three objects, `fur_state` custom property set on each) + three renders.
The resolved records in the JSON match the designed delta arithmetic
exactly; spot checks:

| Field (ruff unless noted) | dry | wet | wind |
|---|---|---|---|
| `hair_length` | 0.1700 | 0.1564 (×0.92) | 0.1700 |
| `clump_factor` ruff / belly | 0.650 / 0.250 | **1.000** / 0.613 (clamp-affine) | 0.488 / 0.188 (×0.75) |
| `clump_shape` | −0.40 | −0.85 | −0.20 |
| kink | WAVE amp 0.012, freq 3.0 | amp 0.0036 (×0.3), freq 2.1 (×0.7) | WAVE all systems; amp by region 0.030 ruff → 0.003 bodyhair |
| `roughness_endpoint` (tip splay) | 0.0 | 0.0 | 0.20 ruff / 0.15 back / 0.10 coat / 0.05 belly·bodyhair |
| material Color (linear) | 0.072/0.054/0.041 | 0.032/0.024/0.018 (×0.45) | unchanged |
| material Roughness | 0.62 | 0.24 | 0.47 |
| `count` (all systems) | 15,500 parents | identical | identical |

**The renders, judged honestly** (single rear three-quarter camera, 640×800,
32 samples + OIDN denoise; the render visibility set is the script's four
body systems — `FUR_bodyhair` carries full deltas in the records but is
hidden in all three frames):

- **Dry** — full woolly loft, pale grey-brown, the body form mostly lost in
  coat volume. The stage-2 groom as shipped.
- **Wet** — unmistakable. The coat collapses onto the body, darkens hard,
  separates into clumped spikes; torso curve, leg and paw read *through*
  the coat, and the back/ruff take a glossy sheen. Parameter deltas alone
  produced a coat a viewer will call wet without being told. This is the
  prototype's real result.
- **Wind** — weak in stills, and the doc won't pretend otherwise. The frame
  sits close to dry; the WAVE kink oscillates each strand instead of
  bending all strands one way, so at amplitude 0.003–0.030 m it reads as
  texture, not streaming. The record already knows this: `bend_vector` is
  a **reserved** field with the note that true root-to-tip bend is an
  engine-side groom-blend field the Blender prototype does not apply.
  `wind_swept` is a correct *record* carried by an approximation.

### 3.4 What the prototype proves / does not prove

Proves: (1) one groom + delta records → materially distinct coats with zero
re-grooming — the state mechanism works end-to-end in the tool the grooms
live in; (2) the delta grammar of §2 is sufficient to *record* wet and wind
losslessly (resolved values reproduce the design arithmetic to float
precision); (3) states cost nothing at author time — three full state
objects + records + renders from one script run.

Does not prove: directional wind (above); any masked or patchy state;
any colour-population state; partial weights or state×state blends;
behaviour on cards/shells (§6); behaviour on the GeoNodes groom that A3
made the authoring route — the grammar is groom-agnostic, the *bindings*
in §2 are particle property names, and GN bindings are future work.

---

## 4. States in the character record (proposal)

Definitions live in the library; the record stores weights. This is A7's
paintmap discipline applied to states — the record stays small, share codes
stay meaningful, definitions stay shared and versioned:

```json
"fur": {
  "profile": "species.wolf.coat",
  "paintmaps": { "set": "furp.wolf.bara", "base": "bara_wolf", "revision": 2,
                 "author": "hand-painted", "data": "library/fur/…" },
  "states": [
    { "id": "wet_clumped", "weight": 0.0 },
    { "id": "wind_swept",  "weight": 0.0, "axis": [1, 0, 0] },
    { "id": "season.summer", "weight": 1.0 }
  ],
  "overrides": { "torso.back.density": 0.9 }
}
```

Rules:

- **Definitions** ship as `library/fur/states/<id>.json` in the
  `anthroforge.fur_states v1` shape (delta grammar of §2, canonical region
  names). `fur_states.json` from the prototype is the seed for
  `wet_clumped` and `wind_swept`, after the §2 region rename.
- **Evaluation order** at groom-build time: profile regions → state deltas
  (in record order, each at its weight, masked states through their mask)
  → the groom is derived. Paintmaps remain the authority for groom
  mechanics (A7 §3): a state multiplies the converter's derived parameters
  and the material, it does not write the maps. Record `overrides` still
  apply last, as today. Per A7's rule, **resolved groom parameters are
  derived, never stored** — the record stores weights, the builder applies
  definitions.
- **Masks**: a state definition may name a mask — a `FURP_` scalar layer
  (propose per-state layers in the character's paintmap set,
  `FURP_state_<id>`, seeded procedurally and hand-fixable, HF9 discipline:
  tooling may re-seed an unpainted mask, never a painted one) or a markings
  layer. Masked application is per-vertex: `delta × weight × mask`.
- **Graceful degradation**: a recipient without a state definition renders
  dry for that state and the share-code/export report **names the missing
  state** — §9.8's "fur is never silently dropped" applied to conditions.
- **Season folds in**: A19's `seasonal.summer` block becomes the definition
  of state `season.summer`; profiles keep shipping their summer scalars as
  that state's deltas. One mechanism, no special case. (Proposal — A19's
  shipped JSON keeps working unchanged until the format adopts it.)

---

## 5. The two unbuilt states, specified

All numbers in this section are **[E]** in A19's sense: design values ordered
by the physics, with no build behind them.

### 5.1 `matted` — mask-required

Global delta set (applied *through the mask*, never bare):

- `clump_factor`: `min(1, 1.6x + 0.35)` — beyond wet; mats are clumping
  that has forgotten how to let go
- `clump_shape`: set −0.95; clump noise on, `clump_noise_size` 0.6
  (coarser lumps than wet's 0.35)
- kink: amplitude ×0.15 but amplitude/axis randomness **up** (0.4 / 0.5) —
  inside a mat, strand direction is disorder, the opposite sign from wet's
  orderly damping; this asymmetry is deliberate
- `roughness_endpoint` +0.30 (felted surface reads rough at the tips that
  escape), `hair_length` ×0.97 (mats sit close to skin)
- material: Roughness 0.55, Color ×0.80 (grime worked into the felt)

The mask is the state. Mats form where fur is long × friction × neglect:
ruff underside, belly, behind the ears, tail base, armpits. Seed =
`FURP_length`-weighted region prior, hand-correctable per A7's brush set.
Applied globally, this delta set felts the muzzle and ear furnishings too
— visibly wrong — which is why matted was **not** prototyped with the
global-only machinery of §3: the honest prototype of matted is a masked
build, and it waits on the mask plumbing of §4.

### 5.2 `dirty_aged` — two mechanisms, one slot, kept separate

**Soiling** (surface, reversible, a true groom/material state):

- zone colour: tip-weighted darkening through `FURP_zone_tip` modulation —
  tips ×0.70 lightness with a grey-brown hue pull (dust sits on the outside
  of the coat); roots ×0.90
- material Roughness +0.15 (dull), Coat 0; `clump_factor` +0.10 (grime tack)
- spatial prior: ventral/lower-body weighted (splash zone) — a height×region
  mask seed, same plumbing as §5.1

**Greying** (follicle-level, permanent, **not a groom delta**):

- A fraction `p` of strands lose pigment: root and tip both go silver-white
  and the A11 pattern function is overridden per strand. In strands this is
  a per-strand pigment flag thrown at groom-build; in cards it is a
  population mix in the bake. Either way it belongs to A11's
  colour-population model, and the state record carries it as data, not as
  groom fields: `"greying": { "fraction": 0.35, "distribution":
  "muzzle-first" }` (muzzle/ears first, or diffuse).
- The groom delta set for greying is **empty by design**. Any
  implementation that greys by tinting the material has modelled a dusty
  dog, not an old one — at strand distance the two are distinguishable
  (mixed silver strands vs uniformly dulled strands) and A11's distance
  rule (population borders survive, banding vanishes) is exactly the test.
- Boundary question, flagged for the format owner: age-related *thinning*
  (`density` scale < 1) looks like a character-age axis on the profile, not
  a condition state. Recorded here; not folded into the state.

---

## 6. Honest limits

- **One groom, one species, one camera.** The bara-wolf stage-2 particle
  groom at prototype lengths (A19 notes it runs ~1.5× long vs the real
  wolf — a stylisation, kept). State *deltas* are relative and should
  transfer; the resolved numbers will not.
- **The material half ran on the wrong shader.** The source groom's hair
  slot is a Principled BSDF, so the prototype's material deltas were
  name-mapped onto a surface shader. Direction of every delta is faithful
  (darker, smoother, coated when wet); **magnitudes are not calibrated**
  to the hair-BSDF values the records are written in — wet Roughness 0.24
  on a surface BSDF reads glossier than the hair terms would. The records
  keep the normative hair-BSDF numbers; the renders are evidence for the
  mechanism, not for the exact values. `Radial Roughness` deltas are
  recorded and were **not applied** (no analog input) — see
  `material_unapplied` in the JSON.
- **Wind is a record in search of a mechanism** (§3.3). Until the
  engine-side bend field exists, `wind_swept` should not be presented as
  a solved look; in stills it is a subtle texture change.
- **Blending is specified, not demonstrated.** No partial-weight or
  wet+wind render exists; the enum-switch rule for kink type is a proposal.
- **Cards/shells behaviour is an open pipeline decision.** §9.8 bakes fur
  per format. A state can re-bake, or modulate the baked cards' shader —
  A12's sheen/clearcoat carriers can do *wet* convincingly at shader level,
  but clump geometry cannot be faked by a shader. The cheap 80% (shader-
  only wet on cards, full states strand-only) is noted, **not decided here**.
- **GeoNodes bindings are future work.** A3's verdict made GN the authoring
  route going forward; §2's bindings name particle properties. The delta
  grammar and record shape carry over unchanged; the binding table needs a
  GN column when the first GN groom takes states.
- §5's numbers are design estimates [E], and §5.1's core claim — that
  matted *requires* the mask — is argued from the delta set's behaviour,
  not from a failed global build.

---

## 7. Deliverables

| File | What |
|---|---|
| `FUR_STATES.md` | this doc |
| `fur_states.json` | state records v1: baseline + wet/wind delta sets + fully resolved per-state snapshots |
| `fur_states.blend` | the three state objects on the stage-2 groom (`fur_state` property per object); JSON also embedded as a text block |
| `render_dry_neutral.png` / `render_wet_clumped.png` / `render_wind_swept.png` | the three state renders (§3.3) |
| `work/build_states.py` | the original agent's script, untouched |
| `work/build_states_run.py` | the finisher's patched run copy (patches documented in its header + §3.2) |
| `work/probe_keys*.py`, `work/probe_mat.py` | the original key-editing probes; the finisher's material probe |
| `work/build_run.log`, `work/build_run2.log` | the failed first run (IndexError, §3.2) and the clean run |

Disk: the pass added ≈ 25 MB (one .blend, three renders, one JSON); free
space stayed at/above the 55 GB floor throughout.
