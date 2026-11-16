# Kaleaon — Creator Reference Profile

**Status:** reference profile / integration specification. This file does not claim that the anatomy assembly is already loadable by the app.

## Visual reference

Source: user-supplied Kaleaon turnaround and expression sheet (front, rear, and head views).

### Silhouette and body
- Broad, heavily muscular upper torso with pronounced shoulders, chest, arms, forearms, and abdominal definition.
- Large, rounded lower-body silhouette with compact digitigrade-looking feet/paws.
- Long, flexible tail.
- Shaggy feline-like head with a broad muzzle, small rounded ears, large cheek/neck ruff, and glasses.
- Preserve the reference's deliberately stylised proportions; do not silently normalise toward a human base.

### Coat and palette
- Main coat: warm off-white / very pale grey.
- Markings: irregular soft grey spots, especially across shoulders, upper arms, and thighs.
- Secondary shading: muted mauve/lilac around the ruff, limbs, and underside.
- Nose and small accents: muted pink.
- The swatch strip includes muted green, off-white, burgundy, near-black, mauve, and greys. Treat these as editable palette seeds, not locked material values.

### Outfit / accessories
- Dark harness straps across chest, back, upper arms, and waist; separate wearable parts, not painted onto the body.
- Dark waist belt with a central metal fitting.
- Glasses are a separate head accessory with editable frame and lens materials.

## Anatomy assembly target

The user explicitly requests a four-unit genital configuration and a hyper-scale shared sac. The repository already contains a separate Kaleaon anatomy build documented in:
anthroforge-v2/parts-lab/kaleaon-anatomy/KALEAON_ANATOMY.md

That build describes four independently articulated shaft meshes, each with its own two-bone chain; a large draped sac assembly with four independently attached teat sub-parts; per-unit length controlled by bone scale and girth controlled by blendshapes; and a shared pelvis socket with a scale exception for the hyper-scale character.

Treat the existing Blender/GLB assembly as the source asset and measured geometry baseline. Do not replace it with guessed primitive geometry or collapse the four units into one mesh/control.

## Required creator behaviour

1. The preset must be selectable as a starting character, but every feature remains editable.
2. The anatomy assembly is one socket occupant (pelvis.genital) containing multiple internal meshes. The four units are not four competing occupants of the same socket.
3. Expose independent length and girth controls for each of the four units, plus assembly-level positioning and sac volume/drape controls.
4. Preserve independent articulation and avoid cross-talk between units.
5. Keep the sac and its attached sub-parts in a shared deformation hierarchy; validate root attachment through motion.
6. Provide per-body-plan socket transforms. Do not reuse biped coordinates for taur, feral, or naga.
7. The adult-only module gate remains default-off and must be combined with the application's actual age/account policy; a UI preference is not age verification.
8. The same resolved geometry and rig must drive viewport preview and GLB/FBX/DAE/BLEND export. A saved character record must reproduce the same result.
9. Include pose-suite checks for ground clearance, body/limb collision, shaft-to-shaft cross-talk, sac drape, teat-root attachment, non-finite geometry, degenerate faces, and skin-weight integrity.

## Integration blockers (must be closed before calling this app-creatable)

- The current Python build_character() path exports the base mesh and slider deformations; it does not assemble anatomy parts into the exported GLB.
- The current anatomy manifest validator verifies metadata and LOD0 file presence/size, but does not parse the GLB or inspect mesh names, skeleton bindings, vertex groups, morph targets, or collision results.
- The existing Kaleaon anatomy deliverables are documented in the v2 parts-lab; they have not yet been staged as a loadable asset under the app's library/parts tree.
- A creator preset must not be marked export-ready until the real asset is staged, loaded by AnatomyLibrary, assembled by the Core Service, and passed through the export QA gauntlet.

## Acceptance criteria

- [ ] Kaleaon appears in the app's preset picker and loads its visual profile.
- [ ] The viewport shows the reference silhouette, coat, markings, tail, face, glasses, and harness.
- [ ] The anatomy module loads as one socket occupant with four independently controllable/articulated units and the shared sac assembly.
- [ ] Save/reopen round-trip preserves all settings.
- [ ] Viewport and exported GLB match.
- [ ] Blender/Unity export checks and the complete anatomy pose suite pass.
