#!/usr/bin/env python3
"""Derive pattern pieces (connected colour components) + furplan.json."""
import json, numpy as np

W = "/home/hatch/workspace/anthroforge-v2/fur-craft/a18printfur/work/"
D = np.load(W + "plan_data.npz")
CM = 30.0  # 1 model unit = 30 cm at plan scale

PILE = {0: ("NO-FUR", 0), 1: ("MICRO", 6), 2: ("SHORT", 13), 3: ("MEDIUM", 25), 4: ("LONG", 50)}
FABRIC = {0: ("NOSE", "nose leather — no fur (vinyl/silicone)"),
          1: ("MAIN", "agouti grey-brown faux fur"),
          2: ("PALE", "cream faux fur"),
          3: ("DARK", "charcoal faux fur (ear backs)"),
          4: ("INNER", "dusty pink-grey minky/felt (inner ear)")}

def nbrs_of(tris, nv):
    nb = [set() for _ in range(nv)]
    for a, b, c in tris:
        nb[a] |= {b, c}; nb[b] |= {a, c}; nb[c] |= {a, b}
    return nb

def components(labels, tris, nv, want):
    nb = nbrs_of(tris, nv); seen = np.zeros(nv, bool); comps = []
    for s in range(nv):
        if seen[s] or labels[s] != want: continue
        stack = [s]; seen[s] = True; comp = []
        while stack:
            i = stack.pop(); comp.append(i)
            for j in nb[i]:
                if not seen[j] and labels[j] == want: seen[j] = True; stack.append(j)
        comps.append(comp)
    return comps

def face_areas(pos, tris):
    a = pos[tris[:, 0]]; b = pos[tris[:, 1]]; c = pos[tris[:, 2]]
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)

pieces = []
def add_piece(pid, name, obj, verts, colour, pos, tris, pile, flow, note=""):
    verts = np.array(sorted(verts))
    fa = face_areas(pos, tris)
    mask = np.isin(tris, verts).all(axis=1)
    area = float(fa[mask].sum() * CM * CM)
    pu, pc = np.unique(pile[verts], return_counts=True)
    nap = flow[verts].mean(axis=0); n = np.linalg.norm(nap)
    nap = (nap / n).round(3).tolist() if n > 1e-6 else [0, -1, 0]
    pieces.append({
        "id": pid, "name": name, "part": obj, "verts": int(len(verts)),
        "area_cm2": round(area, 1),
        "colour_code": int(colour), "fabric": FABRIC[colour][1],
        "pile_code": int(pu[np.argmax(pc)]), "pile_mm": PILE[int(pu[np.argmax(pc)])][1],
        "pile_range_mm": [PILE[int(pu.min())][1], PILE[int(pu.max())][1]],
        "nap_mean_xyz": nap, "note": note})

for obj in ("TissueHead", "Jaw", "Ear_L", "Ear_R", "NoseLeather"):
    pos, tris = D[f"{obj}_pos"], D[f"{obj}_tris"]
    pile, colour, flow = D[f"{obj}_pile"], D[f"{obj}_colour"], D[f"{obj}_flow"]
    nv = len(pos)
    for code in sorted(set(colour.tolist())):
        for comp in components(colour, tris, nv, code):
            if len(comp) < 6: continue  # speckle; noted in doc as blend edge
            # Symmetric head pieces are patterned as mirrored halves: split the
            # main head component at the midline (front wrap pieces stay whole).
            subs = [comp]
            if obj == "TissueHead" and code == 1:
                subs = [[i for i in comp if pos[i, 0] <= 0.005],
                        [i for i in comp if pos[i, 0] > -0.005]]
            for sub in subs:
                if len(sub) < 6: continue
                if obj.startswith("Ear_"): side = obj[-1]  # object name is authoritative
                elif len(subs) == 2: side = "L" if pos[sub][:, 0].mean() < 0 else "R"
                else: side = "C"
                reg = {"TissueHead": "head", "Jaw": "jaw", "Ear_L": "ear", "Ear_R": "ear",
                       "NoseLeather": "nose"}[obj]
                fab = "leather" if (obj == "NoseLeather") else FABRIC[code][0].lower()
                nm = f"{reg}-{fab}" + (f"-{side.lower()}" if side != "C" and obj != "Jaw" else "")
                add_piece(f"P{len(pieces)+1:02d}", nm, obj, sub, code, pos, tris, pile, flow)

plan = {
    "format": "anthroforge.furplan v1 (draft, A18)",
    "base": "neutral_base_head_v3 (AnthroForge library head)",
    "frame": "face +Y, up +Z, L (nose tip to occiput) = 1.0 model unit",
    "plan_scale": {"L_mm": 300, "note": "fursuit head scale; all mm/cm2 values at this scale"},
    "seam_allowance_mm": 10,
    "pile_table": {str(k): {"name": v[0], "mm": v[1]} for k, v in PILE.items()},
    "fabric_table": {str(k): v[1] for k, v in FABRIC.items()},
    "nap_convention": "arrows point in the direction the pile LIES (root->tip fall). "
                      "On the animal: away from the nose/face, back over the skull, down the "
                      "cheeks and jaw; up the ears from base to tip (OpenFur rule).",
    "pieces": pieces,
}
json.dump(plan, open(W + "furplan.json", "w"), indent=1)
for p in pieces:
    print(f"{p['id']} {p['name']:16s} {p['part']:11s} area={p['area_cm2']:7.1f}cm2 pile={p['pile_mm']}mm "
          f"({p['pile_range_mm']}) nap={p['nap_mean_xyz']}")
print("pieces:", len(pieces), " total fur area cm2:",
      round(sum(p['area_cm2'] for p in pieces if p['colour_code'] > 0), 1))
