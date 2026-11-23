#!/usr/bin/env python3
"""
AnthroForge A11 — Blender patch renders.

Two spherical-cap "pelt patches" side by side, each built the way the
blueprint stacks a coat (APP_BLUEPRINT 9.3): shell layers underneath
(coat-level diffuse = integral colour + markings-driven pattern, alpha
eroding per shell), hair cards on top carrying the shaft-atlas colour.

  LEFT  wolf : shells tinted coat_wolf_dorsal, cards card_wolf_agouti_a
  RIGHT tabby: shells tinted coat_tabby (stripes mask in the diffuse),
               cards card_tabby_ground + card_tabby_boundary mixed

Run: blender --background --python render_patches.py
Outputs ../renders/render_patch_near.png and render_patch_far.png
(far = same scene, camera pulled back: the distance-read check on real
geometry).
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(ROOT, "textures")
REN = os.path.join(ROOT, "renders")
os.makedirs(REN, exist_ok=True)
random.seed(23)


def img(name):
    return bpy.data.images.load(os.path.join(TEX, name))


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        pass


def dome_mesh(name, centre, R=1.05, half=0.62, seg=26):
    """Spherical cap: grid over [-half, half]^2 lifted onto a sphere."""
    verts, faces, uvs = [], [], []
    idx = {}
    for j in range(seg + 1):
        for i in range(seg + 1):
            x = -half + 2 * half * i / seg
            y = -half + 2 * half * j / seg
            r2 = x * x + y * y
            z = math.sqrt(max(R * R - r2, 0.05)) - math.sqrt(R * R - half * half * 0.5)
            idx[(i, j)] = len(verts)
            verts.append((centre[0] + x, centre[1] + y, centre[2] + z))
            uvs.append((i / seg, j / seg))
    for j in range(seg):
        for i in range(seg):
            a, b = idx[(i, j)], idx[(i + 1, j)]
            c, d = idx[(i + 1, j + 1)], idx[(i, j + 1)]
            faces.append((a, b, c, d))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uv.data[loop.index].uv = uvs[loop.vertex_index]
    for p in me.polygons:
        p.use_smooth = True
    return me


def shell_material(name, diffuse, alpha_img, alpha_gain=1.0):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    td = nt.nodes.new("ShaderNodeTexImage")
    td.image = diffuse
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = alpha_img
    ta.image.colorspace_settings.name = "Non-Color"
    math_node = nt.nodes.new("ShaderNodeMath")
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = alpha_gain
    nt.links.new(td.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ta.outputs["Color"], math_node.inputs[0])
    nt.links.new(math_node.outputs[0], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return mat


def card_material(name, tex):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = tex
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def card_geometry(name, length=0.17, width=0.065, segs=4):
    """Ribbon: origin at root, extends -Y (down-slope), arcs +Z.
    UV v = 1 at root -> image row 0 (root) per A11 convention."""
    verts, faces, uvs = [], [], []
    for s in range(segs + 1):
        f = s / segs
        y = -length * f
        z = 0.028 * f * f
        for k, xx in enumerate((-width / 2 * (1 - 0.55 * f), width / 2 * (1 - 0.55 * f))):
            verts.append((xx, y, z))
            uvs.append((k, 1 - f))
    for s in range(segs):
        a, b, c, d = 2 * s, 2 * s + 1, 2 * s + 3, 2 * s + 2
        faces.append((a, b, c, d))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uv.data[loop.index].uv = uvs[loop.vertex_index]
    for p in me.polygons:
        p.use_smooth = True
    return me


def surface_frame(centre, R, x, y):
    """Point + frame on the dome: n = radial normal, d = down-slope."""
    z = math.sqrt(max(R * R - x * x - y * y, 0.05)) - math.sqrt(R * R - 0.62 * 0.62 * 0.5)
    p = Vector((centre[0] + x, centre[1] + y, centre[2] + z))
    n = Vector((x, y, math.sqrt(max(R * R - x * x - y * y, 0.05)))).normalized()
    g = Vector((0, 0, -1))
    d = g - n * g.dot(n)
    if d.length < 1e-4:
        d = Vector((0, -1, 0)) - n * Vector((0, -1, 0)).dot(n)
    d.normalize()
    side = d.cross(n).normalized()
    m = Matrix(((side.x, d.x, n.x, p.x),
                (side.y, d.y, n.y, p.y),
                (side.z, d.z, n.z, p.z),
                (0, 0, 0, 1)))
    return m


def build_patch(label, centre, coat_name, card_specs):
    R, half = 1.05, 0.62
    coat = img(coat_name)
    alphas = [img(f"shell_alpha_l{i}.png") for i in range(4)]
    base_me = dome_mesh(f"{label}_dome", centre, R, half)
    gains = [1.0, 0.88, 0.68]
    for k in range(3):
        ob = bpy.data.objects.new(f"{label}_shell{k}", base_me)
        bpy.context.scene.collection.objects.link(ob)
        s = 1.0 + 0.016 * k
        ob.scale = (s, s, s)
        ob.location = Vector(centre) * (1 - s) + Vector((0, 0, 0.012 * k))
        mat = shell_material(f"{label}_shellmat{k}", coat, alphas[min(k, 3)], gains[k])
        ob.data.materials.append(mat)
    geo = card_geometry(f"{label}_card")
    mats = [(card_material(f"{label}_cardmat_{n}", img(n)), w) for n, w in card_specs]
    total_w = sum(w for _, w in mats)
    coll = bpy.data.collections.new(f"{label}_cards")
    bpy.context.scene.collection.children.link(coll)
    count = 170
    for i in range(count):
        # sample the cap; skip the crown where down-slope is degenerate
        r = half * (0.16 + 0.82 * math.sqrt(random.random()))
        a = random.uniform(0, 2 * math.pi)
        x, y = r * math.cos(a), r * math.sin(a)
        m = surface_frame(centre, R, x, y)
        pick = random.random() * total_w
        acc = 0.0
        mat = mats[0][0]
        for mm, w in mats:
            acc += w
            if pick <= acc:
                mat = mm
                break
        ob = bpy.data.objects.new(f"{label}_card{i}", geo)
        coll.objects.link(ob)
        ob.data.materials.append(mat)
        jitter = Matrix.Rotation(random.uniform(-0.35, 0.35), 4, "Z")
        scl = random.uniform(0.8, 1.3)
        ob.matrix_world = m @ jitter @ Matrix.Diagonal((scl, scl, scl, 1.0))


def main():
    clear_scene()
    build_patch("wolf", (-0.78, 0, 0), "coat_wolf_dorsal.png",
                [("card_wolf_agouti_a.png", 0.75), ("card_wolf_agouti_b.png", 0.25)])
    build_patch("tabby", (0.78, 0, 0), "coat_tabby.png",
                [("card_tabby_ground.png", 0.6), ("card_tabby_boundary.png", 0.4)])

    # ground shadow-catcher
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.62))
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("ground")
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.045, 0.04, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    gnd.data.materials.append(gm)

    # lights + camera
    bpy.ops.object.light_add(type="AREA", location=(1.5, -2.0, 3.2))
    key = bpy.context.active_object
    key.data.energy = 900
    key.data.shape = "DISK"
    key.data.size = 2.5
    bpy.ops.object.light_add(type="AREA", location=(-2.5, 1.5, 1.6))
    fill = bpy.context.active_object
    fill.data.energy = 250
    fill.data.size = 2.0

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 2
    scene.cycles.transparent_max_bounces = 3
    scene.render.resolution_x = 480
    scene.render.resolution_y = 340
    scene.world = bpy.data.worlds.new("w")
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.035, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

    def aim(cam_obj, loc, target):
        cam_obj.location = loc
        d = Vector(target) - Vector(loc)
        cam_obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    aim(cam, (0, -1.72, 1.62), (0, 0, 0.02))
    scene.render.filepath = os.path.join(REN, "render_patch_near.png")
    bpy.ops.render.render(write_still=True)
    print("NEAR RENDER SAVED", flush=True)
    if os.environ.get("A11_FAR") == "1":
        aim(cam, (0, -4.4, 3.6), (0, 0, 0.0))
        scene.render.filepath = os.path.join(REN, "render_patch_far.png")
        bpy.ops.render.render(write_still=True)
        print("FAR RENDER SAVED", flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "patch_scene.blend"))
    print("renders done")


if __name__ == "__main__":
    main()
