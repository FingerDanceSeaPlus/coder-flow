# Checkpointer 模块

## 1. 模块概述

Checkpointer 是 LangGraph 框架的核心组件，负责**状态持久化与恢复**功能。它提供了统一的 API 来管理 LangGraph 运行时的检查点（checkpoint），支持多种存储后端，并提供了同步和异步两种使用方式。

## 2. 核心功能

### 2.1 状态持久化
- 保存 LangGraph 运行时的完整状态（节点、边、当前位置、历史记录等）
- 支持在不同执行环境中恢复之前的运行状态
- 实现 agent 工作流的断点续传功能

### 2.2 多后端支持
- **内存存储**：`InMemorySaver`，适合临时测试和开发
- **SQLite**：轻量级文件数据库，适合单机应用和小型部署
- **PostgreSQL**：企业级关系型数据库，适合分布式应用和高可靠性要求

### 2.3 双重 API 设计
- **同步 API**：用于 CLI 工具、脚本和非异步环境
- **异步 API**：用于 FastAPI 等异步服务器环境，支持高并发

## 3. 安装依赖

根据选择的后端存储，需要安装相应的依赖：

### SQLite 后端
```bash
uv add langgraph-checkpoint-sqlite
```

### PostgreSQL 后端
```bash
uv add langgraph-checkpoint-postgres psycopg[binary] psycopg-pool
```

## 4. API 参考

### 4.1 同步 API

#### `get_checkpointer() -> Checkpointer`
获取全局同步检查点单例，首次调用时创建。

**特点**：
- 全局共享一个检查点实例
- 进程退出时自动关闭
- 适合需要长期使用检查点的场景

**使用示例**：
```python
from src.agents.checkpointer import get_checkpointer

# 获取单例检查点
checkpointer = get_checkpointer()

# 在 LangGraph 中使用
graph = Graph(
    nodes=...,  
    edges=...,
    checkpointer=checkpointer
)

# 调用时指定线程 ID，支持状态恢复
graph.invoke(
    input_data,
    config={"configurable": {"thread_id": "user_123"}}
)
```

#### `reset_checkpointer() -> None`
重置同步单例，关闭当前检查点并清除缓存。

**使用场景**：
- 测试环境中需要重新初始化检查点
- 配置更改后需要刷新检查点实例

**示例**：
```python
from src.agents.checkpointer import reset_checkpointer, get_checkpointer

# 重置当前检查点
reset_checkpointer()

# 获取新的检查点实例（会根据最新配置创建）
new_checkpointer = get_checkpointer()
```

#### `checkpointer_context() -> Iterator[Checkpointer]`
同步上下文管理器，每次调用创建新实例，退出上下文时自动清理。

**特点**：
- 不维护全局状态
- 资源自动管理
- 适合 CLI 脚本或测试场景

**使用示例**：
```python
from src.agents.checkpointer import checkpointer_context

# 每次使用新的检查点实例
with checkpointer_context() as checkpointer:
    graph = Graph(..., checkpointer=checkpointer)
    result = graph.invoke(...)
    assert result == expected
```

### 4.2 异步 API

#### `make_checkpointer() -> AsyncIterator[Checkpointer]`
异步上下文管理器，创建异步检查点实例并在退出时清理资源。

**特点**：
- 异步操作，适合高并发环境
- 不维护全局状态
- 资源自动管理

**使用示例（FastAPI）**：
```python
from fastapi import FastAPI
from src.agents.checkpointer import make_checkpointer

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # 初始化异步检查点
    async with make_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield

# 在路由中使用
@app.post("/run")
async def run_graph(input_data: dict):
    graph = Graph(
        nodes=...,  
        edges=...,
        checkpointer=app.state.checkpointer
    )
    result = await graph.ainvoke(
        input_data,
        config={"configurable": {"thread_id": "user_123"}}
    )
    return result
```

## 5. 配置说明

在 `config.yaml` 文件中配置检查点：

### 5.1 内存存储（默认）
```yaml
checkpointer:
  type: memory
```

### 5.2 SQLite 存储
```yaml
checkpointer:
  type: sqlite
  connection_string: ".deer-flow/checkpoints.db"  # 文件路径
  # 或使用内存数据库
  # connection_string: ":memory:"
```

### 5.3 PostgreSQL 存储
```yaml
checkpointer:
  type: postgres
  connection_string: "postgresql://user:pass@localhost:5432/db"
```

## 6. 模块结构

```
checkpointer/
├── __init__.py          # 公共 API 导出
├── provider.py         # 同步检查点实现
├── async_provider.py   # 异步检查点实现
└── readme.md           # 模块文档
```

## 7. 设计原理

### 7.1 初始化流程
1. 检查配置文件中的检查点设置
2. 根据配置类型选择合适的后端
3. 动态导入所需的依赖包
4. 初始化后端连接并设置数据库（如果需要）
5. 返回配置好的检查点实例

### 7.2 状态管理
- **存储**：将 LangGraph 运行时状态序列化并保存到后端
- **检索**：根据线程 ID 和步骤 ID 恢复之前的状态
- **清理**：自动管理连接池和资源，防止泄漏

### 7.3 错误处理
- 提供清晰的错误消息，包括缺失依赖的安装指南
- 处理配置错误和连接问题
- 确保资源正确释放，即使在异常情况下

## 8. 最佳实践

### 8.1 环境选择
- **开发/测试**：使用内存存储或 SQLite
- **生产环境**：使用 PostgreSQL 以获得更好的性能和可靠性

### 8.2 资源管理
- 在长时间运行的应用中使用单例模式（`get_checkpointer()`）
- 在脚本或测试中使用上下文管理器（`checkpointer_context()` 或 `make_checkpointer()`）
- 在配置更改后调用 `reset_checkpointer()` 刷新实例

### 8.3 性能考虑
- 内存存储最快但不持久
- SQLite 适合低并发场景
- PostgreSQL 适合高并发和分布式环境

### 8.4 数据安全
- 定期备份 SQLite 文件或 PostgreSQL 数据库
- 生产环境中使用强密码和安全连接字符串
- 限制数据库访问权限

## 9. 常见问题

### 9.1 为什么检查点不持久化？
- 检查是否使用了内存存储类型（`type: memory`）
- 检查 SQLite 文件路径是否正确且有写入权限
- 检查 PostgreSQL 连接是否正常

### 9.2 如何在测试中使用检查点？
```python
from src.agents.checkpointer import checkpointer_context, reset_checkpointer

def test_graph_execution():
    with checkpointer_context() as checkpointer:
        graph = Graph(..., checkpointer=checkpointer)
        result = graph.invoke(...)
        assert result == expected
    
    # 测试后重置单例
    reset_checkpointer()
```

### 9.3 如何切换检查点后端？
1. 安装新后端的依赖
2. 修改 `config.yaml` 中的 `checkpointer` 配置
3. 调用 `reset_checkpointer()`（仅同步 API）
4. 重启应用

## 10. 版本兼容性

- 兼容 LangGraph 最新版本
- 支持 Python 3.10+
- 同步 API 兼容所有 Python 环境
- 异步 API 要求支持 `asyncio`

## 11. 许可证

该模块遵循与项目相同的许可证。