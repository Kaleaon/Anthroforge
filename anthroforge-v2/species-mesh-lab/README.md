# Species Mesh Lab — first procedural body blockout pass

This folder starts the actual species-body geometry track. It is deliberately an
**unrigged greybox stage**, not a finished furry avatar pack.

## Included

- `species_profiles.v1.json`: six independently parameterized profiles:
  wolf, big cat, horse, drake, gryphon, and naga.
- `scripts/build_species_blockouts.py`: Blender background builder that
  produces a named `.blend` source scene and `.glb` preview for each profile.
- Separate objects for torso, pelvis/chest volume, neck, skull, muzzle, ears,
  upper/lower arms, hands, leg segments, paws, and segmented tail. This keeps
  the blockouts easy to inspect and replace with production topology.
- Naga is treated as an axial body plan: the blockout omits biped leg stubs and
  uses a preliminary coil path. It is not yet a full-resolution serpent body.

## Build

From this directory:

```bash
blender --background --python scripts/build_species_blockouts.py -- --profile all --output ./out
```

Or select one profile:

```bash
blender --background --python scripts/build_species_blockouts.py -- --profile species.feline.big_cat --output ./out
```

Blender 5.2+ is the intended authoring runtime. The script writes a .blend and
a GLB per profile and stamps the profile ID, body-plan ID, and stage marker into
the scene custom properties.

## Geometry status and limitations

The generated parts are simple lofts and ellipsoids with no armature, authored
skin weights, UVs, groom, claws/hooves, wings, facial expression rig, or
production corrective shapes. The surfaces are not yet watertight as a single
body; overlaps are intentional at this greybox stage. Do not use these GLBs as
final VRChat/SL/print exports.

The first real-body milestone after this blockout is to replace the overlaps
with plan-specific continuous topology, then author the canonical rig and
weights, UV/material regions, and QA each species/plan combination. Do not
force every species into a single human-shaped body: quadruped-taur, quadruped-
feral, and naga need distinct axial/limb topology and locomotion.

## Reference assets

The supplied Google Drive folder could not be inspected in this session:
Google Drive access is disabled by the current workspace policy, and the
public folder URL did not resolve through the available browser. No geometry
or design claims in these files are attributed to that folder. Once the
reference assets are made available to the project workspace, compare them
against the profile proportions and update each profile with provenance and
fit QA.

## Next authoring passes

1. Continuous biped body shell with proper shoulder, pelvis, elbow, knee and
   ankle transitions.
2. Dedicated quadruped-feral and taur body builders (not merely biped limb
   placement changes).
3. Full naga axial tube with spline controls, variable cross-section, coil
   solver and ground-contact rig.
4. Species-specific heads, muzzle/mandible, ears, paws/hooves, claws, tails,
   wing mounts and coat surface zones.
5. Canonical rig, authored weights, corrective shapes, pose/collision tests.
6. Preview/export parity and GLB/FBX/BLEND validation.

## Acceptance gates

- Every profile builds without Blender errors.
- No zero-area faces, non-finite vertices, or inverted normals after shell pass.
- Species-specific silhouettes remain distinct at neutral and extreme slider
  values.
- Save/reopen preserves profile ID and component names.
- Rigged preview and exported geometry match within the project tolerance.
