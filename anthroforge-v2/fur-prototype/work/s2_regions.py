import bpy
from mathutils import Vector

SRC = "/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage1.blend"
FRONT = -1.0  # character faces -Y (proven from Mixamo toe/thumb bone directions)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=SRC)

ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
mw = ob.matrix_world

vnorm = [Vector((0, 0, 0)) for _ in me.vertices]
for p in me.polygons:
    for vi in p.vertices:
        vnorm[vi] += p.normal
for i, n in enumerate(vnorm):
    if n.length > 0:
        vnorm[i] = n.normalized()

ws = [mw @ v.co for v in me.vertices]

def ss(a, b, x):
    if a == b:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

def clamp01(x):
    return min(1.0, max(0.0, x))

N = len(me.vertices)
ruff = [0.0] * N
back = [0.0] * N
belly = [0.0] * N
bodyhair = [0.0] * N

for i, v in enumerate(ws):
    n = vnorm[i]
    x, z = v.x, v.z
    ax = abs(x)
    sy = FRONT * v.y   # + toward the chest/face
    sn = FRONT * n.y   # + when the surface faces forward

    # ---------- RUFF: cheeks, jaw, throat, neck, upper chest ----------
    head_band = ss(1.38, 1.46, z) * (1.0 - ss(1.84, 1.92, z))
    cheek = ss(0.05, 0.13, ax) * (1.0 - ss(0.24, 0.34, ax))
    muzzle = ss(0.12, 0.22, sy) * ss(1.56, 1.64, z) * (1.0 - ss(1.74, 1.82, z))
    r_head = head_band * max(cheek, 0.35 * (1.0 - ss(0.10, 0.20, sy))) * (1.0 - muzzle)
    neck_band = ss(1.24, 1.34, z) * (1.0 - ss(1.46, 1.54, z))
    frontish = ss(-0.10, 0.02, sy)
    narrow = 1.0 - ss(0.26, 0.38, ax)
    r_neck = neck_band * max(frontish, 0.45) * narrow
    r_jaw = ss(1.40, 1.48, z) * (1.0 - ss(1.56, 1.64, z)) * ss(-0.2, -0.6, n.z) * (1.0 - ss(0.16, 0.26, ax))
    ruff[i] = clamp01(max(r_head, r_neck, r_jaw))

    # ---------- BACK: dorsal torso, shoulders, rear ----------
    dorsal = ss(0.05, 0.45, -sn)                       # faces backward
    backpos = ss(-0.02, -0.14, sy)                     # behind the spine plane (sy negative)
    band = ss(0.45, 0.60, z) * (1.0 - ss(1.60, 1.72, z))
    shoulder = ss(1.30, 1.44, z) * (1.0 - ss(1.52, 1.62, z)) * ss(0.15, 0.45, n.z) * ss(0.0, 0.12, -sy)
    back[i] = clamp01(max(dorsal * band * max(backpos, 0.35), shoulder * 0.9))

    # ---------- BELLY: front torso ----------
    front = ss(0.15, 0.55, sn)
    bband = ss(0.55, 0.70, z) * (1.0 - ss(1.22, 1.36, z))
    bnarrow = 1.0 - ss(0.28, 0.40, ax)
    belly[i] = clamp01(front * bband * bnarrow)

    # ---------- BODYHAIR variant: chest patch + forearms ----------
    chest = ss(0.35, 0.65, sn) * ss(1.02, 1.12, z) * (1.0 - ss(1.34, 1.44, z)) * (1.0 - ss(0.22, 0.33, ax))
    fore = ss(0.48, 0.62, ax) * (1.0 - ss(0.98, 1.10, ax)) * ss(1.22, 1.30, z) * (1.0 - ss(1.46, 1.54, z))
    bodyhair[i] = clamp01(max(chest, fore))

coat = [max(clamp01(1.0 - max(ruff[i], back[i], belly[i])), 0.04) for i in range(N)]

def make_group(name, weights):
    g = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
    for i, w in enumerate(weights):
        if w > 0.01:
            g.add([i], w, 'REPLACE')

make_group("FUR_ruff", ruff)
make_group("FUR_back", back)
make_group("FUR_belly", belly)
make_group("FUR_coat", coat)
make_group("FUR_bodyhair", bodyhair)

if "FUR_regions" in me.color_attributes:
    me.color_attributes.remove(me.color_attributes["FUR_regions"])
ca = me.color_attributes.new(name="FUR_regions", type='FLOAT_COLOR', domain='POINT')
for i in range(N):
    ca.data[i].color = (ruff[i], back[i], belly[i], coat[i])

def stats(name, w):
    nz = sum(1 for x in w if x > 0.5)
    print(f"{name}: verts>0.5 = {nz} / {N}  mean={sum(w)/N:.3f}")
stats("ruff", ruff); stats("back", back); stats("belly", belly); stats("coat", coat); stats("bodyhair", bodyhair)

mat = bpy.data.materials.get("BodyClay") or bpy.data.materials.new("BodyClay")
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.16, 0.13, 0.11, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9
if mat.name not in [m.name for m in me.materials]:
    me.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
