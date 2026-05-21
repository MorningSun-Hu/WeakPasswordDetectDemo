"""Web API 服务入口

提供 FastAPI 应用实例，实现完整的 REST API 与 WebSocket 端点。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from brute_force.schemas import StartRequest, StartResponse, StatusResponse, StopResponse, ResultResponse
from brute_force.engine import BruteForceEngine
from brute_force.callback import WebCallback
from brute_force.utils import validate_password


# 全局状态
_app_state = {
    "engine": None,
    "callback": None,
    "task_lock": None,
    "executor": None,
}


def _run_engine(engine: BruteForceEngine, password: str) -> None:
    """在线程中运行引擎（阻塞调用）"""
    try:
        engine.start(password)
    finally:
        pass


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

        executor.submit(_run_engine, engine, request.password)

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
