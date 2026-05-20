"""多线程共享状态模块

使用 threading.Lock 保护共享状态。
Python 3.13 free-threading 模式下，所有线程共享同一进程内存空间。
"""

import threading
import time


class SharedState:
    """多线程共享状态"""

    def __init__(self, worker_count: int = 3):
        self._lock = threading.Lock()

        # 是否已找到密码
        self.found = False
        self.found_password = ""
        self.found_worker_id = -1

        # 各线程的尝试次数
        self.attempts = [0] * worker_count

        # 终止标志（用户提前终止）
        self.terminate_flag = False

        # 各线程当前正在执行的规则编号
        self.current_rule = [0] * worker_count

        # 任务开始/结束时间
        self.start_time = 0.0
        self.end_time = 0.0

    def reset(self, worker_count: int = 3):
        """重置所有状态，为下一次破解任务做准备"""
        with self._lock:
            self.found = False
            self.found_password = ""
            self.found_worker_id = -1
            self.terminate_flag = False
            self.start_time = 0.0
            self.end_time = 0.0
            self.attempts = [0] * worker_count
            self.current_rule = [0] * worker_count

    def set_found(self, password: str, worker_id: int):
        """标记密码已找到"""
        with self._lock:
            if self.found:
                return  # 已被其他线程找到
            self.found = True
            self.found_password = password
            self.found_worker_id = worker_id

    def get_found_password(self) -> str:
        """获取找到的密码"""
        with self._lock:
            return self.found_password

    def add_attempts(self, worker_id: int, count: int):
        """增加尝试次数"""
        with self._lock:
            self.attempts[worker_id] += count

    def get_total_attempts(self) -> int:
        """获取所有线程累计尝试次数"""
        with self._lock:
            return sum(self.attempts)

    def get_elapsed(self) -> float:
        """获取已运行时间（秒）"""
        with self._lock:
            if self.end_time > 0:
                return self.end_time - self.start_time
            if self.start_time > 0:
                return time.time() - self.start_time
            return 0.0

    def terminate(self):
        """设置终止标志"""
        with self._lock:
            self.terminate_flag = True

    def is_terminated(self) -> bool:
        """检查是否已终止"""
        with self._lock:
            return self.terminate_flag or self.found
