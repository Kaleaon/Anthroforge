# Export Pipeline Prototype — Format Survival Report

**Subject:** AKM "Border Collie" anthro character —
`~/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models/border_collie.glb`
(parts-library shelf: AKM anthro bases). Chosen because it is the only library
candidate that exercises **every** survival category at once: a real skeleton
(66 joints), full skin weights, morph targets (3 meshes × 4 targets), 12
materials with textures, and an animation clip.

**Pipeline:** GLB → headless Blender 5.2.3 (import) → BLEND / FBX / DAE →
re-import each → measure. Baseline = the Blender scene after GLB import
(13 mesh objects, 8,799 verts, 8,649 weighted verts, 66 bones, 1 action with
245 fcurves, frames 0–199.2 @ 24 fps).

**Headline platform finding:** **Blender 5.2 removed Collada I/O entirely** —
`bpy.ops.wm.collada_export` / `collada_import` do not exist in this build
(verified by operator enumeration; only `export_scene.fbx` / `.gltf` remain).
The DAE therefore comes from a standalone writer in this prototype
(`scripts/dump_interchange.py` → `scripts/write_dae.py`, hand-authored
Collada 1.4.1), and DAE verification is a parse-back with **pycollada**
(an independent implementation), not a Blender re-import. APP_BLUEPRINT §10
must budget a dedicated DAE component — Blender can no longer be it.

---

## Survival matrix

| Feature | Source (GLB→Blender) | BLEND | FBX (Unity) | DAE (SL profile) |
|---|---|---|---|---|
| Bones | 66 | ✅ 66, names identical | ✅ 66, names identical | ✅ 66 by count; **joint binding names sanitised** (see below); originals kept in scene-node `name=` |
| Skin weights | 8,649 weighted verts, max 4 infl. | ✅ exact | ✅ exact counts; **empty vertex groups pruned** (cosmetic) | ✅ exact; per-vertex sums = 1.0000 after SL top-4 renormalise (0 verts needed clamping) |
| Morph targets | 3 meshes × 4 (`target_0..3`) | ✅ names + data | ✅ names + data preserved | ⚠️ data present as `<morph>` controllers (4 weights × 3 meshes); **names survive only inside target-geometry ids**; not scene-instanced (by design, see notes) |
| Materials | 12, 7 texture images | ✅ identical | ✅ 12/12 by name | ✅ 12/12 (bound as `sym-<name>` → `mat-<name>`), 7 images written to `textures_dae/` and referenced |
| Animation | 1 action, 245 fcurves, f 0–199.2 | ✅ identical (245 fcurves) | ⚠️ survives but **split into 4 actions, names mangled, baked** (669 fcurves), range shifted to f 1–200 | ⚠️ survives as **66 per-joint matrix clips**, resampled every 2nd frame (101 samples/ch), LINEAR interp |
| Meshes / verts | 13 objects / 8,799 verts | ✅ identical | ✅ identical | ✅ identical (14,707 tris = source poly count; source was already all-triangle) |
| Scale / dims | body mesh 139.8 × 129.7 × 89.7 (scene units) | ✅ identical | ✅ ±0.005 (axis-conversion rounding) | ⚠️ world transforms baked verbatim; **unit declared metre but data is cm-scale** (see defect note) |
| File size | 1.69 MB (GLB) | 1.38 MB | 3.59 MB | 5.58 MB |

### Worst loss per format

- **BLEND:** none. Native save is a perfect round-trip on every measured axis.
- **FBX:** the animation's *structure*. One action became four
  (`Object_5|Object_5|collie_skeleton|female_skeleton.000Action` for the bones
  at 669 baked fcurves, plus three `Key…|Object_5|…` actions holding the
  shape-key channels), all names re-prefixed, keyframes densified by baking
  (245 → 669 fcurves) and the frame range shifted +1 (0–199.2 → 1–200).
  Geometry, weights, bone names and morph names are untouched — but an
  FBX round-trip can never give you your action library back as authored.
  Secondary cosmetic loss: vertex groups with no nonzero weights are dropped
  (mesh `0`: 66 → 52 groups; mesh `1`: 66 → 2; mesh `2`: 66 → 1). Cross-checked
  against baseline nonzero-weight groups per mesh — the surviving sets match
  **exactly**, so no actual weight data is lost; only Blender's empty
  placeholder groups vanish.
- **DAE:** bone *binding* names. Collada ids/sids cannot contain `.`, so the
  skin controller's JOINT name array sanitises `ear_base.l_07` →
  `ear_base_l_07`: only 16/66 joint names are byte-identical in the binding
  (all `.l_`/`.r_` names change). The original names survive in the scene
  graph (`<node name="ear_base.l_07" type="JOINT">`), and weights reference
  joints positionally, so deformation is unaffected — but any downstream tool
  that matches joints by the controller's name array (Second Life does this)
  sees renamed joints. Secondary losses: split (custom) normals are averaged
  to per-vertex normals by the interchange dump, and animation is
  matrix-resampled rather than curve-faithful.

---

## Per-format settings used (exact, reproducible)

All commands run with `~/workspace/tools/blender/current/blender`.

### Stage 1 — import + BLEND + FBX (`scripts/export_all.py`)

```bash
blender -b --factory-startup --python scripts/export_all.py -- \
  out/_source_border_collie.glb out dumps
```

- Import: `bpy.ops.import_scene.gltf(filepath=SRC)` into a factory-empty scene.
- BLEND: `bpy.ops.wm.save_as_mainfile(filepath=…/border_collie.blend)`.
- FBX: `bpy.ops.export_scene.fbx(` `use_selection=False, global_scale=1.0,
  apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
  use_space_transform=True, bake_space_transform=False,
  object_types={'ARMATURE','MESH','EMPTY'}, use_mesh_modifiers=True,
  mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
  primary_bone_axis='Y', secondary_bone_axis='X',
  use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=True,
  bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True,
  bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True,
  bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='AUTO',
  embed_textures=False, axis_forward='-Z', axis_up='Y'` `)` — the Unity
  convention block (Y-up/−Z-forward, no leaf bones, FACE smoothing).

### Stage 1b/1c — DAE (`scripts/dump_interchange.py`, `scripts/write_dae.py`)

```bash
blender -b --factory-startup --python scripts/dump_interchange.py -- \
  out/_source_border_collie.glb dumps/interchange.npz dumps/interchange.json out/textures_dae
python3 scripts/write_dae.py dumps/interchange.json dumps/interchange.npz \
  dumps/anim_samples.npz border_collie_SL.dae
```

SL profile applied by the writer:

- `<unit name="meter" meter="1.0"/>`, `<up_axis>Z_UP</up_axis>` — Blender's
  native Z-up is what SL's Collada importer expects; no axis conversion.
- Skin weights: top-4 influences per vertex, renormalised to sum 1
  (this character needed no clamping: max influences in source = 4).
- Full 66-joint set written (no deform-only pruning).
- Geometry fan-triangulated per material group (no-op here: source already
  all-triangle, 14,707 tris in = out).
- Morphs: written as `<morph method="NORMALIZED">` controllers **sourced on
  the geometry**, and the visual scene instances the *skin* controller.
  Chained morph→skin controllers are legal Collada 1.4.1, but pycollada
  (verified) refuses them — `Morph.load` only resolves a geometry base —
  and SL's uploader ignores morphs entirely, so geometry-sourced morphs are
  the maximally compatible layout. The morph data is in the file and
  parseable; it is not scene-stacked.
- Animation: per-joint sampled local matrices every 2 frames
  (101 samples over 8.3 s @ 24 fps), `LINEAR` interpolation, channels target
  `<joint-node>/transform`.
- What the classic Blender ≤4.x operator call *would* have been (for the
  blueprint's records): `bpy.ops.wm.collada_export(apply_modifiers=False,
  export_animation=True, include_animations=True, include_armatures=True,
  include_shapekeys=True, deform_bones_only=False, triangulate=False,
  keep_bind_info=True)`.

### Stage 2 — re-import / verification

```bash
blender -b --factory-startup --python scripts/reimport.py -- border_collie_Unity.fbx dumps/reimport_fbx.json
blender -b --python scripts/reimport.py -- border_collie.blend dumps/reimport_blend.json
python3 scripts/verify_dae.py border_collie_SL.dae dumps/reimport_dae.json   # pycollada venv
```

- FBX import: `bpy.ops.import_scene.fbx(use_custom_normals=True,
  use_custom_props=True, ignore_leaf_bones=False,
  automatic_bone_orientation=False, primary_bone_axis='Y',
  secondary_bone_axis='X', use_prepost_rot=True, use_anim=True)`.
- DAE parse-back (pycollada 0.9.3): 25 geometries (13 base + 12 morph
  targets), 12 controllers (9 skin + 3 morph), 12 materials, 12 effects,
  7 images, 14 scene root nodes; up_axis/unit read back as written.

Raw measurement dumps for every cell of the matrix are in `dumps/`
(`baseline_from_glb.json`, `reimport_blend.json`, `reimport_fbx.json`,
`reimport_dae.json`, plus the interchange files).

---

## Defects & notes for the production pipeline

1. **Scale incoherence is inherited, not created.** The source GLB is a
   composite scene: the body meshes sit at ~140 scene units while the lab
   coat/props sit at ~0.5. All three exports preserve the world-space truth
   of the Blender scene. The DAE declares `meter=1.0` while its body spans
   139.8 units — uploaded literally to SL that reads as a ~140 m mesh and
   would exceed SL's 64 m per-dimension cap. **Fix for the real pipeline:
   a scale-normalisation pre-pass before the DAE writer** (pick the primary
   skinned mesh, scale the whole export so its height is real metres).
   Not silently applied here — the prototype's job is to measure the
   pipeline as it stands.
2. **SL joint naming.** SL avatar rigging matches joints by name against
   the SL skeleton (`mPelvis`, …). This character's 66 custom names
   (`pelvis_01`, …) would upload as a rigged *object*, not an avatar-worn
   deform rig, no matter the format quality. An SL-avatar profile needs a
   joint-rename map to Bento names as a pre-pass — orthogonal to DAE
   mechanics, and the sanitisation issue above (dots) disappears with it,
   since Bento names contain no dots.
3. **SL limits check (this file):** largest single mesh 4,051 verts /
   7,084 tris — well under SL's 65,536-verts-per-material-face cap; every
   mesh has exactly 1 material (SL allows ≤8 faces/object); ≤4 influences
   everywhere. Only the scale defect (note 1) would block an upload.
4. **Inspector caveat:** Blender 5.2 slotted actions hide fcurves behind
   `strip.channelbags`; the inspector in `scripts/inspect_core.py` handles
   both legacy and slotted actions. FBX's "4 fcurves" shape-key actions and
   669-fcurve bone action are counted on that basis.
5. **Unskinned passengers:** the source scene carries clipboard props and a
   stray Icosphere. All formats carried them through (13/13 objects); the
   DAE writes them as plain `instance_geometry` nodes. A production profile
   should let the user exclude non-character objects at export time.
