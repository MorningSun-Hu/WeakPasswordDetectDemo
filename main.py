"""程序入口

注意：本程序需要 Python 3.13 free-threading 版本运行。
使用 uv 运行：uv run --python 3.13t main.py
"""

import sys
import multiprocessing

from brute_force.cli import run_cli


def main():
    """主入口函数"""
    # Windows 多进程必须，防止无限递归启动子进程
    multiprocessing.freeze_support()
    run_cli()


if __name__ == "__main__":
    main()
    sys.exit(0)
