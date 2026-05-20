"""核心枚举引擎

与 UI 无关，管理破解任务的生命周期（启动、终止）。
汇总各线程状态，通过回调接口通知 UI。
"""

import time

from brute_force.shared_state import SharedState
from brute_force.thread_manager import ThreadManager


class BruteForceEngine:
    """核心枚举引擎"""

    DEFAULT_WORKER_COUNT = 3
    PROGRESS_INTERVAL = 0.5  # 进度回调间隔（秒）

    def __init__(self, worker_count: int = DEFAULT_WORKER_COUNT, callback=None):
        self.worker_count = worker_count
        self.callback = callback
        self.shared_state = SharedState(worker_count=worker_count)
        self.thread_manager = ThreadManager(self.shared_state)
        self._running = False

    def start(self, target_password: str) -> None:
        """启动破解任务

        Args:
            target_password: 目标密码
        """
        self.shared_state.reset(worker_count=self.worker_count)
        self.shared_state.start_time = time.time()
        self._running = True

        if self.callback:
            self.callback.on_started(len(target_password), self.worker_count)

        # 启动工作线程
        self.thread_manager.spawn_workers(
            target_password, self.worker_count
        )

        # 主循环：定期推送进度，等待完成
        while self._running:
            time.sleep(self.PROGRESS_INTERVAL)

            if not self.thread_manager.is_running():
                self._running = False
                break

            if self.callback:
                self._notify_progress()

            # 检查是否已找到密码
            if self.shared_state.found:
                self._running = False
                self.shared_state.end_time = time.time()
                break

        # 任务结束处理
        if not self.shared_state.end_time:
            self.shared_state.end_time = time.time()

        if self.shared_state.found:
            password = self.shared_state.get_found_password()
            attempts = self.shared_state.get_total_attempts()
            elapsed = self.shared_state.get_elapsed()
            worker_id = self.shared_state.found_worker_id
            if self.callback:
                self.callback.on_found(password, attempts, elapsed, worker_id)
        else:
            # 可能是用户终止或所有规则遍历完
            if self.shared_state.is_terminated() and not self.shared_state.found:
                attempts = self.shared_state.get_total_attempts()
                elapsed = self.shared_state.get_elapsed()
                if self.callback:
                    self.callback.on_terminated(attempts, elapsed)

    def terminate(self) -> None:
        """终止所有工作线程"""
        self._running = False
        self.thread_manager.terminate_all()

    def get_status(self) -> dict:
        """获取当前状态快照（供 Web API 轮询使用）

        Returns:
            状态字典
        """
        workers = []
        for i in range(self.worker_count):
            workers.append({
                "id": i,
                "attempts": self.shared_state.attempts[i],
                "rule_id": self.shared_state.current_rule[i],
            })
        return {
            "running": self._running,
            "found": self.shared_state.found,
            "workers": workers,
            "total_attempts": self.shared_state.get_total_attempts(),
            "elapsed": self.shared_state.get_elapsed(),
        }

    def _notify_progress(self) -> None:
        """推送进度到 UI"""
        if self.callback:
            status = self.get_status()
            self.callback.on_progress(status)
