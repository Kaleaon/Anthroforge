# Kaleaon Sona — Reference-Informed Blockout

This is the first dedicated character asset pass for the Kaleaon creator profile.

## Included

- `kaleaon.v1.json`: editable profile and provisional dimensions.
- `scripts/build_kaleaon_blockout.py`: Blender background builder for a named-object greybox and GLB preview.
- Unified voxel-remeshed coat surface for sculpting, separate facial accents, paw toes/claws, tail curve, rear X harness, arm bands, belt fitting, and glasses.
- A procedural off-white/grey coat material plus separate mauve, nose, harness, frame and metal materials.

## Important reference limitation

The user has now supplied five illustrations, including a front/rear/head turnaround. The profile records the visual observations from that batch. The turnaround has no scale bar. The user selected approximately 7 ft as a working height, so the builder calibrates the character bounds to 2.1336 m. This is a design target, not a measurement from the artwork; other proportions remain editable estimates.

**This remains a greybox, not a faithful final model.** Perspective illustrations are used for expression and secondary design cues, not as orthographic measurement sources.

## Build

From this directory:

```bash
blender --background --python scripts/build_kaleaon_blockout.py -- --output ./out
```

The script imports shared primitives from `scripts/build_species_blockouts.py`. Outputs are editable `.blend` and preview `.glb` files. The builder fuses coat masses into a unified voxel-remeshed sculpt base, then retains accessories and selected facial details separately. This is suitable as a sculpting starting point, but is not quad-retopologized, UV-authored, weighted, or rig-ready.

## Next production passes

1. Replace provisional metric dimensions when a real-world scale anchor is supplied; preserve the visual landmarks recorded in `kaleaon.v1.json`.
2. Sculpt the unified base to refine anatomical transitions, then retopologize with deformation-friendly loops.
3. Author facial, shoulder, arm, hand/paw, hip, hock, foot and tail deformation.
4. Fit separate harness and glasses meshes to the final surface.
5. Add UVs, texture masks and reference-matched irregular grey rosettes/patches rather than uniform procedural dots.
6. Integrate the resolved asset into the shared creator preview/export path and run pose, collision, and GLB QA.
