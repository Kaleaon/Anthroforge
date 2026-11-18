"""Run inside Blender to smoke-test generated Kaleaon BLEND and GLB outputs."""
from __future__ import annotations
import argparse
import struct
import sys
from pathlib import Path
import bpy


def parse_args():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="./out")
    return parser.parse_args(values)


def main():
    args = parse_args()
    out = Path(args.output).resolve()
    blend = out / "Kaleaon_blockout.blend"
    glb = out / "Kaleaon_blockout.glb"
    if not blend.is_file() or blend.stat().st_size < 1024:
        raise RuntimeError("missing or unexpectedly small Kaleaon BLEND output")
    if not glb.is_file():
        raise RuntimeError("missing Kaleaon GLB output")
    raw = glb.read_bytes()
    if len(raw) < 20:
        raise RuntimeError("GLB output is too small to contain a valid header")
    magic, version, declared_length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(raw):
        raise RuntimeError("GLB header/version/declared length is invalid")

    bpy.ops.wm.open_mainfile(filepath=str(blend))
    required = [
        *(f"Kaleaon_Genitalia_Shaft_{i:02d}" for i in range(1, 5)),
        "Kaleaon_Sac_Shared",
        *(f"Kaleaon_Teat_{i:02d}" for i in range(1, 5)),
        "Kaleaon_SculptBase_Unified",
    ]
    missing = [name for name in required if name not in bpy.data.objects]
    if missing:
        raise RuntimeError("missing generated objects: " + ", ".join(missing))
    anatomy = required[:9]
    for name in anatomy:
        obj = bpy.data.objects[name]
        if obj.type != "MESH" or len(obj.data.polygons) < 100:
            raise RuntimeError(f"{name} is not a substantive mesh object")
        if obj.get("anthroforge_independent_component") is not True:
            raise RuntimeError(f"{name} is missing independent-component metadata")
    if len({bpy.data.objects[name].data.as_pointer() for name in anatomy}) != 9:
        raise RuntimeError("anatomy components must not share mesh datablocks")
    if any("Kaleaon_Anatomy_Modules" not in [c.name for c in bpy.data.objects[name].users_collection] for name in anatomy):
        raise RuntimeError("anatomy components are not organized under the modular anatomy root")
    print("KALEAON BLENDER SMOKE TEST PASSED")
    print("Verified 9 independent anatomy meshes, unified sculpt base, editable BLEND and valid GLB")


if __name__ == "__main__":
    main()
