"""Web API 服务入口

提供 FastAPI 应用实例，实现完整的 REST API 与 WebSocket 端点，
并挂载前端静态文件服务。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from brute_force.schemas import StartRequest, StartResponse, StatusResponse, StopResponse, ResultResponse
from brute_force.engine import BruteForceEngine
from brute_force.callback import WebCallback
from brute_force.utils import validate_password
from brute_force.ws_manager import manager


# 静态文件目录路径
STATIC_DIR = Path(__file__).parent / "static"


# 全局状态
_app_state = {
    "engine": None,
    "callback": None,
    "task_lock": None,
    "executor": None,
}


def _run_engine(engine: BruteForceEngine, password: str, loop, lock) -> None:
    """在线程中运行引擎（阻塞调用）"""
    try:
        engine.start(password)
    finally:
        # 引擎结束后释放锁（需通过 call_soon_threadsafe 回到主线程释放 asyncio.Lock）
        # 使用 lock.locked() 检查避免与 stop_crack 中的 release 冲突导致 RuntimeError
        loop.call_soon_threadsafe(lambda: lock.release() if lock.locked() else None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _app_state["task_lock"] = asyncio.Lock()
    _app_state["executor"] = ThreadPoolExecutor(max_workers=1, thread_name_prefix="crack-engine")
    yield
    # 清理资源
    if _app_state.get("engine"):
        _app_state["engine"].terminate()
    if _app_state.get("executor"):
        _app_state["executor"].shutdown(wait=False)
    _app_state.clear()


app = FastAPI(
    title="弱口令破解演示 API",
    description="提供暴力破解任务的 REST API 与 WebSocket 实时推送",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")


@app.get("/")
async def serve_frontend():
    """服务前端页面"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "前端页面未找到"}


# API 路由


@app.post("/api/v1/crack/start", response_model=StartResponse)
async def start_crack(request: StartRequest):
    """启动破解任务"""
    lock = _app_state.get("task_lock")
    if not lock:
        raise HTTPException(status_code=503, detail="服务未就绪")

    # 密码格式校验
    is_valid, invalid_chars = validate_password(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"仅支持字母和数字，检测到: {', '.join(repr(c) for c in invalid_chars)}"
        )
    
    if len(request.password) > 8:
        raise HTTPException(
            status_code=400,
            detail="密码长度不能超过 8 位。超过 8 位的枚举可能需要极长时间。"
        )

    # 检查是否有任务正在运行
    if lock.locked():
        raise HTTPException(status_code=409, detail="任务运行中，请先停止当前任务再启动新任务")

    # 获取锁并启动引擎
    await lock.acquire()
    try:
        callback = WebCallback()
        engine = BruteForceEngine(worker_count=request.worker_count, callback=callback)
        
        _app_state["engine"] = engine
        _app_state["callback"] = callback

        executor = _app_state.get("executor")
        if not executor:
            raise HTTPException(status_code=503, detail="线程池未就绪")

        # 获取当前事件循环，用于在线程结束后释放锁
        loop = asyncio.get_running_loop()
        executor.submit(_run_engine, engine, request.password, loop, lock)

        return StartResponse(
            status="started",
            worker_count=engine.worker_count,
            mode="process" if engine.use_multiprocessing else "thread",
            physical_cores=engine.physical_cores,
        )
    except HTTPException:
        lock.release()
        raise
    except Exception as e:
        lock.release()
        raise HTTPException(status_code=500, detail=f"启动任务失败: {e}")


@app.get("/api/v1/crack/status", response_model=StatusResponse)
async def get_status():
    """获取当前任务状态"""
    engine = _app_state.get("engine")
    if not engine:
        return StatusResponse(running=False, found=False, workers=[], total_attempts=0, elapsed=0.0, mode="none")

    status = engine.get_status()
    return StatusResponse(
        running=status["running"],
        found=status["found"],
        workers=status["workers"],
        total_attempts=status["total_attempts"],
        elapsed=status["elapsed"],
        mode=status.get("mode", "unknown"),
    )


@app.post("/api/v1/crack/stop", response_model=StopResponse)
async def stop_crack():
    """停止当前任务"""
    engine = _app_state.get("engine")
    lock = _app_state.get("task_lock")

    if not engine or not lock or not lock.locked():
        return StopResponse(status="no_running_task")

    # 终止引擎
    engine.terminate()
    
    # 等待线程完成
    future = _app_state.get("future")
    if future:
        try:
            future.result(timeout=5.0)
        except Exception:
            pass

    # 释放锁
    try:
        lock.release()
    except RuntimeError:
        pass

    callback = _app_state.get("callback")
    if callback:
        result = callback.get_result()
        if result:
            return StopResponse(
                status="terminated",
                total_attempts=result.get("attempts", 0),
                elapsed=result.get("elapsed", 0.0),
            )

    return StopResponse(
        status="terminated",
        total_attempts=engine.get_status().get("total_attempts", 0),
        elapsed=engine.get_status().get("elapsed", 0.0),
    )


@app.post("/api/v1/crack/pause")
async def pause_crack():
    """暂停当前任务"""
    engine = _app_state.get("engine")
    if not engine:
        return {"status": "no_running_task"}
    
    engine.pause()
    return {"status": "paused"}


@app.post("/api/v1/crack/resume")
async def resume_crack():
    """恢复当前任务"""
    engine = _app_state.get("engine")
    if not engine:
        return {"status": "no_running_task"}
    
    engine.resume()
    return {"status": "resumed"}


@app.get("/api/v1/crack/result", response_model=ResultResponse)
async def get_result():
    """获取任务结果"""
    callback = _app_state.get("callback")
    if not callback:
        return ResultResponse(found=False)

    result = callback.get_result()
    if not result:
        return ResultResponse(found=False)

    return ResultResponse(
        found=result.get("found", False),
        password=result.get("password") if result.get("found") else None,
        attempts=result.get("attempts", 0),
        elapsed=result.get("elapsed", 0.0),
        worker_id=result.get("worker_id", -1),
    )


@app.websocket("/ws/crack/progress")
async def ws_progress(websocket: WebSocket):
    """WebSocket 端点：实时推送进度"""
    client_id = await manager.connect(websocket)
    try:
        while True:
            callback = _app_state.get("callback")
            
            # 优先检查是否有消息需要推送
            if callback:
                # 使用 asyncio.to_thread 安全地从同步 Queue 读取
                msg = await asyncio.to_thread(callback.get_message, timeout=0.1)
                if msg:
                    await manager.send_personal_message(client_id, msg)
                else:
                    # 无新消息时发送心跳
                    await manager.send_personal_message(client_id, {"type": "ping"})
            else:
                await manager.send_personal_message(client_id, {"type": "status", "data": {"running": False}})
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
