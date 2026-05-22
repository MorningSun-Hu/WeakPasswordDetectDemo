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

- [x] **Worker 管理器**
  - `ProcessManager` 和 `ThreadManager`
  - 批量计数更新（10000 次一批写入共享状态）
  - 规则轮询分配策略（按 Worker ID 取模分配）

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
  - `POST /api/v1/crack/stop` - 停止任务
  - `GET /api/v1/crack/result` - 获取结果

- [x] **WebSocket 实时推送**
  - `WS /ws/crack/progress`
  - 心跳检测机制（无消息时发送 ping）

- [x] **Pydantic 数据模型验证**
  - StartRequest, StartResponse, StatusResponse, StopResponse, ResultResponse

- [x] **异步任务锁** (`asyncio.Lock`)，防止并发启动多个任务
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
| `view-success` | 成功展示页 | 密码被找到 | 数字雨、计时器、皇冠图标、密码明文、返回按钮 |
| `view-stopped` | 停止展示页 | 用户点击停止 | 静态数字雨、计时器、"用户主动停止"文字、返回按钮 |

### 前端交互功能

- [x] **SPA 视图切换逻辑** (`showView` 函数)
- [x] **计时器组件** (`createTimer`: start/stop/pause/resume)
- [x] **Matrix 数字雨动画**
  - 动态动画（破解页）
  - 静态定格（成功页、停止页）

- [x] **前端密码校验**（与后端一致的字母数字白名单）
- [x] **错误提示抖动动画**
- [x] **控制按钮状态管理**
  - 破解中：显示暂停 + 停止
  - 暂停时：暂停按钮消失，显示继续按钮
  - 继续时：恢复暂停按钮，隐藏继续按钮

- [x] **工作状态显示**（破解页左下角）
  - 运行模式（多线程/多进程 | 并发数）
  - Worker 状态
  - 当前枚举规则
  - 破解速度（次/秒）

- [x] **Tooltip 提示**（控制按钮悬停显示功能说明）
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

---

## 待完成工作

### 前后端集成（关键缺口）

- [x] **前端调用后端 start API**
  - 位置：`index.html` 开始按钮点击事件
  - 实现：发送 POST 请求到 `/api/v1/crack/start`
  - 传递：用户输入的密码

- [x] **前端调用后端 stop API**
  - 位置：`index.html` 停止按钮点击事件
  - 实现：发送 POST 请求到 `/api/v1/crack/stop`

- [x] **前端连接 WebSocket**
  - 实现：建立 `/ws/crack/progress` WebSocket 连接
  - 功能：自动重连（3 秒延迟）、消息处理

- [x] **前端接收并处理实时推送**
  - 实现：解析后端推送的消息类型
    - `started` - 任务开始
    - `progress` - 进度更新
    - `found` - 找到密码
    - `terminated` - 任务终止
    - `error` - 错误处理
    - `ping` - 心跳保活

- [x] **前端尝试次数从后端获取**
  - 实现：`cracking-attempts` 由 WebSocket progress 消息驱动更新

- [x] **成功状态联动**
  - 实现：从后端接收找到的密码和真实统计数据，自动切换到成功页

### 前端工作状态展示优化

- [x] **初始值从后端获取**
  - 实现：`initWorkStatus()` 调用 GET /api/v1/crack/status 获取真实状态

- [x] **规则切换逻辑**
  - 实现：从后端推送的真实 `rule_id` 映射到规则名称（纯数字、字母开头+数字等）

### 暂停/继续功能完善

- [ ] **后端暂停/继续支持**
  - 当前：暂停只在前端暂停计时器和动画
  - 需要：后端引擎支持暂停和恢复（如果可行）

### 其他

- [ ] **清理冗余文件**
  - `web_api.py` 仍为预留骨架文件（功能已被 `server.py` 替代）

- [ ] **错误处理**
  - 前端未完全处理网络请求失败的情况
  - 需要添加加载状态、错误提示等

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

- 前端目前使用内联 CSS（约 200 行精简工具类），不依赖 Tailwind CDN，提升加载性能
- 数字雨动画使用 HTML5 Canvas API 实现
- 所有视图使用 `div` 可见性切换实现 SPA 路由，无页面刷新
- 计时器使用 `requestAnimationFrame` 实现高精度更新（毫秒级）
