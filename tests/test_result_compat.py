import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "pachinko-sim"
sys.path.insert(0, str(SIM_DIR))

import result  # noqa: E402
import result_basic_printers  # noqa: E402
import result_matrix_printers  # noqa: E402
import result_printer_common  # noqa: E402
import result_printers  # noqa: E402
import result_store_printers  # noqa: E402
from machines import MACHINES  # noqa: E402
from result_metrics import calculate_metrics  # noqa: E402
from result_output_helpers import border_label  # noqa: E402


class ResultCompatTests(unittest.TestCase):
    def test_result_keeps_legacy_printer_exports(self):
        self.assertIs(result.print_single_result, result_printers.print_single_result)
        self.assertIs(result.print_multiple_result, result_printers.print_multiple_result)
        self.assertIs(result.print_matrix_results, result_printers.print_matrix_results)
        self.assertIs(result.save_matrix_to_csv, result_printers.save_matrix_to_csv)

    def test_result_printers_reexports_focused_printer_modules(self):
        self.assertIs(result_printers.print_single_result, result_basic_printers.print_single_result)
        self.assertIs(result_printers.print_multiple_result, result_basic_printers.print_multiple_result)
        self.assertIs(result_printers.print_matrix_results, result_matrix_printers.print_matrix_results)
        self.assertIs(
            result_printers.print_budget_matrix_results,
            result_matrix_printers.print_budget_matrix_results,
        )
        self.assertIs(
            result_printers.print_store_comparison_results,
            result_store_printers.print_store_comparison_results,
        )

    def test_result_keeps_legacy_helper_exports(self):
        self.assertIs(result.calculate_metrics, calculate_metrics)
        self.assertIs(result.border_label, border_label)
        self.assertIn("print_single_result", result.__all__)
        self.assertIn("calculate_metrics", result.__all__)

    def test_common_printer_context_includes_optional_installed_fields(self):
        rows = [
            {
                "installed_full_name_ko": "테스트 한국어",
                "installed_full_name_ja": "テスト日本語",
                "placement_summary": "테스트 배치",
            }
        ]

        buffer = StringIO()
        with redirect_stdout(buffer):
            result_printer_common.print_machine_context(MACHINES["sea_5"], rows)

        output = buffer.getvalue()
        self.assertIn("기종 일본어: P大海物語5", output)
        self.assertIn("실설치명(한국어): 테스트 한국어", output)
        self.assertIn("실설치명(일본어): テスト日本語", output)
        self.assertIn("가게별 배치: 테스트 배치", output)


if __name__ == "__main__":
    unittest.main()
