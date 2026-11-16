"""A17 fur states: one groom, three parameter states (dry / wet / wind).

FINISHER RUN COPY of build_states.py (original left untouched). The design
is the original's, verbatim, except three compatibility patches, each forced
by the actual stage-2 groom file and recorded here and in fur_states.json:

PATCH 1 (material node resolution): the original assumed the groom's
FurHair material contains a BSDF_HAIR_PRINCIPLED node. It does not —
fur_stage2.blend's FurHair slot holds a plain BSDF_PRINCIPLED (Base Color
0.072/0.054/0.041 linear, Roughness 0.62). hair_node() therefore prefers a
hair BSDF and falls back to the Principled node; deltas map by input-name
candidates (Color->Base Color, Coat->Coat Weight). Deltas with no analog
input on the actual node (Radial Roughness) are recorded in the JSON as
unapplied, never silently dropped.
PATCH 2 (snapshot material): the original snapshot() read the shared
bpy.data.materials["FurHair"] for every object, so the wet/wind "resolved"
records would have shown the DRY material. snapshot() now resolves the
material from the object's own particle-settings material slot.
PATCH 3 (provenance): the records JSON states which node the material
deltas were actually applied to.

Everything else — state construction, particle deltas, records shape,
studio, renders — is the original script unchanged: the original object is
the DRY reference state; WET and WIND are full copies whose particle
settings + hair material differ ONLY by the documented state deltas. No
resimulation, no key editing: every difference between the three renders
is a settings/material value. Writes fur_states.json next to the
deliverables.
"""
import bpy, json, sys
sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera, set_system_visibility

SRC = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend"
OUTDIR = "/home/hatch/workspace/anthroforge-v2/fur-craft/a17-states"
GROOM = {"FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat"}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
base_ob = bpy.data.objects["BaraWolfBody"]

TRACKED = ["count", "hair_length", "root_radius", "radius_scale", "clump_factor",
           "clump_shape", "use_clump_noise", "clump_noise_size", "kink",
           "kink_amplitude", "kink_frequency", "kink_shape",
           "kink_amplitude_random", "kink_axis_random", "roughness_1",
           "roughness_2", "roughness_endpoint", "child_length_threshold",
           "rendered_child_count"]

# ------------------------------------------------------- PATCH 1 helpers
def hair_node(mat):
    """(node, kind): Principled Hair BSDF if present, else the BSDF that
    actually occupies the groom's hair slot."""
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_HAIR_PRINCIPLED':
            return n, 'BSDF_HAIR_PRINCIPLED'
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n, 'BSDF_PRINCIPLED'
    return None, None

def mat_get(node, *names):
    for nm in names:
        if nm in node.inputs:
            return node.inputs[nm].default_value
    return None

def mat_set(node, value, *names):
    for nm in names:
        if nm in node.inputs:
            node.inputs[nm].default_value = value
            return nm
    return None

def snapshot(ob):
    out = {}
    for ps in ob.particle_systems:
        p = ps.settings
        out[ps.name] = {k: getattr(p, k) for k in TRACKED if hasattr(p, k)}
    # PATCH 2: this object's own hair material (via its particle slot)
    slot = ob.particle_systems[0].settings.material
    mat = ob.data.materials[slot - 1]
    hair, kind = hair_node(mat)
    m = {"_node": kind, "_material": mat.name}
    c = mat_get(hair, "Color", "Base Color")
    if c is not None:
        m["Color"] = list(c)
    r = mat_get(hair, "Roughness")
    if r is not None:
        m["Roughness"] = r
    rr = mat_get(hair, "Radial Roughness")
    if rr is not None:
        m["Radial Roughness"] = rr
    out["_material"] = m
    return out

BASELINE = snapshot(base_ob)
print("BASELINE", json.dumps(BASELINE))

def region(psname):
    return psname.replace("FUR_", "")

# ---------------------------------------------------------------- wet
def apply_wet(ob, mat):
    for ps in ob.particle_systems:
        p = ps.settings
        p.clump_factor = min(1.0, 1.45 * p.clump_factor + 0.25)
        p.clump_shape = -0.85
        p.use_clump_noise = True
        p.clump_noise_size = 0.35
        if p.kink != 'NO':
            p.kink_amplitude *= 0.3
            p.kink_frequency *= 0.7
        p.hair_length *= 0.92
        p.root_radius *= 0.85
        p.radius_scale = 0.9
        p.roughness_1 = 0.18
        p.roughness_2 = 0.12
        p.child_length_threshold = 0.05
    hair, kind = hair_node(mat)
    c = mat_get(hair, "Color", "Base Color")
    mat_set(hair, (c[0] * 0.45, c[1] * 0.45, c[2] * 0.45, 1.0), "Color", "Base Color")
    mat_set(hair, 0.24, "Roughness")
    mat_set(hair, 0.38, "Radial Roughness")  # no-op if no such input (PATCH 1)
    mat_set(hair, 0.35, "Coat", "Coat Weight")

# ---------------------------------------------------------------- wind
WIND_AMP = {"ruff": 0.030, "back": 0.020, "coat": 0.014, "belly": 0.006, "bodyhair": 0.003}
WIND_FREQ = {"ruff": 2.0, "back": 2.5, "coat": 3.0, "belly": 3.0, "bodyhair": 3.0}
WIND_SPLAY = {"ruff": 0.20, "back": 0.15, "coat": 0.10, "belly": 0.05, "bodyhair": 0.05}

def apply_wind(ob, mat):
    for ps in ob.particle_systems:
        p = ps.settings
        r = region(ps.name)
        p.kink = 'WAVE'
        try:
            p.kink_axis = 'X'
        except Exception as e:
            print("kink_axis unset:", e)
        p.kink_amplitude = WIND_AMP[r]
        p.kink_frequency = WIND_FREQ[r]
        p.kink_shape = -0.5
        p.kink_amplitude_random = 0.1
        p.kink_axis_random = 0.0
        p.clump_factor *= 0.75
        p.clump_shape = -0.2
        p.roughness_endpoint = WIND_SPLAY[r]
    hair, kind = hair_node(mat)
    mat_set(hair, 0.47, "Roughness")
    mat_set(hair, 0.60, "Radial Roughness")  # no-op if no such input (PATCH 1)

# ---------------------------------------------------------------- build copies
def make_state_copy(state_id, apply_fn):
    ob = base_ob.copy()
    ob.data = base_ob.data.copy()
    ob.name = f"BaraWolfBody_{state_id}"
    bpy.context.scene.collection.objects.link(ob)
    # unique settings per system
    for ps in ob.particle_systems:
        ps.settings = ps.settings.copy()
        ps.settings.name = f"{ps.name}_{state_id}"
    # state material in the same hair slot
    me = ob.data
    slot = next(i for i, m in enumerate(me.materials) if m and m.name == "FurHair")
    mat = bpy.data.materials["FurHair"].copy()
    mat.name = f"FurHair_{state_id}"
    me.materials[slot] = mat
    for ps in ob.particle_systems:
        ps.settings.material = slot + 1
    if apply_fn:
        apply_fn(ob, mat)
    ob["fur_state"] = state_id
    return ob

base_ob.name = "BaraWolfBody_dry_neutral"
base_ob["fur_state"] = "dry_neutral"
wet_ob = make_state_copy("wet_clumped", apply_wet)
wind_ob = make_state_copy("wind_swept", apply_wind)
STATES = {"dry_neutral": base_ob, "wet_clumped": wet_ob, "wind_swept": wind_ob}

for sid, ob in STATES.items():
    print(sid, json.dumps(snapshot(ob)))

# ---------------------------------------------------------------- records json
# PATCH 3: state plainly what the material deltas were applied to.
_wet_mat = wet_ob.data.materials[wet_ob.particle_systems[0].settings.material - 1]
_mat_kind = hair_node(_wet_mat)[1]
MAT_NOTE = ("Source groom's hair slot (FurHair in fur_stage2.blend) is a "
            "BSDF_PRINCIPLED, not a Principled Hair BSDF; material deltas "
            "were applied to it via input-name mapping (Color->Base Color, "
            "Coat->Coat Weight). The delta records below are written in "
            "hair-BSDF terms, the format's normative form.")
UNAPPLIED = ([] if _mat_kind == 'BSDF_HAIR_PRINCIPLED' else
             ["Radial Roughness — no analog input on BSDF_PRINCIPLED; "
              "retained in the delta record, not applied to the prototype "
              "material"])
records = {
    "format": "anthroforge.fur_states v1 (draft for the character format)",
    "groom_ref": "fur-prototype stage2 groom on BaraWolfBody (5 region systems)",
    "rule": "A fur state is a parameter morph over ONE groom: per-region particle-setting deltas + one hair-material delta set. States blend by lerping every numeric field; no resimulation, no re-grooming.",
    "material_note": MAT_NOTE,
    "material_applied_to": _mat_kind,
    "baseline_dry_neutral": BASELINE,
    "states": {
        "wet_clumped": {
            "kind": "fur_state", "blend_weight_default": 1.0,
            "global_deltas": {
                "clump_factor": "min(1, 1.45x + 0.25)", "clump_shape": -0.85,
                "use_clump_noise": True, "clump_noise_size": 0.35,
                "kink_amplitude": "x0.3", "kink_frequency": "x0.7",
                "hair_length": "x0.92", "root_radius": "x0.85",
                "radius_scale": 0.9, "roughness_1": 0.18, "roughness_2": 0.12,
                "child_length_threshold": 0.05},
            "material_deltas": {"Color": "x0.45 (linear)", "Roughness": 0.24,
                                "Radial Roughness": 0.38, "Coat": 0.35},
            "material_unapplied": UNAPPLIED,
            "resolved": snapshot(wet_ob)},
        "wind_swept": {
            "kind": "fur_state", "blend_weight_default": 1.0,
            "wind_axis_world": "+X",
            "global_deltas": {
                "kink": "WAVE (all systems)", "kink_axis": "X",
                "kink_shape": -0.5, "kink_amplitude_random": 0.1,
                "kink_axis_random": 0.0, "clump_factor": "x0.75",
                "clump_shape": -0.2},
            "region_deltas": {"kink_amplitude": WIND_AMP,
                              "kink_frequency": WIND_FREQ,
                              "roughness_endpoint": WIND_SPLAY},
            "material_deltas": {"Roughness": 0.47, "Radial Roughness": 0.60},
            "material_unapplied": UNAPPLIED,
            "reserved": {"bend_vector": [1, 0, 0],
                         "note": "true root-to-tip directional bend is an engine-side groom-blend field; this Blender prototype approximates it with the coherent WAVE kink and does not apply bend_vector"},
            "resolved": snapshot(wind_ob)},
    },
}
with open(f"{OUTDIR}/fur_states.json", "w") as f:
    json.dump(records, f, indent=1)
txt = bpy.data.texts.new("fur_states.json")
txt.write(json.dumps(records, indent=1))
print("RECORDS WRITTEN")

# ---------------------------------------------------------------- studio + save
sc = bpy.context.scene
cam = build_studio(sc)
sc.render.engine = 'CYCLES'
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.device = 'CPU'
try:
    sc.cycles.hair_shape_type = 'CURVE'
except Exception:
    pass
sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x, sc.render.resolution_y = 640, 800
set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
for ob in STATES.values():
    set_system_visibility(ob, GROOM)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUTDIR}/fur_states.blend")
print("SAVED BLEND")

# ---------------------------------------------------------------- renders
for sid, ob in STATES.items():
    for other in STATES.values():
        other.hide_render = other is not ob
        other.hide_viewport = other is not ob
    sc.render.filepath = f"{OUTDIR}/render_{sid}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sid, flush=True)
print("ALL DONE")
