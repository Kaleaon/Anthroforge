#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 1: base audit (spec S8 stage 1).

Opens base-head-v5's .blend and records: objects, vertex groups,
hinge, pal_z, landmarks, vertical-family reads in the build frame,
teeth island analysis (felid canine check), tongue proportions vs
S5.3, lid rest coverage estimate. Then opens the r3 rig blend and
records the armature's JawRoot pivot + head-zone objects for the
assembly/context render.

    blender -b --threads 2 --python stage1_audit.py
Writes work/audit.json + work/rig_audit.json beside the character dir.
"""
import json
from pathlib import Path

import bpy
import numpy as np

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
V5 = "/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend"
RIG = "/home/hatch/workspace/bodies-3d/kaleaon-rigged3/kaleaon_rigged3.blend"


def world_co(o):
    M = np.array(o.matrix_world)
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co @ M[:3, :3].T + M[:3, 3], M


def islands(o):
    """Connected components of a mesh by edge adjacency."""
    n = len(o.data.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in o.data.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


# ------------------------------------------------------------ v5 base
bpy.ops.wm.open_mainfile(filepath=V5)
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
audit = {"objects": {}}
for name, o in sorted(objs.items()):
    W, _ = world_co(o)
    audit["objects"][name] = {
        "verts": len(o.data.vertices), "faces": len(o.data.polygons),
        "bbox_min": np.round(W.min(axis=0), 4).tolist(),
        "bbox_max": np.round(W.max(axis=0), 4).tolist(),
        "origin": np.round(np.array(o.matrix_world)[:3, 3], 4).tolist(),
        "groups": {g.name: sum(1 for v in o.data.vertices
                               if any(gr.group == g.index
                                      for gr in v.groups))
                   for g in o.vertex_groups},
    }

tis = objs["TissueHead"]
TW, _ = world_co(tis)
L = float(TW[:, 1].max() - TW[:, 1].min())
nose_y = float(TW[:, 1].max())
occ_y = float(TW[:, 1].min())
eye_c = {}
for s in ("L", "R"):
    W0, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W0.mean(axis=0)
eye_mid = 0.5 * (eye_c["L"] + eye_c["R"])
eye_y, eye_z = float(eye_mid[1]), float(eye_mid[2])
TU, _ = world_co(objs["TeethUpper"])
ant = TU[TU[:, 1] > eye_y + 0.10 * L]
pal_z = float(ant[:, 2].max())
hinge = np.array(objs["Jaw"].matrix_world)[:3, 3]
top_z = float(TW[:, 2].max())

audit["landmarks"] = {
    "L": L, "nose_y": nose_y, "occiput_y": occ_y,
    "eye_centre_mid": np.round(eye_mid, 4).tolist(),
    "eye_L": np.round(eye_c["L"], 4).tolist(),
    "eye_R": np.round(eye_c["R"], 4).tolist(),
    "pal_z": pal_z, "hinge": np.round(hinge, 4).tolist(),
    "hinge_in_L_units": np.round(hinge / L, 4).tolist(),
    "tissue_top_z": top_z,
    "head_height_palate_to_crown_L": (top_z - pal_z) / L,
    "orbit_height_L": (eye_z - pal_z) / L,
    "orbit_station_u": (nose_y - eye_y) / L,
}
# OrbitRise: dorsal midline z at the orbit station minus orbit height
band = TW[np.abs(TW[:, 1] - eye_y) < 0.03 * L]
audit["landmarks"]["orbit_rise_L"] = float(band[:, 2].max() - eye_z) / L
audit["landmarks"]["braincase_rise_L"] = float(top_z - eye_z) / L

# ears: base (nearest quartile to tissue) + tip, per builder convention
ear_info = {}
for s in ("L", "R"):
    E, _ = world_co(objs[f"Ear_{s}"])
    d = np.sqrt(((E[:, None, :] - TW[None, :, :]) ** 2).sum(-1)).min(axis=1)
    base = E[d < np.percentile(d, 25)].mean(axis=0)
    tip = E[np.argmax(np.linalg.norm(E - base, axis=1))]
    ear_info[s] = {
        "base": np.round(base, 4).tolist(), "tip": np.round(tip, 4).tolist(),
        "length_L": float(np.linalg.norm(tip - base)) / L,
        "tip_height_above_palate_L": float(tip[2] - pal_z) / L,
        "base_height_above_palate_L": float(base[2] - pal_z) / L,
    }
audit["ears"] = ear_info

# teeth islands - felid plan check (canines vs cheek teeth)
teeth_info = {}
for name in ("TeethUpper", "TeethLower"):
    o = objs[name]
    W, _ = world_co(o)
    isl = islands(o)
    recs = []
    for idxs in isl:
        P = W[idxs]
        recs.append({
            "verts": len(idxs),
            "centroid": np.round(P.mean(axis=0), 4).tolist(),
            "height": float(P[:, 2].max() - P[:, 2].min()),
            "width": float(np.ptp(P[:, 0])),
            "y_mid": float(P[:, 1].mean()),
        })
    recs.sort(key=lambda r: -r["y_mid"])   # anterior first
    teeth_info[name] = {
        "islands": len(recs), "arcade_width_L": float(np.ptp(W[:, 0])) / L,
        "arcade_length_L": float(np.ptp(W[:, 1])) / L,
        "teeth": recs,
    }
    if recs:
        hs = sorted(r["height"] for r in recs)
        teeth_info[name]["height_median"] = float(np.median(hs))
        teeth_info[name]["height_max"] = float(hs[-1])
audit["teeth"] = teeth_info

# tongue proportions vs S5.3 (arcade width W: tongue 0.56 W wide, 0.98 W long)
TG, _ = world_co(objs["Tongue"])
audit["tongue"] = {
    "width_over_arcadeW": float(np.ptp(TG[:, 0]) / np.ptp(TU[:, 0])),
    "length_over_arcadeW": float(np.ptp(TG[:, 1]) / np.ptp(TU[:, 0])),
    "width_L": float(np.ptp(TG[:, 0])) / L,
    "length_L": float(np.ptp(TG[:, 1])) / L,
    "verts": len(objs["Tongue"].data.vertices),
}

# lid rest coverage estimate (iris fraction under the upper lid margin)
cov = {}
for s in ("L", "R"):
    IR, _ = world_co(objs[f"Iris_{s}"])
    LD, _ = world_co(objs[f"Eyelid_{s}"])
    cx = IR[:, 0].mean()
    near = LD[np.abs(LD[:, 0] - cx) < 0.30 * np.ptp(IR[:, 0])]
    near = near[near[:, 1] > IR[:, 1].mean()]
    margin_z = float(near[:, 2].min()) if len(near) else None
    top, bot = float(IR[:, 2].max()), float(IR[:, 2].min())
    cov[s] = {
        "iris_top": top, "iris_bottom": bot, "lid_margin_z": margin_z,
        "coverage_frac": (float((top - margin_z) / (top - bot))
                          if margin_z is not None else None),
    }
audit["lid_coverage_est"] = cov

(CHAR / "work" / "audit.json").write_text(json.dumps(audit, indent=1))
print("AUDIT v5 objects:", sorted(objs))
print("landmarks:", json.dumps(audit["landmarks"], indent=1))
print("ears:", json.dumps(ear_info, indent=1))
print("teeth islands U/L:", teeth_info["TeethUpper"]["islands"],
      teeth_info["TeethLower"]["islands"])
print("tongue:", json.dumps(audit["tongue"], indent=1))
print("lid coverage:", json.dumps(cov, indent=1))

# ------------------------------------------------------------ r3 rig
bpy.ops.wm.open_mainfile(filepath=RIG)
rig = {"objects": {}, "bones": {}}
arm = None
for o in bpy.data.objects:
    if o.type == "ARMATURE":
        arm = o
        for b in o.data.bones:
            rig["bones"][b.name] = {
                "head": np.round(np.array(b.head_local), 4).tolist(),
                "tail": np.round(np.array(b.tail_local), 4).tolist(),
                "parent": b.parent.name if b.parent else None,
            }
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    W, _ = world_co(o)
    rig["objects"][o.name] = {
        "verts": len(o.data.vertices),
        "bbox_min": np.round(W.min(axis=0), 3).tolist(),
        "bbox_max": np.round(W.max(axis=0), 3).tolist(),
        "centre": np.round(W.mean(axis=0), 3).tolist(),
        "parent": o.parent.name if o.parent else None,
    }
(CHAR / "work" / "rig_audit.json").write_text(json.dumps(rig, indent=1))
print("RIG bones:", len(rig["bones"]))
print("JawRoot:", rig["bones"].get("CC_Base_JawRoot"))
print("RIG objects:", sorted(rig["objects"]))
print("STAGE 1 AUDIT DONE")
