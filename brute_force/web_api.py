"""Web API 预留接口

定义未来 Web UI 需要使用的 REST API 端点和 WebSocket 推送框架。
当前仅保留接口定义和路由骨架，具体实现需在引入 FastAPI 后补充。

计划依赖：
- FastAPI >= 0.100.0
- uvicorn
- websockets (FastAPI 内置支持)
"""

# ============================================
# 预留 REST API 端点定义
# ============================================
#
# POST /api/v1/crack/start
#   请求体: { "password": "target_pwd", "worker_count": 3 }
#   响应: { "status": "started", "worker_count": 3 }
#
# GET  /api/v1/crack/status
#   响应: {
#     "running": true,
#     "found": false,
#     "workers": [...],
#     "total_attempts": 12345,
#     "elapsed": 1.5
#   }
#
# POST /api/v1/crack/stop
#   响应: { "status": "terminated", "total_attempts": 12345, "elapsed": 1.5 }
#
# GET  /api/v1/crack/result
#   响应: {
#     "found": true,
#     "password": "abc123",
#     "attempts": 5678,
#     "elapsed": 2.3,
#     "worker_id": 1
#   }


# ============================================
# 预留 WebSocket 端点定义
# ============================================
#
# WS   /ws/crack/progress
#   推送消息: {
#     "type": "progress",
#     "data": { "workers": [...], "total_attempts": 12345, "elapsed": 1.5 }
#   }
#   或: { "type": "found", "data": { "password": "...", ... } }
#   或: { "type": "terminated", "data": { ... } }


class WebAPI:
    """Web API 路由骨架

    未来实现方式示例（使用 FastAPI）：

    ```python
    from fastapi import FastAPI, WebSocket
    from brute_force.engine import BruteForceEngine
    from brute_force.shared_state import SharedState

    app = FastAPI(title="弱口令破解演示 API")
    engine: BruteForceEngine | None = None

    @app.post("/api/v1/crack/start")
    async def start_crack(password: str, worker_count: int = 3):
        global engine
        engine = BruteForceEngine(worker_count=worker_count, callback=WebCallback())
        # 在线程中启动引擎，避免阻塞 API
        import threading
        threading.Thread(target=engine.start, args=(password,), daemon=True).start()
        return {"status": "started", "worker_count": worker_count}

    @app.get("/api/v1/crack/status")
    async def get_status():
        if engine:
            return engine.get_status()
        return {"running": False}

    @app.post("/api/v1/crack/stop")
    async def stop_crack():
        if engine:
            engine.terminate()
            return {"status": "terminated"}
        return {"status": "no_running_task"}

    @app.websocket("/ws/crack/progress")
    async def ws_progress(websocket: WebSocket):
        await websocket.accept()
        # 定期推送引擎状态到 WebSocket
        while True:
            if engine:
                status = engine.get_status()
                await websocket.send_json({"type": "progress", "data": status})
                if not status["running"]:
                    break
            await asyncio.sleep(0.5)
    ```

    注意：
    1. 引擎启动需要在线程池中运行，避免阻塞 FastAPI 事件循环
    2. 需要实现 WebCallback 类，将引擎事件通过 WebSocket 推送给客户端
    3. 需添加 CORS 中间件以支持跨域请求
    """
    pass


class WebCallback:
    """Web UI 回调预留实现

    未来将引擎状态变化通过 WebSocket 实时推送给前端。
    """

    def __init__(self):
        self.active_connections = []

    def on_started(self, target_length: int, worker_count: int, cpu_count: int, is_process: bool) -> None:
        pass

    def on_progress(self, status: dict) -> None:
        # for conn in self.active_connections:
        #     await conn.send_json({"type": "progress", "data": status})
        pass

    def on_found(self, password: str, attempts: int, elapsed: float, worker_id: int) -> None:
        pass

    def on_terminated(self, attempts: int, elapsed: float) -> None:
        pass

    def on_error(self, message: str) -> None:
        pass
