# Species-Aware Anatomy Authoring System

**Status:** implementation contract / next build slice, 16 Nov 2026  
**Scope:** editable anatomy modules in the desktop creator, across supported species and body plans. This document defines the data and interaction contract; it does not claim that every listed species mesh or runtime control has shipped.

## 1. Product rule

Anatomy is a first-class, optional, swappable part family. The creator must never assume one universal mesh, one fixed count, or one universal pelvis transform. A species preset proposes compatible parts and parameter defaults; every choice remains editable after applying the preset.

The app has two distinct layers:

- **Anatomy family:** a reusable design family (canid, feline, equine, draconic, avian/gryphon, aquatic/serpentine, custom).
- **Part implementation:** a concrete mesh, rig, weights, morph channels, fit data, material zones and supported body-plan instances.

A family is not itself a mesh. A part can declare several compatible species tags, but compatibility is explicit and fit-tested.

## 2. Initial species pack matrix

This is a content roadmap, not a claim that all assets already exist.

| Family | Initial variants to author | Geometry/rig traits that must be independently authored |
|---|---|---|
| Canid / vulpine | wolf, fox, fennec | sheath profile, optional knot feature, paired tissue forms, tail/coat fit |
| Feline | domestic cat, big cat, snow leopard | feline-specific profile and base fit; do not alias to canid |
| Equine | horse, donkey, zebra | equine pelvis fit and species-specific proportions |
| Draconic / reptilian | dragon, wyvern, drake | scale-aware surface fit, optional external sheath/crest variants |
| Avian / gryphon | bird, gryphon | avian pelvis fit; feathers and tail clearance |
| Serpentine / aquatic | naga, aquatic hybrid | plan-specific ventral placement and coil clearance |
| Custom | user-authored | user-supplied mesh, explicit compatibility declaration and validation |

The initial shipping target is a small, quality-controlled pack (one canid, one feline, one equine, one draconic, one avian/gryphon, plus the existing Kaleaon biped reference assembly). Additional variants are added by data, not by branching the editor code.

## 3. Part and assembly model

Use one assembly manifest at `pelvis.genital` with child components. The parent owns the socket fit and body-plan placement; children own their own mesh, weights, morphs, and animation/dynamics profile.

Required assembly fields:

- `id`, `kind`, `version`, `class`, `tier`, `size_class`
- `species_tags`, `plan_fit`, `socket_by_plan`, `variant_by_plan`
- `components[]` with stable IDs and parent relationships
- `rig.bones[]` and per-component skin mode / weight asset
- `morph_channels[]` with stable IDs, range, default, units, and affected component IDs
- `fit_qa` with base ID, score, tool/version, and notes
- `conflicts[]`, material zones, LOD references, licence/provenance

The assembly can contain a variable number of components. Four shafts, a single external module, paired modules, a sheath-only configuration, and null/SFW geometry are all data configurations—not hard-coded special cases. The Kaleaon reference is represented as four independent shaft components plus a shared sac assembly and separately attached sub-parts, but it must not become the default anatomy for other species.

## 4. Editability contract

All editable values are stored in the character record by stable channel ID, never by UI label or array index.

| Editor group | Channel families | Required behaviour |
|---|---|---|
| Configuration | part selection, component count/visibility, variant | Equip/unequip, reorder only where topology permits, reset to preset |
| Proportions | length, base/mid/tip girth, taper, curvature, spacing, angle, placement | Independent per component; linked symmetry is an explicit reversible mode |
| Shared tissue | volume, drape, attachment, separation, clearance | Shared assembly controls plus optional per-component overrides |
| Surface | material, roughness, colour zones, texture scale | Per material zone; does not mutate geometry |
| Rig | bone scale, chain pose, limits, weight profile | Preview pose and restore neutral; never silently convert a length control into a shape key |
| Dynamics | stiffness, damping, gravity, collision radius, follow lag | Per chain/component, with conservative safe defaults |
| Fit | socket offset, rotation, scale, per-plan variant | Plan-specific values; changing body plan re-solves fit and reports unsupported variants |

Rules:

1. **Length is a rig/transform channel** where the part contract defines a chain; girth and local profile are morph channels. Do not mix these semantics.
2. Every channel exposes name, unit, min/max, default, current value, and a reset action. Ranges come from authored QA, not arbitrary UI constants.
3. Symmetry is a reversible editor mode. Asymmetry is saved per component instance.
4. Each component can be selected in the viewport and isolated, hidden, locked, duplicated, or reset.
5. A parameter change is one undoable command. Undo/redo must restore both character data and evaluated geometry.
6. Save/reopen must preserve all component IDs, channel values, local transforms, plan instances, and symmetry flags.
7. UI visibility is adult-content gated; the core validator still checks structural integrity. An application preference is not age verification.

## 5. Species and body-plan compatibility

Reuse the normative four plans from `BODY_PLANS.md`: biped, quadruped-taur, quadruped-feral, and naga.

A module equips only when all conditions pass:

- The active plan provides the declared socket.
- The plan is explicitly listed or the module has a plan-agnostic declaration and a passing fit score for that plan.
- Required fit regions exist.
- The plan-specific transform/variant exists.
- No plan-scoped conflict remains unresolved.
- The module's size class is within the socket's allowed adapter range.

Never copy the biped transform to taur, feral, or naga. On plan switch, retain the unequipped module in inventory and preserve its last plan instance.

## 6. Viewport workflow

The anatomy editor is a dedicated tab in the part inspector, not a separate app.

1. Choose an anatomy family and compatible module.
2. Select an assembly or a child component in the viewport/outliner.
3. Edit grouped channels with numeric entry, slider, reset, and optional symmetry link.
4. Toggle neutral / preview poses and show rig, socket, collision, and fit overlays.
5. Run local validation; each warning points to the affected component and offers focus/isolate.
6. Save the character; export runs the same resolver and geometry assembly used by the viewport.

The UI must display the active plan, selected part ID, compatibility status, fit QA, triangle/bone/morph cost, and whether the current geometry is preview-only or export-resolved.

## 7. Validation and export gates

Hard failures:

- missing mesh, rig, or weight asset for a required component
- duplicate stable component IDs or broken parent references
- non-finite transforms/vertices or invalid channel ranges
- unknown species/body-plan identifiers
- unsupported plan with no declared variant
- socket collision or fit below the part-class minimum
- missing required bones, weights, or material zones
- invalid morph target or out-of-range saved channel value

Warnings (must be visible in the report):

- partial fit score, documented clearance risk, high complexity cost
- dynamics profile not authored for a target runtime
- export profile must bake or omit a channel
- untested pose or species/plan combination

Export must resolve: base + sliders + selected parts + component transforms + morphs + skin weights + materials + rig + dynamics metadata. The exported geometry must match the viewport's evaluated geometry. If a target format cannot represent a feature, the export report names the baked, merged, omitted, or unsupported feature.

## 8. Required QA suite

- manifest round-trip and schema validation
- component add/remove/reorder and stable-ID persistence
- per-component controls do not affect sibling components
- symmetry on/off is reversible and round-trips
- body-plan switch preserves per-plan transforms and inventory
- fit checks on every declared species/base/plan combination
- extreme channel values do not create non-finite or degenerate geometry
- pose/collision suite for each authored rig
- save → reopen → preview parity
- preview → GLB/FBX/BLEND export parity
- adult-content preference off by default and does not bypass the app's age policy

## 9. Kaleaon reference integration

The existing Kaleaon build is a high-complexity reference fixture, not a universal template. Its source document records four independent shaft chains, a shared draped sac assembly, separately attached sub-parts, length-by-bone-scale, girth-by-morph, and measured static QA. Preserve that design as a named preset and use it to test variable component counts and shared/child hierarchy.

Before it is selectable in the production library, stage the actual part assets, author a native AnthroForge rig/weight mapping (the current source build uses a foreign 89-bone host rig), provide per-plan fit records, and verify the unified viewport/Core/export path. Do not infer that the existing host GLB is already compatible with the canonical 36-bone rig.

## 10. Delivery sequence

1. Schema + manifest loader + validator.
2. Generic assembly resolver with arbitrary child component counts.
3. Character-record persistence and undo/redo for anatomy channels.
4. Viewport inspector and component selection.
5. One complete canid and one complete feline module with authored weights and QA.
6. Equine, draconic, avian/gryphon and serpentine plan variants.
7. Kaleaon fixture migration and viewport/export parity.
8. Runtime-specific dynamics/export adapters.

**Definition of done:** a user can select a species module, edit every declared channel, save/reopen it, switch supported body plans without losing edits, preview rigged poses, and export the same resolved assembly with an honest conformance report.
