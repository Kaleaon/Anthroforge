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


## Second geometry pass: plan bodies and species modules

Additional builders now exist:

- `scripts/build_species_plan_meshes.py` creates separate feral quadruped,
  taur, and naga silhouettes. Feral uses a horizontal ribcage/abdomen/pelvis
  axis and four limb stations; taur combines an upper torso with a distinct
  quadruped lower body; naga uses a continuous variable-radius axial coil.
- `scripts/build_species_addons.py` creates species-specific head and
  extremity modules: canid pinnae, feline ears, equine ears and hoof caps,
  draconic horns/jaw fins/dorsal scutes, avian crest/wings/feather fan, and
  serpentine crest fins. Toe/claw objects remain separate for editing.
- `scripts/validate_species_mesh_lab.py` validates profile completeness,
  species-family coverage, positive dimensions, and Python syntax without
  requiring Blender.

Build the plan-specific meshes:

```bash
blender --background --python scripts/build_species_plan_meshes.py -- --profile all --plan all --output ./out/plans
```

Build species add-ons:

```bash
blender --background --python scripts/build_species_addons.py -- --profile all --output ./out/addons
```

Run the dependency-free checks:

```bash
python scripts/validate_species_mesh_lab.py
```

The plan builders currently emit distinct greybox shapes, not production
quad topology or rigged creatures. The accessory builder creates separate
parts, but attachment transforms and fit adapters still need to be authored
against each canonical species base. In particular, a gryphon wing module
needs a flight-ready shoulder rig, equine hoof placement needs fetlock/limb
validation, and the naga coil needs ground-contact and spline deformation
tests. The static validator does not substitute for Blender runtime tests.


## Adult-only parametric external-anatomy module

`anatomy_profiles.v1.json` defines six family-specific adult-only module
profiles: canid, feline, equine, draconic, avian cloacal, and serpentine.
The canid profile defaults to four independently named members, matching the
multi-member customization direction; the member count can be changed from
one through four at build time.

The scale multiplier is continuous from 0.15 to 8.0. It scales length, girth,
member spacing and shared sac dimensions together. The source profile also
defines the neutral dimensions and longitudinal shape stations. The Blender
builder writes separate base, sac, and member objects, plus an interim
segmented armature and per-member vertex groups.

Build an adult-only module:

```bash
blender --background --python scripts/build_adult_anatomy.py -- --profile adult_quad_canid --scale 1.0 --count 4 --output ./out/adult-anatomy
```

Other profile IDs: `adult_feline_modular`, `adult_equine_modular`,
`adult_draconic_modular`, `adult_avian_cloacal`, and
`adult_serpentine_modular`.

### Editing contract

The eventual creator UI should expose these as separate controls, not a single
"size" slider:

- Overall scale (0.15–8.0), plus independent length, girth and spacing.
- Member count (1–4) and per-member length/girth/curve/offset.
- Base volume and sac width/height/depth.
- Profile morphology and body-plan socket placement.
- Adult-only visibility/export gate, independent of ordinary character age
  metadata. This flag is not age verification; the application must enforce
  its own age policy.

### Accuracy and safety gates

These are procedural starting profiles, not validated species-specific
clinical anatomy. In particular, family labels do not imply that every
species in a family shares identical anatomy. Anatomical references and
expert review are required before calling a profile accurate. Do not infer
the user's character anatomy from unrelated references.

The current auto weights are a deterministic longitudinal placeholder, not
production skinning. The module still needs authored attachment transforms
for each body plan, collision volumes, extreme-scale clearance checks,
corrective shapes, pose/deformation tests, and round-trip preview/export QA.
At the maximum multiplier, the UI should warn when anatomy intersects the
thighs, abdomen, clothing, ground, or other modules; it must not silently
shrink the requested dimensions.

The builder exports a separate anatomy GLB and a Blender source scene. It is
not yet assembled into the character core or the Babylon preview. The next
integration task is to resolve the part manifest/socket, compose its geometry
and rig with the selected body plan, and export the same assembled result
that the creator previews.
