#!/usr/bin/env python3
"""B16 hyper extension: how the morph sets behave at 2-4x authored values.
Fold counts on a scale grid, thigh midline crossing for the belly stack,
and definition-relief visibility under scaled tissue.
Field cosine is scale-invariant for linear morphs (cross-terms grow at the
same rate as self-terms), so hyper interference is measured where it is
actually nonlinear: fold onset, interpenetration, relief submersion."""
import zipfile, json
from pathlib import Path
import numpy as np

HOME = Path.home()
FP = HOME/"workspace/anthroforge-v2/first-proof"
BP = HOME/"workspace/anthroforge-v2/bara-proof"
z = zipfile.ZipFile(HOME/"workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
obj = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
V, F = [], []
for l in obj:
    if l.startswith("v "):
        p = l.split(); V.append([float(p[1]), float(p[3]), float(p[2])])
    elif l.startswith("f "):
        F.append([int(t.split("/")[0])-1 for t in l.split()[1:4]])
V = np.array(V)*0.1; F = np.array(F)
BODY = np.zeros(len(V), bool); BODY[:13380] = True
Fb = F[np.array([BODY[f].all() for f in F])]
def load_target(path):
    d = np.zeros((19158,3))
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"): continue
        p = line.split(); d[int(p[0])] = [float(p[1]), float(p[3]), float(p[2])]
    return d*0.1
def nrm(P):
    n = np.cross(P[Fb[:,1]]-P[Fb[:,0]], P[Fb[:,2]]-P[Fb[:,0]])
    return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-14)
N0 = nrm(V)
def flips(d): return int((np.einsum("ij,ij->i", N0, nrm(V+d))<0).sum())

SCALES = [1.0, 1.5, 2.0, 3.0, 4.0]
fields = {
 "protrusion": load_target(FP/"body.belly.protrusion.target"),
 "belly stack v5.1": load_target(FP/"body.belly.protrusion_v5.1.target"),
 "belly stack + contact": load_target(FP/"body.belly.protrusion_v5.1.target") + load_target(FP/"body.belly.protrusion_contact_v52.target"),
 "muscle": load_target(BP/"body.muscle.target"),
 "tissue.strongman": load_target(BP/"body.tissue.strongman.target"),
 "strongman combo": load_target(BP/"body.bara.strongman.target"),
 "combo pear": load_target(BP/"body.coupling.pear.target"),
 "combo bigchest": load_target(BP/"body.coupling.bigchest.target"),
 "combo gachidebu": load_target(BP/"body.coupling.gachidebu.target"),
 "belly + strongman (all)": load_target(FP/"body.belly.protrusion_v5.1.target") + load_target(BP/"body.bara.strongman.target"),
}
print("=== fold counts by scale (of %d body faces) ===" % len(Fb))
res = {}
for name, d in fields.items():
    row = {s: flips(d*s) for s in SCALES}
    res[name] = row
    onset = next((s for s in SCALES if row[s] > 0), None)
    print(f"  {name:26s} " + "  ".join(f"{s}x:{row[s]}" for s in SCALES) + f"   onset: {onset}")

# thigh midline crossing under the belly stack: verts originally on +x side
# of the thigh band that end up at x<0 (and mirror) = interpenetration count
stack = fields["belly stack + contact"]
thigh = BODY & (V[:,2] > V[:13380,2].min()) & (np.abs(V[:,0]) > 0.02)
# restrict to leg band: below crotch approx by z < 40th pct of body z, |x|<0.16
zleg = V[:,2] < np.percentile(V[BODY,2], 42)
band = thigh & zleg & (np.abs(V[:,0]) < 0.16)
print("\n=== thigh midline crossing (belly stack + contact) ===")
cross_res = {}
for s in SCALES:
    P = V + stack*s
    crossed = int(((V[band,0] > 0) & (P[band,0] < 0)).sum() + ((V[band,0] < 0) & (P[band,0] > 0)).sum())
    cross_res[s] = crossed
    print(f"  {s}x: {crossed} verts across midline")

# definition visibility: flat_abs relief amplitude vs tissue displacement
# at the abs verts, as tissue scales (relief fixed, mass grows)
absd = load_target(BP/"body.definition.flat_abs.target")
tis = fields["tissue.strongman"]
sup = np.linalg.norm(absd, axis=1) > 1e-4
relief_rms = float(np.sqrt((np.linalg.norm(absd[sup],axis=1)**2).mean())*1000)
print(f"\n=== definition visibility: flat_abs relief RMS {relief_rms:.2f} mm (fixed) ===")
vis_res = {}
for s in [0.0, 0.6, 1.0, 2.0, 3.0, 4.0]:
    disp = float(np.sqrt((np.linalg.norm(tis[sup],axis=1)**2).mean())*1000) * s if s else 0.0
    ratio = relief_rms/disp if disp else float("inf")
    vis_res[s] = {"tissue_rms_at_abs_mm": round(disp,1), "relief_to_mass": round(ratio,3) if disp else None}
    print(f"  tissue {s}x: local tissue RMS {disp:6.1f} mm, relief/mass ratio {ratio if disp else float('inf'):.3f}")

json.dump({"folds": {k: {str(s): v for s, v in r.items()} for k, r in res.items()},
           "midline_crossing": {str(s): v for s, v in cross_res.items()},
           "definition_visibility": {str(s): v for s, v in vis_res.items()}},
          open(HOME/"workspace/anthroforge-v2/model-craft/b16-morphs/audit_hyper_results.json","w"), indent=1)
print("\nwrote audit_hyper_results.json")
