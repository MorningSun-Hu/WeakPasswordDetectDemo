# 弱口令枚举暴力破解演示程序 - 技术设计文档

## 1. 技术选型

| 项目 | 选择 | 说明 |
|------|------|------|
| 编程语言 | Python 3.13+ (free-threading) | 无 GIL 版本，支持真正的多线程并发 |
| 包管理器 | uv | 快速、现代的 Python 包管理器 |
| 并发方案 | `threading` 标准库 | Python 3.13 free-threading 模式下无 GIL，多线程可真正并行执行 |
| 进程间通信 | 不适用（单进程多线程） | 线程间共享内存，无需跨进程通信 |
| 核心引擎 | 与 UI 解耦 | 枚举引擎通过回调/事件接口与 UI 交互 |
| CLI UI | 控制台刷新 | 命令行交互界面 |
| Web UI（预留） | 异步 API 接口层 | 预留 REST API / WebSocket 接口，供前端调用 |

**为什么选择 Python 3.13 free-threading？**
- Python 3.13 提供了 experimental free-threading 构建（通过 `python3.13t` 访问）
- GIL 被移除，多线程可以真正并行执行 CPU 密集型任务
- 相比多进程，线程间共享状态更简单，无需序列化
- 内存开销更低（无需为每个进程复制内存）

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
│  │  │BruteForce│─▶│ Thread │─▶│ EnumRules│ │              │
│  │  │ Engine   │  │ Pool   │  │ Generator│ │              │
│  │  └──────────┘  └────────┘  └──────────┘ │              │
│  └─────────────────────────────────────────┘              │
│                       │                                    │
│           ┌───────────┴───────────┐                       │
│           ▼                       ▼                       │
│     ┌──────────┐           ┌──────────┐                   │
│     │ Worker 1 │  ...      │ Worker N │                   │
│     │ Thread   │           │ Thread   │                   │
│     └──────────┘           └──────────┘                   │
└────────────────────────────────────────────────────────────┘
```

## 3. 核心模块设计

### 3.1 枚举引擎 (brute_force/engine.py)

**职责**：
- 管理破解任务的生命周期（启动、暂停、终止）
- 创建工作进程池
- 汇总各进程状态，通过回调接口通知 UI

**关键类**：

```python
class BruteForceEngine:
    """核心枚举引擎，与 UI 无关"""
    
    def __init__(self, worker_count=3, progress_callback=None):
        self.worker_count = worker_count
        self.callback = progress_callback  # UI 回调接口
        self.shared_state = SharedState()
        self.workers = []
        
    def start(self, target_password: str) -> None:
        """启动破解任务"""
        
    def terminate(self) -> None:
        """终止所有工作进程"""
        
    def get_status(self) -> dict:
        """获取当前状态快照（供 Web API 轮询使用）"""
```

### 3.2 线程管理器 (brute_force/thread_manager.py)

**职责**：
- 使用 `threading.Thread` 创建工作线程
- 分配枚举任务区间给各线程
- 监控线程状态

**关键类**：

```python
class ThreadManager:
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        
    def spawn_workers(self, target: str, worker_count: int) -> list:
        """创建并启动工作线程"""
        
    def wait_for_completion(self, timeout: float = None) -> bool:
        """等待任意线程完成或超时"""
        
    def terminate_all(self) -> None:
        """终止所有线程"""
```

### 3.3 枚举规则生成器 (brute_force/enum_rules.py)

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

### 3.4 共享状态 (brute_force/shared_state.py)

**结构**：

```python
import threading

class SharedState:
    """多线程共享状态（Python 3.13 free-threading 模式）"""
    
    def __init__(self, worker_count: int = 3):
        # 使用 threading.Lock 保护共享状态
        self._lock = threading.Lock()
        
        # 是否已找到密码
        self.found = False
        self.found_password = ""
        self.found_worker_id = -1
        
        # 各线程的尝试次数
        self.attempts = [0] * worker_count
        
        # 终止标志（用户提前终止）
        self.terminate_flag = False
        
        # 各线程当前正在执行的规则编号
        self.current_rule = [0] * worker_count
        
        # 任务开始时间
        self.start_time = 0.0
        self.end_time = 0.0
```

**优势**：
- 无需 `multiprocessing.Value/Array` 的复杂 API
- 直接使用 Python 原生数据类型
- `threading.Lock` 提供轻量级同步
- 线程间直接共享内存，无需序列化

### 3.5 工作线程 (brute_force/worker.py)

**职责**：
- 按分配的规则枚举密码
- 比对目标密码
- 更新共享状态
- 检查终止信号

**关键函数**：

```python
def worker_thread(worker_id: int, target: str, 
                  shared_state: SharedState, rules: list) -> None:
    """工作线程入口函数"""
    
def check_and_update(candidate: str, target: str, 
                     worker_id: int, shared_state: SharedState) -> bool:
    """比对密码，找到则更新共享状态并返回 True"""
```

## 4. UI 接口设计

### 4.1 UI 回调接口 (brute_force/ui_interface.py)

定义核心引擎与 UI 层交互的标准接口：

```python
class UICallback(Protocol):
    """UI 回调接口，CLI 和 Web UI 各自实现"""
    
    def on_started(self, target_password: str, worker_count: int) -> None:
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
    "workers": [
        {
            "id": 0,
            "attempts": 1234567,
            "current_rule": 1,  # 当前规则编号
        },
        # ...
    ],
    "total_attempts": 3703701,
    "elapsed": 83.5,           # 秒
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

## 5. 线程间共享设计

### 5.1 共享内存

Python 3.13 free-threading 模式下，所有线程共享同一进程的内存空间：

```python
# 主线程创建共享状态
shared_state = SharedState()

# 传递给工作线程（直接引用，无需特殊序列化）
thread = threading.Thread(
    target=worker_thread,
    args=(worker_id, target, shared_state, assigned_rules)
)
thread.start()
```

### 5.2 同步机制

```python
# 工作线程定期检查终止信号
if shared_state.found or shared_state.terminate_flag:
    return

# 使用锁保护共享状态更新
BATCH_SIZE = 10000
local_count = 0
for candidate in generator:
    local_count += 1
    if local_count >= BATCH_SIZE:
        with shared_state._lock:
            shared_state.attempts[worker_id] += local_count
        local_count = 0
```

## 6. 进度显示设计

### 6.1 CLI 显示效果

```
========================================
  弱口令枚举暴力破解演示
========================================
枚举进程: 3 个运行中

[Worker 1] 尝试次数: 1,234,567    规则: 纯数字
[Worker 2] 尝试次数: 1,234,567    规则: 数字+字母结尾
[Worker 3] 尝试次数: 1,234,567    规则: 数字+小写混合

累计尝试: 3,703,701
已用时间: 00:01:23
按 Ctrl+C 提前终止
========================================
```

### 6.2 刷新策略

- 主进程每 500ms 读取共享状态并刷新显示
- 使用控制台光标定位实现原地刷新
- Windows 兼容：使用 `os.system('cls')` 或 ANSI 转义序列

## 7. 提前终止机制

```python
import signal

def signal_handler(signum, frame):
    """处理 Ctrl+C"""
    shared_state.terminate_flag.value = True
    
signal.signal(signal.SIGINT, signal_handler)
# Windows 额外处理
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, False)
```

## 8. 项目结构

```
weak-password-bruteforce/
├── pyproject.toml          # uv 项目配置
├── README.md
├── main.py                 # 程序入口
├── brute_force/
│   ├── __init__.py
│   ├── engine.py           # BruteForceEngine 核心引擎
│   ├── thread_manager.py   # ThreadManager 线程管理
│   ├── shared_state.py     # SharedState 共享状态
│   ├── worker.py           # worker_thread 工作线程入口
│   ├── enum_rules.py       # EnumGenerator 枚举规则
│   ├── ui_interface.py     # UICallback 接口定义
│   ├── cli.py              # CLIUI 命令行界面
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

### 9.2 打包

使用 PyInstaller 打包为独立 exe：

```bash
uv run pyinstaller --onefile --name bruteforce main.py
```

生成的 exe 文件内置 Python 运行时，用户无需安装 Python。

### 9.3 多线程兼容性

Python 3.13 free-threading 模式在 Windows 上完全支持 `threading` 模块，无需特殊处理。

## 10. 性能优化

### 10.1 批量更新

工作进程本地计数累加到阈值后再写入共享内存，减少跨进程同步开销。

### 10.2 字符集预计算

枚举规则中使用预计算的字符集列表，避免重复创建：

```python
DIGITS = [str(i) for i in range(10)]
LOWERCASE = [chr(c) for c in range(ord('a'), ord('z') + 1)]
UPPERCASE = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
```

### 10.3 密码比对优化

```python
# 直接字符串比对，Python 内部已优化
if candidate == target:
    # found
```

## 11. 任务分解

根据模块依赖关系，将实现工作分解为以下子任务，按优先级排序：

### P0 - 基础核心（无外部依赖，可并行开始）

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 1 | 项目骨架初始化 | `pyproject.toml`, `main.py`, `brute_force/__init__.py` | 无 | uv 项目初始化、入口文件 |
| 2 | 共享状态模块 | `brute_force/shared_state.py` | 无 | `threading.Lock` 保护共享状态 |
| 3 | 枚举规则生成器 | `brute_force/enum_rules.py` | 无 | 5 种枚举规则的迭代器生成器 |

### P1 - 引擎与界面（核心功能，按依赖顺序推进）

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 4 | 工作线程逻辑 | `brute_force/worker.py` | 任务 2、3 | 枚举循环、密码比对、批量更新共享计数 |
| 5 | UI 回调接口定义 | `brute_force/ui_interface.py` | 无 | `UICallback` Protocol 定义、状态字典格式 |
| 6 | 线程管理器 | `brute_force/thread_manager.py` | 任务 2、4 | 创建/监控/终止工作线程 |
| 7 | 核心引擎 | `brute_force/engine.py` | 任务 2、5、6 | `BruteForceEngine` 生命周期管理、回调调度 |
| 8 | CLI 界面 | `brute_force/cli.py` | 任务 5 | 控制台输入、进度刷新、Ctrl+C 处理 |

### P2 - Web API 预留（接口框架）

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 9 | Web API 骨架 | `brute_force/web_api.py` | 任务 5 | REST 端点定义、WebSocket 框架（注释标记待实现） |

### P3 - 测试与打包（收尾）

| # | 子任务 | 产出文件 | 依赖 | 说明 |
|---|--------|----------|------|------|
| 10 | 单元测试 | `tests/test_*.py` | 任务 1-8 | 枚举规则、共享状态并发安全、引擎流程 |
| 11 | 项目文档 | `README.md` | 任务 8 | 使用说明、uv 环境要求、构建打包指南 |
| 12 | PyInstaller 打包 | 打包配置 | 任务 8 | `--onefile` 打包验证 |

### 执行依赖图

```
P0:  [1]    [2]    [3]          (可并行)
          ↓      ↓
P1:        [4]    [5]
           ↓  ↙   ↓
         [6]     [5]
          ↓     ↙
         [7]
          ↓
         [8]
          ↓
P2:      [9]          (可与 P3 并行)
          ↓
P3:     [10] → [11] → [12]
```

### 推荐执行顺序

1. 先完成 P0 的三个任务（1、2、3），它们无依赖可并行开发
2. P1 按 4→5→6→7→8 顺序推进
3. P2（任务 9）可在任务 8 完成后并行于 P3 进行
4. P3 的测试和打包在核心功能完成后执行

## 12. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Free-threading 兼容性 | 部分第三方库可能不支持 | 本程序仅使用标准库，无此风险 |
| 线程安全问题 | 共享状态竞争条件 | 使用 `threading.Lock` 保护关键区 |
| 枚举空间过大 | 规则 E 需要极长时间 | 提供提前终止，显示进度提示 |
| PyInstaller 包体积 | 包含完整 Python 运行时 | 使用 `--onefile` 和 strip 优化 |
