"""Unit tests for persistent anatomy editing state; no Blender dependency."""
import json
import tempfile
import unittest
from pathlib import Path

from anatomy_editing import (
    AnatomyStateError, MemberOverride, instance_from_dict, instance_to_dict,
    load_profiles, new_instance, resolve_anatomy, save_instance, load_instance,
)

ROOT = Path(__file__).resolve().parents[1]


class AnatomyEditingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load_profiles(ROOT / "anatomy_profiles.v1.json")

    def make(self):
        profile = self.profiles["adult_quad_canid"]
        return new_instance(profile, "sona-anatomy-01")

    def test_four_independent_members_have_stable_ids(self):
        instance = self.make()
        result = resolve_anatomy(instance, self.profiles, "plan.biped", True)
        self.assertEqual(len(result["members"]), 4)
        self.assertEqual(result["members"][2]["component_id"], "sona-anatomy-01:member-03")

    def test_independent_member_and_axis_editing(self):
        instance = self.make()
        instance.axis_scale["length"] = 1.5
        instance.members["member-02"] = MemberOverride(length=1.2, girth=0.8, curve=0.3)
        result = resolve_anatomy(instance, self.profiles, "plan.biped", True)
        self.assertAlmostEqual(result["members"][0]["length_m"], 0.34)
        self.assertAlmostEqual(result["members"][1]["length_m"], 0.34 * 1.5 * 1.2)
        self.assertAlmostEqual(result["members"][1]["girth_m"], 0.052 * 0.8)

    def test_extreme_scale_is_not_silently_clamped(self):
        instance = self.make()
        instance.scale = 8.0
        result = resolve_anatomy(instance, self.profiles, "plan.biped", True)
        self.assertAlmostEqual(result["dimensions_m"]["length"], 2.72)
        instance.scale = 8.01
        with self.assertRaises(AnatomyStateError):
            resolve_anatomy(instance, self.profiles, "plan.biped", True)

    def test_micro_scale_supported(self):
        instance = self.make()
        instance.scale = 0.15
        result = resolve_anatomy(instance, self.profiles, "plan.biped", True)
        self.assertAlmostEqual(result["dimensions_m"]["length"], 0.051)

    def test_adult_gate_and_plan_fit(self):
        instance = self.make()
        with self.assertRaises(AnatomyStateError):
            resolve_anatomy(instance, self.profiles, "plan.biped", False)
        with self.assertRaises(AnatomyStateError):
            resolve_anatomy(instance, self.profiles, "plan.naga", True)

    def test_round_trip_preserves_edits(self):
        instance = self.make()
        instance.scale = 2.25
        instance.axis_scale["girth"] = 1.4
        instance.members["member-04"] = MemberOverride(curve=-0.4, offset_x=0.025)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "anatomy.json"
            save_instance(instance, path)
            loaded = load_instance(path)
        self.assertEqual(instance_to_dict(instance), instance_to_dict(loaded))

    def test_unknown_schema_rejected(self):
        data = instance_to_dict(self.make())
        data["version"] = 99
        with self.assertRaises(AnatomyStateError):
            instance_from_dict(data)

    def test_invalid_member_count_rejected(self):
        instance = self.make()
        instance.member_count = 5
        with self.assertRaises(AnatomyStateError):
            resolve_anatomy(instance, self.profiles, "plan.biped", True)


if __name__ == "__main__":
    unittest.main()
