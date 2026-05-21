"""命令行界面实现 (Windows 优化版)

避免频繁清屏导致画面闪烁。
使用固定区域刷新进度。
"""

import sys
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
        self._progress_start_line = 0  # 记录进度区域的起始行

    def on_started(self, target_length: int, worker_count: int, cpu_count: int, is_process: bool) -> None:
        # 记录当前行号作为进度区域的起点
        mode_str = "多进程" if is_process else "多线程"
        
        print("=" * 50)
        print("  弱口令枚举暴力破解演示")
        print("=" * 50)
        print("运行模式: %s | 物理核心: %d | 并发数: %d" % (mode_str, cpu_count, worker_count))
        print("目标密码: %s 位" % ("*" * target_length))
        print("按 Ctrl+C 提前终止")
        print("-" * 50)
        print()  # 空行分隔
        
        # Windows 控制台行号计算：打印了多少行
        # 简单起见，我们通过打印固定行来占位，或者使用 ANSI 移动
        # 这里使用简单的换行策略：进度显示在下方
        self._progress_start_line = 8  # 大致行号

    def on_progress(self, status: dict) -> None:
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
        
        # 简单覆盖刷新：向上移动，清除并打印
        line_count = len(lines)
        if os.name == "nt":
            # Windows 回退方案：打印 \r 覆盖当前行不太适合多行
            # 使用 cls 会破坏布局，这里使用 ANSI 转义（Win10+ 支持）
            sys.stdout.write("\033[%dA\r" % line_count)
            for line in lines:
                sys.stdout.write("\033[K%s\n" % line)
            # 光标移回起始位置以便下次覆盖
            sys.stdout.write("\033[%dA\r" % line_count)
        else:
            sys.stdout.write("\033[%dA\r" % line_count)
            for line in lines:
                sys.stdout.write("\033[K%s\n" % line)
            sys.stdout.write("\033[%dA\r" % line_count)
        sys.stdout.flush()

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        # 清除下方进度内容
        print("\033[J", end="")
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
        print("\033[J", end="")
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
    # 初始欢迎界面
    clear_screen()
    print("弱口令枚举暴力破解演示程序")
    print("Python 3.13 Free-threading 版本")
    print()

    engine_ref = [None]

    def signal_handler(signum, frame):
        if engine_ref[0]:
            engine_ref[0].terminate()

    import signal
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

        # 每次开始前清屏
        clear_screen()
        
        engine = BruteForceEngine(worker_count=3, callback=CLIUI.__new__(CLIUI))
        engine.callback = CLIUI(engine)
        engine.callback.engine = engine
        engine_ref[0] = engine

        try:
            engine.start(target)
        except KeyboardInterrupt:
            engine.terminate()
        finally:
            engine_ref[0] = None
