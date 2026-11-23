import json, statistics
from collections import Counter, defaultdict
import numpy as np

D = json.load(open('/home/hatch/workspace/anthroforge-v2/model-craft/b1-topology/work/static_dump.json'))
bones = D['bones']
print("ALL BONES:", sorted(bones.keys()))

def region(bone):
    if bone is None: return 'NONE'
    b = bone.lower()
    if 'ear' in b: return 'EAR'
    if 'tail' in b: return 'TAIL'
    if 'head' in b or 'jaw' in b or 'eye' in b or 'teeth' in b or 'tongue' in b: return 'HEAD'
    if 'neck' in b: return 'NECK'
    if 'toe' in b or 'foot' in b: return 'FOOT'
    if 'femur' in b or 'shin' in b: return 'LEG'
    if 'hand' in b or 'finger' in b or 'thumb' in b: return 'HAND'
    if 'forearm' in b or 'arm' in b or 'shoulder' in b: return 'ARM'
    if 'spine' in b or 'pelvis' in b or 'root' in b or 'chest' in b: return 'TORSO'
    return 'OTHER:'+bone

bone_heads = {n: np.array(v['head']) for n,v in bones.items()}
bone_len = {n: max(v['len'], 1e-6) for n,v in bones.items()}

allverts = []  # dict per vert: pos, valence, mesh, region, inzone flags
region_stats = defaultdict(lambda: {'verts':0,'poles':0,'poles_zone':0,'severe':0,'edge_len':[]})
tot_val = Counter()
pole_list = []
for mname, m in D['meshes'].items():
    pos = np.array(m['positions']); edges = m['edge_list']; val = m['valence']
    elen = defaultdict(list)
    for a,b in edges:
        L = float(np.linalg.norm(pos[a]-pos[b]))
        elen[a].append(L); elen[b].append(L)
    for i,p in enumerate(pos):
        v = val[i]; tot_val[v]+=1
        reg = region(m['dominant_bone'][i])
        # zone A: near a joint pivot (bone head), radius 0.6 * that bone's length
        zoneA, nearest = False, None
        dmin = 1e18
        for n,h in bone_heads.items():
            d = float(np.linalg.norm(p-h))
            if d < dmin: dmin, nearest = d, n
            if d <= 0.6*bone_len[n]: zoneA = True
        zoneB = len([x for x in m['blend_bones'][i]]) >= 2
        zone = zoneA or zoneB
        pole = v!=6
        severe = v<=4 or v>=8
        rs = region_stats[reg]; rs['verts']+=1
        rs['edge_len'].append(statistics.mean(elen[i]))
        if pole:
            rs['poles']+=1
            if zone: rs['poles_zone']+=1
            if severe: rs['severe']+=1
            pole_list.append({'pos':p.tolist(),'valence':v,'mesh':mname,'region':reg,
                              'zoneA':zoneA,'zoneB':zoneB,'nearest_bone':nearest,'dist':dmin})
        allverts.append({'pos':p.tolist(),'valence':v,'mesh':mname,'region':reg,
                         'mel': statistics.mean(elen[i]), 'zone': zone})

tot = sum(tot_val.values())
print(f"\nTOTAL skinned verts: {tot}")
print("VALENCE HISTOGRAM (triangulated mesh: 6 = regular grid vertex):")
for v in sorted(tot_val): print(f"  valence {v}: {tot_val[v]} ({100*tot_val[v]/tot:.1f}%)")
poles = [p for p in pole_list]
pz = [p for p in poles if p['zoneA'] or p['zoneB']]
print(f"\nPOLES (valence != 6): {len(poles)} = {100*len(poles)/tot:.1f}% of verts")
print(f"  of those, inside a deformation zone (near pivot or in a >=0.25/0.25 blend band): {len(pz)} ({100*len(pz)/len(poles):.0f}% of poles)")
print(f"  severe (valence <=4 or >=8): {sum(1 for p in poles if p['valence']<=4 or p['valence']>=8)}")
print("\nREGION STATS:")
print(f"  {'region':8} {'verts':>6} {'%poles':>7} {'%polesInZone':>12} {'medianEdgeLen':>13}")
for r, s in sorted(region_stats.items(), key=lambda kv:-kv[1]['verts']):
    print(f"  {r:8} {s['verts']:6} {100*s['poles']/max(s['verts'],1):6.1f}% {100*s['poles_zone']/max(s['poles'],1):11.0f}% {statistics.median(s['edge_len']):13.4f}")
json.dump({'allverts':allverts,'poles':pole_list,'bones':{k:{'head':v['head'],'len':v['len']} for k,v in bones.items()}},
          open('/home/hatch/workspace/anthroforge-v2/model-craft/b1-topology/work/analysis.json','w'))
print("\nWORST pole-in-zone clusters (by nearest bone):")
c = Counter(p['nearest_bone'] for p in pz)
for b,n in c.most_common(12): print(f"  {b}: {n}")
