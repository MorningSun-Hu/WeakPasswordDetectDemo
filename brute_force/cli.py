"""命令行界面实现"""

import sys
import signal
import os
import time

from brute_force.engine import BruteForceEngine
from brute_force.enum_rules import RULE_NAMES


def format_number(n: int) -> str:
    """格式化数字，添加千分位分隔符"""
    return "{:,}".format(n)


def format_time(seconds: float) -> str:
    """格式化时间为 HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return "%02d:%02d:%02d" % (hours, minutes, secs)


class CLIUI:
    """命令行界面，实现 UICallback 接口"""

    def __init__(self, engine: BruteForceEngine):
        self.engine = engine
        self._last_line_count = 0

    def on_started(self, target_length: int, worker_count: int) -> None:
        print("\n" + "=" * 50)
        print("  弱口令枚举暴力破解演示")
        print("=" * 50)
        print("目标密码: %s 位" % ("*" * target_length))
        print("枚举线程: %d 个运行中" % worker_count)
        print("按 Ctrl+C 提前终止")
        print("-" * 50)

    def on_progress(self, status: dict) -> None:
        # 清屏并重新显示
        self._clear_lines(self._last_line_count)

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

        output = "\n".join(lines)
        print(output)
        self._last_line_count = len(lines)

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        self._clear_lines(self._last_line_count)
        print("\n" + "=" * 50)
        print("  破解成功!")
        print("=" * 50)
        print("密码: %s" % password)
        print("由 Worker %d 找到" % worker_id)
        print("总尝试次数: %s" % format_number(attempts))
        print("总用时: %s (%.2f 秒)" % (format_time(elapsed), elapsed))
        print("=" * 50)

    def on_terminated(self, attempts: int, elapsed: float) -> None:
        self._clear_lines(self._last_line_count)
        print("\n" + "=" * 50)
        print("  已提前终止")
        print("=" * 50)
        print("截止尝试次数: %s" % format_number(attempts))
        print("截止用时: %s (%.2f 秒)" % (format_time(elapsed), elapsed))
        print("=" * 50)

    def on_error(self, message: str) -> None:
        print("\n错误: %s" % message)

    def _clear_lines(self, count: int) -> None:
        """清除控制台最后 N 行"""
        if os.name == "nt":
            # Windows: 使用 cls 不太适合局部清除，简单跳过
            return
        # ANSI 转义序列：上移 + 清除行
        if count > 0:
            sys.stdout.write("\033[%dA" % count)
            for _ in range(count):
                sys.stdout.write("\r\033[K")
            sys.stdout.flush()


def run_cli() -> None:
    """CLI 主循环"""
    print("弱口令枚举暴力破解演示程序")
    print("Python 3.13 Free-threading 版本")
    print()

    # 注册 Ctrl+C 处理
    engine_ref = [None]

    def signal_handler(signum, frame):
        if engine_ref[0]:
            engine_ref[0].terminate()

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        target = input("\n请输入目标密码 (输入 'quit' 退出): ").strip()
        if target.lower() in ("quit", "exit", "q"):
            print("退出程序。")
            break
        if not target:
            print("密码不能为空，请重新输入。")
            continue

        # 检查长度，超过8位警告
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
