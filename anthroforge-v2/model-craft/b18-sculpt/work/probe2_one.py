"""B18 probe #2, one test per process (argv after --). Writes probe2_<name>.txt.
A segfault in one operator cannot take the other results with it."""
import bpy, sys

name = sys.argv[sys.argv.index("--") + 1]
BASE = "/home/hatch/workspace/anthroforge-v2/model-craft/b18-sculpt/work/"

def emit(ok, detail):
    with open(BASE + "probe2_" + name + ".txt", "w") as f:
        f.write(("PASS  " if ok else "FAIL  ") + name + " :: " + str(detail)[:600] + "\n")
    print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:200], flush=True)

def fresh_cube(sub=3):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    mod = ob.modifiers.new("Sub", 'SUBSURF'); mod.levels = sub
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return bpy.context.active_object

def props(op):
    return [p.identifier for p in op.get_rna_type().properties if p.identifier != 'rna_type']

if name == "mesh_filter":
    emit_started = None
    ob = fresh_cube()
    bpy.ops.object.mode_set(mode='SCULPT')
    pr = props(bpy.ops.sculpt.mesh_filter)
    kw = {}
    if 'type' in pr: kw['type'] = 'SMOOTH'
    if 'iteration_count' in pr: kw['iteration_count'] = 2
    v0 = tuple(round(c, 6) for c in ob.data.vertices[10].co)
    try:
        bpy.ops.sculpt.mesh_filter(**kw)
        v1 = tuple(round(c, 6) for c in ob.data.vertices[10].co)
        emit(True, f"props={pr}; vert10 moved={v0 != v1}")
    except Exception as e:
        emit(False, f"props={pr}; {e!r}")

elif name == "brush_stroke":
    ob = fresh_cube()
    bpy.ops.object.mode_set(mode='SCULPT')
    pr = props(bpy.ops.sculpt.brush_stroke)
    note = "stroke props=" + str(pr)
    try:
        br = bpy.data.brushes.get("Draw") or bpy.data.brushes.new("B18Draw", mode='SCULPT')
        note += f"; brush in data: {br.name}"
    except Exception as e:
        note += "; brush create failed " + repr(e)[:100]
    v0 = tuple(round(c, 6) for c in ob.data.vertices[10].co)
    elem = {"name": "stroke", "mouse_event": (200.0, 200.0), "pen_flip": False,
            "is_start": True, "location": (0.0, 0.0, 0.55), "size": 60.0,
            "pressure": 1.0, "time": 0.0, "mouse": (200.0, 200.0),
            "x_tilt": 0.0, "y_tilt": 0.0}
    try:
        bpy.ops.sculpt.brush_stroke(stroke=[elem])
        v1 = tuple(round(c, 6) for c in ob.data.vertices[10].co)
        emit(True, note + f"; executed; vert10 moved={v0 != v1}")
    except Exception as e:
        emit(False, note + "; " + repr(e))

elif name == "face_sets_init":
    ob = fresh_cube()
    bpy.ops.object.mode_set(mode='SCULPT')
    try:
        bpy.ops.sculpt.face_sets_init(mode='LOOSE_PARTS')
        emit(True, "executed")
    except Exception as e:
        emit(False, repr(e))

elif name == "quadriflow":
    ob = fresh_cube()
    n0 = len(ob.data.vertices)
    try:
        bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=True, use_preserve_sharp=True,
                                         use_preserve_boundary=True, smooth_normals=True,
                                         mode='FACES', target_faces=200)
        emit(True, f"verts {n0} -> {len(ob.data.vertices)}")
    except Exception as e:
        emit(False, repr(e))
print("DONE", name, flush=True)
