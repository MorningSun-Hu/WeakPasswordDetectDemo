"""进程管理器模块"""

import multiprocessing
import sys

from brute_force.worker import worker_process

class ProcessManager:
    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.processes = []

    def spawn_workers(self, target: str, worker_count: int, max_len: int = 8) -> list:
        """创建并启动工作进程"""
        self.processes = []
        print(f"Spawning {worker_count} workers...", file=sys.stderr)
        
        for i in range(worker_count):
            proc = multiprocessing.Process(
                target=worker_process,
                args=(i, target, self.shared_state, worker_count, max_len),
                name=f"Worker-{i}"
            )
            proc.daemon = True
            self.processes.append(proc)
            
            try:
                proc.start()
                print(f"Worker {i} started successfully (PID: {proc.pid})", file=sys.stderr)
            except Exception as e:
                print(f"FAILED to start Worker {i}: {e}", file=sys.stderr)
                raise

        return self.processes

    def is_running(self) -> bool:
        return any(p.is_alive() for p in self.processes)

    def terminate_all(self) -> None:
        print("Terminating all workers...", file=sys.stderr)
        self.shared_state.terminate()
        for proc in self.processes:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=1.0)
