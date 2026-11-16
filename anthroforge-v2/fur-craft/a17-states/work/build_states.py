"""A17 fur states: one groom, three parameter states (dry / wet / wind).

Loads the fur-prototype stage-2 groom (Bara Wolf, 5 particle systems),
keeps the original object as the DRY reference state, and builds WET and
WIND as full copies whose particle settings + hair material differ ONLY
by the documented state deltas. No resimulation, no key editing: every
difference between the three renders is a settings/material value.
Writes fur_states.json (the state records) next to the deliverables.
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

def snapshot(ob):
    out = {}
    for ps in ob.particle_systems:
        p = ps.settings
        out[ps.name] = {k: getattr(p, k) for k in TRACKED if hasattr(p, k)}
    hair = [n for n in bpy.data.materials["FurHair"].node_tree.nodes
            if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
    out["_material"] = {
        "Color": list(hair.inputs["Color"].default_value),
        "Roughness": hair.inputs["Roughness"].default_value,
        "Radial Roughness": hair.inputs["Radial Roughness"].default_value,
    }
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
    hair = [n for n in mat.node_tree.nodes if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
    c = hair.inputs["Color"].default_value
    hair.inputs["Color"].default_value = (c[0] * 0.45, c[1] * 0.45, c[2] * 0.45, 1.0)
    hair.inputs["Roughness"].default_value = 0.24
    hair.inputs["Radial Roughness"].default_value = 0.38
    if "Coat" in hair.inputs:
        hair.inputs["Coat"].default_value = 0.35

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
    hair = [n for n in mat.node_tree.nodes if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
    hair.inputs["Roughness"].default_value = 0.47
    hair.inputs["Radial Roughness"].default_value = 0.60

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
records = {
    "format": "anthroforge.fur_states v1 (draft for the character format)",
    "groom_ref": "fur-prototype stage2 groom on BaraWolfBody (5 region systems)",
    "rule": "A fur state is a parameter morph over ONE groom: per-region particle-setting deltas + one hair-material delta set. States blend by lerping every numeric field; no resimulation, no re-grooming.",
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
