"""Render the A7 comparison frames.

Modes:
  groom   open a groom_from_paint_<tag>.blend, render the strand
          preview on the body (particle-binding duplicate + guides hidden)
  guides  same scene, groom curves hidden, FURP_guides shown over the body
  viz     open a paintable blend, render the body with FURP_viz as a
          material override (painted density heat view)

Usage: blender -b --python render_compare.py -- --mode groom \
         --input out/groom_from_paint_rev1.blend --out out/render_before.png
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def build_studio(scene):
    world = bpy.data.worlds.new("FurWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.015, 0.015, 0.02, 1.0)
    bg.inputs[1].default_value = 0.7
    scene.world = world

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.002))
    g = bpy.context.active_object
    g.name = "Ground"
    gm = bpy.data.materials.new("GroundMat")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    g.data.materials.append(gm)

    def area(name, pos, energy, size):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.shape = "DISK"
        ld.size = size
        o = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(o)
        o.location = pos
        aim(o, (0, 0, 1.0))

    area("KeyLight", (-2.3, -2.5, 3.1), 140, 2.2)
    area("FillLight", (2.5, -1.4, 1.5), 60, 2.6)
    area("RimLight", (0.7, 2.7, 2.7), 80, 1.8)

    cd = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(cam)
    cam.location = (1.9, -3.4, 1.6)
    cam.data.lens = 42
    aim(cam, (0, 0, 1.0))
    scene.camera = cam


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["groom", "guides", "viz"])
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    bpy.ops.wm.open_mainfile(filepath=args.input)
    scene = bpy.context.scene

    if args.mode == "viz":
        m = bpy.data.materials.new("VizMat")
        m.use_nodes = True
        nt = m.node_tree
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "FURP_viz"
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 0.85
        nt.links.new(attr.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"],
                     nt.nodes["Material Output"].inputs["Surface"])
        scene.view_layers[0].material_override = m
    else:
        groom_body = bpy.data.objects.get("BaraWolfBody_groom")
        if groom_body:
            groom_body.hide_render = True
        guides = bpy.data.objects.get("FURP_guides")
        if args.mode == "groom" and guides:
            guides.hide_render = True
        if args.mode == "guides":
            for name, o in bpy.data.objects.items():
                if name.startswith("FURP_groom_"):
                    o.hide_render = True

    build_studio(scene)
    # Principled Hair blows out to white under prototype-strength
    # lights (verified with a constant-colour control patch: dark
    # brown 0.05 albedo still rendered pale). Presentation exposure
    # is pulled down so the authored zone colours stay in mid-tones
    # where they read; the data/materials are untouched.
    scene.view_settings.exposure = -0.8
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.04
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 480
    scene.render.resolution_y = 600
    scene.render.filepath = str(Path(args.out).resolve())
    bpy.ops.render.render(write_still=True)
    print("RENDERED", args.out)


main()
