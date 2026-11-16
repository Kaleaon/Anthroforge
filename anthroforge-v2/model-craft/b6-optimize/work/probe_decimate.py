#!/usr/bin/env python3
"""Probe: does Blender 5.2's Decimate (Collapse) honour a vertex group,
and how do the factor / invert settings behave?

Synthetic test: a 40x40 grid plane. Left half gets importance weight 1.0,
right half 0.0. Decimate to ratio 0.25 three ways:
  A) no vertex group (naive control)
  B) vertex group + factor 1.0
  C) vertex group + factor + invert
Report surviving vertex counts per half for each.
  blender -b --python probe_decimate.py
"""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

# --- inspect the modifier's RNA properties first -------------------------
tmp = bpy.data.meshes.new("tmp")
o = bpy.data.objects.new("tmp", tmp)
bpy.context.collection.objects.link(o)
m = o.modifiers.new("d", 'DECIMATE')
props = [p.identifier for p in m.bl_rna.properties]
print("DECIMATE PROPS:", [p for p in props if 'vert' in p or 'group' in p
                         or 'factor' in p or 'ratio' in p or 'invert' in p])
bpy.data.objects.remove(o)

def build():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40,
                                    size=2.0)
    ob = bpy.context.active_object
    vg = ob.vertex_groups.new(name="importance")
    left = [v.index for v in ob.data.vertices if v.co.x < 0]
    vg.add(left, 1.0, 'REPLACE')
    return ob

def run(tag, use_vg, factor=None, invert=False):
    ob = build()
    n0 = len(ob.data.vertices)
    left0 = sum(1 for v in ob.data.vertices if v.co.x < 0)
    mod = ob.modifiers.new("dec", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = 0.25
    if use_vg:
        mod.vertex_group = "importance"
        if factor is not None:
            try:
                mod.vertex_group_factor = factor
            except Exception as e:
                print(tag, "factor set failed:", e)
        mod.invert_vertex_group = invert
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    me = ob.data
    left1 = sum(1 for v in me.vertices if v.co.x < -1e-6)
    print(f"{tag}: verts {n0}->{len(me.vertices)} "
          f"left(weighted) {left0}->{left1} "
          f"faces->{len(me.polygons)}")
    bpy.data.objects.remove(ob)

run("A naive      ", False)
run("B vg f=1.0   ", True, 1.0)
run("C vg f=1.0inv", True, 1.0, invert=True)
run("D vg f=5.0   ", True, 5.0)
print("PROBE DONE")
