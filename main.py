"""程序入口

注意：本程序需要 Python 3.13 free-threading 版本运行。
使用 uv 运行：uv run --python 3.13t main.py
"""

import sys
from brute_force.cli import run_cli


def main():
    """主入口函数"""
    run_cli()


if __name__ == "__main__":
    main()
    sys.exit(0)
