import sys

from cli_modes import run_cli


main = run_cli


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n시뮬레이터를 종료합니다.")
        sys.exit(0)
