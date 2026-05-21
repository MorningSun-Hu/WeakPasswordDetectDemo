"""共享状态模块

根据运行模式（多进程/多线程）使用不同的同步原语。
多进程模式：使用 multiprocessing.Value / Array
多线程模式：使用 threading.Lock + 原生变量
"""

import threading

class SharedStateThreadMode:
    """多线程模式下的共享状态实现"""
    
    def __init__(self, worker_count: int = 3):
        self._lock = threading.Lock()
        self.found = False
        self.found_password = ""
        self.found_worker_id = -1
        self.attempts = [0] * worker_count
        self.terminate_flag = False
        self.current_rule = [0] * worker_count
        self.start_time = 0.0
        self.end_time = 0.0

    def reset(self, worker_count: int = 3):
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
        import time
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


class SharedStateProcessMode:
    """多进程模式下的共享状态实现"""
    
    def __init__(self, worker_count: int = 3):
        import multiprocessing
        
        # 使用 Lock 保护非原子操作
        self._lock = multiprocessing.Lock()
        
        # 布尔标志和整型使用 Value
        self.found = multiprocessing.Value('b', False, lock=False)
        self.found_worker_id = multiprocessing.Value('i', -1, lock=False)
        self.found_password = multiprocessing.Array('c', 256)
        
        self.terminate_flag = multiprocessing.Value('b', False, lock=False)
        
        # 尝试计数器和当前规则
        self.attempts = [multiprocessing.Value('q', 0) for _ in range(worker_count)]
        self.current_rule = [multiprocessing.Value('i', 0) for _ in range(worker_count)]
        
        self.start_time = multiprocessing.Value('d', 0.0, lock=False)
        self.end_time = multiprocessing.Value('d', 0.0, lock=False)

    def reset(self, worker_count: int = 3):
        with self._lock:
            self.found.value = False
            self.found_password.value = b"\x00"
            self.found_worker_id.value = -1
            self.terminate_flag.value = False
            self.start_time.value = 0.0
            self.end_time.value = 0.0
            for i in range(len(self.attempts)):
                self.attempts[i].value = 0
                self.current_rule[i].value = 0

    def set_found(self, password: str, worker_id: int):
        with self._lock:
            if self.found.value: return
            self.found.value = True
            self.found_worker_id.value = worker_id
            # SynchronizedString 赋值
            pw_bytes = password.encode("utf-8")[:255] + b"\x00"
            self.found_password.value = pw_bytes

    def get_found_password(self) -> str:
        with self._lock:
            raw = self.found_password.value
            end = raw.find(b"\x00")
            if end >= 0: raw = raw[:end]
            return raw.decode("utf-8", errors="replace")

    def add_attempts(self, worker_id: int, count: int):
        with self._lock:
            self.attempts[worker_id].value += count

    def get_total_attempts(self) -> int:
        with self._lock:
            return sum(a.value for a in self.attempts)

    def get_elapsed(self) -> float:
        import time
        with self._lock:
            if self.end_time.value > 0:
                return self.end_time.value - self.start_time.value
            if self.start_time.value > 0:
                return time.time() - self.start_time.value
            return 0.0

    def terminate(self):
        with self._lock:
            self.terminate_flag.value = True

    def is_terminated(self) -> bool:
        with self._lock:
            return self.terminate_flag.value or self.found.value


def create_shared_state(worker_count: int, use_multiprocessing: bool):
    """工厂函数：根据模式创建共享状态"""
    if use_multiprocessing:
        return SharedStateProcessMode(worker_count)
    else:
        return SharedStateThreadMode(worker_count)
