"""Regression tests for species/anatomy profile validation."""
import json
import shutil
import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_species_mesh_lab import validate


class SpeciesProfileValidationTests(unittest.TestCase):
    def test_repository_profiles_pass(self):
        summary = validate(ROOT)
        self.assertEqual(summary["species_profiles"], 6)
        self.assertEqual(summary["species_families"], 6)
        self.assertEqual(summary["anatomy_profiles"], 6)

    def copy_profiles(self):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        shutil.copy(ROOT / "species_profiles.v1.json", root)
        shutil.copy(ROOT / "anatomy_profiles.v1.json", root)
        (root / "scripts").mkdir()
        return directory, root

    def test_non_finite_json_constants_are_rejected(self):
        directory, root = self.copy_profiles()
        with directory:
            path = root / "species_profiles.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["profiles"][0]["head"]["length"] = float("nan")
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-standard JSON numeric constant"):
                validate(root)

    def test_duplicate_station_positions_are_rejected(self):
        directory, root = self.copy_profiles()
        with directory:
            path = root / "anatomy_profiles.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            stations = data["profiles"]["adult_quad_canid"]["shape"]["stations"]
            stations[2]["t"] = stations[1]["t"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "increase strictly"):
                validate(root)

    def test_member_count_must_be_an_integer(self):
        directory, root = self.copy_profiles()
        with directory:
            path = root / "anatomy_profiles.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["profiles"]["adult_quad_canid"]["default_member_count"] = 2.5
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integer from 1 to 4"):
                validate(root)


if __name__ == "__main__":
    unittest.main()
