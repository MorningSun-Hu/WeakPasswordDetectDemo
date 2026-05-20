"""命令行界面实现

使用 os.system 清屏，保证跨平台兼容性。
破解完成后等待用户按回车键再继续，避免结果被立刻清除。
"""

import sys
import signal
import os
import time

from brute_force.engine import BruteForceEngine
from brute_force.enum_rules import RULE_NAMES


def format_number(n: int) -> str:
    return "{:,}".format(n)


def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return "%02d:%02d:%02d" % (hours, minutes, secs)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_enter() -> None:
    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass


class CLIUI:
    def __init__(self, engine: BruteForceEngine):
        self.engine = engine

    def _build_progress_lines(self, status: dict) -> list:
        lines = []
        for w in status["workers"]:
            rule_name = RULE_NAMES.get(w["rule_id"], "未知")
            lines.append(
                "[Worker %d] 尝试次数: %s    规则: %s"
                % (w["id"], format_number(w["attempts"]), rule_name)
            )
        lines.append("")
        lines.append("累计尝试: %s" % format_number(status["total_attempts"]))
        lines.append("已用时间: %s" % format_time(status["elapsed"]))
        return lines

    def on_started(self, target_length: int, worker_count: int) -> None:
        clear_screen()
        print("=" * 50)
        print("  弱口令枚举暴力破解演示")
        print("=" * 50)
        print("目标密码: %s 位" % ("*" * target_length))
        print("枚举线程: %d 个运行中" % worker_count)
        print("按 Ctrl+C 提前终止")
        print("-" * 50)
        print()

    def on_progress(self, status: dict) -> None:
        lines = self._build_progress_lines(status)
        # 向上移动对应行数并清除
        line_count = len(lines)
        sys.stdout.write("\033[%dA\r" % line_count)
        for line in lines:
            sys.stdout.write("\033[K%s\n" % line)
        sys.stdout.flush()
        # 将光标移回上方，覆盖下次输出
        sys.stdout.write("\033[%dA\r" % line_count)
        sys.stdout.flush()

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        sys.stdout.write("\033[J")  # 清除下方内容
        print("\n" + "=" * 50)
        print("  破解成功!")
        print("=" * 50)
        print("密码: %s" % password)
        print("由 Worker %d 找到" % worker_id)
        print("总尝试次数: %s" % format_number(attempts))
        print("总用时: %s (%.2f 秒)" % (format_time(elapsed), elapsed))
        print("=" * 50)
        wait_for_enter()

    def on_terminated(self, attempts: int, elapsed: float) -> None:
        sys.stdout.write("\033[J")
        print("\n" + "=" * 50)
        print("  已提前终止")
        print("=" * 50)
        print("截止尝试次数: %s" % format_number(attempts))
        print("截止用时: %s (%.2f 秒)" % (format_time(elapsed), elapsed))
        print("=" * 50)
        wait_for_enter()

    def on_error(self, message: str) -> None:
        print("\n错误: %s" % message)


def run_cli() -> None:
    clear_screen()
    print("弱口令枚举暴力破解演示程序")
    print("Python 3.13 Free-threading 版本")
    print()

    engine_ref = [None]

    def signal_handler(signum, frame):
        if engine_ref[0]:
            engine_ref[0].terminate()

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            target = input("请输入目标密码 (输入 'quit' 退出): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出程序。")
            break

        if target.lower() in ("quit", "exit", "q"):
            print("退出程序。")
            break
        if not target:
            print("密码不能为空，请重新输入。")
            continue

        if len(target) > 8:
            print("警告：目标密码超过8位，枚举可能需要很长时间。")
            confirm = input("是否继续? (y/n): ").strip().lower()
            if confirm != "y":
                continue

        engine = BruteForceEngine(worker_count=3)
        engine_ref[0] = engine
        ui = CLIUI(engine)
        engine.callback = ui

        try:
            engine.start(target)
        except KeyboardInterrupt:
            engine.terminate()
        finally:
            engine_ref[0] = None
