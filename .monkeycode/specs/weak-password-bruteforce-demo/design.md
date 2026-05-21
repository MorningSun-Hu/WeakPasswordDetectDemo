# 弱口令枚举暴力破解演示程序 - 技术设计文档

> **状态**: Phase 1 已完成（核心引擎 + CLI Interface）
> **最后更新**: 2026-05-21

## 1. 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| 编程语言 | Python 3.13+ (free-threading) | 无 GIL 版本，支持真正的多线程并发 |
| 包管理器 | uv | 快速、现代的 Python 包管理器 |
| 并发方案 | `multiprocessing` (主) / `threading` (降级) | 根据 CPU 物理核心数动态选择：>2 核使用多进程，否则降级为多线程 |
| 硬件检测 | `psutil` 库 | 获取物理核心数、逻辑线程数 |
| 进程间通信 | 共享内存 (multiprocessing) / 原生共享 (threading) | 多进程使用 `multiprocessing.Value/Array`，多线程直接共享内存 |
| 核心引擎 | 与 UI 解耦 | 枚举引擎通过回调/事件接口与 UI 交互 |
| CLI UI | 控制台 ANSI 刷新 | Windows 终端支持 VT100 转义序列实现原地刷新 |
| Web UI（预留） | 异步 API 接口层 | 预留 REST API / WebSocket 接口，供前端调用 |

**为什么使用动态并发策略？**
- **多进程 (`multiprocessing`)**：在物理核心数 > 2 时优先使用，充分利用多核 CPU 的并行计算能力，规避 Python GIL 的潜在限制（即使在 free-threading 模式下，多进程也能获得更好的隔离性）
- **多线程 (`threading`)**：在低核设备（≤2 核）上作为降级方案，避免进程创建开销，利用 free-threading 的无 GIL 特性实现轻量并发

**为什么选择 Python 3.13 free-threading？**
- GIL 被移除，多线程可以真正并行执行 CPU 密集型任务
- 内存开销更低（无需为每个进程复制内存）
- 在降级到多线程模式时，仍然能获得真正的并发性能

## 2. 系统架构

```
┌────────────────────────────────────────────────────────────┐
│                      UI 层 (可替换)                         │
│  ┌──────────────────┐           ┌──────────────────────┐   │
│  │   CLI Interface  │           │   Web API (预留)     │   │
│  │  (当前实现)      │           │   REST / WebSocket   │   │
│  └────────┬─────────┘           └──────────┬───────────┘   │
│           │                                │               │
│           └────────────┬───────────────────┘               │
│                        ▼                                   │
│              ┌──────────────────┐                          │
│              │   UI Callback    │                          │
│              │   Interface      │                          │
│              └────────┬─────────┘                          │
│                       │                                    │
│  ┌────────────────────┼────────────────────┐              │
│  │              核心枚举引擎                │              │
│  │  ┌──────────┐  ┌───┴────┐  ┌──────────┐ │              │
│  │  │BruteForce│─▶│ Worker │─▶│ EnumRules│ │              │
│  │  │ Engine   │  │Manager │  │ Generator│ │              │
│  │  └──────────┘  └────────┘  └──────────┘ │              │
│  └─────────────────────────────────────────┘              │
│                       │                                    │
│           ┌───────────┴───────────┐                       │
│           ▼                       ▼                       │
│     ┌──────────┐           ┌──────────┐                   │
│     │ Worker 1 │  ...      │ Worker N │                   │
│     │ Process/ │           │ Process/ │                   │
│     │ Thread   │           │ Thread   │                   │
│     └──────────┘           └──────────┘                   │
└────────────────────────────────────────────────────────────┘
```

## 3. 核心模块设计

### 3.1 枚举引擎 (brute_force/engine.py)

**职责**：
- 管理破解任务的生命周期（启动、暂停、终止）
- 根据 CPU 硬件自动选择并发模式（多进程/多线程）
- 创建工作进程/线程池
- 汇总各 Worker 状态，通过回调接口通知 UI

**关键类**：

```python
class BruteForceEngine:
    """核心枚举引擎，与 UI 无关"""
    
    def __init__(self, worker_count=0, callback=None):
        self.worker_count = worker_count  # 0 表示自动检测
        self.use_multiprocessing = True   # 根据硬件自动调整
        self.physical_cores = 0
        self.logical_threads = 0
        self.callback = callback
        self.shared_state = create_shared_state(...)
        self.manager = ProcessManager(...) 或 ThreadManager(...)
        
    def _setup_hardware_config(self, requested_count: int):
        """检测硬件并决定运行模式
        - 如果物理核心 > 2: 使用 multiprocessing，Worker数 = 核心数 - 1
        - 如果物理核心 <= 2: 使用 threading，Worker数 = 逻辑线程数 - 1
        """
        
    def start(self, target_password: str) -> None:
        """启动破解任务"""
        
    def terminate(self) -> None:
        """终止所有工作进程/线程"""
        
    def get_status(self) -> dict:
        """获取当前状态快照（供 Web API 轮询使用）"""
        
    def _cleanup_old_logs(self) -> None:
        """清理旧的 worker 日志文件"""
```

### 3.2 Worker 管理器 (brute_force/process_manager.py & thread_manager.py)

**职责**：
- `ProcessManager`: 使用 `multiprocessing.Process` 创建工作进程
- `ThreadManager`: 使用 `threading.Thread` 创建工作线程
- 分配枚举任务区间给各 Worker
- 监控 Worker 状态

**关键类**：

```python
class ProcessManager:
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        
    def spawn_workers(self, target: str, worker_count: int) -> list:
        """创建并启动工作进程"""
        
    def is_running(self) -> bool:
        """检查是否有进程存活"""
        
    def terminate_all(self) -> None:
        """终止所有进程"""

class ThreadManager:
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        
    def spawn_workers(self, target: str, worker_count: int) -> list:
        """创建并启动工作线程"""
        
    def is_running(self) -> bool:
        """检查是否有线程存活"""
        
    def terminate_all(self) -> None:
        """终止所有线程"""
```

### 3.3 共享状态适配 (brute_force/shared_state.py)

**结构**：

```python
class SharedStateProcessMode:
    """多进程模式共享状态（使用 multiprocessing.Value/Array）"""
    def __init__(self, worker_count):
        self.found = multiprocessing.Value('i', 0)
        self.attempts = [multiprocessing.Value('i', 0) for _ in range(worker_count)]
        self.current_rule = [multiprocessing.Value('i', 0) for _ in range(worker_count)]
        self.start_time = multiprocessing.Value('d', 0.0)
        self.end_time = multiprocessing.Value('d', 0.0)
        # ...

class SharedStateThreadMode:
    """多线程模式共享状态（原生 Python 变量）"""
    def __init__(self, worker_count):
        self.found = False
        self.attempts = [0] * worker_count
        self.current_rule = [0] * worker_count
        self.start_time = 0.0
        self.end_time = 0.0
        # ...

def create_shared_state(worker_count: int, use_multiprocessing: bool):
    """工厂函数：根据并发模式返回对应的共享状态实例"""
```

**设计说明**：
- **多进程模式**：使用 `multiprocessing.Value/Array` 实现跨进程内存共享，通过 `val.get_lock()` 保护单个值
- **多线程模式**：直接使用 Python 原生列表和变量，通过 `threading.Lock` 保护关键区
- **统一接口**：两种模式提供相同的方法签名（`get_total_attempts()`, `get_elapsed()`, `set_found()`, `is_terminated()` 等），使引擎无需关心底层实现

### 3.4 枚举规则生成器 (brute_force/enum_rules.py)

**枚举规则与数量**：

| 规则编号 | 规则描述 | 字符集 | 长度 | 数量级 |
|---------|---------|--------|------|--------|
| 1 | 纯数字 | 0-9 | 1-8 | ~1.1*10^8 |
| 2 | 字母开头+数字 | a-zA-Z + 0-9 | 2-9 | ~5.7*10^9 |
| 3 | 数字+字母结尾 | 0-9 + a-zA-Z | 2-9 | ~5.7*10^9 |
| 4 | 数字+小写混合 | 0-9, a-z | 1-8 | ~2.9*10^12 |
| 5 | 数字+大小写混合 | 0-9, a-z, A-Z | 1-8 | ~2.2*10^14 |

**生成器设计**：

```python
class EnumGenerator:
    """密码枚举生成器，使用迭代器模式"""
    
    @staticmethod
    def digits(length: int):
        """生成指定长度的纯数字密码"""
        
    @staticmethod
    def letter_prefix_digit(letter: str, digit_len: int):
        """生成字母开头+数字的密码"""
        
    @staticmethod
    def digit_letter_suffix(digit_len: int, letter: str):
        """生成数字+字母结尾的密码"""
        
    @staticmethod
    def mixed(length: int, charset: str):
        """生成指定字符集的混合密码"""
        
    @staticmethod
    def all_rules():
        """按顺序返回所有枚举规则的迭代器"""
```

### 3.5 工作进程/线程入口 (brute_force/worker.py)

**职责**：
- 按分配的规则枚举密码
- 比对目标密码
- 更新共享状态
- 检查终止信号
- 生成诊断日志 (`worker_PID.log`)

**关键函数**：

```python
def worker_process(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作进程入口函数（多进程模式）"""
    
def worker_thread(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作线程入口函数（多线程模式）"""

def assign_rules(worker_id: int, total_workers: int) -> list:
    """按轮询策略分配规则给 Worker"""
```

**Worker 日志机制**：
- 每个 Worker 启动时立即创建 `worker_PID.log` 文件
- 记录启动、导入、规则执行、异常等关键步骤
- 每次任务开始前自动清理旧日志，只保留本次运行文件

## 4. UI 接口设计

### 4.1 UI 回调接口 (brute_force/ui_interface.py)

定义核心引擎与 UI 层交互的标准接口：

```python
class UICallback(Protocol):
    """UI 回调接口，CLI 和 Web UI 各自实现"""
    
    def on_started(self, target_length: int, worker_count: int, 
                   cpu_count: int, is_process: bool) -> None:
        """破解任务开始"""
        
    def on_progress(self, status: dict) -> None:
        """进度更新（定期回调）"""
        
    def on_found(self, password: str, attempts: int, 
                 elapsed: float, worker_id: int) -> None:
        """密码找到"""
        
    def on_terminated(self, attempts: int, elapsed: float) -> None:
        """用户提前终止"""
        
    def on_error(self, message: str) -> None:
        """错误发生"""
```

**状态字典格式**：

```python
status = {
    "running": True,           # 是否运行中
    "found": False,            # 是否已找到
    "workers": [
        {
            "id": 0,
            "attempts": 1234567,
            "rule_id": 1,      # 当前规则编号
        },
        # ...
    ],
    "total_attempts": 3703701,
    "elapsed": 83.5,           # 秒
    "mode": "process"          # "process" 或 "thread"
}
```

### 4.2 CLI 实现 (brute_force/cli.py)

```python
class CLIUI:
    """命令行界面实现 UICallback 接口"""
    
    def on_started(self, ...): ...
    def on_progress(self, status): ...
    def on_found(self, ...): ...
    def on_terminated(self, ...): ...
```

**Windows 终端刷新策略**：
- 通过 `ctypes` 调用 `SetConsoleMode` 启用 `ENABLE_VIRTUAL_TERMINAL_PROCESSING`
- 使用 ANSI 转义序列实现多行原地刷新：`\033[nA`（上移）、`\033[0J`（清除到末尾）
- 避免频繁清屏 (`cls`) 导致闪烁，保持标题区域固定，仅刷新进度区域

### 4.3 Web API 预留接口 (brute_force/web_api.py)

预留 FastAPI 接口框架，供后续 Web UI 使用：

```python
# 预留接口定义，暂不实现
# from fastapi import FastAPI

class WebAPI:
    """Web API 预留接口
    
    计划提供的 REST API 端点：
    - POST /api/v1/crack/start    - 启动破解任务
    - GET  /api/v1/crack/status   - 获取当前状态
    - POST /api/v1/crack/stop     - 终止破解任务
    - GET  /api/v1/crack/result   - 获取结果
    
    计划提供的 WebSocket 端点：
    - WS   /ws/crack/progress     - 实时推送进度
    """
    pass
```

## 5. 并发间共享设计

### 5.1 多进程模式 (Multiprocessing)

Windows 默认使用 `spawn` 模式创建子进程，需要确保：
- `main.py` 中包含 `multiprocessing.freeze_support()` 调用
- Worker 入口代码保护在 `if __name__ == '__main__':` 块中（由引擎内部管理）
- 传递给子进程的参数必须是可序列化的（pickleable）

```python
# 主进程创建共享状态
shared_state = SharedStateProcessMode(worker_count)

# 传递给工作进程（通过 spawn 参数）
proc = multiprocessing.Process(
    target=worker_process,
    args=(worker_id, target, shared_state, rule_ids)
)
proc.start()
```

### 5.2 多线程模式 (Threading)

Python 3.13 free-threading 模式下，所有线程共享同一进程的内存空间：

```python
# 主线程创建共享状态
shared_state = SharedStateThreadMode(worker_count)

# 传递给工作线程（直接引用）
thread = threading.Thread(
    target=worker_thread,
    args=(worker_id, target, shared_state, rule_ids)
)
thread.start()
```

### 5.3 同步机制

```python
# 工作进程/线程定期检查终止信号
if shared_state.is_terminated():
    return

# 多进程：使用 per-value lock
with shared_state.attempts[worker_id].get_lock():
    shared_state.attempts[worker_id].value += count

# 多线程：使用全局 threading.Lock
with shared_state._lock:
    shared_state.attempts[worker_id] += count
```

## 6. 进度显示设计

### 6.1 CLI 显示效果

```
==================================================
  弱口令枚举暴力破解演示
==================================================
运行模式: 多进程 | 物理核心: 4 | 并发数: 3
目标密码: *** 位
按 Ctrl+C 提前终止
--------------------------------------------------

[Worker 0] 尝试次数: 1,234,567    规则: 纯数字
[Worker 1] 尝试次数: 1,234,567    规则: 字母开头+数字
[Worker 2] 尝试次数: 1,234,567    规则: 数字+字母结尾

累计尝试: 3,703,701
已用时间: 00:01:23
```

### 6.2 刷新策略

- 主进程每 500ms 读取共享状态并刷新显示
- **Windows 终端优化**：通过 `ctypes` 启用 ANSI 支持，使用 `\033[nA` 上移光标 + `\033[0J` 清除旧内容，实现原地刷新
- 标题区域固定不动，仅刷新进度区域，避免闪烁

## 7. 输入约束与提前终止机制

### 7.1 密码输入校验

为确保演示程序的枚举范围可控，对用户输入的密码进行格式校验：

- **允许字符**：仅限 ASCII 字母 (`a-z`, `A-Z`) 和数字 (`0-9`)。
- **拒绝符号**：如果检测到特殊符号（如 `!@#$%^&*()` 等），程序将拒绝输入并提示：
  ```text
  提示：本演示程序仅支持纯字母和数字密码。
  检测到不支持的符号: '!', '@' ...
  请重新输入。
  ```
- **校验逻辑**：使用 Python `string.ascii_letters` 和 `string.digits` 构建白名单。

### 7.2 提前终止机制

```python
import signal

def signal_handler(signum, frame):
    """处理 Ctrl+C"""
    engine.terminate()
    
signal.signal(signal.SIGINT, signal_handler)
```

## 8. 项目结构

```
weak-password-bruteforce/
├── pyproject.toml          # uv 项目配置
├── README.md
├── main.py                 # 程序入口 (含 multiprocessing.freeze_support)
├── brute_force/
│   ├── __init__.py
│   ├── engine.py           # BruteForceEngine 核心引擎 (动态并发调度)
│   ├── process_manager.py  # ProcessManager 多进程管理
│   ├── thread_manager.py   # ThreadManager 多线程管理
│   ├── shared_state.py     # SharedState 双模式共享状态
│   ├── worker.py           # worker_process/worker_thread 入口
│   ├── enum_rules.py       # EnumGenerator 枚举规则
│   ├── ui_interface.py     # UICallback 接口定义
│   ├── cli.py              # CLIUI 命令行界面 (ANSI 刷新)
│   └── web_api.py          # WebAPI 预留接口
└── tests/
    ├── __init__.py
    ├── test_enum_rules.py
    ├── test_shared_state.py
    └── test_engine.py
```

## 9. Windows 兼容性

### 9.1 Python 版本

- 最低要求：Python 3.13 (free-threading build)
- 访问方式：`python3.13t` 或通过 `uv run --python 3.13t`

### 9.2 多进程支持

Windows 使用 `spawn` 模式创建子进程，必须：
- `main.py` 中包含 `multiprocessing.freeze_support()` 调用
- Worker 日志使用文件输出（`worker_PID.log`），避免控制台输出缓冲或丢失

### 9.3 终端 ANSI 支持

通过 `ctypes.WinDLL('kernel32').SetConsoleMode` 启用 VT100 转义序列支持，确保 Win 7/10/11 均能正确刷新界面。

### 9.4 打包

使用 PyInstaller 打包为独立 exe：

```bash
uv run pyinstaller --onefile --name bruteforce main.py
```

生成的 exe 文件内置 Python 运行时，用户无需安装 Python。

## 10. 性能优化

### 10.1 硬件自适应并发

- 物理核心 > 2：使用多进程，Worker 数 = 核心数 - 1
- 物理核心 ≤ 2：降级为多线程，Worker 数 = 逻辑线程数 - 1

### 10.2 批量更新

工作进程本地计数累加到阈值（10000）后再写入共享内存，减少同步开销。

### 10.3 字符集预计算

枚举规则中使用预计算的字符集列表，避免重复创建。

### 10.4 Worker 日志清理

每次任务启动前自动清理旧的 `worker_*.log` 文件，避免磁盘空间占用。

## 11. 开发节点规划

根据模块依赖关系与功能演进，将项目划分为多个开发阶段。

### Phase 1: 核心及 CLI Interface 开发（已完成）

Phase 1 是项目的核心基础，实现了完整的枚举引擎、并发调度机制与命令行交互界面。

#### 1.1 基础核心层

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 1 | 项目骨架初始化 | `pyproject.toml`, `main.py`, `brute_force/__init__.py` | 无 | uv 项目初始化、入口文件 |
| 2 | 共享状态模块 | `brute_force/shared_state.py` | 无 | 双模式适配（Process/Thread）、`threading.Lock` 保护 |
| 3 | 枚举规则生成器 | `brute_force/enum_rules.py` | 无 | 5 种枚举规则的迭代器生成器 |

#### 1.2 引擎与并发层

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 4 | 工作线程/进程逻辑 | `brute_force/worker.py` | 任务 2、3 | 枚举循环、密码比对、批量更新共享计数、诊断日志 |
| 5 | 线程管理器 | `brute_force/thread_manager.py` | 任务 2、4 | 创建/监控/终止工作线程 |
| 6 | 进程管理器 | `brute_force/process_manager.py` | 任务 2、4 | `multiprocessing.Process` 创建与监控、spawn 兼容 |
| 7 | 硬件检测与模式切换 | `brute_force/engine.py` | psutil | 根据 CPU 核心数自动选择多进程/多线程 |
| 8 | 核心引擎生命周期 | `brute_force/engine.py` | 任务 2、5、6、7 | `BruteForceEngine` 启动、终止、回调调度 |

#### 1.3 UI 交互层

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 9 | UI 回调接口定义 | `brute_force/ui_interface.py` | 无 | `UICallback` Protocol 定义、状态字典格式 |
| 10 | CLI 界面实现 | `brute_force/cli.py` | 任务 9 | 控制台输入、ANSI 原地刷新、Ctrl+C 处理 |
| 11 | 密码输入校验 | `brute_force/cli.py` | 任务 10 | 白名单校验（字母+数字）、拒绝符号并提示 |

#### 1.4 Web 预留与测试层

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 12 | Web API 骨架 | `brute_force/web_api.py` | 任务 9 | REST 端点定义、WebSocket 框架（注释标记待实现） |
| 13 | 单元测试 | `tests/test_*.py` | 任务 1-11 | 枚举规则、共享状态并发安全、引擎流程 |

### Phase 2: Web API 开发（进行中）

Phase 2 将实现完整的后端 Web API 服务，包括 REST 接口与 WebSocket 实时推送。

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 14 | 基础设施搭建 | `brute_force/server.py`, `pyproject.toml` | Phase 1 | FastAPI/uvicorn 依赖、Pydantic 模型、CORS 配置 |
| 15 | REST API 实现 | `brute_force/server.py` | 任务 14 | 启动/停止/状态/结果接口、任务锁保护、异步引擎调度 |
| 16 | WebSocket 实时推送 | `brute_force/server.py` | 任务 14、15 | `WebCallback` 异步推送、连接管理、心跳检测 |

### Phase 3: 前端界面开发（规划中）

Phase 3 将实现可视化 Web 前端，提供用户交互界面。

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 17 | 前端界面开发 | `web/` 目录 | Phase 2 | 原生 HTML/JS + Tailwind CDN、进度可视化、任务控制 |

### Phase 4: 集成测试与优化（规划中）

Phase 4 将完成前后端联调、测试与性能优化。

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 18 | 集成测试 | `tests/test_web_*.py` | Phase 3 | REST/WebSocket 测试、并发冲突验证、跨域检查 |
| 19 | 性能优化 | 配置调整 | 任务 18 | WebSocket 推送频率优化、事件循环非阻塞验证 |

### 11.2 Phase 2: Web API 开发（进行中）

Phase 2 基于 FastAPI 实现完整的后端 Web API 服务。

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 14 | 基础设施搭建 | `server.py`, `pyproject.toml`, `schemas.py` | Phase 1 | FastAPI/uvicorn 依赖、Pydantic 模型、CORS 配置 |
| 15 | REST API 实现 | `server.py`, `callback.py` | 任务 14 | 启动/停止/状态/结果接口、任务锁、异步引擎调度 |
| 16 | WebSocket 实时推送 | `server.py` | 任务 14、15 | `WebCallback` 异步推送、连接管理、心跳检测 |

**Phase 2 技术架构更新**:

- **应用服务器**: FastAPI + Uvicorn (ASGI)
- **数据验证**: Pydantic v2 (`schemas.py`)
- **异步架构**: `ThreadPoolExecutor` 运行阻塞的 `BruteForceEngine`，避免阻塞事件循环
- **并发控制**: `asyncio.Lock` 保护任务状态，防止同时运行多个破解任务
- **回调适配**: `WebCallback` 实现 `UICallback` 接口，通过队列将引擎事件转发给 API 端点
- **跨域支持**: CORS 中间件配置 (`allow_origins=["*"]`)

### 执行依赖图

```
Phase 1:  [1]    [2]    [3]          (基础核心，可并行)
              ↓      ↓
           [4]     [5]     [9]        (引擎+并发+UI接口)
           ↓  ↙    ↓       ↓
         [6]      [7]     [10]        (进程管理+模式切换+CLI)
           ↓       ↓      ↓
            [8]         [11]          (引擎生命周期+输入校验)
             ↓          ↓
           [12]       [13]            (Web预留+测试)

Phase 2:                  [14] → [15] → [16]  (FastAPI→前端→集成)

Phase 3:                            [17] → [18] → [19]  (文档→打包→发布)
```

## 12. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Free-threading 兼容性 | 部分第三方库可能不支持 | 本程序仅使用标准库，无此风险 |
| 线程安全问题 | 共享状态竞争条件 | 使用 `threading.Lock` 保护关键区 |
| 枚举空间过大 | 规则 E 需要极长时间 | 提供提前终止，显示进度提示 |
| PyInstaller 包体积 | 包含完整 Python 运行时 | 使用 `--onefile` 和 strip 优化 |
