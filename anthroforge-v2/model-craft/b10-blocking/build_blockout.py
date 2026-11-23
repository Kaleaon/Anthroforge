#!/usr/bin/env python3
"""B10 demo: wolf (feral plan) blocked from primitives at sourced proportions.

Run: blender -b --python build_blockout.py
Outputs (next to this script): wolf_blockout.blend, measurements.json,
renders/{side,front,threequarter}.png + side_silhouette.png

Proportion targets (metres) — sources in BLOCKING.md §5:
  shoulder height 0.82 | skull L 0.25 (module) | head-body ~1.30 (stations)
  ZB/L 0.53 | ear 0.40 L | tail 0.40 | chest brisket at elbow height
Axes: +X forward (nose), +Z up, Y lateral. Ground plane z=0.
Block stage ONLY: named primitives, transforms unapplied, one clay material.
"""
import bpy, json, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- targets
T = {
    "shoulder_height": 0.82,
    "skull_L": 0.25,
    "ZB_over_L": 0.53,
    "ear_over_L": 0.40,
    "tail_len": 0.40,
    "headbody_stations": 1.30,   # nose tip x to tail-base x, head carried level
}

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'

clay = bpy.data.materials.new("block_clay")
clay.diffuse_color = (0.62, 0.60, 0.58, 1.0)
clay.use_nodes = True
_bsdf = clay.node_tree.nodes["Principled BSDF"]
_bsdf.inputs["Base Color"].default_value = (0.48, 0.46, 0.43, 1.0)
_bsdf.inputs["Roughness"].default_value = 0.9

dark = bpy.data.materials.new("silhouette")
dark.diffuse_color = (0.05, 0.05, 0.05, 1.0)
dark.use_nodes = True
_bsdf2 = dark.node_tree.nodes["Principled BSDF"]
_bsdf2.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
_bsdf2.inputs["Roughness"].default_value = 1.0

def finish(obj, name):
    obj.name = name
    obj.data.materials.append(clay)
    return obj

def box(name, loc, size):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.dimensions = size
    return finish(o, name)

def ball(name, loc, radii, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, scale=(1, 1, 1))
    o = bpy.context.object
    o.scale = radii
    o.rotation_euler = rot
    return finish(o, name)

def limb(name, p1, p2, r):
    """Capsule-read segment: sphere stretched between two points."""
    a, b = Vector(p1), Vector(p2)
    mid = (a + b) / 2
    d = b - a
    bpy.ops.mesh.primitive_uv_sphere_add(location=mid)
    o = bpy.context.object
    o.scale = (r, r, d.length / 2)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return finish(o, name)

def cone(name, loc, r, h, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(location=loc, radius1=r, radius2=0.15 * r,
                                    depth=h, rotation=rot)
    return finish(bpy.context.object, name)

# ---------------------------------------------------------------- torso masses
# Spine line of action: withers (x +0.22, top z .84) sloping gently to
# pelvis (x -0.38, top z .78). Chest deep & narrow (keel), brisket to elbow.
ball("Chest",      (0.20, 0, 0.63), (0.27, 0.13, 0.20))          # ribcage mass
ball("Belly",      (-0.05, 0, 0.62), (0.24, 0.12, 0.17))         # mid-torso
ball("Pelvis",     (-0.31, 0, 0.64), (0.16, 0.115, 0.16))        # hip mass
ball("Neck",       (0.51, 0, 0.68), (0.20, 0.10, 0.13), rot=(0, -0.55, 0))
# neck ~ as wide as head at base (heavily muscled) -- radii y .10 vs head .066*1.5 mass incl. fur block

# ---------------------------------------------------------------- head (module L = 0.25)
L = T["skull_L"]
ball("Cranium",    (0.695, 0, 0.705), (0.085, 0.5 * T["ZB_over_L"] * L, 0.078))
box("Muzzle",      (0.805, 0, 0.662), (0.125, 0.052, 0.058))     # ~0.45-0.50 of head length, blunt
box("Jaw",         (0.79, 0, 0.622), (0.115, 0.044, 0.026))      # mandible 0.74 L block
for s, tag in ((1, "L"), (-1, "R")):
    cone(f"Ear_{tag}", (0.645, s * 0.046, 0.81), 0.030, 0.36 * L,
         rot=(s * 0.10, -0.05, 0))

# ---------------------------------------------------------------- legs
# Front: near-vertical column under the shoulder. Elbow z .42, brisket meets it.
for s, tag in ((1, "L"), (-1, "R")):
    y = s * 0.095
    limb(f"FrontUpper_{tag}", (0.36, y, 0.64), (0.37, y, 0.42), 0.046)
    limb(f"FrontFore_{tag}",  (0.37, y, 0.44), (0.375, y, 0.13), 0.030)
    limb(f"FrontCannon_{tag}", (0.375, y, 0.15), (0.38, y, 0.045), 0.024)
    box(f"FrontPaw_{tag}", (0.415, y, 0.022), (0.105, 0.045, 0.044))
# Hind: three-segment angle chain -- thigh forward, gaskin back, cannon down.
for s, tag in ((1, "L"), (-1, "R")):
    y = s * 0.10
    limb(f"HindThigh_{tag}",  (-0.33, y, 0.62), (-0.20, y, 0.35), 0.062)
    limb(f"HindGaskin_{tag}", (-0.20, y, 0.35), (-0.395, y, 0.15), 0.036)
    limb(f"HindCannon_{tag}", (-0.395, y, 0.16), (-0.385, y, 0.045), 0.024)
    box(f"HindPaw_{tag}", (-0.35, y, 0.022), (0.105, 0.045, 0.044))

# ---------------------------------------------------------------- tail: 3 segments, relaxed ~45 deg hang
p = Vector((-0.45, 0, 0.72))
step = Vector((-0.094, 0, -0.094))          # |step| = 0.133; 3 segs = 0.40 m
for i in range(3):
    q = p + step
    limb(f"Tail_{i+1}", tuple(p), tuple(q), 0.030 - 0.005 * i)
    p = q

# ground reference (not part of the figure; excluded from measurements)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0.1, 0, 0))
gnd = bpy.context.object
gnd.name = "Ground_REF"
gm = bpy.data.materials.new("ground")
gm.diffuse_color = (0.85, 0.85, 0.85, 1.0)
gnd.data.materials.append(gm)

# ---------------------------------------------------------------- measurements
_dg = bpy.context.evaluated_depsgraph_get()
def wbbox(o):
    eo = o.evaluated_get(_dg)
    cs = [eo.matrix_world @ Vector(c) for c in eo.bound_box]
    xs = [c.x for c in cs]; ys = [c.y for c in cs]; zs = [c.z for c in cs]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

objs = {o.name: o for o in bpy.context.scene.objects if o.name != "Ground_REF"}
head_x = (min(wbbox(objs[n])[0][0] for n in ("Cranium", "Muzzle", "Jaw")),
          max(wbbox(objs[n])[0][1] for n in ("Cranium", "Muzzle", "Jaw")))
meas = {
    "shoulder_height_m": round(wbbox(objs["Chest"])[2][1], 3),
    "head_length_m": round(head_x[1] - head_x[0], 3),
    "head_width_m": round(wbbox(objs["Cranium"])[1][1] - wbbox(objs["Cranium"])[1][0], 3),
    "ear_height_m": round(wbbox(objs["Ear_L"])[2][1] - wbbox(objs["Ear_L"])[2][0], 3),
    "nose_to_tailbase_m": round(head_x[1] - (-0.45), 3),
    "tail_reach_m": round(math.dist((-0.45, 0, 0.72), tuple(p)), 3),
    "brisket_bottom_m": round(wbbox(objs["Chest"])[2][0], 3),
    "elbow_z_m": 0.42,
}
meas["ZB_over_L_measured"] = round(meas["head_width_m"] / T["skull_L"], 3)
meas["ear_over_L_measured"] = round(meas["ear_height_m"] / T["skull_L"], 3)
meas["targets"] = T
with open(os.path.join(HERE, "measurements.json"), "w") as f:
    json.dump(meas, f, indent=1)
print("MEASUREMENTS:", json.dumps(meas))

# ---------------------------------------------------------------- cameras + render
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 760, 560
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.92, 0.92, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
bpy.ops.object.light_add(type='SUN', location=(1.5, -2.5, 3.5))
sun = bpy.context.object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

def shot(name, loc, rot, ortho=2.0, silh=False, aim=None):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.object
    if aim is not None:
        cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    scene.camera = cam
    swapped = []
    if silh:  # material_override proved unreliable headless; swap directly
        for o in bpy.context.scene.objects:
            if o.type == 'MESH' and o.name != "Ground_REF" and o.data.materials:
                swapped.append((o, o.data.materials[0]))
                o.data.materials[0] = dark
    scene.render.filepath = os.path.join(HERE, "renders", name + ".png")
    bpy.ops.render.render(write_still=True)
    for o, m in swapped:
        o.data.materials[0] = m
    bpy.data.objects.remove(cam, do_unlink=True)

D = math.radians
shot("side",          (0.1, -3.2, 0.5),  (D(90), 0, 0),            ortho=1.9)
shot("front",         (3.2, 0, 0.5),     (D(90), 0, D(90)),       ortho=1.4)
shot("threequarter",  (2.4, -2.4, 1.35), (D(62), 0, D(45)),       ortho=2.2, aim=(0.05, 0, 0.42))
shot("side_silhouette", (0.1, -3.2, 0.5), (D(90), 0, 0),           ortho=1.9, silh=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "wolf_blockout.blend"))
print("DONE")
