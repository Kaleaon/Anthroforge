"""B18 probe #2: corrected attempts. Introspect operator RNA first, build calls
from the real property lists, log outcomes verbatim.
Run: blender -b --factory-startup -noaudio --python probe2_headless.py
"""
import bpy

OUT = []
def log(name, ok, detail=""):
    OUT.append((name, bool(ok), str(detail)[:500]))
    print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:220])

def fresh_cube():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    mod = ob.modifiers.new("Sub", 'SUBSURF'); mod.levels = 3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return bpy.context.active_object

def props(op_path):
    op = eval(op_path)
    return [p.identifier for p in op.get_rna_type().properties if p.identifier != 'rna_type']

# --- mesh_filter with real kwargs ----------------------------------------------
ob = fresh_cube()
try:
    bpy.ops.object.mode_set(mode='SCULPT')
    pr = props("bpy.ops.sculpt.mesh_filter")
    kwargs = {}
    if 'type' in pr: kwargs['type'] = 'SMOOTH'
    if 'iteration_count' in pr: kwargs['iteration_count'] = 2
    if 'repeat' in pr: kwargs['repeat'] = 2
    before = tuple(round(c, 6) for c in ob.data.vertices[0].co)
    bpy.ops.sculpt.mesh_filter(**kwargs)
    after = tuple(round(c, 6) for c in ob.data.vertices[0].co)
    log("sculpt.mesh_filter(SMOOTH) corrected", True, f"props={pr} vert moved={before != after}")
except Exception as e:
    log("sculpt.mesh_filter(SMOOTH) corrected", False, repr(e))
finally:
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except Exception: pass

# --- brush stroke with introspected stroke-element props ------------------------
ob = fresh_cube()
try:
    bpy.ops.object.mode_set(mode='SCULPT')
    pr = props("bpy.ops.sculpt.brush_stroke")
    log("brush_stroke RNA props", True, f"{pr}")
    # try to give the tool a brush
    brush_note = ""
    try:
        br = bpy.data.brushes.get("Draw")
        if br is None:
            br = bpy.data.brushes.new("B18Draw", mode='SCULPT')
        bpy.context.tool_settings.sculpt.brush = br
        brush_note = "brush assigned via tool_settings"
    except Exception as e:
        brush_note = "brush assign failed: " + repr(e)[:120]
    elem = {"name": "stroke", "mouse_event": (200.0, 200.0), "pen_flip": False,
            "is_start": True, "location": (0.0, 0.0, 0.55), "size": 60.0,
            "pressure": 1.0, "time": 0.0, "mouse": (200.0, 200.0),
            "x_tilt": 0.0, "y_tilt": 0.0}
    elem = {k: v for k, v in elem.items()}
    before = len(ob.data.vertices)
    bpy.ops.sculpt.brush_stroke(stroke=[elem])
    log("sculpt.brush_stroke corrected", True, f"executed; {brush_note}; verts={before}")
except Exception as e:
    log("sculpt.brush_stroke corrected", False, repr(e))
finally:
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except Exception: pass

# --- face_sets_init op -----------------------------------------------------------
ob = fresh_cube()
try:
    bpy.ops.object.mode_set(mode='SCULPT')
    bpy.ops.sculpt.face_sets_init(mode='LOOSE_PARTS')
    log("sculpt.face_sets_init", True, "executed")
except Exception as e:
    log("sculpt.face_sets_init", False, repr(e))
finally:
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except Exception: pass

# --- quadriflow (object mode; shell timeout guards a hang) -----------------------
ob = fresh_cube()
try:
    bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=True, use_preserve_sharp=True,
                                     use_preserve_boundary=True, smooth_normals=True,
                                     mode='FACES', target_faces=200)
    log("object.quadriflow_remesh", True, f"verts -> {len(ob.data.vertices)}")
except Exception as e:
    log("object.quadriflow_remesh", False, repr(e))

with open("/home/hatch/workspace/anthroforge-v2/model-craft/b18-sculpt/work/probe2_results.txt", "w") as f:
    for n, ok, d in OUT:
        f.write(("PASS  " if ok else "FAIL  ") + n + " :: " + d + "\n")
print("B18 PROBE2 DONE")
