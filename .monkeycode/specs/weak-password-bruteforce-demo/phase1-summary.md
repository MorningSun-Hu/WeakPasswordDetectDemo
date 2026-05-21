# 弱口令枚举暴力破解演示程序 - Phase 1 项目总结

> **阶段**: Phase 1 - 核心及 CLI Interface 开发
> **创建日期**: 2026-05-20
> **最后更新**: 2026-05-21
> **状态**: 已完成

---

## 1. Phase 1 概述

Phase 1 聚焦于核心枚举引擎与 CLI 交互界面的开发，实现了完整的暴力破解演示程序基础功能。

### 阶段目标

1. 实现可动态选择并发模式的多进程/多线程枚举引擎
2. 支持用户输入目标密码并显示实时破解进度
3. 提供稳定的 Windows 终端体验（ANSI 刷新、Ctrl+C 终止）
4. 完成基础测试与文档建设

### 交付成果

- 完整的枚举引擎 (`brute_force/engine.py`)
- 双模式共享状态 (`brute_force/shared_state.py`)
- 进程/线程管理器 (`process_manager.py`, `thread_manager.py`)
- CLI 交互界面 (`brute_force/cli.py`)
- 5 种枚举规则生成器 (`brute_force/enum_rules.py`)
- 单元测试覆盖 (`tests/`)

---

## 2. 技术选型与关键决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 编程语言 | Python 3.13 | 利用 Free-threading 无 GIL 特性 |
| 并发方案 | `multiprocessing` (主) / `threading` (降级) | 根据 CPU 物理核心数动态选择：>2 核使用多进程，否则降级为多线程 |
| 硬件检测 | `psutil` 库 | 获取物理核心数、逻辑线程数 |
| 打包工具 | PyInstaller | 生成独立 exe，无需用户安装 Python |
| UI 架构 | 引擎与 UI 解耦 | `UICallback` 协议接口，便于扩展 Web UI |

### 动态并发策略

- **物理核心 > 2**：优先使用多进程 (`multiprocessing`)，Worker 数 = 核心数 - 1
- **物理核心 ≤ 2**：降级为多线程 (`threading`)，Worker 数 = 逻辑线程数 - 1
- 多进程充分利用多核 CPU 并行能力，多线程在低核设备上避免进程创建开销

### 为什么选择 Python 3.13 Free-threading？

Python 3.13 提供了 experimental free-threading 构建（通过 `python3.13t` 访问），GIL 被移除。即使在降级到多线程模式时，也能获得真正的并发性能。

---

## 3. 系统架构

```
┌────────────────────────────────────────────────────────┐
│                      UI 层 (可替换)                     │
│  ┌──────────────┐            ┌─────────────────────┐   │
│  │  CLI (当前)  │            │  Web API (预留)     │   │
│  └──────┬───────┘            └──────────┬──────────┘   │
│         │                               │              │
│         └─────────────┬─────────────────┘              │
│                       ▼                                │
│              ┌───────────────┐                         │
│              │ UICallback    │                         │
│              │   Protocol    │                         │
│              └───────┬───────┘                         │
│                      │                                 │
│  ┌───────────────────┼───────────────────┐            │
│  │           核心枚举引擎                 │            │
│  │  ┌──────────┐  ┌────┴────┐  ┌───────┐ │            │
│  │  │ Engine   │─▶│ Worker  │─▶│ Rules │ │            │
│  │  │          │  │Manager  │  │ Gen   │ │            │
│  │  └──────────┘  └─────────┘  └───────┘ │            │
│  └───────────────────────────────────────┘            │
│                      │                                 │
│         ┌────────────┴────────────┐                   │
│         ▼                         ▼                   │
│    ┌──────────┐  ...  ┌──────────┐                   │
│    │ Worker 1 │       │ Worker N │                   │
│    │ Process/ │       │ Process/ │                   │
│    │ Thread   │       │ Thread   │                   │
│    └──────────┘       └──────────┘                   │
└────────────────────────────────────────────────────────┘
```

---

## 4. 模块说明

| 模块文件 | 职责 |
|----------|------|
| `brute_force/engine.py` | 核心引擎：硬件检测、模式切换、任务生命周期管理、回调调度 |
| `brute_force/process_manager.py` | 多进程管理：创建/监控/终止工作进程 |
| `brute_force/thread_manager.py` | 多线程管理：创建/监控/终止工作线程 |
| `brute_force/shared_state.py` | 共享状态：双模式适配（Process/Thread） |
| `brute_force/worker.py` | 工作入口：枚举循环、密码比对、诊断日志 |
| `brute_force/enum_rules.py` | 枚举规则：5 种规则的迭代器生成器 |
| `brute_force/ui_interface.py` | UI 接口：`UICallback` Protocol 定义 |
| `brute_force/cli.py` | CLI 实现：ANSI 终端刷新、Ctrl+C 处理 |
| `brute_force/web_api.py` | Web 预留：REST API + WebSocket 框架 |
| `main.py` | 程序入口 (含 `multiprocessing.freeze_support`) |

---

## 5. 枚举规则

| 规则编号 | 描述 | 字符集 | 长度 | 数量级 |
|---------|------|--------|------|--------|
| 1 | 纯数字 | 0-9 | 1-8 | ~10^8 |
| 2 | 字母开头+数字 | a-zA-Z + 0-9 | 2-9 | ~5.7*10^9 |
| 3 | 数字+字母结尾 | 0-9 + a-zA-Z | 2-9 | ~5.7*10^9 |
| 4 | 数字+小写混合 | 0-9, a-z | 1-8 | ~2.9*10^12 |
| 5 | 数字+大小写混合 | 0-9, a-z, A-Z | 1-8 | ~2.2*10^14 |

### Worker 分配策略

按轮询方式分配规则到各个 Worker（数量动态决定）。

---

## 6. 性能优化

- **硬件自适应并发**：物理核心 > 2 使用多进程，否则降级多线程
- **批量更新**：Worker 本地计数累加 10000 次后才写入共享状态，减少同步开销
- **字符集预计算**：DIGITS、LOWERCASE、UPPERCASE 等字符集在模块加载时预计算
- **早期终止**：发现密码后立即设置 `found` 标志，其他 Worker 检查后退出
- **旧日志清理**：每次任务启动前自动清理 `worker_*.log`，避免磁盘堆积

---

## 7. 构建与打包

### 开发环境

```bash
# 安装 Python 3.13 free-threading
uv python install 3.13t

# 安装依赖
uv add psutil

# 运行程序
uv run --python 3.13t main.py

# 运行测试
uv run --python 3.13t pytest tests/
```

### Windows 打包

在 Windows 上执行：
```cmd
build.ps1        # 使用 uv（推荐）
```

生成文件：`dist\WeakPasswordBruteForce.exe`

---

## 8. Web API 预留接口

预留了以下端点（定义在 `brute_force/web_api.py` 中）：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/crack/start` | POST | 启动破解任务 |
| `/api/v1/crack/status` | GET | 查询当前状态 |
| `/api/v1/crack/stop` | POST | 终止破解任务 |
| `/api/v1/crack/result` | GET | 获取结果 |
| `/ws/crack/progress` | WebSocket | 实时推送进度 |

---

## 9. Phase 1 提交历史

| Commit | 说明 |
|--------|------|
| `1535a4c` | 项目骨架初始化、共享状态、枚举规则 |
| `f6e584c` | 工作线程、引擎、线程管理、CLI 界面 |
| `1e3d63b` | Web API 预留：REST 端点定义、WebSocket 框架 |
| `708b3dd` | 测试与打包：单元测试、README、Windows 构建脚本 |
| `15f287b` | CLI 体验优化：清屏、破解完成等待 |
| `93e8774` | 动态多进程/多线程调度、Worker 文件日志、CLI 刷新修复 |
| `5d69aeb` | 修复 Windows 多进程启动问题：freeze_support()、诊断日志 |
| `c0a974e` | 忽略 worker 日志文件 |
| `991679e` | 修复 CLI 终端刷新：启用 ANSI 支持、修复内容残留 |
| `5c2bc09` | 启动前自动清理旧 worker 日志 |
| `2f59f47` | 移除 build.bat |
| `1c24a79` | 密码输入格式校验：拒绝符号、更新文档 |

---

## 10. Phase 2 & 3 规划

### Phase 2: Web UI 开发（待定）

- FastAPI 后端服务实现
- Vue/React 前端进度面板
- WebSocket 实时推送

### Phase 3: 打包发布（待定）

- README 文档完善
- PyInstaller 打包验证
- Windows 兼容性测试
- 版本标记与发布

---

## 11. 注意事项

- 本程序仅为演示用途，请勿用于非法目的
- **输入限制**：仅支持字母和数字组合，输入包含符号时会被拒绝并提示重新输入
- 规则 5（全字母混合）空间极大，8 位密码可能需要极长时间
- 建议在测试时使用短密码（1-4 位）
- 当前环境 Linux 上打包生成的是 ELF 格式可执行文件，Windows 打包需在 Windows 上执行
- Windows 多进程必须包含 `multiprocessing.freeze_support()`，否则可能递归崩溃
- 终端刷新依赖 Windows ANSI 支持（Win 7/10/11 均兼容）
