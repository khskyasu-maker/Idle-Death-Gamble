import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

import result  # noqa: E402
import result_printers  # noqa: E402
from result_metrics import calculate_metrics  # noqa: E402
from result_output_helpers import border_label  # noqa: E402


class ResultCompatTests(unittest.TestCase):
    def test_result_keeps_legacy_printer_exports(self):
        self.assertIs(result.print_single_result, result_printers.print_single_result)
        self.assertIs(result.print_multiple_result, result_printers.print_multiple_result)
        self.assertIs(result.print_matrix_results, result_printers.print_matrix_results)
        self.assertIs(result.save_matrix_to_csv, result_printers.save_matrix_to_csv)

    def test_result_keeps_legacy_helper_exports(self):
        self.assertIs(result.calculate_metrics, calculate_metrics)
        self.assertIs(result.border_label, border_label)
        self.assertIn("print_single_result", result.__all__)
        self.assertIn("calculate_metrics", result.__all__)


if __name__ == "__main__":
    unittest.main()
