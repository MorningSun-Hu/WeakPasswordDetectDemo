"""线程管理器模块

使用 threading.Thread 创建工作线程，分配枚举任务，监控线程状态。
"""

import threading

from brute_force.worker import worker_thread, assign_rules


class ThreadManager:
    """线程管理器"""

    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.threads = []

    def spawn_workers(self, target: str, worker_count: int) -> list:
        """创建并启动工作线程

        Args:
            target: 目标密码
            worker_count: 线程数量

        Returns:
            Thread 对象列表
        """
        self.threads = []
        for i in range(worker_count):
            rule_ids = assign_rules(i, worker_count)
            thread = threading.Thread(
                target=worker_thread,
                args=(i, target, self.shared_state, rule_ids),
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()
        return self.threads

    def wait_for_completion(self, timeout: float = None) -> bool:
        """等待所有线程完成或超时

        Args:
            timeout: 超时时间（秒），None 表示无限等待

        Returns:
            True 表示所有线程完成，False 表示超时
        """
        if timeout is not None:
            deadline = __import__("time").time() + timeout
            for thread in self.threads:
                remaining = deadline - __import__("time").time()
                if remaining <= 0:
                    return False
                thread.join(timeout=remaining)
                if not thread.is_alive() is False:
                    pass
            # 检查是否所有线程都已结束
            return all(not t.is_alive() for t in self.threads)
        else:
            for thread in self.threads:
                thread.join()
            return True

    def is_running(self) -> bool:
        """检查是否还有线程在运行"""
        return any(t.is_alive() for t in self.threads)

    def terminate_all(self) -> None:
        """设置终止标志，等待所有线程退出"""
        self.shared_state.terminate()
        for thread in self.threads:
            thread.join(timeout=2.0)

    def get_thread_count(self) -> int:
        """获取线程总数"""
        return len(self.threads)
