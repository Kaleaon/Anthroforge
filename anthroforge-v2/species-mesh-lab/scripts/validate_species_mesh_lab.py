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
  for group,keys in REQUIRED.items():
   assert keys <= set(p[group]), f'{p["id"]}: missing {group} keys {keys-set(p[group])}'
  for group in ("head","torso"):
   for key,value in p[group].items():
    if isinstance(value,(int,float)): assert value>0, f'{p["id"]}: {group}.{key} must be positive'
  assert p["tail"]["length"]>0 and p["tail"]["girth"]>0
  assert p["limbs"]["paw_scale"]>=0
 assert families==ALLOWED_FAMILIES, f"missing species families: {ALLOWED_FAMILIES-families}"
 # Parse Blender scripts without importing bpy; catches syntax regressions in CI.
 for path in (ROOT/"scripts").glob("*.py"):
  ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
 print(f"OK: {len(ids)} species profiles, {len(families)} families, Blender scripts parse")

if __name__=="__main__":
 try: validate()
 except Exception as exc:
  print("FAIL:",exc,file=sys.stderr);sys.exit(1)
