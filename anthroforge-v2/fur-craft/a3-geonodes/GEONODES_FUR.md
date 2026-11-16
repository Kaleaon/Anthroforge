# A3 — Procedural Fur with Geometry Nodes — GEONODES_FUR.md

**Status:** prototype built and verified on the fur-prototype subject.
**Subject:** Bara Wolf base (`fur_stage1.blend`, object `BaraWolfBody`, 63,557 verts) — the same body, region maps, hair material, studio and hero camera as the particle-system prototype in `fur-prototype/`, so the two grooms are directly comparable.
**Deliverables:** `geonodes_fur.blend` (body + five per-region hair objects `AF_Fur_<region>` + curtain), renders in this folder, build script `work/build_geonodes_fur.py` (the whole pipeline is one reproducible script — rerun it and you get this file).

---

## 1. What Blender ships: the hair-curves node stack (study)

Since 3.3 and maturing through 4.x/5.x, Blender's hair system is *curves + Geometry Nodes*, and the particle hair system is legacy. The install's Essentials library (`5.2/datafiles/assets/nodes/procedural_hair_node_assets.blend`, inspected directly for this study) ships 31 production node groups in three families:

- **Generation:** `Generate Hair Curves`, `Interpolate Hair Curves`, `Duplicate Hair Curves`.
- **Grooming:** `Curl`, `Frizz`, `Clump`, `Braid`, `Roll`, `Smooth`, `Straighten`, `Trim`, `Shrinkwrap`, `Rotate`, `Displace Hair Curves`, `Hair Curves Noise`.
- **Plumbing:** `Curve Info / Root / Tip / Segment`, `Create Guide Index Map`, `Attach Hair Curves to Surface`, `Set Attachment Surface`, `Get Attachment Surface`, `Rest Surface`.

Two architectural facts drive everything below:

1. **Guides first, children by interpolation.** `Generate Hair Curves` distributes root points on the surface (its internals are `Distribute Points on Faces` → guide lines → `Interpolate Curves`), growing strands along the surface normal. `Interpolate Hair Curves` then densifies: it spawns child curves across the surface and shapes each from its nearest guides (inputs: `Interpolation Guides`, `Distance to Guides`, `Density`, `Density Mask`, Poisson-disk or random distribution). This is exactly the particle system's parent/child split — except it is a *node graph*, so it is inspectable, reorderable, and scriptable.
2. **Attachment is data, carried on the geometry (Blender 5.2).** A Curves object's `surface` + `surface_uv_map` properties make Blender inject the surface into the modifier's input geometry as a *geometry bundle*; the assets recover it with `Get Attachment Surface` (internally `Get Geometry Bundle` / `Separate Bundle`). **Consequence that cost real probe time:** if you nest `Generate Hair Curves` inside your own wrapper group, you must wire the wrapper's Group Input geometry into the asset's **`Hair Surface`** socket, or the bundle never arrives and the asset silently emits zero curves. With that link made, fields passed into the nested group (e.g. a Named Attribute driving `Density Mask`) resolve against the surface *inside* the asset — verified empirically: on a subdivided test plane, a vertex-group mask confined 100% of roots to the masked half.

Grooming groups accept **field inputs** for most parameters, and `Curl`/`Clump` take `Guide Index` / `Guide Mask` / `Guide Distance`, i.e. they are designed to run *after* interpolation too, deforming children consistently with their guides via the guide-index map that `Interpolate Hair Curves` outputs. Parameter scripting caveat: node-group modifier inputs cannot be reliably assigned via `modifier["Socket_x"]` from Python (ID-property errors); the robust pattern used here is a **thin wrapper group per asset** whose inner group-node input defaults carry the parameters.

3. **Two field behaviours that shape the design (found empirically, probes 8–11):**
   - The generator's **Density Mask field works through the nesting** — a Named Attribute (vertex-group) field confined 100% of roots to the masked half of a test surface.
   - The generator's **Hair Length field does not** — in the nested configuration, strands come out a uniform ≈0.03 m regardless of the field, whether the field is a math tree, a single attribute, or baked per-vertex. A **constant** Hair Length works exactly (curtain strands measure 0.30 m at a 0.30 setting). Consequence: per-region lengths are achieved by **per-region hair objects with constant lengths** (§3), not by one object with a length field. This mirrors the particle architecture (one system per region) and turns out to be a clean split: each region object also gets its own grooming stack for free.
   - A related readout trap: freshly generated curves' stored `position` attribute reads as **zero-length** (all points at the root) until a shape-rebuilding grooming node (Curl/Clump/Frizz) has processed them — the shape lives in the generator's curve offsets until then. Measure lengths *after* a grooming node, and set Frizz **Preserve Length = True** (its default False contracts strands, which otherwise masquerades as a length error).

## 2. The GeoFeathers pattern (study — product not downloaded)

MiauArts' **GeoFeathers 1.2** (Gumroad, licence unstated → study tier in our library manifest; described here from its product page, not hands-on) is the feather analogue of this fur stack and validates the same architecture from the opposite direction: instead of curves, it distributes *structured geometry* — a parametric feather (shaft + barb "fur" density, fuzziness and shape controls, per its page) — with 1.1 adding asymmetric feathers and **non-constant barb distribution (fluffier near the base)**, and 1.2 adopting the Blender 4.x panel inputs and converting to the new hair system. Lessons for AnthroForge:

- The distribution + per-instance-parameter pattern is identical; only the payload differs (curves for fur, instanced structured geometry for feathers). Our region plumbing (§3) transfers directly: a feather system would read the same `FUR_*` maps as per-region density/length parameters for instances.
- "Non-constant distribution along the strand" (GeoFeathers' base-heavy fluff) is the feather version of a lesson our groom also needs: density/length *along* the curve is a parameter, not a constant — in fur terms, that's taper/profile (`Set Hair Curve Profile`) and root-vs-tip frizz shaping.
- Third-party GN systems ship as **node-group assets with exposed panels**, not plug-ins — the same packaging our `AF Fur Generate` wrapper uses, so artist tooling and pipeline tooling stay the same artefact.

## 3. The prototype graph — five region objects

**One Curves object per region** (`AF_Fur_ruff`, `AF_Fur_back`, `AF_Fur_belly`, `AF_Fur_coat`, `AF_Fur_bodyhair`), each attached to the body and carrying the same six-modifier stack (wrappers around shipped assets). The split is forced by finding §1.3 — the generator's Hair Length field doesn't survive nesting, but a constant length does — and it matches the particle prototype's one-system-per-region structure:

```
AF_Fur_<region> (Curves, surface = BaraWolfBody, uv = tripo_node_0ffa5503DiffuseUVLayer)
├─ 1  AF Generate <region>  (wrapper → Generate Hair Curves:
│                            Density Mask = FUR_<region> field, Hair Length = region constant)
├─ 2  AF Smooth             (Smooth Hair Curves:  Amount 0.35, Iterations 4)
├─ 3  AF Curl               (Curl Hair Curves:    Factor 0.55, Radius 0.014, Random Offset 0.35, Curl Start 0.15)
├─ 4  AF Clump              (Clump Hair Curves:   Factor 0.45, Shape 0.6)
├─ 5  AF Interpolate <region> (wrapper → Interpolate Hair Curves:
│                            Density Mask = FUR_<region> field again, Distance to Guides 0.03,
│                            Guides 4, Follow Surface Normal, Density = calibrated per region)
├─ 6  AF Frizz              (Frizz Hair Curves:   Factor 0.5, Distance 0.006, Preserve Length True)
└─ 7  AF Radius             (Set Curve Radius, tapered root 0.0011 m → tip 0.00025 m
                             via Spline Parameter factor — corrective pass, §5)
```

**Inside `AF Generate <region>`** — the AnthroForge-specific part: a Named Attribute node samples the region's `FUR_<region>` vertex group and feeds the asset's **Density Mask** socket; the asset's **Density** is the guide density and **Hair Length** the region's constant length. Per-region lengths are held at particle-prototype parity for an honest A/B: ruff 0.170 / back 0.095 / belly 0.042 / coat 0.066 / bodyhair 0.018 m. Because the region maps are smooth overlapping fields (not a partition), each region object's guides concentrate where its field dominates and feather out across borders — measured: 64.1% of the coat object's guide roots are coat-dominant, the rest spread over neighbouring fields, exactly the particle behaviour.

Guide counts are **calibrated in the build script**: a first pass at a probe density measures each region's yield, scales densities by target/guide ratio (one feedback step landed 13,498 vs the 13,500 guide target), and the per-region **Interpolate density** is then computed as (region's share of the ≈85–90k child budget) ÷ (region's effective surface area = guide count ÷ guide density). Children totals land at 85,413 vs the particle groom's 89,100.

**Grooming choices** deliberately answer the particle prototype's documented flaws: its WAVE/CURL kinks at high amplitude read *woolly/poodle* and directionless. Here curl is small-radius (14 mm) and moderate, frizz distance is 6 mm (below the asset's 10 mm default), and smoothing runs first so interpolation kinks don't survive — the aim is a sleeker, laid coat. Clumping stays moderate so silhouette doesn't go stringy. The stack is identical per region in this prototype; because each region is its own object, per-region grooming variation (the thing the particle design gets from per-system settings) is available by editing that object's wrappers — no extra plumbing needed.

**Parameters exposed for art direction** (edit the wrapper groups' inner node defaults, or rebuild with different constants): per-region guide density + seed, per-region constant length, per-region children density, and each grooming wrapper's parameter set.

## 4. The curtain (card-bake source)

`CurtainSheet` (1.1 × 0.55 m subdivided grid, vertical) + `CurtainHair` (attached curves):

```
AF Curtain Generate (Generate Hair Curves: Density 42,000/m², Hair Length 0.30, mask = 1)
→ AF Curtain Rotate (Rotate Hair Curves: Axis X, Angle +105°, Random Offset 0.12)  — swings strands to hang
→ AF Curtain Frizz  (Frizz: Factor 0.5, Distance 0.008)
```

`curtain_card_texture.png` is the bake: the curtain rendered alone, orthographic, on transparent film at 512×1024 — a drop-in replacement for the particle curtain bake (`fur_card_texture_a/b.png`), produced from a *parametric* curtain whose density, length and waviness are three numbers. The build script verifies the hang direction from evaluated tips (mean tip below mean root) and flips the rotate angle automatically if the sign convention differs — it did engage here (the −105° convention pointed tips *up* on this sheet orientation; final angle +105°). The beauty render (`render_curtain.png`) confirms it visually: a clean brown fringe hanging below the sheet's lower edge. The curtain keeps the generator's default (thicker) strand radius on purpose — card alpha wants visible strand width.

## 5. Measured results

| Metric | Particle prototype | This GN prototype |
|---|---|---|
| Guides / parents | 15,500 | **13,498** |
| Rendered strands total | 89,100 | **85,413** children |
| Bodyhair strands | 3,900 | 8,157 children (+1,325 guides) |
| Full-stack eval (this VM, contended) | n/a | guides ≈2 s; full stack ≈36 s |
| Hero render | — | 774 s wall at peak contention; **95 s** on re-render once the fleet drained (720×900, 32 samples, denoise) — the pipeline is not slow, the shared VM was |

Per-region results (lengths measured on the full evaluated stack, per object):

| Region | Guides | Children | Mean strand length | Target | Note |
|---|---|---|---|---|---|
| ruff | 2,332 | 14,724 | 0.167 m | 0.170 | on target |
| back | 2,399 | 15,397 | 0.105 m | 0.095 | +11% |
| belly | 971 | 5,983 | 0.061 m | 0.042 | +45% — children inherit guide shape across region borders |
| coat | 6,471 | 41,152 | 0.077 m | 0.066 | +17% |
| bodyhair | 1,325 | 8,157 | 0.038 m | 0.018 | +111% — shortest region, worst overshoot |
| **total** | **13,498** | **85,413** | | | |

Guide placement (coat object): 64.1% of guide roots sit on coat-dominant vertices; the remainder spread across the overlapping ruff/back/belly/bodyhair fields — the maps are smooth fields, not a partition, same as the particle design.

**Look, honestly (first pass):** the hero render read denser, softer and more voluminous than the particle groom, with visibly clumped locks — and **paler**: the same nominal hair colour (Principled Hair 0.30/0.21/0.14; verified present on the evaluated curves, so not a material-assignment failure) rendered cream-tan, and the close-up showed why: the generator's default strand radius is ribbon-thick (≈5–9 mm wide strands at close range — shredded-paper, not hair). The "woolly" failure mode was reduced versus the particle groom (tangled wire → clumped locks) but the radius flaw dominated at close range. Pre-fix renders are preserved as `work/prefix_hero.png` / `work/prefix_closeup.png`.

**Corrective pass (applied, and what the shipped renders show):** a final `AF Radius` modifier on each region object — Set Curve Radius driven by Spline Parameter factor, tapering root 0.0011 m → tip 0.00025 m. The blend and the headline renders (`render_geonodes_strands.png`, `render_geonodes_closeup.png`) include this pass; the build script emits it as stack step 7, and `work/finish_a3.py` is the patch that applied it to the already-built blend. The close-up transforms: ribbons become individual strands, clumps read as fur tufts, the muzzle shows through the ruff. It also exposes the honest trade-off — at particle-parity strand counts, hair-thin strands **under-cover**: the torso reads patchy where the thick-radius version (and the particle groom) read continuous. The fix is a budget change, not an architecture change — raise the Interpolate density (one number per region) or split the difference on root radius (≈0.0016 m) — but as shipped, coverage is the GN groom's remaining visible deficit at close range, and the taper values are a first pass, not art-directed. The pale cast persists in the body renders (the curtain bake, same material, renders properly brown against transparency) — a lighting/scattering interaction not isolated in this pass.

## 6. Verdict — GN vs particle system for authoring grooms

**Author grooms in Geometry Nodes. The particle groom should become the legacy reference.** Reasons, in order of weight:

1. **Blender's own direction of travel.** Hair curves + GN is the actively developed system (new bundle-based attachment in 5.2, a full grooming asset library in Essentials); particle hair has been in maintenance for years. AnthroForge tooling should not deepen its investment in the deprecated stack.
2. **The groom is code.** The entire GN groom — generation fields, grooming stack, children calibration, curtain — is one deterministic Python script that rebuilds the .blend from the stage-1 region maps. The particle groom is UI state scattered across five particle-system panels; the prototype's own history shows the cost (a restart mid-run forced a forensic recovery pass; the GN build just reruns).
3. **Deformation behaviour.** Surface-attached curves follow the surface (attachment + rest-surface machinery is built into the assets), so the groom survives re-posing the body. The particle prototype groomed the *posed frame* and lists that as a known limit.
4. **Children are a first-class, guidable stage.** Interpolation with guide-index output means clump/curl can be applied to guides and *inherited* by children, or applied post-interpolation with guide awareness — strictly more control than per-system particle children, whose parameters live and die inside each system.
5. **Region parity is real, structured the same way.** The GN build ended up mirroring the particle structure — one object per region, each with its own length, densities and grooming stack — because the generator's length *field* doesn't survive nesting (§1.3). Per-region grooming variation is therefore available the same way particles offer it (edit that region's stack). What GN adds on top: the whole thing is one script, and region maps stay live fields for density, so re-cutting regions means repainting vertex groups, not rebuilding systems.

**Limits found (honest):**
- **The generator's Hair Length field doesn't work in the nested (wrapped) configuration** in Blender 5.2.3 — fields of any construction produce a uniform ≈0.03 m. Constant lengths work. If a future Blender fixes field-driven length through wrappers, the five objects could collapse back into one; until then per-region objects are the architecture. (Not verified: whether the field works when the asset is used *unwrapped*, as a bare modifier — the wrapper pattern is what our scripting requires, so that path wasn't pursued.)
- **Children overshoot short-region lengths.** Interpolation shapes children from nearby guides; at region borders the longer neighbours win, so belly lands +45% and bodyhair +111% over target while long regions are accurate. Mitigations for a production pass: tighter `Distance to Guides`, a post-interpolation Trim scaled by a root-sampled length attribute, or denser guides in short regions.
- Nesting the shipped generator inside a wrapper only works if the input geometry is wired to its `Hair Surface` socket (bundle-carried attachment, §1) — undocumented in the manual pages we checked; found by reading the asset's internals and bisecting with probes.
- Modifier input values can't be set reliably from Python; every parameterized asset needs a wrapper group (visual clutter: six modifier entries per region object).
- Strand **radius profile** ships at the generator default, which renders as ribbons at close range — the corrective pass (§5) adds a Set-Curve-Radius taper as a separate modifier. A production groom should fold radius into the generate step and art-direct it per region (guard-hair vs undercoat widths); here it is one global taper.
- Evaluation cost: DISTRIBUTE+INTERPOLATE on a 63k-vert surface is noticeably heavier per iteration than toggling particle systems. Render times on this shared VM swung 8× with fleet contention (hero: 774 s contended vs 95 s drained), so treat all timings here as environment reports, not pipeline benchmarks.
- The `Generate` asset's density is in curves/m² of *masked* surface; hitting an exact strand budget requires the calibrate-after-first-eval step the build script performs.

## 7. Files

| File | What |
|---|---|
| `geonodes_fur.blend` | body + 5× `AF_Fur_<region>` + curtain + studio |
| `render_geonodes_strands.png` | hero groom render (same camera/material as particle hero) |
| `render_geonodes_closeup.png` | ruff/coat boundary close-up |
| `render_curtain.png` | curtain beauty render |
| `curtain_card_texture.png` | 512×1024 alpha bake from the GN curtain |
| `work/build_geonodes_fur.py` | the full pipeline as one script (staged: build / render) |
| `work/finish_a3.py` | radius-patch + bake + re-render finisher (the combined render stage was interrupted during the bake; this recovered it) |
| `work/prefix_hero.png`, `work/prefix_closeup.png` | pre-radius-fix renders, kept as evidence for §5 |
| `work/probe1…probe11*.py` | the bisect probes behind §1's attachment + field findings |
