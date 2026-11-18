"""Dependency-free structural checks for species-mesh profile data and Blender scripts."""
from __future__ import annotations
import ast, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILE_FILE=ROOT/"species_profiles.v1.json"
ALLOWED_FAMILIES={"canid","feline","equine","draconic","avian","serpentine"}
PLANS={"plan.biped","plan.quadruped_feral","plan.quadruped_taur","plan.naga"}
REQUIRED={"head":{"length","width","height","muzzle_length","ear"},
          "torso":{"shoulder_width","waist_width","hip_width","chest_depth","pelvis_depth"},
          "limbs":{"arm_girth","thigh_girth","shin_girth","digitigrade","paw_scale"},
          "tail":{"enabled","length","girth","curve"}}

def validate():
 data=json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
 assert data["schema"]=="anthroforge.species-mesh-profiles"
 assert data["version"]==1 and data["units"]=="metres"
 ids=set(); families=set()
 for p in data["profiles"]:
  assert p["id"] not in ids, "duplicate profile id: "+p["id"]
  ids.add(p["id"]);families.add(p["family"])
  assert p["family"] in ALLOWED_FAMILIES
  assert p["body_plan"] in PLANS
  assert set(p["supported_plans"]) <= PLANS
  assert p["body_plan"] in p["supported_plans"]
  if p["family"] == "serpentine":
   assert "plan.naga" in p["supported_plans"]
  else:
   assert "plan.naga" not in p["supported_plans"]
  for group,keys in REQUIRED.items():
   assert keys <= set(p[group]), f'{p["id"]}: missing {group} keys {keys-set(p[group])}'
  for group in ("head","torso"):
   for key,value in p[group].items():
    if isinstance(value,(int,float)): assert value>0, f'{p["id"]}: {group}.{key} must be positive'
  assert p["tail"]["length"]>0 and p["tail"]["girth"]>0
  assert p["limbs"]["paw_scale"]>=0
 assert families==ALLOWED_FAMILIES, f"missing species families: {ALLOWED_FAMILIES-families}"
 # Adult-only anatomy data has an independent schema and explicit family/plan fit.
 anatomy=json.loads((ROOT/"anatomy_profiles.v1.json").read_text(encoding="utf-8"))
 assert anatomy["schema"]=="anthroforge.adult-anatomy-profiles" and anatomy["version"]==1
 assert anatomy["scale"]["minimum"]==0.15 and anatomy["scale"]["maximum"]==8.0
 for key,profile in anatomy["profiles"].items():
  assert profile["id"]==key and profile["adult_only"] is True
  assert 1<=profile["default_member_count"]<=4
  assert profile["compatible_families"] and profile["compatible_plans"]
  dims=profile["dimensions_m"]
  for name in ("length","girth","sac_width","sac_height"):
   assert dims[name]>0, str(key)+": "+name+" must be positive"
  stations=profile["shape"]["stations"]
  assert len(stations)>=3
  ts=[station["t"] for station in stations]
  assert ts==sorted(ts) and ts[0]==0 and ts[-1]==1
  assert all(station["radius"]>0 for station in stations)
 # Parse Blender scripts without importing bpy; catches syntax regressions in CI.
 for path in (ROOT/"scripts").glob("*.py"):
  ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
 print("OK: "+str(len(ids))+" species profiles, "+str(len(families))+" families, "+str(len(anatomy["profiles"]))+" adult anatomy profiles, Blender scripts parse")

if __name__=="__main__":
 try: validate()
 except Exception as exc:
  print("FAIL:",exc,file=sys.stderr);sys.exit(1)
