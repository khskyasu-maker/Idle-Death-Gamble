import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_data  # noqa: E402


class ValidateDataTests(unittest.TestCase):
    def test_border_consistency_accepts_dmm_rate_conversions(self):
        errors = []
        warnings = []
        machine = {
            "rate": "1.111yen",
            "border_4yen_per_250": 17.8,
            "border_1yen_per_200": 14.2,
            "border_1_111yen_per_180": 12.8,
            "border_spins_per_1000yen": 64.0,
            "border_unit_value": 12.8,
            "border_unit": "200円/180玉",
        }

        validate_data.validate_border_consistency(
            machine,
            "data/test.machines[0]",
            errors,
            warnings,
        )

        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_border_consistency_rejects_bad_dmm_conversion(self):
        errors = []
        warnings = []
        machine = {
            "rate": "1yen",
            "border_4yen_per_250": 17.8,
            "border_1yen_per_200": 15.2,
            "border_spins_per_1000yen": 76.0,
            "border_unit_value": 15.2,
            "border_unit": "200円/200玉",
        }

        validate_data.validate_border_consistency(
            machine,
            "data/test.machines[0]",
            errors,
            warnings,
        )

        self.assertTrue(any("border_1yen_per_200" in error for error in errors))

    def test_dmm_machine_id_map_rejects_mismatched_url(self):
        errors = []
        warnings = []
        raw = {
            "dmm_machine_id_map": {
                "machines": [
                    {
                        "machine_name": "新世紀エヴァンゲリオン〜未来への咆哮〜",
                        "dmm_machine_id": 4021,
                        "url": "https://p-town.dmm.com/machines/9999",
                        "checked_at": "2026-05-19",
                        "confirmed_fields": ["大当り確率", "ボーダーライン"],
                    }
                ]
            }
        }

        validate_data.validate_dmm_machine_id_map(
            raw,
            {"新世紀エヴァンゲリオン〜未来への咆哮〜"},
            errors,
            warnings,
        )

        self.assertTrue(any("same numeric ID" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
