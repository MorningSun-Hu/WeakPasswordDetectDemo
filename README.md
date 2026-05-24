# 弱口令枚举暴力破解演示程序 v1.0.1

使用 Python 3.13 Free-threading 版本实现的弱口令枚举暴力破解演示程序。
支持 Windows 7/10/11 运行，提供 Web 图形界面和 CLI 命令行两种模式。

## 功能特性

- **8 种枚举规则**：弱口令库、纯数字、纯小写字母、纯大写字母、大小写混合字母、数字+小写混合、数字+大写混合、数字+大小写混合（规则互不重叠，动态任务队列按长度/行数分段）
- **Web 界面**：Matrix 风格数字雨动画，实时显示破解进度，支持暂停/恢复/停止操作
- **CLI 模式**：传统命令行界面，支持 ANSI 彩色输出
- **多线程/多进程并发**：利用 Python 3.13 无 GIL 特性实现真正并行
- **实时进度显示**：各 Worker 尝试次数、当前规则、累计耗时
- **高精度计时**：微秒级精度显示
- **Windows 打包**：一键打包为独立 exe，无需安装 Python 即可运行

## 当前状态

- 当前版本：`v1.0.1`
- Web 标题和 CLI 标题已显示版本号
- 弱口令库 `weak_passwords.txt` 已纳入 Windows PyInstaller 打包产物
- 动态任务队列已修复规则切换时机，当前规则会等待活跃 Worker 全部完成后再切换下一规则
- 成功命中后，Worker 会优雅退出并尽量先回写本地尝试次数，Web 端累计尝试次数更接近真实值
- Worker 日志已拆分为独立文件，线程模式使用 `worker_thread_<id>.log`，进程模式使用 `worker_<pid>_<id>.log`
- Web 端速度显示已修复，不再出现"时间在走、速度为 0"的问题
- 单元测试已覆盖全部 8 类密码族，每类至少 2 个样本

## 环境要求

- Python 3.13 (Free-threading build)
- uv 包管理器（推荐）
- Windows 7/10/11 或 Linux

## 安装与运行

```bash
# 克隆仓库
git clone <repository-url>
cd weak-password-bruteforce

# 安装 Python 3.13 free-threading 版本
uv python install 3.13t

# 安装依赖
uv sync --python 3.13t
```

### Web 模式（默认）

```bash
uv run --python 3.13t main.py
```

启动后自动打开浏览器访问 `http://127.0.0.1:8000`。

### CLI 模式

```bash
uv run --python 3.13t main.py --cli
```

## 枚举规则说明

| 规则编号 | 描述 | 约束 | 示例 |
|---------|------|------|------|
| 0 | 弱口令库 | Top 10000常见密码 | 123456, password, admin |
| 1 | 纯数字 | 仅数字 | 0, 1, 42, 99999999 |
| 2 | 纯小写字母 | 仅小写 | a, z, abc, zzzzzzzz |
| 3 | 纯大写字母 | 仅大写 | A, Z, ABC, ZZZZZZZZ |
| 4 | 大小写混合字母 | 至少1小写+1大写 | aA, Aa, bC, aBcD |
| 5 | 数字+小写混合 | 至少1数字+1小写 | 0a, a0, 1b, a1b2 |
| 6 | 数字+大写混合 | 至少1数字+1大写 | 0A, A0, 1B, A1B2 |
| 7 | 数字+大小写混合 | 至少1数字+1小写+1大写 | 0aA, a0B, A1b, aA1bB2 |

## 项目结构

```
weak-password-bruteforce/
├── main.py               # 程序入口 (Web/CLI 双模式)
├── pyproject.toml        # 项目配置
├── bruteforce.spec       # PyInstaller 打包配置
├── build.ps1             # Windows 打包脚本
├── README.md             # 项目说明
├── .gitignore
├── brute_force/
│   ├── data/             # 数据文件
│   │   └── weak_passwords.txt  # 弱口令库（10000条）
│   ├── engine.py         # 核心引擎 (线程/进程调度)
│   ├── worker.py         # Worker 实现 (枚举循环)
│   ├── enum_rules.py     # 8 种枚举规则生成器
│   ├── shared_state.py   # 共享状态管理（动态任务队列）
│   ├── server.py         # FastAPI Web 服务
│   ├── ws_manager.py     # WebSocket 连接管理
│   ├── callback.py       # Web 回调实现
│   ├── schemas.py        # Pydantic 数据模型
│   ├── utils.py          # 工具函数 (密码校验等)
│   ├── cli.py            # CLI 界面
│   ├── ui_interface.py   # UI 回调接口定义
│   ├── thread_manager.py # 线程管理器
│   ├── process_manager.py# 进程管理器
│   └── static/           # 前端静态文件
│       ├── index.html    # SPA 单页应用
│       └── assets/       # 图片资源
├── tests/
│   ├── test_enum_rules.py
│   ├── test_shared_state.py
│   └── test_engine.py
└── .monkeycode/          # 项目文档
    ├── MEMORY.md
    ├── docs/
    └── specs/
```

## 打包为独立 exe

在 Windows 上执行：

```powershell
.\build.ps1
```

打包完成后，可执行文件位于 `dist\WeakPasswordBruteForce.exe`。
该 exe 文件内置 Python 运行时，用户无需安装 Python 即可直接运行。

## 最近修复

### 1. 弱口令库阶段被跳过

- 原因：Windows 打包产物未包含 `brute_force/data/weak_passwords.txt`
- 修复：`bruteforce.spec` 已加入数据文件打包配置

### 2. 纯数字阶段末尾长度被提前切走

- 原因：最后一个长度任务刚被分配后，调度器提前切换到下一规则
- 修复：新增当前规则活跃 Worker 计数，所有活跃 Worker 完成后再切换规则

### 3. Web 端累计尝试次数偏小

- 原因：成功后直接强制终止 Worker，部分本地计数未来得及 flush 到共享状态
- 修复：引擎结束阶段改为优雅等待 Worker 自然退出并回写计数

### 4. 日志看起来像有 Worker 没领到任务

- 原因：线程模式多个 Worker 共写一个日志文件，内容会互相穿插
- 修复：每个 Worker 单独输出自己的日志文件

### 5. Web 端速度显示为 0

- 原因：前端页面存在本地模拟状态逻辑，覆盖了 WebSocket 推送的真实进度
- 修复：移除 `updateWorkStatus()` 本地模拟逻辑，速度/规则显示统一使用后端真实数据
- 影响：纯字母密码破解时，Web 端现在能正确显示速度和当前规则

### 6. 测试覆盖不足

- 修复：新增 `test_engine_finds_two_passwords_per_rule_family()` 测试
- 覆盖范围：8 类密码族，每类至少 2 个样本（共 16 个测试用例）
- 测试样本包括：
  - 弱口令库：`12345678`, `admin`
  - 纯数字：`42`, `99`
  - 纯小写字母：`ab`, `zz`
  - 纯大写字母：`AB`, `ZX`
  - 大小写混合：`aA`, `bC`
  - 数字+小写：`1a`, `a2`
  - 数字+大写：`1A`, `B2`
  - 数字+大小写混合：`1aA`, `2bC`

### 手动打包

```bash
uv run --python 3.13t pyinstaller --clean bruteforce.spec
```

## 运行截图

### Web 模式

```
==================================================
  弱口令枚举暴力破解演示程序 (Web 版)
==================================================
服务地址: http://127.0.0.1:8000
正在打开浏览器...
按 Ctrl+C 停止服务
==================================================
```

### CLI 模式

```
弱口令枚举暴力破解演示程序
Python 3.13 Free-threading 版本

请输入目标密码 (输入 'quit' 退出): 42

==================================================
  弱口令枚举暴力破解演示
==================================================
运行模式: 多线程 | 物理核心: 8 | 并发数: 3
目标密码: ** 位
按 Ctrl+C 提前终止
--------------------------------------------------
[Worker 0] 尝试次数: 53    规则: 弱口令库
[Worker 1] 尝试次数: 48    规则: 弱口令库
[Worker 2] 尝试次数: 45    规则: 弱口令库

累计尝试: 146
已用时间: 00:00:00

==================================================
  破解成功!
==================================================
密码: 42
由 Worker 0 找到
总尝试次数: 53
总用时: 00:00:00 (0.50 秒)
==================================================
```

## 单元测试

```bash
uv run --python 3.13t tests/test_enum_rules.py
uv run --python 3.13t tests/test_shared_state.py
uv run --python 3.13t tests/test_engine.py
```

## 调试与日志

- 线程模式日志文件：`worker_thread_<id>.log`
- 进程模式日志文件：`worker_<pid>_<id>.log`
- 日志重点关注以下关键字：
  - `processing weak dict`
  - `processing rule`
  - `FOUND PASSWORD`
  - `Flushed`
  - `termination requested, exiting`
- 如果需要验证弱口令库是否生效，优先测试 `12345678`

## 注意事项

- 本程序仅为演示用途，请勿用于非法目的
- 规则 0 优先使用弱口令库（10000条常见密码），可快速破解简单密码
- 规则 7（数字+大小写混合）空间极大，8 位密码可能需要极长时间
- 建议在测试时使用短密码（1-4 位）
- 密码最大长度限制为 8 位（统一应用于 CLI 和 Web 模式）
- CLI 模式下按 Ctrl+C 可提前终止，子进程会优雅退出

## 署名

胡晨阳 | 丹阳市新桥初级中学
