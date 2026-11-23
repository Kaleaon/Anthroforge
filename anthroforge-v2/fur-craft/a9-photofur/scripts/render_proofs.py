#!/usr/bin/env python3
"""
A9 seamlessness proof renders (run inside Blender, headless Cycles):
  blender -b --factory-startup -noaudio --python render_proofs.py

Per texture (textures/fur_<name>_diffuse.png):
  * proof_<name>_plane3x3.png  - plane, texture repeated 3x3, so all four
    wrap seams cross the frame interior.
  * proof_<name>_sphere.png    - UV sphere, repeat 3x2, wrap seam visible
    as the sphere's UV seam + horizontal tiling bands.
Physical scale: plane is 3 tiles wide -> width = 3 * tile_cm (from the
texture's JSON sidecar); sphere circumference = 3 tiles around.
"""
import json
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(ROOT, "textures")
OUT = os.path.join(ROOT, "proofs")
NAMES = ["wolf", "bear", "fox"]


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(tex_path, rx, ry):
    mat = bpy.data.materials.new("fur")
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(tex_path)
    tex.image.colorspace_settings.name = "sRGB"
    tex.extension = "REPEAT"
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (rx, ry, 1.0)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def setup_world_and_lights():
    world = bpy.data.worlds["World"]
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs[1].default_value = 1.0
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    bpy.context.scene.collection.objects.link(sun)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
    fill.data.energy = 250.0
    fill.data.shape = "DISK"
    fill.data.size = 4.0
    fill.location = (-3, -2, 3)
    bpy.context.scene.collection.objects.link(fill)


def add_camera(loc, look_at):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.location = loc
    direction = Vector(look_at) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam


def render(path):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.device = "CPU"
    sc.render.resolution_x = 768
    sc.render.resolution_y = 576
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def proof(name):
    tex_path = os.path.join(TEX, f"fur_{name}_diffuse.png")
    with open(os.path.join(TEX, f"fur_{name}.json")) as f:
        tile_m = json.load(f)["tile_cm"] / 100.0

    # --- plane, 3x3 repeats
    clear_scene()
    setup_world_and_lights()
    bpy.ops.mesh.primitive_plane_add(size=3 * tile_m)
    plane = bpy.context.active_object
    plane.data.materials.append(make_material(tex_path, 3, 3))
    add_camera((0, -1.6 * tile_m * 1.6, 2.2 * tile_m * 1.6), (0, 0, 0))
    render(os.path.join(OUT, f"proof_{name}_plane3x3.png"))

    # --- sphere, circumference = 3 tiles
    clear_scene()
    setup_world_and_lights()
    r = 3 * tile_m / (2 * math.pi)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=32)
    sph = bpy.context.active_object
    sph.data.materials.append(make_material(tex_path, 3, 2))
    add_camera((0, -3.2 * r, 1.1 * r), (0, 0, 0))
    render(os.path.join(OUT, f"proof_{name}_sphere.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n in NAMES:
        proof(n)
