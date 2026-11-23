#!/usr/bin/env python3
"""B16 morph audit: orthogonality / interference measurements.

Sets audited:
  A. hm08 belly stack components (first-proof) - the shipped v5.2 stack
  B. hm08 bara-proof components + definition set + coupling combos
  C. BOOTH Lesser Mokuri shape keys (dumped from .blend via Blender)

Metrics per morph: support (#verts |d|>0.1mm), energy sum|d|^2, RMS, max.
Per pair: field cosine <A,B>/(|A||B|), support Jaccard, overlap coeff,
shared-vertex mean direction cosine, cross-energy ratio 2<A,B>/(EA+EB).
Fold test (hm08 only): flipped faces at +1 alone vs (+1,+1) combined.
Stack integrity: residual of combined targets vs sum of components.
All deltas in metres, canonical frame (x, z-up, y) as in the proofs.
"""
import json, zipfile
from pathlib import Path
import numpy as np

HOME = Path.home()
FP = HOME/"workspace/anthroforge-v2/first-proof"
BP = HOME/"workspace/anthroforge-v2/bara-proof"
NV = 19158  # hm08 total verts

# ---------- load hm08 base + faces ----------
z = zipfile.ZipFile(HOME/"workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
obj = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
V, F = [], []
for l in obj:
    if l.startswith("v "):
        p = l.split(); V.append([float(p[1]), float(p[3]), float(p[2])])
    elif l.startswith("f "):
        F.append([int(t.split("/")[0])-1 for t in l.split()[1:4]])
V = np.array(V) * 0.1            # dm -> m, canonical (x, z, y)
F = np.array(F)
BODY = np.zeros(len(V), bool); BODY[:13380] = True
Fb = F[np.array([BODY[f].all() for f in F])]
print(f"hm08: {len(V)} verts, {len(F)} faces, {len(Fb)} body faces")

def load_target(path):
    d = np.zeros((NV, 3))
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"): continue
        p = line.split()
        i = int(p[0]); a, b, c = float(p[1]), float(p[2]), float(p[3])
        d[i] = [a, c, b]         # file stores (x, z, y) dm -> canonical m
    return d * 0.1

def stats(d):
    mag = np.linalg.norm(d, axis=1)
    sup = mag > 1e-4
    return {"support": int(sup.sum()),
            "energy": float((d*d).sum()),
            "rms_mm": float(np.sqrt((mag[sup]**2).mean())*1000) if sup.any() else 0.0,
            "max_mm": float(mag.max()*1000)}

def pair(a, b):
    A, B = a.ravel(), b.ravel()
    ea, eb = (A*A).sum(), (B*B).sum()
    dot = float(A @ B)
    ma = np.linalg.norm(a, axis=1) > 1e-4
    mb = np.linalg.norm(b, axis=1) > 1e-4
    inter = ma & mb
    out = {"cos": dot/np.sqrt(ea*eb) if ea and eb else 0.0,
           "jaccard": float(inter.sum()/max((ma|mb).sum(),1)),
           "overlap": float(inter.sum()/max(min(ma.sum(), mb.sum()),1)),
           "cross_ratio": 2*dot/(ea+eb) if ea+eb else 0.0,
           "shared": int(inter.sum()), "shared_cos": None}
    if inter.sum() > 5:
        va, vb = a[inter], b[inter]
        cs = (va*vb).sum(1)/np.maximum(np.linalg.norm(va,axis=1)*np.linalg.norm(vb,axis=1), 1e-12)
        out["shared_cos"] = float(cs.mean())
    return out

def face_normals(P):
    n = np.cross(P[Fb[:,1]]-P[Fb[:,0]], P[Fb[:,2]]-P[Fb[:,0]])
    return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True), 1e-14)
N0 = face_normals(V)
def flips(delta):
    nn = face_normals(V+delta)
    return int((np.einsum("ij,ij->i", N0, nn) < 0).sum())

def audit_set(name, morphs, fold_pairs=True):
    print(f"\n=== {name} ===")
    st = {k: stats(d) for k, d in morphs.items()}
    for k, s in st.items():
        print(f"  {k:34s} sup {s['support']:6d}  rms {s['rms_mm']:6.2f}mm  max {s['max_mm']:6.1f}mm")
    keys = list(morphs)
    pairs = {}
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            p = pair(morphs[keys[i]], morphs[keys[j]])
            if abs(p["cos"]) > 0.01 or p["overlap"] > 0.05:
                pairs[f"{keys[i]} x {keys[j]}"] = p
                print(f"  PAIR {keys[i]} x {keys[j]}: cos {p['cos']:+.3f} jacc {p['jaccard']:.2f} "
                      f"ovl {p['overlap']:.2f} sharedcos {p['shared_cos']} cross {p['cross_ratio']:+.3f}")
    res = {"stats": st, "pairs": pairs}
    if fold_pairs:
        fl = {}
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                fa, fb = flips(morphs[keys[i]]), flips(morphs[keys[j]])
                fc = flips(morphs[keys[i]]+morphs[keys[j]])
                if fc > fa+fb:
                    fl[f"{keys[i]} x {keys[j]}"] = {"a": fa, "b": fb, "combined": fc}
                    print(f"  FOLD {keys[i]} x {keys[j]}: {fa}+{fb} alone -> {fc} combined")
        res["fold_interference"] = fl
    return res

report = {}

belly = {
 "protrusion(v1)": load_target(FP/"body.belly.protrusion.target"),
 "sag_v3": load_target(FP/"body.belly.protrusion_sag_v3.target"),
 "distribution_v4": load_target(FP/"body.belly.protrusion_distribution_v4.target"),
 "limb_v5": load_target(FP/"body.belly.protrusion_limb_v5.target"),
 "terminal_v51": load_target(FP/"body.belly.protrusion_terminal_v51.target"),
 "contact_v52": load_target(FP/"body.belly.protrusion_contact_v52.target"),
}
report["belly_stack"] = audit_set("hm08 belly stack (shipped components)", belly)

bara = {
 "muscle": load_target(BP/"body.muscle.target"),
 "chest.width": load_target(BP/"body.chest.width.target"),
 "tissue.strongman": load_target(BP/"body.tissue.strongman.target"),
 "neck.mass": load_target(BP/"body.neck.mass.target"),
 "forearm.mass": load_target(BP/"body.forearm.mass.target"),
 "def.flat_abs": load_target(BP/"body.definition.flat_abs.target"),
 "def.pecs_crease": load_target(BP/"body.definition.pecs_crease.target"),
 "def.traps_valleys": load_target(BP/"body.definition.traps_valleys.target"),
 "def.back": load_target(BP/"body.definition.back.target"),
}
report["bara"] = audit_set("hm08 bara components + definition", bara)

# ---- stack integrity: combined target vs sum of components ----
def resid(combined_path, parts):
    c = load_target(combined_path)
    s = sum(parts)
    r = np.linalg.norm(c-s, axis=1)
    return {"max_mm": float(r.max()*1000), "rms_mm": float(np.sqrt((r**2).mean())*1000)}
integ = {
 "v5 == v4 + limb": resid(FP/"body.belly.protrusion_v5.target",
    [load_target(FP/"body.belly.protrusion_v4.target"), belly["limb_v5"]]),
 "v5.1 == v5 + terminal": resid(FP/"body.belly.protrusion_v5.1.target",
    [load_target(FP/"body.belly.protrusion_v5.target"), belly["terminal_v51"]]),
 "strongman == muscle+chest+tissue": resid(BP/"body.bara.strongman.target",
    [bara["muscle"], bara["chest.width"], bara["tissue.strongman"]]),
}
print("\n=== stack integrity (max residual, mm) ===")
for k, v in integ.items(): print(f"  {k}: {v}")
report["integrity"] = integ

# coupling combos vs their parents (combo-morph audit)
for combo, path in [("pear", BP/"body.coupling.pear.target"),
                    ("bigchest", BP/"body.coupling.bigchest.target"),
                    ("gachidebu", BP/"body.coupling.gachidebu.target")]:
    c = load_target(path)
    print(f"\ncombo {combo}: support {stats(c)['support']}, max {stats(c)['max_mm']:.1f}mm")
    for k in ("muscle", "tissue.strongman", "chest.width"):
        print(f"   cos vs {k}: {pair(c, bara[k])['cos']:+.3f}")
    report.setdefault("combos", {})[combo] = {k: pair(c, bara[k])["cos"] for k in ("muscle","tissue.strongman","chest.width")}

# ---------- Mokuri ----------
mk = np.load("/tmp/b16/mokuri_keys.npz")
mok = {k.split("::")[1]: mk[k].astype(np.float64) for k in mk.files}
report["mokuri"] = audit_set("BOOTH Lesser Mokuri shape keys (Body, 3792 v)", mok, fold_pairs=False)

json.dump(report, open(HOME/"workspace/anthroforge-v2/model-craft/b16-morphs/audit_results.json","w"), indent=1)
print("\nwrote audit_results.json")
