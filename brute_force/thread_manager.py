"""线程管理器模块

使用 threading.Thread 创建工作线程（回退模式）。
"""

import threading

from brute_force.worker import worker_thread


class ThreadManager:
    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.threads = []

    def spawn_workers(self, target: str, worker_count: int, max_len: int = 8) -> list:
        self.threads = []
        for i in range(worker_count):
            thread = threading.Thread(
                target=worker_thread,
                args=(i, target, self.shared_state, worker_count, max_len),
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()
        return self.threads

    def wait_for_completion(self) -> bool:
        for t in self.threads:
            t.join()
        return True

    def is_running(self) -> bool:
        return any(t.is_alive() for t in self.threads)

    def terminate_all(self) -> None:
        self.shared_state.terminate()
        for t in self.threads:
            t.join(timeout=2.0)

    def get_worker_count(self) -> int:
        return len(self.threads)
