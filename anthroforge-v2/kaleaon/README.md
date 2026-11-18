# Kaleaon Sona — Reference-Informed Blockout

This is the first dedicated character asset pass for the Kaleaon creator profile.

## Included

- `kaleaon.v1.json`: editable profile and provisional dimensions.
- `scripts/build_kaleaon_blockout.py`: Blender background builder for a named-object greybox and GLB preview.
- Separate body masses, head/muzzle/ruff/ears, digitigrade limbs and paws, tail curve, harness straps, belt fitting, and glasses.
- A procedural off-white/grey coat material plus separate mauve, nose, harness, frame and metal materials.

## Important reference limitation

The user previously supplied a Google Photos share link, but it could not be fetched by the repository environment. The shape notes are retained in `anthroforge-app/KALEAON_CREATOR_PROFILE.md`; all numeric dimensions in this blockout are explicitly provisional estimates, not measurements from the turnaround.

**Do not call this a faithful final model.** Attach the front/rear/head reference sheet and replace the provisional dimensions, head silhouette, spot distribution, harness routing, tail shape and paw details from the actual views.

## Build

From this directory:

```bash
blender --background --python scripts/build_kaleaon_blockout.py -- --output ./out
```

The script imports shared primitives from `scripts/build_species_blockouts.py`. Outputs are editable `.blend` and preview `.glb` files. This greybox is intended for proportion review and sculpt/retopology, not rig-ready production export.

## Next production passes

1. Measure front/rear/head reference views and update `kaleaon.v1.json`.
2. Replace overlapping primitive masses with continuous sculpted surfaces and retopologized deformation loops.
3. Author facial, shoulder, arm, hand/paw, hip, hock, foot and tail deformation.
4. Fit separate harness and glasses meshes to the final surface.
5. Add UVs, texture masks and reference-matched irregular spot placement.
6. Integrate the resolved asset into the shared creator preview/export path and run pose, collision, and GLB QA.
