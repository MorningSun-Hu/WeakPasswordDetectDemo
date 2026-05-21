"""Web UI 回调实现

实现 UICallback 协议，将引擎事件推送到异步队列供 WebSocket 使用。
"""

import asyncio
from typing import Optional, Callable, Any
from queue import Queue, Empty

from brute_force.ui_interface import UICallback


class WebCallback(UICallback):
    """Web UI 回调实现

    将引擎的同步回调事件转换为异步消息队列，供 WebSocket 端消费。
    """

    def __init__(self):
        self._queue: Queue = Queue()
        self._latest_status: Optional[dict] = None
        self._result: Optional[dict] = None

    def on_started(self, target_length: int, worker_count: int, cpu_count: int, is_process: bool) -> None:
        """破解任务开始"""
        msg = {
            "type": "started",
            "data": {
                "target_length": target_length,
                "worker_count": worker_count,
                "cpu_count": cpu_count,
                "mode": "process" if is_process else "thread",
            }
        }
        self._queue.put(msg)

    def on_progress(self, status: dict) -> None:
        """进度更新"""
        self._latest_status = status.copy()
        msg = {
            "type": "progress",
            "data": status.copy()
        }
        self._queue.put(msg)

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        """密码找到"""
        self._result = {
            "found": True,
            "password": password,
            "attempts": attempts,
            "elapsed": elapsed,
            "worker_id": worker_id,
        }
        msg = {
            "type": "found",
            "data": self._result.copy()
        }
        self._queue.put(msg)

    def on_terminated(self, attempts: int, elapsed: float) -> None:
        """用户提前终止"""
        self._result = {
            "found": False,
            "attempts": attempts,
            "elapsed": elapsed,
        }
        msg = {
            "type": "terminated",
            "data": self._result.copy()
        }
        self._queue.put(msg)

    def on_error(self, message: str) -> None:
        """错误发生"""
        msg = {
            "type": "error",
            "data": {"message": message}
        }
        self._queue.put(msg)

    def get_message(self, timeout: float = 0.1) -> Optional[dict]:
        """从队列获取一条消息（非阻塞）"""
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def get_latest_status(self) -> Optional[dict]:
        """获取最新的进度状态"""
        return self._latest_status

    def get_result(self) -> Optional[dict]:
        """获取最终结果"""
        return self._result
