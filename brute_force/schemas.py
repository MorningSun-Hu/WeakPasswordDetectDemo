"""Pydantic 数据模型定义

定义 Web API 的请求/响应 Schema，提供类型安全验证。
"""

from pydantic import BaseModel, Field
from typing import Optional


class StartRequest(BaseModel):
    """启动破解任务请求体"""
    password: str = Field(..., min_length=1, description="目标密码")
    worker_count: int = Field(0, ge=0, description="Worker数量，0表示自动检测")


class StartResponse(BaseModel):
    """启动破解任务响应"""
    status: str
    worker_count: int
    mode: str = Field(description="运行模式: process 或 thread")
    physical_cores: int


class StatusResponse(BaseModel):
    """任务状态查询响应"""
    running: bool
    found: bool
    workers: list
    total_attempts: int
    elapsed: float
    mode: str


class StopResponse(BaseModel):
    """停止任务响应"""
    status: str
    total_attempts: int = 0
    elapsed: float = 0.0


class ResultResponse(BaseModel):
    """任务结果查询响应"""
    found: bool
    password: Optional[str] = None
    attempts: int = 0
    elapsed: float = 0.0
    worker_id: int = -1
