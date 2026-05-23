"""共享状态模块

支持多进程模式（基于 multiprocessing.Value/Array）和多线程模式。
支持动态任务队列：按规则+长度范围分段，所有worker同时处理同一规则的不同长度段。
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
        
        # 动态任务队列
        self.current_rule = 0
        self.length_start = 1    # 当前规则的起始长度
        
        # 弱口令库专用
        self.dict_lines_loaded = False
        self.dict_total_lines = 0
        self.dict_next_line = 0  # 下一行索引
        self.dict_active_workers = 0  # 正在处理字典的worker数
        self.dict_all_assigned = False  # 所有字典块是否已分配完毕
        
        self.start_time = 0.0
        self.end_time = 0.0

    def reset(self, worker_count: int = 3):
        with self._lock:
            self.found = False
            self.found_password = ""
            self.found_worker_id = -1
            self.terminate_flag = False
            self.paused = False
            self.current_rule = 0
            self.length_start = 1
            # 不清零字典状态（字典只需加载一次，reset只重置运行时状态）
            self.dict_next_line = 0
            self.dict_active_workers = 0
            self.start_time = 0.0
            self.end_time = 0.0
            self.attempts = [0] * worker_count

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

    # 动态任务队列方法
    def set_dict_total(self, total: int):
        """设置弱口令库总行数"""
        with self._lock:
            self.dict_total_lines = total
            self.dict_lines_loaded = True

    def get_next_task(self, worker_count: int, max_len: int = 8) -> tuple:
        """获取下一个任务块

        Returns:
            (rule_id, min_len, max_len) 或 (None, 0, 0) 表示无任务
            (0, -1, -1) 表示等待中（字典处理中或规则切换中）
        """
        with self._lock:
            if self.terminate_flag or self.found:
                return (None, 0, 0)
            
            # 检查当前规则是否有更多任务
            if self.current_rule == 0:
                # 弱口令库：按行数分段
                if not self.dict_lines_loaded:
                    return (0, -1, -1)  # 等待字典加载
                if self.dict_next_line >= self.dict_total_lines:
                    # 所有字典块已分配，但需等待活跃worker完成
                    if self.dict_active_workers <= 0:
                        # 字典全部完成，进入下一规则
                        self.current_rule = 1
                        self.length_start = 1
                    else:
                        return (0, -1, -1)  # 等待活跃worker完成
                else:
                    # 分配字典块
                    chunk = max(100, self.dict_total_lines // (worker_count * 2))
                    start = self.dict_next_line
                    end = min(start + chunk, self.dict_total_lines)
                    self.dict_next_line = end
                    self.dict_active_workers += 1
                    return (0, start, end)
            
            # 枚举规则：按长度分段
            if self.length_start > max_len:
                # 当前规则完成，进入下一规则
                self.current_rule += 1
                self.length_start = 1
                if self.current_rule > 7:
                    return (None, 0, 0)
            
            # 每次分配一个长度
            length = self.length_start
            self.length_start += 1
            return (self.current_rule, length, length)

    def get_current_rule(self) -> int:
        with self._lock:
            return self.current_rule


class SharedStateProcessMode:
    """多进程模式下的共享状态实现"""
    
    def __init__(self, worker_count: int = 3):
        import multiprocessing
        
        self.found = multiprocessing.Value('b', False)
        self.found_worker_id = multiprocessing.Value('i', -1)
        self.found_password = multiprocessing.Array('c', 256)
        
        self.terminate_flag = multiprocessing.Value('b', False)
        self.paused = multiprocessing.Value('b', False)
        
        self.attempts = [multiprocessing.Value('q', 0) for _ in range(worker_count)]
        
        # 动态任务队列
        self.current_rule = multiprocessing.Value('i', 0)
        self.length_start = multiprocessing.Value('i', 1)
        
        # 弱口令库专用
        self.dict_lines_loaded = multiprocessing.Value('b', False)
        self.dict_total_lines = multiprocessing.Value('q', 0)
        self.dict_next_line = multiprocessing.Value('q', 0)
        self.dict_active_workers = multiprocessing.Value('i', 0)
        
        self._task_lock = multiprocessing.Lock()
        
        self.start_time = multiprocessing.Value('d', 0.0)
        self.end_time = multiprocessing.Value('d', 0.0)

    def reset(self, worker_count: int = 3):
        with self.found.get_lock():
            self.found.value = False
            self.found_password.value = b"\x00"
            self.found_worker_id.value = -1
            self.terminate_flag.value = False
            self.paused.value = False
            self.current_rule.value = 0
            self.length_start.value = 1
            self.dict_lines_loaded.value = False
            self.dict_total_lines.value = 0
            self.dict_next_line.value = 0
            self.dict_active_workers.value = 0
            self.start_time.value = 0.0
            self.end_time.value = 0.0
            for i in range(len(self.attempts)):
                self.attempts[i].value = 0

    def set_found(self, password: str, worker_id: int):
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
        return self.terminate_flag.value or self.found.value

    def pause(self):
        self.paused.value = True

    def resume(self):
        self.paused.value = False

    def is_paused(self) -> bool:
        return self.paused.value

    # 动态任务队列方法
    def set_dict_total(self, total: int):
        """设置弱口令库总行数"""
        with self._task_lock:
            self.dict_total_lines.value = total
            self.dict_lines_loaded.value = True

    def get_next_task(self, worker_count: int, max_len: int = 8) -> tuple:
        """获取下一个任务块
        
        Returns:
            (rule_id, min_len, max_len) 或 (None, 0, 0) 表示无任务
            (0, -1, -1) 表示等待中（字典处理中或规则切换中）
        """
        with self._task_lock:
            if self.terminate_flag.value or self.found.value:
                return (None, 0, 0)
            
            # 检查当前规则是否有更多任务
            if self.current_rule.value == 0:
                # 弱口令库
                if not self.dict_lines_loaded.value:
                    return (0, -1, -1)  # 等待字典加载
                if self.dict_next_line.value >= self.dict_total_lines.value:
                    # 所有字典块已分配，但需等待活跃worker完成
                    if self.dict_active_workers.value <= 0:
                        self.current_rule.value = 1
                        self.length_start.value = 1
                    else:
                        return (0, -1, -1)  # 等待活跃worker完成
                else:
                    chunk = max(100, self.dict_total_lines.value // (worker_count * 2))
                    start = self.dict_next_line.value
                    end = min(start + chunk, self.dict_total_lines.value)
                    self.dict_next_line.value = end
                    self.dict_active_workers.value += 1
                    return (0, start, end)
            
            # 枚举规则：按长度分段
            if self.length_start.value > max_len:
                self.current_rule.value += 1
                self.length_start.value = 1
                if self.current_rule.value > 7:
                    return (None, 0, 0)
            
            length = self.length_start.value
            self.length_start.value += 1
            return (self.current_rule.value, length, length)

    def get_current_rule(self) -> int:
        return self.current_rule.value


def create_shared_state(worker_count: int, use_multiprocessing: bool):
    if use_multiprocessing:
        return SharedStateProcessMode(worker_count)
    else:
        return SharedStateThreadMode(worker_count)
