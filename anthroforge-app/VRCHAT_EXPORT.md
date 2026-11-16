# Unity / VRChat avatar export

AnthroForge's in-app GLB exporter writes a skinned glTF 2.0 avatar. The Blender sidecar converts that GLB into an FBX with Unity Humanoid bone names and preserves the armature and mesh weights.

## Requirements

- Blender 3.6 LTS or newer with built-in glTF and FBX support.
- A skinned AnthroForge GLB with the expected source rig.
- Unity with the VRChat Creator Companion / VRChat SDK for final upload.

## Convert

    blender --background --python tools/blender/export_unity_fbx.py -- --input avatar.glb --output avatar_vrchat.fbx --profile vrchat

The script refuses export if the source armature or required humanoid bones are missing. It renames standard body bones and matching vertex groups so skin weights remain bound to the correct joints. Tail, wing, ear and other extension bones remain as extras. A companion `.avatar-report.json` records the mapping and remaining work.

## Unity / VRChat finalization

1. Import the FBX into Unity and set Rig > Animation Type to **Humanoid**.
2. Configure the Avatar mapping and resolve invalid bone or pose warnings.
3. Add eye-look transforms/constraints if eye tracking is desired.
4. Add viseme blendshapes (or a jaw-based fallback), blink shapes, and expression blendshapes; configure the VRChat expression parameters/menu.
5. Add PhysBones and colliders for ears, tail, wings, hair and other secondary motion.
6. Add the VRChat Avatar Descriptor, configure view position and lip-sync, then run the SDK's Build & Test validation.

**Honest status:** FBX conversion is automated; Unity Humanoid validation, facial expression authoring, PhysBones, and VRChat SDK upload are not yet automated. The exporter never labels the result upload-ready merely because an FBX file was written.

## Other targets

The FBX can be imported into Unity or Unreal as a rigged interchange asset. Unreal may need target-skeleton retarget/IK setup. Blender `.blend` remains the editable source route; GLB remains the portable preview/share route. DAE and platform-specific optimization profiles remain future work.
