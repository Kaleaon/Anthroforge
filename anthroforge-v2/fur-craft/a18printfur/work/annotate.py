#!/usr/bin/env python3
"""Annotate raw renders (titles/legends/arrows), build pattern sheet + stencils."""
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont

W = "/home/hatch/workspace/anthroforge-v2/fur-craft/a18printfur/work/"
OUT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a18printfur/"
D = np.load(W + "plan_data.npz")
HG = np.load(W + "head_geom.npz", allow_pickle=True)
PLAN = json.load(open(W + "furplan.json"))

def font(sz, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    try: return ImageFont.truetype(p, sz)
    except Exception: return ImageFont.load_default()

PILE_RGB = {0: (41, 41, 41), 1: (77, 173, 242), 2: (51, 191, 102), 3: (250, 199, 38), 4: (235, 77, 51)}
COL_RGB = {0: (33, 28, 26), 1: (148, 115, 77), 2: (245, 230, 194), 3: (64, 56, 51), 4: (224, 158, 148)}
PILE_LEG = [(1, "MICRO 6 mm"), (2, "SHORT 13 mm"), (3, "MEDIUM 25 mm"), (4, "LONG 50 mm"), (0, "NO FUR")]
COL_LEG = [(1, "MAIN agouti"), (2, "PALE cream"), (3, "DARK charcoal"), (4, "INNER minky"), (0, "NOSE leather")]

def finish(mode, view, kind):
    img = Image.open(W + f"raw_{mode}_{view}.png").convert("RGB")
    Wd, H = img.size
    bar = 118 if kind != "direction" else 96
    canvas = Image.new("RGB", (Wd, H + bar), "white")
    canvas.paste(img, (0, bar))
    dr = ImageDraw.Draw(canvas)
    titles = {"pile": "PILE ZONES — shave / fabric map", "colour": "COLOUR ZONES — fabric pieces",
              "direction": "NAP DIRECTION — how the pile lies"}
    dr.text((18, 12), f"FUR PLAN · neutral head v3 · {titles[kind]}", fill=(20, 20, 20), font=font(23, True))
    dr.text((18, 46), view.upper() + " VIEW · plan scale L = 300 mm", fill=(90, 90, 90), font=font(19))
    if kind == "direction":
        arrows = json.load(open(W + "arrows.json"))[view]
        for x0, y0, x1, y1, pc in arrows:
            y0 += bar; y1 += bar
            dr.line([x0, y0, x1, y1], fill=(255, 255, 255), width=5)
            dr.line([x0, y0, x1, y1], fill=(18, 53, 91), width=3)
            ang = np.arctan2(y1 - y0, x1 - x0)
            for s in (2.6, -2.6):
                hx = x1 - 11 * np.cos(ang + s * 0.42); hy = y1 - 11 * np.sin(ang + s * 0.42)
                dr.line([x1, y1, hx, hy], fill=(18, 53, 91), width=3)
        dr.text((18, bar - 30), "Flow: away from nose/face, back over skull, down cheeks & jaw; up the ears.",
                fill=(90, 90, 90), font=font(17))
    else:
        leg = PILE_LEG if kind == "pile" else COL_LEG
        table = PILE_RGB if kind == "pile" else COL_RGB
        x = 18
        for code, label in leg:
            dr.rectangle([x, bar - 40, x + 26, bar - 14], fill=table[code], outline=(60, 60, 60))
            dr.text((x + 33, bar - 38), label, fill=(30, 30, 30), font=font(18))
            x += 33 + int(dr.textlength(label, font=font(18))) + 26
    name = {"pile": "furplan_pile", "colour": "furplan_colour", "direction": "furplan_direction"}[kind]
    canvas.save(OUT + f"{name}_{view}.png")
    print("wrote", name + "_" + view)

for v in ("front", "side", "back"):
    finish("pile", v, "pile"); finish("colour", v, "colour")
for v in ("front", "side", "back", "top"):
    finish("neutral", v, "direction")

# ---------- UV / flatten helpers ----------
def fan_tris(faces):
    tris = []
    for f in faces:
        for k in range(1, len(f) - 1): tris.append([f[0], f[k], f[k + 1]])
    return np.array(tris)

def face_labels(obj):
    tris = D[f"{obj}_tris"]; col = D[f"{obj}_colour"]
    return np.array([np.bincount(col[t], minlength=5).argmax() for t in tris])

def uv_tris():
    faces = [list(f) for f in HG["TissueHead_faces"]]
    uvf = HG["TissueHead_uv_face"]
    tris, uvt = [], []
    for fi, f in enumerate(faces):
        for k in range(1, len(f) - 1):
            tris.append([f[0], f[k], f[k + 1]])
            uvt.append([uvf[fi][0], uvf[fi][k], uvf[fi][k + 1]])
    return np.array(tris), np.array(uvt)

def uv_nap(obj_tris, uvt, flow, labels, want, n=14):
    """Mean UV-space nap direction for faces with label == want."""
    dirs = []
    pos = D["TissueHead_pos"]
    cand = np.where(labels == want)[0]
    if len(cand) == 0: return None
    for fi in cand[np.linspace(0, len(cand) - 1, min(n, len(cand))).astype(int)]:
        t = obj_tris[fi]; p = pos[t]; uv = uvt[fi]
        E = np.stack([p[1] - p[0], p[2] - p[0]], axis=1)       # 3x2
        T = np.stack([uv[1] - uv[0], uv[2] - uv[0]], axis=1)   # 2x2
        f = flow[t].mean(axis=0)
        a, *_ = np.linalg.lstsq(E, f, rcond=None)
        d = T @ a
        if np.linalg.norm(d) > 1e-9: dirs.append(d / np.linalg.norm(d))
    if not dirs: return None
    m = np.mean(dirs, axis=0); return m / (np.linalg.norm(m) + 1e-12)

# ---------- pattern sheet ----------
S = Image.new("RGB", (1740, 1290), "white")
dr = ImageDraw.Draw(S)
dr.text((24, 14), "FUR PLAN — PATTERN PIECES (cut layout)", fill=(20, 20, 20), font=font(30, True))
dr.text((24, 54), "Head pieces in base UV space · ears auto-flattened (PCA) · jaw in side profile. "
                  "Add 10 mm seam allowance. Arrows = nap.", fill=(90, 90, 90), font=font(19))

def draw_panel(box, title):
    x0, y0, x1, y1 = box
    dr.rectangle(box, outline=(150, 150, 150), width=2)
    dr.text((x0 + 10, y0 + 8), title, fill=(30, 30, 30), font=font(20, True))
    return box

def plot_tris(box, pts2d, tris, labels, lo, hi, label_pts):
    x0, y0, x1, y1 = box; pad = 46
    def map2(px, py):
        return (x0 + pad + (px - lo[0]) / (hi[0] - lo[0]) * (x1 - x0 - 2 * pad),
                y1 - pad - (py - lo[1]) / (hi[1] - lo[1]) * (y1 - y0 - 2 * pad - 18))
    for t, lb in zip(tris, labels):
        poly = [map2(pts2d[i, 0], pts2d[i, 1]) for i in t]
        dr.polygon(poly, fill=COL_RGB[int(lb)])
    for (px, py), txt in label_pts:
        cx, cy = map2(px, py)
        dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(18, 53, 91))
        dr.text((cx + 8, cy - 10), txt, fill=(18, 53, 91), font=font(19, True))
    return map2

# head panel
tris, uvt = uv_tris(); labels = face_labels("TissueHead")
pos = D["TissueHead_pos"]; colv = D["TissueHead_colour"]; flow = D["TissueHead_flow"]
box = draw_panel((24, 96, 880, 700), "HEAD — UV space (P01/P02 main halves, P03 pale)")
uv_all = uvt.reshape(-1, 2)
lo, hi = uv_all.min(axis=0), uv_all.max(axis=0)
maph = plot_tris(box, np.zeros((1, 2)), [], [], lo, hi, [])  # placeholder for mapper
def maph(px, py):
    x0, y0, x1, y1 = box; pad = 46
    return (x0 + pad + (px - lo[0]) / (hi[0] - lo[0]) * (x1 - x0 - 2 * pad),
            y1 - pad - (py - lo[1]) / (hi[1] - lo[1]) * (y1 - y0 - 2 * pad - 18))
for t, uv, lb in zip(tris, uvt, labels):
    dr.polygon([maph(u[0], u[1]) for u in uv], fill=COL_RGB[int(lb)])
for code, pid in ((1, "P01/P02"), (2, "P03")):
    m = colv == code
    cu = np.array([HG["TissueHead_uv_vert"][i] for i in np.where(m)[0]])
    c = cu.mean(axis=0); cx, cy = maph(c[0], c[1])
    dr.text((cx - 20, cy - 10), pid, fill=(18, 53, 91), font=font(21, True))
    d = uv_nap(tris, uvt, flow, labels, code)
    if d is not None:
        ex, ey = cx + d[0] * 52, cy - d[1] * 52
        dr.line([cx, cy, ex, ey], fill=(18, 53, 91), width=4)
        ang = np.arctan2(ey - cy, ex - cx)
        for s in (2.6, -2.6):
            dr.line([ex, ey, ex - 13 * np.cos(ang + s * 0.42), ey - 13 * np.sin(ang + s * 0.42)],
                    fill=(18, 53, 91), width=4)

# ears panel (PCA flatten)
box = draw_panel((904, 96, 1716, 700), "EARS — flattened (P05–P08)")
ox = 930
for side in ("Ear_L", "Ear_R"):
    p = D[f"{side}_pos"]; t = D[f"{side}_tris"]; lb = face_labels(side)
    cen = p.mean(axis=0); X = p - cen
    _, _, Vt = np.linalg.svd(X, full_matrices=False)
    p2 = X @ Vt[:2].T
    lo2, hi2 = p2.min(axis=0), p2.max(axis=0)
    sc = min(360 / (hi2[0] - lo2[0]), 500 / (hi2[1] - lo2[1]))
    for tri, l in zip(t, lb):
        poly = [(ox + (p2[i, 0] - lo2[0]) * sc, 660 - (p2[i, 1] - lo2[1]) * sc) for i in tri]
        dr.polygon(poly, fill=COL_RGB[int(l)])
    dr.text((ox + 6, 668), side.replace("_", " "), fill=(30, 30, 30), font=font(18, True))
    dr.line([ox + 60, 620, ox + 60, 540], fill=(18, 53, 91), width=4)
    dr.polygon([(ox + 60, 528), (ox + 50, 552), (ox + 70, 552)], fill=(18, 53, 91))
    ox += 400

# jaw panel (side profile Y-Z)
box = draw_panel((24, 724, 880, 1050), "JAW — side profile (P04, one piece, worn part)")
p = D["Jaw_pos"]; t = D["Jaw_tris"]; lb = face_labels("Jaw")
lo2 = np.array([p[:, 1].min(), p[:, 2].min()]); hi2 = np.array([p[:, 1].max(), p[:, 2].max()])
for tri, l in zip(t, lb):
    poly = [(24 + 46 + (p[i, 1] - lo2[0]) / (hi2[0] - lo2[0]) * (880 - 24 - 92),
             1050 - 40 - (p[i, 2] - lo2[1]) / (hi2[1] - lo2[1]) * (1050 - 724 - 90)) for i in tri]
    dr.polygon(poly, fill=COL_RGB[int(l)])
dr.text((70, 760), "P04 nap: back + down", fill=(18, 53, 91), font=font(19, True))

# piece table
box = draw_panel((904, 724, 1716, 1050), "PIECE LIST")
y = 724 + 44
for p in PLAN["pieces"]:
    dr.text((922, y), f"{p['id']}  {p['name']:<14s} {p['fabric'].split('(')[0][:26]:<26s} "
                      f"pile {p['pile_mm']:>2} mm  {p['area_cm2']:>6.0f} cm²", fill=(30, 30, 30), font=font(19))
    y += 30
dr.text((24, 1070), "Notes: head-main is cut as two mirrored halves (centre seam at midline). Pile gradients inside a piece are "
                    "SHAVED, not sewn — see PRINT_FUR.md §3.", fill=(60, 60, 60), font=font(19))
dr.text((24, 1100), "Ears/jaw have no production UV on this base: their panels are drafting previews — production pattern via "
                    "DTD or paper-model flatten (PRINT_FUR.md §5).", fill=(60, 60, 60), font=font(19))
dr.text((24, 1130), "Stencil masks (UV space) ship alongside: stencil_main.png, stencil_pale.png, stencil_ear_dark.png.",
        fill=(60, 60, 60), font=font(19))
S.save(OUT + "furplan_pieces.png"); print("wrote furplan_pieces")

# ---------- stencils (MARKINGS §7 style, extended to fur pieces) ----------
def stencil(tris2d, labels, want, path, res=1024):
    img = Image.new("L", (res, res), 255)
    d2 = ImageDraw.Draw(img)
    for uv, lb in zip(tris2d, labels):
        if int(lb) == want:
            d2.polygon([(u[0] * res, (1 - u[1]) * res) for u in uv], fill=0)
    img.save(OUT + path); print("wrote", path)
stencil(uvt, labels, 1, "stencil_main.png")
stencil(uvt, labels, 2, "stencil_pale.png")
# ear dark stencil in PCA space of Ear_L
p = D["Ear_L_pos"]; t = D["Ear_L_tris"]; lb = face_labels("Ear_L")
cen = p.mean(axis=0); X = p - cen
_, _, Vt = np.linalg.svd(X, full_matrices=False)
p2 = X @ Vt[:2].T
lo2, hi2 = p2.min(axis=0), p2.max(axis=0)
p2n = (p2 - lo2) / (hi2 - lo2)
img = Image.new("L", (1024, 1024), 255); d2 = ImageDraw.Draw(img)
for tri, l in zip(t, lb):
    if int(l) == 3:
        d2.polygon([(p2n[i, 0] * 1024, (1 - p2n[i, 1]) * 1024) for i in tri], fill=0)
img.save(OUT + "stencil_ear_dark.png"); print("wrote stencil_ear_dark")
