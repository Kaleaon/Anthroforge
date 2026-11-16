"""A12 fur shading testbed v2 (Blender 5.2, Cycles).

Substrate: a curved pelt PATCH (spherical cap) instead of v1's full ball --
on a sphere every tangent flow field has a whorl singularity and the crown
renders bald (v1 renders discarded for exactly that reason; the patch is
also how production swatches are built). One deterministic card set on an
undercoat cap, rendered under three card materials that differ ONLY in
shading terms:
  A  plain alpha-card PBR
  B  + sheen (Principled sheen -> KHR_materials_sheen)
  C  + anisotropic GGX (UV tangent) + Fresnel rim/fuzz approximation
Undercoat uses the materials-lab skin_furred_base values in all three.

Run: blender -b --python build_testbed.py
Outputs: renders/{a_plain,b_sheen,c_aniso_rim}.png, fur_shading_testbed.blend
"""
import bpy, math, os, random, time
from mathutils import Vector

BASE = "/home/hatch/workspace/anthroforge-v2/fur-craft/a12-shading"
TEX = os.path.join(BASE, "textures", "fur_card_a12.png")

# ---------------------------------------------------------------- helpers
def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex2lin(hx):
    hx = hx.lstrip("#")
    return tuple(srgb2lin(int(hx[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)

# ---------------------------------------------------------------- patch rig
CAP_R, CAP_PHI = 1.1, 0.8
AXIS = Vector((0.15, -1.0, 0.42)).normalized()          # patch faces camera
U = Vector((0, 0, 1)).cross(AXIS).normalized()
V = AXIS.cross(U).normalized()
CENTER = Vector((0, 0, -0.5))
PATCH_C = CENTER + AXIS * CAP_R                          # patch centre point
N_CARDS = 1150
DOWN = Vector((0, 0, -1))

def cap_point(phi, psi):
    d = (AXIS * math.cos(phi)
         + (U * math.cos(psi) + V * math.sin(psi)) * math.sin(phi))
    return CENTER + d * CAP_R, d

def build_undercoat():
    NR, NS = 20, 56
    verts, faces = [], []
    for ir in range(NR + 1):
        phi = CAP_PHI * ir / NR
        for is_ in range(NS + 1):
            psi = 2 * math.pi * is_ / NS
            p, _ = cap_point(phi, psi)
            verts.append(tuple(p))
    for ir in range(NR):
        for is_ in range(NS):
            a = ir * (NS + 1) + is_
            faces.append((a, a + 1, a + 1 + NS + 1, a + NS + 1))
    me = bpy.data.meshes.new("UndercoatCap")
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    return me

def build_card_mesh(rng):
    """Cards merged into one mesh. Roots uniform on the cap, flow = world
    -Z projected on the tangent plane, per-card roll/length/bend jitter.
    Custom normals = underlying cap normals (production card trick: cards
    lit as part of the surface volume, not as flat planes)."""
    verts, faces, uvs, cols, norms = [], [], [], [], []
    for _ in range(N_CARDS):
        phi = CAP_PHI * math.sqrt(rng.random())
        psi = rng.uniform(0, 2 * math.pi)
        root, n = cap_point(phi, psi)
        root = root - n * 0.015
        flow = DOWN - n * DOWN.dot(n)
        if flow.length_squared < 0.04:
            continue
        flow.normalize()
        side = n.cross(flow).normalized()
        # roll jitter around the flow axis breaks the shingle pattern
        roll = rng.uniform(-0.15, 0.15)
        n2 = n * math.cos(roll) + side * math.sin(roll)
        side = side * math.cos(roll) - n * math.sin(roll)
        L = rng.uniform(0.14, 0.20)
        W = rng.uniform(0.06, 0.10)
        bend = rng.uniform(0.06, 0.18)
        shade = rng.uniform(0.82, 1.05)
        tint = (shade * rng.uniform(0.96, 1.04),
                shade * rng.uniform(0.95, 1.0),
                shade * rng.uniform(0.9, 0.98), 1.0)
        base_i = len(verts)
        NU, NV = 3, 4
        for iv in range(NV):
            t = iv / (NV - 1)
            for iu in range(NU):
                u = iu / (NU - 1)
                p = (root + flow * (t * L) + side * ((u - 0.5) * W * (1 - 0.35 * t))
                     + n2 * (bend * L * t * t))
                verts.append(tuple(p)); norms.append(tuple(n))
                uvs.append((u, t)); cols.append(tint)
        for iv in range(NV - 1):
            for iu in range(NU - 1):
                a = base_i + iv * NU + iu
                faces.append((a, a + 1, a + 1 + NU, a + NU))
    me = bpy.data.meshes.new("FurCards")
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop_i, l in enumerate(me.loops):
        uv.data[loop_i].uv = uvs[l.vertex_index]
    ca = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    for vi, c in enumerate(cols):
        ca.data[vi].color = c
    try:
        me.normals_split_custom_set_from_pydata(norms)
    except Exception as e:
        print("custom normals skipped:", e)
    return me

def build_group(card_mat, under_mat, xoff, seed=1212):
    rng = random.Random(seed)
    cap = bpy.data.objects.new("UndercoatCap", build_undercoat())
    bpy.context.collection.objects.link(cap)
    cap.location.x = xoff
    cap.data.materials.append(under_mat)
    cards = bpy.data.objects.new("FurCards", build_card_mesh(rng))
    bpy.context.collection.objects.link(cards)
    cards.location.x = xoff
    cards.data.materials.append(card_mat)
    return cap, cards

# ---------------------------------------------------------------- materials
def tex_nodes(nt, principled):
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(TEX)
    tex.image.colorspace_settings.name = "sRGB"
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[1])
    nt.links.new(vc.outputs["Color"], mix.inputs[2])
    nt.links.new(mix.outputs["Color"], principled.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], principled.inputs["Alpha"])
    return tex

def base_principled(nt):
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    bsdf.inputs["IOR"].default_value = 1.45
    tex_nodes(nt, bsdf)
    return bsdf

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.surface_render_method = "DITHERED"   # Eevee hashed-alpha equivalent
    return m

GUARD_TINT = hex2lin("#d9ae7a")

def mat_plain():
    m = new_mat("FurCard_A_plain")
    base_principled(m.node_tree)
    return m

def mat_sheen():
    m = new_mat("FurCard_B_sheen")
    bsdf = base_principled(m.node_tree)
    # proposed fur_card record values: weight 0.6, roughness 0.5,
    # tint = guard-hair colour. Exporter folds weight x tint -> sheenColorFactor.
    bsdf.inputs["Sheen Weight"].default_value = 0.6
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    bsdf.inputs["Sheen Tint"].default_value = GUARD_TINT
    return m

def mat_aniso_rim():
    m = new_mat("FurCard_C_aniso_rim")
    nt = m.node_tree
    bsdf = base_principled(nt)
    bsdf.inputs["Anisotropic"].default_value = 0.7
    bsdf.inputs["Anisotropic Rotation"].default_value = 0.0
    tan = nt.nodes.new("ShaderNodeTangent")
    tan.direction_type = "UV_MAP"
    tan.uv_map = "UVMap"
    nt.links.new(tan.outputs["Tangent"], bsdf.inputs["Tangent"])
    # rim/fuzz: Fresnel -> shaped ramp -> emission mixed over the BSDF
    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = 1.35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.62
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    # ADDITIVE rim (v2): emission scaled BY the ramp, added over the BSDF.
    # v1 used a Mix Shader -- at grazing angles the mix factor saturates
    # across texel-thin card fragments and REPLACES their shading with flat
    # emission (kept as renders/c_rim_mix_failure.png). Additive keeps the
    # underlying shading and only adds halo energy.
    tintn = nt.nodes.new("ShaderNodeRGB")
    tintn.outputs[0].default_value = GUARD_TINT
    scal = nt.nodes.new("ShaderNodeMixRGB")
    scal.blend_type = "MULTIPLY"
    scal.inputs[0].default_value = 1.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.35
    add = nt.nodes.new("ShaderNodeAddShader")
    out = nt.nodes["Material Output"]
    nt.links.new(fres.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], scal.inputs[1])
    nt.links.new(tintn.outputs["Color"], scal.inputs[2])
    nt.links.new(scal.outputs["Color"], em.inputs["Color"])
    nt.links.new(bsdf.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    return m

def mat_undercoat():
    m = new_mat("Undercoat_skin_furred_base")
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex2lin("#6b4c33")
    bsdf.inputs["Roughness"].default_value = 0.88
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    bsdf.inputs["Sheen Weight"].default_value = 0.6
    bsdf.inputs["Sheen Roughness"].default_value = 0.55
    bsdf.inputs["Sheen Tint"].default_value = GUARD_TINT
    return m

# ---------------------------------------------------------------- scene
def setup_world_lights():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    w = bpy.data.worlds.new("Studio")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.03, 0.03, 0.04, 1)
    bg.inputs[1].default_value = 0.25
    def area(name, loc, size, size_y, energy, color):
        ld = bpy.data.lights.new(name, "AREA")
        ld.shape = "RECTANGLE"; ld.size = size; ld.size_y = size_y
        ld.energy = energy; ld.color = color
        o = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(o)
        o.location = loc; look_at(o, tuple(PATCH_C))
        return o
    PC = PATCH_C
    area("Key", PC + Vector((-1.35, -0.75, 1.15)), 2.4, 0.5, 300, (1.0, 0.96, 0.9))
    area("Fill", PC + Vector((1.25, -0.45, 0.25)), 1.5, 1.5, 30, (0.8, 0.88, 1.0))
    area("BackRim", PC - AXIS * 1.1 + Vector((0.2, 0.35, 0.85)), 1.2, 0.6, 380,
         (1.0, 0.85, 0.66))
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 42
    cam = bpy.data.objects.new("Cam", cam_d)
    bpy.context.collection.objects.link(cam)
    cam.location = PC + AXIS * 2.35 + Vector((0, 0, 0.18))
    look_at(cam, tuple(PC))
    sc.camera = cam
    return sc

def render(sc, path, res, samples):
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.cycles.samples = samples
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"RENDERED {path} in {dt:.1f}s ({res}px, {samples}spp)", flush=True)
    return dt

def main():
    clear_scene()
    sc = setup_world_lights()
    under = mat_undercoat()
    setups = [("a_plain", mat_plain), ("b_sheen", mat_sheen),
              ("c_aniso_rim", mat_aniso_rim)]
    only = os.environ.get("A12_ONLY")
    if only:
        setups = [x for x in setups if x[0] == only]
    times = {}
    for name, ctor in setups:
        build_group(ctor(), under, 0.0)
        times[name] = render(sc, os.path.join(BASE, "renders", name + ".png"), 512, 64)
        for o in list(bpy.context.scene.objects):
            if o.name.startswith(("UndercoatCap", "FurCards")):
                bpy.data.objects.remove(o, do_unlink=True)
    print("RENDER TIMES:", times, flush=True)
    if os.environ.get("A12_SKIP_BLEND"):
        return
    # saved testbed: all three side by side
    setups = [("a_plain", mat_plain), ("b_sheen", mat_sheen),
              ("c_aniso_rim", mat_aniso_rim)]
    for i, (name, ctor) in enumerate(setups):
        build_group(ctor(), under, (i - 1) * 1.85)
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(BASE, "fur_shading_testbed.blend"))
    print("SAVED testbed blend", flush=True)

main()
