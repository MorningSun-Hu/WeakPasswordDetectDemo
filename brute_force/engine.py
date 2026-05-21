"""核心枚举引擎

根据 CPU 物理核心数自动选择多进程或多线程模式。
- 物理核心数 > 2: 多进程 (进程数 = 物理核心数 - 1)
- 物理核心数 <= 2: 多线程 (线程数 = 逻辑线程数 - 1)
"""

import time

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

    def _setup_hardware_config(self, requested_count: int):
        """检测硬件并决定运行模式"""
        import psutil
        
        self.physical_cores = psutil.cpu_count(logical=False) or 1
        self.logical_threads = psutil.cpu_count(logical=True) or 1

        if requested_count > 0:
            self.worker_count = requested_count
            # 如果用户指定了数量，默认使用多进程（除非物理核极少）
            self.use_multiprocessing = self.physical_cores > 2 if requested_count <= 2 else True
        else:
            if self.physical_cores <= 2:
                self.use_multiprocessing = False
                self.worker_count = max(1, self.logical_threads - 1)
            else:
                self.use_multiprocessing = True
                self.worker_count = max(1, self.physical_cores - 1)

    def start(self, target_password: str) -> None:
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

        self.manager.spawn_workers(target_password, self.worker_count)

        while self._running:
            time.sleep(self.PROGRESS_INTERVAL)

            if not self.manager.is_running():
                self._running = False
                break

            if self.callback:
                self._notify_progress()

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

        if self.use_multiprocessing:
            if not self.shared_state.end_time.value:
                self.shared_state.end_time.value = time.time()
        else:
            if not self.shared_state.end_time:
                self.shared_state.end_time = time.time()

        if self.use_multiprocessing:
            found = self.shared_state.found.value
            password = self.shared_state.get_found_password()
            worker_id = self.shared_state.found_worker_id.value
        else:
            found = self.shared_state.found
            password = self.shared_state.get_found_password()
            worker_id = self.shared_state.found_worker_id

        attempts = self.shared_state.get_total_attempts()
        elapsed = self.shared_state.get_elapsed()

        if found:
            if self.callback:
                self.callback.on_found(password, attempts, elapsed, worker_id)
        else:
            if self.callback:
                self.callback.on_terminated(attempts, elapsed)

    def terminate(self) -> None:
        self._running = False
        self.manager.terminate_all()

    def get_status(self) -> dict:
        workers = []
        for i in range(self.worker_count):
            attempts = self.shared_state.attempts[i].value if self.use_multiprocessing else self.shared_state.attempts[i]
            rule_id = self.shared_state.current_rule[i].value if self.use_multiprocessing else self.shared_state.current_rule[i]
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
