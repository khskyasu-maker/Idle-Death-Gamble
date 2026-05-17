from cli_inputs import get_int_input
from result_metrics import calculate_metrics
from result_public_export import save_public_sim_results


def ask_public_sim_result_export(store_name: str, mode_label: str, machine, result_rows, iterations: int):
    print("\n[공개용 최신 시뮬 결과 공유]")
    print("저장하면 docs/latest-sim-results.* 파일이 최신 집계표로 덮어써집니다.")
    print("공개되는 값: 점포/기종/가정 예산/회전수/집계 지표. 포함하지 않는 값: 원시 표본, 개인 일정, 실제 지출/손익.")
    share = get_int_input("GitHub Pages 공유용 최신 표로 저장할까요? 1=예, 0=아니오 [기본값: 0]: ", 0, 1, 0)
    if not share:
        return

    paths = save_public_sim_results(
        store_name,
        mode_label,
        machine,
        result_rows,
        iterations,
        calculate_metrics,
    )
    print(f"[안내] 공개용 최신 시뮬 결과를 저장했습니다: {paths['html']}")
