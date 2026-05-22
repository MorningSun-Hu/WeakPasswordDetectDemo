# 弱口令枚举暴力破解演示程序

使用 Python 3.13 Free-threading 版本实现的多线程弱口令枚举暴力破解演示程序。
支持 Windows 7/10/11 运行，提供 Web 图形界面和 CLI 命令行两种模式。

## 功能特性

- **9 种枚举规则**：纯数字、纯小写字母、纯大写字母、大小写混合字母、字母头+数字、数字+字母尾、数字+小写混合、数字+大写混合、数字+全字母混合
- **Web 界面**：Matrix 风格数字雨动画，实时显示破解进度，支持暂停/恢复/停止操作
- **CLI 模式**：传统命令行界面，支持 ANSI 彩色输出
- **多线程/多进程并发**：利用 Python 3.13 无 GIL 特性实现真正并行
- **实时进度显示**：各 Worker 尝试次数、当前规则、累计耗时
- **高精度计时**：微秒级精度显示
- **Windows 打包**：一键打包为独立 exe，无需安装 Python 即可运行

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

| 规则编号 | 描述 | 示例 | 数量级 |
|---------|------|------|--------|
| 1 | 1-8 位纯数字 | 0 ~ 99999999 | ~10^8 |
| 2 | 1-8 位纯小写字母 | a ~ zzzzzzzz | ~26^8 |
| 3 | 1-8 位纯大写字母 | A ~ ZZZZZZZZ | ~26^8 |
| 4 | 1-8 位大小写混合字母 | a ~ ZZZZZZZZ | ~52^8 |
| 5 | 1位字母开头 + 1-8位数字 | a0 ~ Z99999999 | ~52*10^8 |
| 6 | 1-8位数字 + 1位字母结尾 | 0a ~ 99999999Z | ~52*10^8 |
| 7 | 1-8位数字+小写混合 | 0 ~ zzzzzzzz | ~36^8 |
| 8 | 1-8位数字+大写混合 | 0 ~ ZZZZZZZZ | ~36^8 |
| 9 | 1-8位数字+大小写混合 | 0 ~ ZZZZZZZZ | ~62^8 |

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
│   ├── engine.py         # 核心引擎 (线程/进程调度)
│   ├── worker.py         # Worker 实现 (枚举循环)
│   ├── enum_rules.py     # 9 种枚举规则生成器
│   ├── shared_state.py   # 共享状态管理
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
[Worker 0] 尝试次数: 53    规则: 纯数字
[Worker 1] 尝试次数: 48    规则: 字母开头+数字
[Worker 2] 尝试次数: 45    规则: 数字+字母结尾

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

## 注意事项

- 本程序仅为演示用途，请勿用于非法目的
- 规则 9（数字+大小写混合）空间极大，8 位密码可能需要极长时间
- 建议在测试时使用短密码（1-4 位）
- 密码最大长度限制为 8 位（统一应用于 CLI 和 Web 模式）
- CLI 模式下按 Ctrl+C 可提前终止，子进程会优雅退出

## 署名

胡晨阳 | 丹阳市新桥初级中学
