"""共享状态模块

支持多进程模式（基于 multiprocessing.Value/Array）和多线程模式。
多进程模式下移除了全局锁，直接使用 Value 的原子操作或独立锁，避免死锁和性能瓶颈。
"""

import threading
import time


class SharedStateThreadMode:
    """多线程模式下的共享状态实现"""
    
    def __init__(self, worker_count: int = 3):
        self._lock = threading.Lock()
        self.found = False
        self.found_password = ""
        self.found_worker_id = -1
        self.attempts = [0] * worker_count
        self.terminate_flag = False
        self.paused = False
        self.current_rule = [0] * worker_count
        self.start_time = 0.0
        self.end_time = 0.0

    def reset(self, worker_count: int = 3):
        with self._lock:
            self.found = False
            self.found_password = ""
            self.found_worker_id = -1
            self.terminate_flag = False
            self.paused = False
            self.start_time = 0.0
            self.end_time = 0.0
            self.attempts = [0] * worker_count
            self.current_rule = [0] * worker_count

    def set_found(self, password: str, worker_id: int):
        with self._lock:
            if self.found: return
            self.found = True
            self.found_password = password
            self.found_worker_id = worker_id

    def get_found_password(self) -> str:
        with self._lock:
            return self.found_password

    def add_attempts(self, worker_id: int, count: int):
        with self._lock:
            self.attempts[worker_id] += count

    def get_total_attempts(self) -> int:
        with self._lock:
            return sum(self.attempts)

    def get_elapsed(self) -> float:
        with self._lock:
            if self.end_time > 0:
                return self.end_time - self.start_time
            if self.start_time > 0:
                return time.time() - self.start_time
            return 0.0

    def terminate(self):
        with self._lock:
            self.terminate_flag = True

    def is_terminated(self) -> bool:
        with self._lock:
            return self.terminate_flag or self.found

    def pause(self):
        with self._lock:
            self.paused = True

    def resume(self):
        with self._lock:
            self.paused = False

    def is_paused(self) -> bool:
        with self._lock:
            return self.paused


class SharedStateProcessMode:
    """多进程模式下的共享状态实现"""
    
    def __init__(self, worker_count: int = 3):
        import multiprocessing
        
        # Value/Array 自带锁，此处直接使用它们
        self.found = multiprocessing.Value('b', False)
        self.found_worker_id = multiprocessing.Value('i', -1)
        self.found_password = multiprocessing.Array('c', 256)
        
        self.terminate_flag = multiprocessing.Value('b', False)
        self.paused = multiprocessing.Value('b', False)
        
        self.attempts = [multiprocessing.Value('q', 0) for _ in range(worker_count)]
        self.current_rule = [multiprocessing.Value('i', 0) for _ in range(worker_count)]
        
        self.start_time = multiprocessing.Value('d', 0.0)
        self.end_time = multiprocessing.Value('d', 0.0)

    def reset(self, worker_count: int = 3):
        # 重置各状态
        with self.found.get_lock():
            self.found.value = False
            self.found_password.value = b"\x00"
            self.found_worker_id.value = -1
            self.terminate_flag.value = False
            self.paused.value = False
            self.start_time.value = 0.0
            self.end_time.value = 0.0
            for i in range(len(self.attempts)):
                self.attempts[i].value = 0
                self.current_rule[i].value = 0

    def set_found(self, password: str, worker_id: int):
        # 使用 found 的锁保护原子性检查+设置
        with self.found.get_lock():
            if self.found.value:
                return
            self.found.value = True
            self.found_worker_id.value = worker_id
            pw_bytes = password.encode("utf-8")[:255] + b"\x00"
            self.found_password.value = pw_bytes

    def get_found_password(self) -> str:
        raw = self.found_password.value
        end = raw.find(b"\x00")
        if end >= 0: raw = raw[:end]
        return raw.decode("utf-8", errors="replace")

    def add_attempts(self, worker_id: int, count: int):
        # 直接操作，Value 自带简单同步，或使用独立锁
        with self.attempts[worker_id].get_lock():
            self.attempts[worker_id].value += count

    def get_total_attempts(self) -> int:
        total = 0
        for val in self.attempts:
            with val.get_lock():
                total += val.value
        return total

    def get_elapsed(self) -> float:
        if self.end_time.value > 0:
            return self.end_time.value - self.start_time.value
        if self.start_time.value > 0:
            return time.time() - self.start_time.value
        return 0.0

    def terminate(self):
        self.terminate_flag.value = True

    def is_terminated(self) -> bool:
        # 直接读取，避免争抢锁导致卡死
        return self.terminate_flag.value or self.found.value

    def pause(self):
        self.paused.value = True

    def resume(self):
        self.paused.value = False

    def is_paused(self) -> bool:
        return self.paused.value


def create_shared_state(worker_count: int, use_multiprocessing: bool):
    if use_multiprocessing:
        return SharedStateProcessMode(worker_count)
    else:
        return SharedStateThreadMode(worker_count)
