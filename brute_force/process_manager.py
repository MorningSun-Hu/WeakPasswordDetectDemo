"""进程管理器模块

使用 multiprocessing.Process 创建工作进程。
"""

import multiprocessing
import sys

from brute_force.worker import worker_process, assign_rules


class ProcessManager:
    """进程管理器"""

    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.processes = []

    def spawn_workers(self, target: str, worker_count: int) -> list:
        """创建并启动工作进程"""
        self.processes = []
        for i in range(worker_count):
            rule_ids = assign_rules(i, worker_count)
            proc = multiprocessing.Process(
                target=worker_process,
                args=(i, target, self.shared_state, rule_ids),
            )
            proc.daemon = True
            self.processes.append(proc)
            proc.start()
        return self.processes

    def wait_for_completion(self) -> bool:
        """等待所有进程完成"""
        for proc in self.processes:
            proc.join()
        return True

    def is_running(self) -> bool:
        """检查是否还有进程在运行"""
        return any(p.is_alive() for p in self.processes)

    def terminate_all(self) -> None:
        """设置终止标志并终止所有进程"""
        self.shared_state.terminate()
        for proc in self.processes:
            proc.terminate()
            proc.join(timeout=2.0)

    def get_worker_count(self) -> int:
        return len(self.processes)
