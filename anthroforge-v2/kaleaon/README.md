# Kaleaon Sona — Reference-Informed Blockout

This is the first dedicated character asset pass for the Kaleaon creator profile.

## Included

- `kaleaon.v1.json`: editable profile and provisional dimensions.
- `scripts/build_kaleaon_blockout.py`: Blender background builder for a named-object greybox and GLB preview.
- Separate body masses, head/muzzle/ruff/ears, digitigrade limbs and paws, tail curve, harness straps, belt fitting, and glasses.
- A procedural off-white/grey coat material plus separate mauve, nose, harness, frame and metal materials.

## Important reference limitation

The user has now supplied five illustrations, including a front/rear/head turnaround. The profile records the visual observations from that batch. The turnaround has no scale bar, so metric dimensions remain provisional; relative silhouette, coat palette, spot placement, face, tail and harness routing are now reference-informed.

**This remains a greybox, not a faithful final model.** Perspective illustrations are used for expression and secondary design cues, not as orthographic measurement sources.

## Build

From this directory:

```bash
blender --background --python scripts/build_kaleaon_blockout.py -- --output ./out
```

The script imports shared primitives from `scripts/build_species_blockouts.py`. Outputs are editable `.blend` and preview `.glb` files. This greybox is intended for proportion review and sculpt/retopology, not rig-ready production export.

## Next production passes

1. Replace provisional metric dimensions when a real-world scale anchor is supplied; preserve the visual landmarks recorded in `kaleaon.v1.json`.
2. Replace overlapping primitive masses with continuous sculpted surfaces and retopologized deformation loops.
3. Author facial, shoulder, arm, hand/paw, hip, hock, foot and tail deformation.
4. Fit separate harness and glasses meshes to the final surface.
5. Add UVs, texture masks and reference-matched irregular grey rosettes/patches rather than uniform procedural dots.
6. Integrate the resolved asset into the shared creator preview/export path and run pose, collision, and GLB QA.
