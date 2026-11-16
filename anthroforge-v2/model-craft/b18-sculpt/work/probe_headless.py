"""B18 probe: which sculpt-related operations actually run in Blender -b (headless)?
Each test logs PASS/FAIL + the exception text verbatim to probe_results.txt.
Run: blender -b --factory-startup -noaudio --python probe_headless.py
"""
import bpy, traceback, json, sys

LOG = []
def log(name, ok, detail=""):
    LOG.append({"test": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:200])

def fresh_cube():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    return bpy.context.active_object

# --- 0. can we even enter sculpt mode headless? -------------------------------
ob = fresh_cube()
try:
    bpy.ops.object.mode_set(mode='SCULPT')
    log("mode_set(SCULPT)", bpy.context.object.mode == 'SCULPT', "mode=" + bpy.context.object.mode)
except Exception as e:
    log("mode_set(SCULPT)", False, repr(e))

# --- 1. a real brush stroke ----------------------------------------------------
try:
    ts = bpy.context.scene.tool_settings
    ts.sculpt.brush = bpy.data.brushes.get('Draw') or bpy.data.brushes[0] if bpy.data.brushes else None
    stroke = [dict(name="stroke", mouse_event=(100.0, 100.0), pen_flip=False, is_start=True,
                   location=(0.0, 0.0, 0.5), size=0.5, pressure=1.0, time=0.0, mouse=(100.0, 100.0),
                   x_tilt=0.0, y_tilt=0.0)]
    bpy.ops.sculpt.brush_stroke(stroke=stroke)
    log("sculpt.brush_stroke", True, "executed without exception")
except Exception as e:
    log("sculpt.brush_stroke", False, repr(e))

# --- 2. mesh filter ------------------------------------------------------------
try:
    bpy.ops.sculpt.mesh_filter(type='SMOOTH', repeat=1)
    log("sculpt.mesh_filter(SMOOTH)", True, "executed")
except Exception as e:
    log("sculpt.mesh_filter(SMOOTH)", False, repr(e))

# --- 3. dyntopo toggle ----------------------------------------------------------
try:
    bpy.ops.sculpt.dynamic_topology_toggle()
    log("sculpt.dynamic_topology_toggle", True,
        "use_dyntopo=" + str(bpy.context.scene.tool_settings.sculpt.use_unified_color if False else bpy.context.object.data.use_dynamic_topology_sculpting if hasattr(bpy.context.object.data,'use_dynamic_topology_sculpting') else 'n/a'))
except Exception as e:
    log("sculpt.dynamic_topology_toggle", False, repr(e))
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except Exception:
    pass

# --- 4. voxel remesh (object mode) ----------------------------------------------
ob = fresh_cube()
before = len(ob.data.vertices)
try:
    ob.data.remesh_voxel_size = 0.2
    bpy.ops.object.voxel_remesh()
    log("object.voxel_remesh", len(ob.data.vertices) != before,
        f"verts {before} -> {len(ob.data.vertices)}")
except Exception as e:
    log("object.voxel_remesh", False, repr(e))

# --- 5. multires: add + subdivide (object mode op) -------------------------------
ob = fresh_cube()
try:
    mod = ob.modifiers.new("MR", 'MULTIRES')
    bpy.ops.object.multires_subdivide(modifier=mod.name, mode='CATMULL_CLARK')
    log("object.multires_subdivide", mod.total_levels >= 1, f"total_levels={mod.total_levels}")
except Exception as e:
    log("object.multires_subdivide", False, repr(e))

# --- 6. face sets + mask as raw attributes ---------------------------------------
ob = fresh_cube()
try:
    me = ob.data
    fs = me.attributes.get(".sculpt_face_set") or me.attributes.new(name=".sculpt_face_set", type='INT', domain='FACE')
    fs.data[0].value = 3
    mk = me.attributes.get(".sculpt_mask") or me.attributes.new(name=".sculpt_mask", type='FLOAT', domain='POINT')
    mk.data[0].value = 0.5
    ok = me.attributes[".sculpt_face_set"].data[0].value == 3 and abs(me.attributes[".sculpt_mask"].data[0].value - 0.5) < 1e-6
    log("attributes .sculpt_face_set/.sculpt_mask", ok, "round-trip read OK" if ok else "mismatch")
except Exception as e:
    log("attributes .sculpt_face_set/.sculpt_mask", False, repr(e))

# --- 7. edit-mode symmetrize ------------------------------------------------------
try:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.symmetrize(direction='POSITIVE_Y', threshold=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
    log("mesh.symmetrize (edit mode)", True, "executed")
except Exception as e:
    log("mesh.symmetrize (edit mode)", False, repr(e))

# --- 8. context facts --------------------------------------------------------------
log("context.window is None in -b", bpy.context.window is None, f"window={bpy.context.window}")
areas = []
try:
    areas = [a.type for w in bpy.data.windows for a in w.areas] if hasattr(bpy.data, 'windows') else []
except Exception:
    pass
log("VIEW_3D areas available", 'VIEW_3D' in areas, f"areas={areas}")

with open("/home/hatch/workspace/anthroforge-v2/model-craft/b18-sculpt/work/probe_results.txt", "w") as f:
    for row in LOG:
        f.write(("PASS  " if row["ok"] else "FAIL  ") + row["test"] + " :: " + row["detail"] + "\n")
print("B18 PROBE DONE", sum(1 for r in LOG if r['ok']), "/", len(LOG))
