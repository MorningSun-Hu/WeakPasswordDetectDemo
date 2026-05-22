"""核心枚举引擎

根据 CPU 物理核心数自动选择多进程或多线程模式。
"""

import glob
import time
import os
import sys

from brute_force.shared_state import create_shared_state
from brute_force.process_manager import ProcessManager
from brute_force.thread_manager import ThreadManager


class BruteForceEngine:
    PROGRESS_INTERVAL = 0.5

    def __init__(self, worker_count: int = 0, callback=None):
        self._setup_hardware_config(worker_count)
        
        self.callback = callback
        self.shared_state = create_shared_state(self.worker_count, self.use_multiprocessing)
        
        if self.use_multiprocessing:
            self.manager = ProcessManager(self.shared_state)
        else:
            self.manager = ThreadManager(self.shared_state)
            
        self._running = False

    def _cleanup_old_logs(self) -> None:
        """清理旧的 worker 日志"""
        try:
            for f in glob.glob("worker_*.log"):
                os.remove(f)
        except Exception:
            pass

    def _setup_hardware_config(self, requested_count: int):
        """检测硬件并决定运行模式"""
        import psutil
        
        self.physical_cores = psutil.cpu_count(logical=False) or 1
        self.logical_threads = psutil.cpu_count(logical=True) or 1

        if requested_count > 0:
            self.worker_count = requested_count
            self.use_multiprocessing = True
        else:
            if self.physical_cores <= 2:
                self.use_multiprocessing = False
                self.worker_count = max(1, self.logical_threads - 1)
            else:
                self.use_multiprocessing = True
                self.worker_count = max(1, self.physical_cores - 1)

    def start(self, target_password: str) -> None:
        # 清理旧的 worker 日志，只保留本次运行的
        self._cleanup_old_logs()
        
        self.shared_state.reset(worker_count=self.worker_count)
        if self.use_multiprocessing:
            self.shared_state.start_time.value = time.time()
        else:
            self.shared_state.start_time = time.time()

        self._running = True

        if self.callback:
            self.callback.on_started(
                len(target_password), self.worker_count, self.physical_cores, 
                self.use_multiprocessing
            )

        # 启动 Worker
        try:
            self.manager.spawn_workers(target_password, self.worker_count)
        except Exception as e:
            print("启动 Worker 失败:", e)
            self._running = False
            return

        # 主循环
        while self._running:
            time.sleep(self.PROGRESS_INTERVAL)

            # 检查 Worker 是否还活着
            if not self.manager.is_running():
                self._running = False
                break

            # 推送进度
            if self.callback:
                self._notify_progress()

            # 检查是否已找到密码
            if self.use_multiprocessing:
                if self.shared_state.found.value:
                    self._running = False
                    self.shared_state.end_time.value = time.time()
                    break
            else:
                if self.shared_state.found:
                    self._running = False
                    self.shared_state.end_time = time.time()
                    break

        # 任务结束处理
        if self.use_multiprocessing:
            if not self.shared_state.end_time.value:
                self.shared_state.end_time.value = time.time()
        else:
            if not self.shared_state.end_time:
                self.shared_state.end_time = time.time()

        found_status = self.shared_state.found.value if self.use_multiprocessing else self.shared_state.found
        if found_status:
            password = self.shared_state.get_found_password()
            attempts = self.shared_state.get_total_attempts()
            elapsed = self.shared_state.get_elapsed()
            worker_id = self.shared_state.found_worker_id.value if self.use_multiprocessing else self.shared_state.found_worker_id
            if self.callback:
                self.callback.on_found(password, attempts, elapsed, worker_id)
        else:
            attempts = self.shared_state.get_total_attempts()
            elapsed = self.shared_state.get_elapsed()
            if self.callback:
                self.callback.on_terminated(attempts, elapsed)

    def terminate(self) -> None:
        self._running = False
        self.manager.terminate_all()

    def pause(self) -> None:
        """暂停破解任务"""
        self.shared_state.pause()

    def resume(self) -> None:
        """恢复破解任务"""
        self.shared_state.resume()

    def get_status(self) -> dict:
        workers = []
        for i in range(self.worker_count):
            if self.use_multiprocessing:
                attempts = self.shared_state.attempts[i].value
                rule_id = self.shared_state.current_rule[i].value
            else:
                attempts = self.shared_state.attempts[i]
                rule_id = self.shared_state.current_rule[i]
            workers.append({"id": i, "attempts": attempts, "rule_id": rule_id})
        
        found_status = self.shared_state.found.value if self.use_multiprocessing else self.shared_state.found
        return {
            "running": self._running,
            "found": found_status,
            "workers": workers,
            "total_attempts": self.shared_state.get_total_attempts(),
            "elapsed": self.shared_state.get_elapsed(),
            "mode": "process" if self.use_multiprocessing else "thread"
        }

    def _notify_progress(self) -> None:
        if self.callback:
            self.callback.on_progress(self.get_status())
