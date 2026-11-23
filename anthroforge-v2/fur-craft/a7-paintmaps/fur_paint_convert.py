"""fur_paint_convert -- painted fur maps -> groom parameters + groom scene.

The A7 tool script. Reads a paintable blend (FURP_* layers on the body
mesh) and produces, in --outdir:

  groom_params_<tag>.json   per-region groom parameters, APP_BLUEPRINT
                            SS9.5 record shape, measured FROM THE MAPS
  groom_from_paint_<tag>.blend
      - <body>_groom : production binding -- one legacy particle system
        per region, its density vertex group baked as
        FURP_density x region, length/clump/curl bound to the global
        FURP groups (Blender 5.2 binds these on the ParticleSystem)
      - FURP_groom_<region> : strand preview -- hair curves grown from
        the maps (density sampling, painted length, flow-following
        with lift + sag, clump attraction, curl wiggle, zone colours)
      - FURP_guides : guide curves integrated along the painted flow
        field (the record's guide_set)

Usage:
  blender -b --python fur_paint_convert.py -- \
      --input fur_paintable_rev2.blend --outdir out --tag rev2 \
      [--strands 9000]
"""
import argparse
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import kdtree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import furp_common as fc  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--strands", type=int, default=9000)
args = ap.parse_args(argv)

OUTDIR = Path(args.outdir)
OUTDIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=args.input)
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
N = len(me.vertices)
rev = int(me.get("FURP_revision", 0))
set_id = str(me.get("FURP_set_id", "unknown"))
author = str(me.get("FURP_author", "unknown"))

pos, nrm, tan, bit, tris = fc.mesh_arrays(ob)
reg = {r: fc.read_group(ob, "FUR_" + r, N) for r in fc.REGION_ORDER}
density = fc.read_group(ob, "FURP_density", N)
length = fc.read_group(ob, "FURP_length", N)
clump = fc.read_group(ob, "FURP_clump", N)
curl = fc.read_group(ob, "FURP_curl", N)
d_flow, lift = fc.decode_direction(fc.read_color_attr(me, "FURP_direction", N), tan, bit)
root_rgba = fc.read_color_attr(me, "FURP_zone_root", N)
tip_rgba = fc.read_color_attr(me, "FURP_zone_tip", N)
root_rgb, tip_rgb = root_rgba[:, :3], tip_rgba[:, :3]

# ---------------------------------------------------------------- params
p = pos[tris]
face_area = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
total_area = float(face_area.sum())


def wmean(vals, w):
    return float((vals * w).sum() / max(w.sum(), 1e-9))


def lin2hex(c):
    s = np.clip(np.power(np.clip(c, 0.0, 1.0), 1.0 / 2.2) * 255.0, 0, 255)
    return "#" + "".join(f"{int(round(v)):02X}" for v in s)


params = {
    "format": "anthroforge.fur.groom_params",
    "version": 1,
    "source": {"paintmap_set": set_id, "revision": rev, "author": author,
               "mesh": ob.name, "verts": N, "input": Path(args.input).name},
    "profile": {"length_ref_m": fc.LENGTH_REF_M,
                "pattern_default": "tipped"},
    "regions": {},
    "groom": {"guide_set": f"FURP_guides@rev{rev}"},
    "perf": {"surface_area_m2": round(total_area, 3),
             "preview_strands": args.strands},
}
region_stats = {}
for r in fc.REGION_ORDER:
    w = reg[r]
    st = {
        "density": round(wmean(density, w), 3),
        "length_m": round(wmean(length * fc.LENGTH_REF_M, w), 4),
        "length_variation": round(float(np.sqrt(
            max(wmean((length * fc.LENGTH_REF_M) ** 2, w)
                - wmean(length * fc.LENGTH_REF_M, w) ** 2, 0.0))), 4),
        "clump": round(wmean(clump, w), 3),
        "curl": round(wmean(curl, w), 3),
        "lift": round(wmean(lift, w), 3),
        "colour": {"root": lin2hex([wmean(root_rgb[:, c], w) for c in range(3)]),
                   "tip": lin2hex([wmean(tip_rgb[:, c], w) for c in range(3)]),
                   "pattern": "tipped"},
        "area_share": round(float(w.sum() / sum(reg[q].sum() for q in fc.REGION_ORDER)), 3),
    }
    params["regions"][r] = st
    region_stats[r] = st
# perf estimate, calibrated on the fur prototype (15.5k parents + x6
# children over this same body): hero strands ~ parents x 6.
hero = int(round(sum(region_stats[r]["density"] * region_stats[r]["area_share"]
                     for r in fc.REGION_ORDER) * total_area * 52000))
params["perf"]["est_hero_strands_x6_children"] = hero
params["perf"]["est_lod0_cards"] = int(hero * 0.19)

# ------------------------------------------------------- strand preview
rng = np.random.default_rng(1200 + rev)
face_w = face_area * density[tris].mean(axis=1)
cdf = np.cumsum(face_w)
cdf /= cdf[-1]
S = args.strands
fi = np.searchsorted(cdf, rng.random(S))
u = rng.random(S)
v = rng.random(S)
su = np.sqrt(u)
b0 = 1.0 - su
b1 = su * (1.0 - v)
b2 = su * v
B = np.stack([b0, b1, b2], axis=1)                     # (S,3) barycentric
fv = tris[fi]                                          # (S,3)


def interp(arr):
    return np.einsum("sj,sji->si", B, arr[fv])


rpos = interp(pos)
rnrm = interp(nrm)
rnrm /= np.maximum(np.linalg.norm(rnrm, axis=1, keepdims=True), 1e-12)
rflow = interp(d_flow)
rflow -= np.einsum("ij,ij->i", rflow, rnrm)[:, None] * rnrm
rflow /= np.maximum(np.linalg.norm(rflow, axis=1, keepdims=True), 1e-12)
rbit = interp(bit)
rlift = np.einsum("sj,sj->s", B, lift[fv])
rlen_map = np.einsum("sj,sj->s", B, length[fv])
rclump = np.einsum("sj,sj->s", B, clump[fv])
rcurl = np.einsum("sj,sj->s", B, curl[fv])
rregw = np.stack([np.einsum("sj,sj->s", B, reg[r][fv]) for r in fc.REGION_ORDER], axis=1)
rregion = np.array(fc.REGION_ORDER)[np.argmax(rregw, axis=1)]

P = 6
strand_len = rlen_map * fc.LENGTH_REF_M * (0.85 + 0.30 * rng.random(S))
dir0 = rlift[:, None] * rnrm + (1.0 - rlift)[:, None] * rflow
dir0 /= np.maximum(np.linalg.norm(dir0, axis=1, keepdims=True), 1e-12)

# clump targets: mean root + mean dir per 7 cm cell
cell = np.floor(rpos / 0.07).astype(np.int64)
keys = cell[:, 0] * 73856093 ^ cell[:, 1] * 19349663 ^ cell[:, 2] * 83492791
uniq, inv = np.unique(keys, return_inverse=True)
cell_root = np.zeros((len(uniq), 3))
cell_dir = np.zeros((len(uniq), 3))
for c in range(3):
    cell_root[:, c] = np.bincount(inv, weights=rpos[:, c]) / np.bincount(inv)
    cell_dir[:, c] = np.bincount(inv, weights=dir0[:, c]) / np.bincount(inv)
cell_dir /= np.maximum(np.linalg.norm(cell_dir, axis=1, keepdims=True), 1e-12)

pts = np.zeros((S, P, 3))
cur = rpos + rnrm * 0.002
dcur = dir0.copy()
step = strand_len / (P - 1)
sag = 0.5 * (1.0 - rlift) * np.clip(strand_len / 0.17, 0.0, 1.2)
phase = rng.random(S) * 6.283
for j in range(P):
    t = j / (P - 1)
    pts[:, j, :] = cur
    # curl wiggle along the bitangent
    wig = np.sin(t * np.pi * (1.0 + 3.0 * rcurl) + phase) * 0.12 * strand_len * rcurl
    pts[:, j, :] += rbit * wig[:, None] * t
    # clump attraction toward the cell's mean strand line
    axis_pt = cell_root[inv] + cell_dir[inv] * (strand_len * t)[:, None]
    pts[:, j, :] = pts[:, j, :] * (1.0 - rclump[:, None] * 0.5 * t * t) \
        + axis_pt * (rclump[:, None] * 0.5 * t * t)
    dcur = dcur + np.array([0.0, 0.0, -1.0])[None, :] * (sag * (1.0 / (P - 1)))[:, None]
    dcur /= np.maximum(np.linalg.norm(dcur, axis=1, keepdims=True), 1e-12)
    cur = cur + dcur * step[:, None]

# surface skim: a coat hugs the body -- cap each point's height above
# its root's tangent plane (lift raises the cap), and never let a
# point sink below the surface. Without this the preview dangles in
# free space beside the limbs and reads as tinsel, not fur.
off = pts - rpos[:, None, :]
hgt = np.einsum("spj,sj->sp", off, rnrm)
max_h = strand_len[:, None] * (0.15 + 0.55 * rlift[:, None])
over = np.maximum(hgt - max_h, 0.0)
under = np.minimum(hgt, 0.0)
pts -= rnrm[:, None, :] * (over * 0.85 + under)[:, :, None]


def hair_material(name, root_hex, tip_hex):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    bsdf = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], nt.nodes["Material Output"].inputs["Surface"])
    info = nt.nodes.new("ShaderNodeHairInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    root = tuple(int(root_hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    tip = tuple(int(tip_hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 1.0
    nt.links.new(info.outputs["Intercept"], ramp.inputs["Fac"])
    melanin = False
    try:
        bsdf.parametrization = "MELANIN"
        melanin = "Melanin" in bsdf.inputs
    except Exception:
        melanin = False
    if melanin:
        # COLOR parametrization leaves the specular lobe untinted, so
        # thousands of strands blow out to white and the painted zone
        # colours never read (verified with a constant dark-brown
        # control patch). The melanin model absorbs in every lobe:
        # zone colour -> melanin amount graded along the strand,
        # tip colour -> tint.
        def mel(c):
            lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
            return max(0.03, min(1.0, 1.05 - lum))
        ramp.color_ramp.elements[0].color = (mel(root),) * 3 + (1.0,)
        ramp.color_ramp.elements[1].color = (mel(tip),) * 3 + (1.0,)
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Melanin"])
        bsdf.inputs["Tint"].default_value = tuple(
            min(1.0, c ** 0.5) for c in tip) + (1.0,)
        bsdf.inputs["Melanin Redness"].default_value = 0.25
    else:
        ramp.color_ramp.elements[0].color = root + (1.0,)
        ramp.color_ramp.elements[1].color = tip + (1.0,)
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    return m


for r in fc.REGION_ORDER:
    sel = np.where(rregion == r)[0]
    if len(sel) == 0:
        continue
    cd = bpy.data.hair_curves.new(f"FURP_groom_{r}")
    cd.add_curves([P] * len(sel))
    cd.points.foreach_set("position",
                          pts[sel].astype(np.float32).ravel().tolist())
    rad = np.tile((0.0019 * (1.0 - 0.65 * np.linspace(0, 1, P))).astype(np.float32),
                  len(sel))
    if "radius" not in cd.attributes:
        cd.attributes.new("radius", "FLOAT", "POINT")
    cd.attributes["radius"].data.foreach_set("value", rad.tolist())
    st = region_stats[r]
    cd.materials.append(hair_material(f"FURP_hair_{r}",
                                      st["colour"]["root"], st["colour"]["tip"]))
    co = bpy.data.objects.new(f"FURP_groom_{r}", cd)
    bpy.context.collection.objects.link(co)
    print(f"groom[{r}]: {len(sel)} strands")

# ---------------------------------------------------------------- guides
kd = kdtree.KDTree(N)
for i, pnt in enumerate(pos):
    kd.insert(pnt, i)
kd.balance()
order = np.argsort(-density)
occupied = set()
seeds = []
for i in order:
    if density[i] < 0.5:
        break
    key = tuple(np.floor(pos[i] / 0.085).astype(int))
    if any((key[0] + dx, key[1] + dy, key[2] + dz) in occupied
           for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)):
        continue
    occupied.add(key)
    seeds.append(int(i))
    if len(seeds) >= 300:
        break
GSTEPS, GSTEP = 16, 0.011
gpts = []
for s0 in seeds:
    pnt = pos[s0] + nrm[s0] * 0.003
    line = [pnt.copy()]
    for _ in range(GSTEPS - 1):
        _, idx, _dist = kd.find(pnt)
        dd = d_flow[idx] - nrm[idx] * float(np.dot(d_flow[idx], nrm[idx]))
        ln = np.linalg.norm(dd)
        if ln < 1e-9:
            dd = d_flow[idx]
        else:
            dd = dd / ln
        pnt = pnt + dd * GSTEP + nrm[idx] * 0.0012
        line.append(pnt.copy())
    gpts.append(np.stack(line))
if gpts:
    garr = np.stack(gpts)
    gcd = bpy.data.hair_curves.new("FURP_guides")
    gcd.add_curves([GSTEPS] * len(gpts))
    gcd.points.foreach_set("position", garr.astype(np.float32).ravel().tolist())
    if "radius" not in gcd.attributes:
        gcd.attributes.new("radius", "FLOAT", "POINT")
    gcd.attributes["radius"].data.foreach_set(
        "value", [0.003] * (len(gpts) * GSTEPS))
    gm = bpy.data.materials.new("FURP_guide_mat")
    gnt = gm.node_tree
    gnt.nodes.remove(gnt.nodes["Principled BSDF"])
    gb = gnt.nodes.new("ShaderNodeBsdfHairPrincipled")
    gnt.links.new(gb.outputs["BSDF"], gnt.nodes["Material Output"].inputs["Surface"])
    gb.inputs["Color"].default_value = (0.55, 0.50, 0.42, 1.0)
    gcd.materials.append(gm)
    go = bpy.data.objects.new("FURP_guides", gcd)
    bpy.context.collection.objects.link(go)
params["groom"]["guide_count"] = len(gpts)
print(f"guides: {len(gpts)} streamlines")

# ------------------------------------------------------- particle binding
ob2 = ob.copy()
ob2.data = ob.data.copy()
ob2.name = "BaraWolfBody_groom"
bpy.context.collection.objects.link(ob2)
binding = {}
for r in fc.REGION_ORDER:
    eff = fc.clamp01(density * reg[r])
    fc.write_group(ob2, f"FURP_eff_density_{r}", eff)
    mod = ob2.modifiers.new(f"FURP_psys_{r}", "PARTICLE_SYSTEM")
    psys = ob2.particle_systems[-1]
    pset = psys.settings
    pset.type = "HAIR"
    st = region_stats[r]
    pset.count = int(max(60, round(2400 * st["density"])))
    pset.hair_length = fc.LENGTH_REF_M
    pset.child_type = "NONE"
    pset.use_even_distribution = True
    psys.vertex_group_density = f"FURP_eff_density_{r}"
    psys.vertex_group_length = "FURP_length"
    psys.vertex_group_clump = "FURP_clump"
    pset.clump_factor = 1.0
    if st["curl"] > 0.12:
        pset.kink = "CURL"
        pset.kink_amplitude = 0.004 + 0.010 * st["curl"]
        pset.kink_frequency = 2.0 + 3.0 * st["curl"]
        psys.vertex_group_kink = "FURP_curl"
    hm = hair_material(f"FURP_hair_psys_{r}", st["colour"]["root"], st["colour"]["tip"])
    ob2.data.materials.append(hm)
    try:
        pset.material = len(ob2.data.materials)
    except Exception:
        pass
    mod.show_render = False   # strand preview is the verification render
    binding[r] = {"count": pset.count, "hair_length_m": fc.LENGTH_REF_M,
                  "density_group": f"FURP_eff_density_{r}",
                  "length_group": "FURP_length", "clump_group": "FURP_clump",
                  "kink": pset.kink}
params["particle_binding"] = binding

out_json = OUTDIR / f"groom_params_{args.tag}.json"
out_json.write_text(json.dumps(params, indent=2) + "\n")
out_blend = OUTDIR / f"groom_from_paint_{args.tag}.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
print(json.dumps({r: params["regions"][r] for r in fc.REGION_ORDER}, indent=1))
print("WROTE", out_json)
print("WROTE", out_blend)
