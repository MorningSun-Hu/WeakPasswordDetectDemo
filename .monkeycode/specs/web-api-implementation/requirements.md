# Phase 2: Web API 实现 - 开发任务指导

> **阶段**: Phase 2 - Web API 开发
> **分支**: `260521-feat-web-api`
> **创建日期**: 2026-05-21
> **最后更新**: 2026-05-21
> **状态**: Node 1-2 已完成，Node 3 进行中

---

## 1. Phase 1 遗留接口 Review

（保持不变，略）

---

## 2. Phase 2 开发任务编排

（保持不变）

### Node 1: 基础设施搭建 [已完成]

...

### Node 2: REST API 实现 [已完成]

...

### Node 3: WebSocket 实时推送 [待开发]

...

---

## 3. 技术栈更新

（保持不变）

---

## 4. 开发进度总结

### Node 1: 基础设施 (100%)
- [x] 依赖安装 (`fastapi`, `uvicorn`)
- [x] `server.py` 基础骨架
- [x] Pydantic 模型定义 (`schemas.py`)
- [x] CORS 配置
- [x] 密码校验工具 (`utils.py`)
- [x] 任务锁初始化 (`asyncio.Lock`)

### Node 2: REST API (100%)
- [x] `POST /api/v1/crack/start` (含参数校验、异步调度)
- [x] `GET /api/v1/crack/status`
- [x] `POST /api/v1/crack/stop`
- [x] `GET /api/v1/crack/result`
- [x] `WebCallback` 异步队列实现
- [x] `ThreadPoolExecutor` 集成

### Node 3: WebSocket (0%)
- [ ] `WS /ws/crack/progress`
- [ ] 广播机制
- [ ] 心跳检测

---


根据第一阶段核心引擎与 CLI 的实际开发成果，对原有 `web_api.py` 预留接口进行审查，发现以下需要调整的问题：

### 1.1 接口设计问题

| 问题编号 | 问题描述 | 影响 | 调整方案 |
|---------|---------|------|---------|
| P01 | `start` 接口的 `worker_count` 固定为 3，缺少自动检测支持 | 无法利用 Phase 1 的硬件自适应能力 | 支持传 `0` 表示自动根据 CPU 核心数分配 |
| P02 | 缺少运行模式返回 | 前端无法获知当前是多进程还是多线程 | `start` 响应应返回 `mode` 字段（"process"/"thread"） |
| P03 | 缺少密码格式校验 | CLI 已实现符号拦截，Web API 未同步 | 添加与 CLI 一致的白名单校验（字母+数字） |
| P04 | 缺少 Pydantic 模型 | 只有注释说明，无类型安全 | 定义正式的请求/响应 Schema |
| P05 | `WebCallback.on_progress` 为同步方法 | 无法直接用于 FastAPI 异步 WebSocket 推送 | 实现异步推送机制，使用 `asyncio.Queue` 或事件循环 |
| P06 | 缺少 CORS 配置 | Web 前端跨域访问会被拒绝 | 添加 FastAPI CORS 中间件 |
| P07 | `engine` 实例为全局变量，无状态保护 | 可能并发启动多个任务导致冲突 | 实现任务锁，同一时间只允许一个任务运行 |
| P08 | 缺少心跳检测 | WebSocket 连接可能因超时而断开 | 添加心跳保活机制与断线重连支持 |

### 1.2 架构调整

```
原预留架构:
  engine (全局变量)
  ↓
  WebCallback (同步方法，无推送)
  ↓
  WebSocket (简单轮询，无状态管理)

调整后架构:
  FastAPI App
  ├── CORS 中间件
  ├── REST API (带任务锁保护)
  │   ├── POST /api/v1/crack/start
  │   ├── GET  /api/v1/crack/status
  │   ├── POST /api/v1/crack/stop
  │   └── GET  /api/v1/crack/result
  └── WebSocket (/ws/crack/progress)
      ├── 连接管理器
      ├── 异步推送队列
      └── 心跳检测
```

---

## 2. Phase 2 开发任务编排

Phase 2 聚焦于后端 Web API 的完整实现，包含三个开发节点（Node 1-3），按依赖顺序推进。

### Node 1: 基础设施搭建

**目标**：建立 FastAPI 服务基础框架，配置依赖与中间件。

| 子任务 ID | 任务名称 | 产出文件 | 说明 |
|-----------|---------|----------|------|
| N1-1 | 依赖安装 | `pyproject.toml` | 添加 fastapi, uvicorn, websockets, pydantic |
| N1-2 | 服务入口创建 | `brute_force/server.py` | FastAPI app 初始化、uvicorn 启动配置 |
| N1-3 | Pydantic 模型定义 | `brute_force/schemas.py` | 请求/响应 Schema（StartRequest, StatusResponse 等） |
| N1-4 | CORS 配置 | `brute_force/server.py` | 添加 `CORSMiddleware`，允许前端跨域访问 |
| N1-5 | 密码校验函数 | `brute_force/utils.py` | 与 CLI 一致的白名单校验（字母+数字） |
| N1-6 | 任务锁实现 | `brute_force/server.py` | `asyncio.Lock` 保护，防止并发任务冲突 |

**验收标准**：
- `uv run uvicorn brute_force.server:app --reload` 可正常启动
- 访问 `/docs` 可查看自动生成的 Swagger UI
- CORS 配置允许 `*` 或指定域名访问

---

### Node 2: REST API 实现

**目标**：实现完整的 REST API 端点，集成核心引擎。

| 子任务 ID | 任务名称 | 产出文件 | 说明 |
|-----------|---------|----------|------|
| N2-1 | 启动任务接口 | `brute_force/server.py` | `POST /api/v1/crack/start`，含参数校验、任务锁、引擎异步启动 |
| N2-2 | 状态查询接口 | `brute_force/server.py` | `GET /api/v1/crack/status`，返回引擎实时状态 |
| N2-3 | 停止任务接口 | `brute_force/server.py` | `POST /api/v1/crack/stop`，安全终止引擎 |
| N2-4 | 结果查询接口 | `brute_force/server.py` | `GET /api/v1/crack/result`，返回最终破解结果 |
| N2-5 | 引擎异步调度 | `brute_force/server.py` | 使用 `concurrent.futures.ThreadPoolExecutor` 在线程池中运行引擎，不阻塞事件循环 |
| N2-6 | WebCallback 同步实现 | `brute_force/callback.py` | 实现 `UICallback` 协议，将引擎事件推送到异步队列 |

**API 规范**：

#### POST /api/v1/crack/start

**请求体**:
```json
{
  "password": "abc123",
  "worker_count": 0
}
```
- `worker_count`: 0 表示自动检测，>0 表示指定数量

**成功响应** (200):
```json
{
  "status": "started",
  "worker_count": 3,
  "mode": "process",
  "physical_cores": 4
}
```

**错误响应** (400/409):
```json
{
  "error": "密码包含不支持的符号: !, @",
  "detail": "仅支持字母和数字"
}
```
或
```json
{
  "error": "任务运行中",
  "detail": "请先停止当前任务"
}
```

#### GET /api/v1/crack/status

**响应** (200):
```json
{
  "running": true,
  "found": false,
  "workers": [
    {"id": 0, "attempts": 12345, "rule_id": 1},
    {"id": 1, "attempts": 12340, "rule_id": 2}
  ],
  "total_attempts": 24685,
  "elapsed": 1.5,
  "mode": "process"
}
```

#### POST /api/v1/crack/stop

**响应** (200):
```json
{
  "status": "terminated",
  "total_attempts": 24685,
  "elapsed": 1.5
}
```

#### GET /api/v1/crack/result

**响应** (200):
```json
{
  "found": true,
  "password": "abc123",
  "attempts": 5678,
  "elapsed": 2.3,
  "worker_id": 1
}
```

---

### Node 3: WebSocket 实时推送

**目标**：实现 WebSocket 端点，实时推送引擎状态到前端。

| 子任务 ID | 任务名称 | 产出文件 | 说明 |
|-----------|---------|----------|------|
| N3-1 | WebSocket 端点 | `brute_force/server.py` | `WS /ws/crack/progress`，接受连接并推送 |
| N3-2 | 连接管理器 | `brute_force/ws_manager.py` | 管理多个 WebSocket 连接，支持广播 |
| N3-3 | 异步推送队列 | `brute_force/callback.py` | `WebCallback` 将引擎事件放入 `asyncio.Queue` |
| N3-4 | 心跳检测 | `brute_force/ws_manager.py` | 定期发送 ping/pong，检测断线 |
| N3-5 | 断线重连支持 | `brute_force/ws_manager.py` | 客户端断线后自动清理连接，重连后重新订阅 |
| N3-6 | 消息格式定义 | `brute_force/schemas.py` | 统一 WebSocket 消息格式（progress/found/terminated/error） |

**WebSocket 消息格式**：

```json
// 进度推送
{
  "type": "progress",
  "data": {
    "running": true,
    "found": false,
    "workers": [...],
    "total_attempts": 12345,
    "elapsed": 1.5
  }
}

// 找到密码
{
  "type": "found",
  "data": {
    "password": "abc123",
    "attempts": 5678,
    "elapsed": 2.3,
    "worker_id": 1
  }
}

// 任务终止
{
  "type": "terminated",
  "data": {
    "attempts": 12345,
    "elapsed": 5.0
  }
}

// 错误
{
  "type": "error",
  "data": {
    "message": "密码包含不支持的符号"
  }
}

// 心跳
{
  "type": "ping"
}
```

---

## 3. 技术栈

| 组件 | 选择 | 版本要求 | 说明 |
|------|------|---------|------|
| Web 框架 | FastAPI | >= 0.100.0 | 异步支持、自动文档、类型安全 |
| ASGI 服务器 | uvicorn | >= 0.23.0 | 高性能、支持 WebSocket |
| 数据验证 | Pydantic | v2 | 与 FastAPI 原生集成 |
| WebSocket | websockets | FastAPI 内置 | 实时双向通信 |
| CORS | fastapi.middleware.cors | 内置 | 跨域资源共享 |

---

## 4. 执行依赖图

```
Node 1:  [N1-1] → [N1-2] → [N1-3]
                      ↓
                    [N1-4] → [N1-5] → [N1-6]
                                 ↓
Node 2:                       [N2-1] → [N2-2] → [N2-3]
                                 ↓        ↓
                               [N2-5]   [N2-4]
                                 ↓
                               [N2-6]
                                 ↓
Node 3:                       [N3-1] → [N3-2] → [N3-3]
                                           ↓
                                         [N3-4] → [N3-5]
                                           ↓
                                         [N3-6]
```

---

## 5. 开发顺序建议

1. **Node 1 先行**：完成基础设施搭建，确保 FastAPI 服务可启动
2. **Node 2 跟进**：实现 REST API，验证引擎集成与异步调度
3. **Node 3 收尾**：添加 WebSocket 推送，完善实时通信

每个节点完成后应进行独立验证，确保功能正常后再进入下一节点。

---

## 6. 注意事项

- **引擎异步调度**：引擎的 `start()` 方法是阻塞的，必须在线程池中运行，避免阻塞 FastAPI 事件循环
- **任务锁保护**：同一时间只允许一个破解任务运行，启动新任务前需检查锁状态
- **密码校验同步**：Web API 的密码校验逻辑必须与 CLI 保持一致（仅允许字母和数字）
- **资源清理**：任务终止或完成后，需正确释放引擎实例与 WebSocket 连接
- **错误处理**：所有 API 端点需包含完整的错误处理与友好的错误提示
