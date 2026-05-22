# Web UI 实现进度文档

## 项目概述

弱口令暴力破解演示系统 - Phase 3: Web UI 实现

将原有的 CLI 命令行交互界面升级为现代化的 Web 图形界面，提供直观的用户体验和实时可视化反馈。

**分支**: `260521-feat-web-ui`
**技术栈**: Python 3.13 (Free-threading) + FastAPI + 纯 HTML/CSS/JS (SPA)

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        浏览器 (SPA)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  首页    │→│ 输入页   │→│ 破解页   │→│ 结果页   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↑              ↑            ↑              ↑          │
│       └──────────────┴────────────┴──────────────┘          │
│                         返回                                │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI 后端服务                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  REST API    │  │  WebSocket   │  │  任务管理    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                           │                                 │
│              ┌────────────▼────────────┐                   │
│              │   BruteForceEngine      │                   │
│              │  ┌─────────┐ ┌───────┐  │                   │
│              │  │ Worker1 │ │Worker2│  │                   │
│              │  └─────────┘ └───────┘  │                   │
│              └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
前端 -> REST API -> FastAPI 路由 -> ThreadPoolExecutor -> BruteForceEngine
                                                          |
                                                          v
前端 <- WebSocket <- WebCallback <- Queue <- 引擎回调
```

### 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | ASGI 服务器，提供 REST API 和 WebSocket |
| **数据验证** | Pydantic v2 | 请求/响应 Schema 定义 |
| **并发模型** | multiprocessing / threading | 根据 CPU 核心数自动选择 |
| **异步架构** | asyncio + ThreadPoolExecutor | 引擎在线程池运行，不阻塞事件循环 |
| **前端** | 纯 HTML/CSS/JS (SPA) | 无外部 CDN 依赖，内联 Tailwind 精简类 |
| **实时通信** | WebSocket + 消息队列 | 后端通过 Queue 推送事件到前端 |
| **Python 版本** | 3.13+ free-threading | 无 GIL，支持真正多线程并行 |

---

## 项目文件结构

```
/workspace/brute_force/
├── __init__.py                  # 包初始化
├── static/                      # 前端静态资源
│   ├── assets/
│   │   ├── Enter-button.png     # Enter 按钮图片
│   │   ├── crown.png            # 皇冠图标（破解成功）
│   │   └── index-background.png # 首页背景图
│   └── index.html               # 前端 SPA 页面
├── server.py                    # FastAPI 主服务（REST API + WebSocket）
├── schemas.py                   # Pydantic 数据模型
├── engine.py                    # BruteForceEngine 核心引擎
├── worker.py                    # Worker 进程/线程入口
├── callback.py                  # WebCallback 回调实现
├── ws_manager.py                # WebSocket 连接管理器
├── shared_state.py              # 双模式共享状态（Process/Thread）
├── enum_rules.py                # 5 种枚举规则生成器
├── process_manager.py           # 多进程管理器
├── thread_manager.py            # 多线程管理器
├── ui_interface.py              # UICallback 接口定义 (Protocol)
├── cli.py                       # CLI 命令行界面
└── utils.py                     # 工具函数（密码校验）
```

---

## 已实现功能

### 核心引擎 (Phase 1)

- [x] **5 种枚举规则生成器**
  - 纯数字 (1-8 位)
  - 字母开头 + 数字
  - 数字 + 字母结尾
  - 数字 + 小写字母混合
  - 数字 + 大小写字母混合

- [x] **硬件自适应并发**
  - 物理核心 > 2: 自动使用多进程
  - 物理核心 <= 2: 降级为多线程

- [x] **双模式共享状态**
  - `SharedStateProcessMode` (multiprocessing.Value/Array)
  - `SharedStateThreadMode` (threading.Lock)
  - **支持暂停/恢复** (`paused` 标志位，跨进程/线程安全)

- [x] **Worker 管理器**
  - `ProcessManager` 和 `ThreadManager`
  - 批量计数更新（10000 次一批写入共享状态）
  - 规则轮询分配策略（按 Worker ID 取模分配）
  - **Worker 暂停检查**：`is_paused()` 循环等待，支持热暂停

- [x] **CLI 命令行界面**
  - ANSI 转义序列原地刷新
  - Windows VT100 兼容
  - Ctrl+C 信号处理
  - 密码输入校验

### Web 后端 API (Phase 2)

- [x] **FastAPI 应用实例** + Uvicorn ASGI 服务器
- [x] **REST API 端点**
  - `POST /api/v1/crack/start` - 启动破解任务
  - `GET /api/v1/crack/status` - 获取当前状态
  - `POST /api/v1/crack/stop` - 停止任务并释放资源锁
  - `GET /api/v1/crack/result` - 获取结果
  - `POST /api/v1/crack/pause` - 暂停任务 (新增)
  - `POST /api/v1/crack/resume` - 恢复任务 (新增)

- [x] **WebSocket 实时推送**
  - `WS /ws/crack/progress`
  - 心跳检测机制（无消息时发送 ping）
  - 消息队列处理引擎回调事件

- [x] **Pydantic 数据模型验证**
  - StartRequest, StartResponse, StatusResponse, StopResponse, ResultResponse

- [x] **异步任务锁管理**
  - `asyncio.Lock` 防止并发启动多个任务
  - 引擎线程结束后自动安全释放锁
  - `lock.locked()` 检查避免重复释放导致 RuntimeError

- [x] **ThreadPoolExecutor** 调度阻塞引擎，不阻塞事件循环
- [x] **CORS 中间件**配置
- [x] **WebSocket 连接管理器**（连接/断开/单发/广播）
- [x] **WebCallback 回调**：同步引擎事件转异步队列消息

### 前端视图 (Phase 3)

| 视图 ID | 名称 | 触发条件 | 主要元素 |
|---------|------|---------|---------|
| `view-home` | 首页 | 初始加载 / 返回 | 背景图、标题、Enter 按钮、署名 |
| `view-input` | 密码输入页 | 点击 Enter | 标题、密码输入框、开始按钮、错误提示 |
| `view-cracking` | 破解过程页 | 点击开始 | 数字雨 Canvas、计时器、尝试次数、工作状态、暂停/停止按钮 |
| `view-success` | 成功展示页 | 密码被找到 | **静态数字雨**、计时器、皇冠图标、密码明文、返回按钮 |
| `view-stopped` | 停止展示页 | 用户点击停止 | **静态数字雨**、计时器、"用户主动停止"文字、返回按钮 |

### 前端交互功能

- [x] **SPA 视图切换逻辑** (`showView` 函数)
- [x] **计时器组件** (`createTimer`: start/stop/pause/resume)
- [x] **Matrix 数字雨动画**
  - 动态动画（破解页）
  - 静态定格（成功页、停止页）

- [x] **前端密码校验**（与后端一致的字母数字白名单，最大长度 8 位）
- [x] **错误提示抖动动画**
- [x] **控制按钮状态管理**
  - 破解中：显示暂停 + 停止
  - 暂停时：暂停按钮消失，显示继续按钮
  - 继续时：恢复暂停按钮，隐藏继续按钮
- [x] **用户反馈机制**
  - Toast 通知系统（成功/错误/信息）
  - 按钮加载状态指示器（API 请求期间禁用并显示动画）
  - 按钮 Tooltip 提示

- [x] **工作状态显示**（破解页左下角）
  - 运行模式（多线程/多进程 | 并发数）
  - Worker 状态
  - 当前枚举规则
  - 破解速度（次/秒）
  - **数据源**：从后端 WebSocket 推送获取真实数据

- [x] **WebSocket 实时通信**
  - 自动连接和重连（3 秒延迟）
  - 处理 6 种消息类型：started/progress/found/terminated/error/ping
  - 进度推送驱动 UI 更新（尝试次数、Worker 状态、规则切换）

- [x] **REST API 调用**
  - startCrack() / stopCrack() / pauseCrack() / resumeCrack()
  - getStatus() / getResult()
  - 完整的错误处理和异步调用

- [x] **成功页资源自动清理**
  - 破解成功后自动调用后端 stop API 释放锁
  - 为下一次破解任务做好准备

- [x] **响应式设计**（支持移动端和桌面端）
- [x] **署名信息**（胡晨阳，丹阳市新桥初级中学）

---

## 后端 API 状态

| API 端点 | 方法 | 状态 | 说明 |
|----------|------|------|------|
| `/` | GET | **已实现** | 返回 index.html 前端页面 |
| `/assets/*` | GET | **已实现** | 静态文件服务 |
| `/api/v1/crack/start` | POST | **已实现** | 启动破解任务，含密码校验和任务锁 |
| `/api/v1/crack/status` | GET | **已实现** | 返回引擎当前状态 |
| `/api/v1/crack/stop` | POST | **已实现** | 终止引擎并释放锁 |
| `/api/v1/crack/result` | GET | **已实现** | 返回最终结果（密码/尝试次数/用时） |
| `/ws/crack/progress` | WebSocket | **已实现** | 实时推送进度、心跳、状态消息 |
| `/api/v1/crack/pause` | POST | **已实现** | 暂停当前任务 (新增) |
| `/api/v1/crack/resume` | POST | **已实现** | 恢复当前任务 (新增) |

---

## 已完成工作

### 前后端集成
- [x] **前端调用后端 start API**
- [x] **前端调用后端 stop API**
- [x] **前端连接 WebSocket**（自动重连）
- [x] **前端接收并处理实时推送**（started/progress/found/terminated/error）
- [x] **前端尝试次数从后端获取**
- [x] **成功状态联动**（自动切换视图并显示密码明文）
- [x] **成功页资源自动清理**（防止锁未释放导致二次启动报错）

### 暂停/恢复功能完善
- [x] **后端引擎支持暂停/恢复**
  - `SharedState` 添加 `paused` 标志和对应方法
  - Worker 核心循环增加暂停检查
  - `engine.pause()` / `engine.resume()` 接口
- [x] **REST API 暴露暂停/恢复端点**
- [x] **前端按钮调用真实后端 API**

### UI 优化
- [x] **成功页皇冠位置**：调整至计时器右上角
- [x] **成功页时间格式**：`HH:MM:SS.mmm.uuuu`（保留四位微秒精度）
- [x] **成功页密码样式**：字号加大，行距统一
- [x] **成功页/停止页背景**：改为静态数字雨冻结效果
- [x] **控制按钮 Tooltip**：悬停显示功能说明
- [x] **左下角工作状态显示**：白色文字，紧凑行距

### 修复与完善
- [x] **密码长度限制统一**：CLI、后端 API、前端输入框统一限制最大 8 位，超限报错提示
- [x] **微秒显示修复**：前端计时器改用 `performance.now()` 替代 `Date.now()`，修复微秒显示始终为 0 的问题
- [x] **锁冲突修复**：解决 `stop_crack` 与引擎线程结束时重复释放锁导致的 `RuntimeError`
- [x] **成功页资源清理**：破解成功后自动调用 `stopCrack()` 释放后端任务锁，允许二次启动

---

## 待完成工作

### 其他

- [x] **清理冗余文件**
  - `web_api.py` 已删除（功能已被 `server.py` 完全替代）

- [x] **前端错误提示优化**
  - 已添加 Toast 通知系统（支持 success/error/info 三种类型及动画）

- [x] **前端加载状态**
  - API 请求期间按钮显示 Loading 动画及禁用状态

---

## 运行方式

### 启动服务

```bash
uv run uvicorn brute_force.server:app --reload --host 0.0.0.0 --port 8000
```

### 访问地址

- 前端页面：`http://localhost:8000/`
- API 文档：`http://localhost:8000/docs`

---

## 设计文档

完整技术设计文档位于：`.monkeycode/specs/web-ui-implementation/design.md`

包含 21 个子任务，分布在 5 个节点：
- Node 1: 基础设施（静态文件目录、服务配置）
- Node 2: UI 实现（视图容器、样式、动画）
- Node 3: WebSocket 集成
- Node 4: 后端 API 连接
- Node 5: 测试与优化

---

## 备注

- 前端使用内联 CSS（精简工具类），无外部 CDN 依赖，提升加载性能
- 数字雨动画使用 HTML5 Canvas API 实现
- 所有视图使用 `div` 可见性切换实现 SPA 路由，无页面刷新
- **高精度计时**：使用 `performance.now()` 实现微秒级精度显示，`requestAnimationFrame` 驱动 UI 更新
- **用户反馈机制**：内置 Toast 通知系统与按钮 Loading 状态指示器，提供即时操作反馈
- **安全限制**：密码枚举最大长度限制为 8 位（统一应用于 CLI、Web 前后端），防止资源耗尽
