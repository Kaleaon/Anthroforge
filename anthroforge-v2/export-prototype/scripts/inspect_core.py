"""Shared scene-inspection for the AnthroForge export prototype.

Collects the survival metrics we compare across formats:
bones (count/names), skin weights (vgroups, weighted verts, max influences),
shape keys, materials, actions. Defensive against Blender 5.x API changes.
"""
import bpy
import json


def action_fcurves(act):
    """Return list of fcurves for a slotted Blender 5.2 action."""
    fcs = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs.extend(cb.fcurves)
    return fcs


def inspect_scene():
    data = {"armatures": [], "meshes": [], "actions": [], "objects": []}

    for obj in bpy.data.objects:
        data["objects"].append({"name": obj.name, "type": obj.type})
        if obj.type == "ARMATURE":
            bones = [b.name for b in obj.data.bones]
            data["armatures"].append({
                "object": obj.name,
                "bone_count": len(bones),
                "bones": bones,
            })
        elif obj.type == "MESH":
            me = obj.data
            vg_names = [g.name for g in obj.vertex_groups]
            weighted = 0
            max_infl = 0
            for v in me.vertices:
                infl = sum(1 for g in v.groups if g.weight > 0.0)
                if infl:
                    weighted += 1
                if infl > max_infl:
                    max_infl = infl
            shape_keys = []
            if me.shape_keys:
                shape_keys = [kb.name for kb in me.shape_keys.key_blocks]
            mats = []
            for slot in obj.material_slots:
                mats.append(slot.material.name if slot.material else None)
            data["meshes"].append({
                "object": obj.name,
                "verts": len(me.vertices),
                "polys": len(me.polygons),
                "vgroup_count": len(vg_names),
                "vgroups": vg_names,
                "weighted_verts": weighted,
                "max_influences": max_infl,
                "shape_keys": shape_keys,
                "materials": mats,
                "parent": obj.parent.name if obj.parent else None,
                "dims": [round(d, 4) for d in obj.dimensions],
            })

    for act in bpy.data.actions:
        fcs = action_fcurves(act)
        fr = None
        try:
            fr = [float(act.frame_range[0]), float(act.frame_range[1])]
        except Exception:
            if fcs:
                pts = [p.co[0] for fc in fcs for p in fc.keyframe_points]
                if pts:
                    fr = [min(pts), max(pts)]
        data["actions"].append({
            "name": act.name,
            "fcurves": len(fcs),
            "frame_range": fr,
        })

    return data


def write_dump(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print("DUMPED", path)
