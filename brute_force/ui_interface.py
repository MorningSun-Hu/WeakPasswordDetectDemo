"""UI 回调接口定义

定义核心引擎与 UI 层交互的标准接口。
CLI 和 Web UI 各自实现该接口。
"""

from typing import Protocol


class UICallback(Protocol):
    """UI 回调接口

    所有 UI 实现（CLI、Web 等）必须实现此接口。
    """

    def on_started(self, target_length: int, worker_count: int, cpu_count: int) -> None:
        """破解任务开始

        Args:
            target_length: 目标密码长度（不显示明文）
            worker_count: 工作线程数量
            cpu_count: CPU 核心数
        """
        ...

    def on_progress(self, status: dict) -> None:
        """进度更新（定期回调）

        Args:
            status: 状态字典，格式如下：
                {
                    "running": True,
                    "workers": [
                        {"id": 0, "attempts": 12345, "rule_id": 1},
                        ...
                    ],
                    "total_attempts": 37035,
                    "elapsed": 1.5,
                }
        """
        ...

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        """密码找到

        Args:
            password: 找到的密码
            attempts: 总尝试次数
            elapsed: 总用时（秒）
            worker_id: 找到密码的线程编号
        """
        ...

    def on_terminated(self, attempts: int, elapsed: float) -> None:
        """用户提前终止

        Args:
            attempts: 截止终止时的总尝试次数
            elapsed: 截止终止时的用时（秒）
        """
        ...

    def on_error(self, message: str) -> None:
        """错误发生

        Args:
            message: 错误信息
        """
        ...
