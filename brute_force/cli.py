"""命令行界面实现 (Windows 优化版)

实现稳定的多行刷新，避免内容重叠和残留。
"""

import sys
import os
import time
import ctypes

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


def _enable_ansi():
    """在 Windows 上启用 ANSI 转义支持"""
    if os.name != 'nt':
        return True
    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        if not kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING):
            return False
        return True
    except Exception:
        return False


class CLIUI:
    def __init__(self, engine: BruteForceEngine):
        self.engine = engine
        self._last_line_count = 0

    def on_started(self, target_length: int, worker_count: int, cpu_count: int, is_process: bool) -> None:
        # 启用 ANSI 支持
        _enable_ansi()

        mode_str = "多进程" if is_process else "多线程"
        
        lines = [
            "=" * 50,
            "  弱口令枚举暴力破解演示",
            "=" * 50,
            "运行模式: %s | 物理核心: %d | 并发数: %d" % (mode_str, cpu_count, worker_count),
            "目标密码: %s 位" % ("*" * target_length),
            "按 Ctrl+C 提前终止",
            "-" * 50,
            ""
        ]
        
        # 使用 sys.stdout.write 确保输出控制精确
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        
        # 记录标题行数，用于后续定位（虽然 on_progress 是相对移动）
        self._header_lines = len(lines)
        self._last_line_count = 0

    def on_progress(self, status: dict) -> None:
        # 构建进度行
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
        
        # 刷新逻辑：
        # 1. 如果上次有打印内容，光标在内容下方。
        # 2. 向上移动上次打印的行数。
        # 3. 清除从光标到屏幕末尾的内容（清除旧数据）。
        # 4. 打印新数据。
        
        if self._last_line_count > 0:
            sys.stdout.write("\033[%dA" % self._last_line_count)
            sys.stdout.write("\r")  # 回到行首
            sys.stdout.write("\033[0J")  # 清除从光标到屏幕末尾
        
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        
        self._last_line_count = len(lines)

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        # 清除进度区域
        if self._last_line_count > 0:
            sys.stdout.write("\033[%dA" % self._last_line_count)
            sys.stdout.write("\r")
            sys.stdout.write("\033[0J")

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
        # 清除进度区域
        if self._last_line_count > 0:
            sys.stdout.write("\033[%dA" % self._last_line_count)
            sys.stdout.write("\r")
            sys.stdout.write("\033[0J")
            
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

    # 定义支持的字符集
    import string
    _ALLOWED_CHARS = set(string.ascii_letters + string.digits)

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

        # 检查是否包含不支持的符号
        invalid_chars = [c for c in target if c not in _ALLOWED_CHARS]
        if invalid_chars:
            print("提示：本演示程序仅支持纯字母和数字密码。")
            print("检测到不支持的符号: %s" % ", ".join(repr(c) for c in set(invalid_chars)))
            print("请重新输入。")
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
