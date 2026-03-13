# 内置工具文档

本文档描述了系统中实现的两个核心内置工具：`ask_clarification_tool` 和 `task_tool`，包括它们的功能、设计思路和实现原理。

## 1. ask_clarification_tool - 澄清请求工具

### 1.1 工具概述

`ask_clarification_tool` 是一个用于向用户请求澄清信息的工具，当代理无法继续执行任务而需要更多用户输入时使用。该工具允许代理以结构化的方式向用户提问，并等待用户的响应后继续执行。

### 1.2 核心功能

- **多种澄清类型**：支持5种预设的澄清类型，覆盖常见的澄清场景
- **上下文提供**：可选择性提供上下文信息，帮助用户理解澄清需求的背景
- **选项支持**：对于方法选择或建议类型，可以提供预设选项供用户选择
- **执行中断**：调用该工具会中断当前执行流程，等待用户响应

### 1.3 设计思路

该工具采用了清晰的分层设计：

1. **工具接口层**：通过 `@tool` 装饰器定义工具接口和参数规范
2. **类型安全层**：使用 `Literal` 类型确保澄清类型的合法性
3. **中间件处理层**：实际的中断和用户交互逻辑由 `ClarificationMiddleware` 处理
4. **文档驱动设计**：详细的文档字符串指导用户如何正确使用该工具

### 1.4 实现原理

```python
@tool("ask_clarification", parse_docstring=True, return_direct=True)
def ask_clarification_tool(
    question: str,
    clarification_type: Literal["missing_info", "ambiguous_requirement", "approach_choice", "risk_confirmation", "suggestion"],
    context: str|None = None,
    options: list[str]|None = None,
)->str:
    # 占位符，实际逻辑在ClarificationMiddleware实现
    return "Clarification request processed by middleware"
```

该工具的实现特点：

- 使用 `return_direct=True` 确保工具的返回值直接传递给中间件处理
- 工具本身只是一个占位符，实际中断和用户交互逻辑由中间件实现
- 详细的文档字符串包含了使用场景、最佳实践和参数说明

### 1.5 支持的澄清类型

| 类型 | 描述 | 使用场景 |
|------|------|----------|
| missing_info | 缺少必要信息 | 文件路径、URL、具体需求等未提供 |
| ambiguous_requirement | 需求模糊 | 有多种有效解释的情况 |
| approach_choice | 方法选择 | 存在多种有效实现方法，需要用户偏好 |
| risk_confirmation | 风险确认 | 即将执行破坏性操作，需要明确确认 |
| suggestion | 建议 | 有推荐方案但需要用户批准 |

### 1.6 最佳实践

- 每次只提一个澄清问题，保持清晰
- 问题要具体明确，避免模糊
- 不要在需要澄清时做出假设
- 对于有风险的操作，必须先请求确认
- 提供足够的上下文帮助用户理解情况

## 2. task_tool - 子代理任务委托工具

### 2.1 工具概述

`task_tool` 是一个用于将任务委托给专门子代理的工具，子代理在独立的上下文中运行。该工具允许主代理将复杂任务分解为子任务，由更专业的代理完成，从而提高整体执行效率和质量。

### 2.2 核心功能

- **子代理类型支持**：目前支持 "general-purpose" 类型子代理
- **任务隔离**：子代理在独立的上下文中运行，避免干扰主代理
- **异步执行**：任务以异步方式执行，主代理可以继续其他操作
- **状态跟踪**：实时跟踪任务执行状态和进度
- **配置覆盖**：支持覆盖子代理的默认配置，如最大轮次数
- **超时保护**：内置超时机制，防止任务无限执行

### 2.3 设计思路

该工具的设计遵循了以下原则：

1. **职责分离**：主代理专注于任务分解和结果整合，子代理专注于具体任务执行
2. **上下文隔离**：子代理拥有独立的上下文，避免上下文污染
3. **异步处理**：采用异步执行模型，提高系统整体效率
4. **实时反馈**：通过事件流提供任务执行的实时状态更新
5. **安全防护**：防止子代理嵌套调用，避免无限递归

### 2.4 实现原理

```python
@tool("task", parse_docstring=True)
def task_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    description: str,
    prompt: str,
    subagent_type: Literal["general-purpose"],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_turns: int|None=None,
)->str:
    # 获取子代理配置
    config = get_subagent_config(subagent_type)
    # 配置覆盖
    if max_turns is not None:
        config = replace(config, max_turns=max_turns)
    # 提取父上下文
    sandbox_state = runtime.state.get("sandbox")
    # ...
    # 创建执行器
    executor = SubagentExecutor(
        config=config,
        tools=tools,
        parent_model=parent_model,
        sandbox_state=sandbox_state,
        # ...
    )
    # 异步执行任务
    task_id = executor.execute_async(task=prompt)
    # 轮询任务状态
    while True:
        result = get_background_task_result(task_id)
        # 检查任务状态并返回结果
```

### 2.5 技术特点

1. **配置系统**：
   - 通过 `get_subagent_config` 获取子代理配置
   - 支持通过 `replace` 函数覆盖默认配置

2. **上下文传递**：
   - 从运行时提取沙箱状态、线程数据等上下文信息
   - 子代理继承父代理的模型配置
   - 生成跟踪ID用于分布式追踪

3. **工具管理**：
   - 通过 `get_available_tools` 获取可用工具
   - 禁用子代理工具，防止嵌套调用
   - 根据父代理模型选择合适的工具集

4. **异步执行**：
   - 使用 `execute_async` 方法异步执行任务
   - 通过 `get_background_task_result` 轮询任务状态
   - 实现了自定义的超时机制

5. **事件驱动**：
   - 通过流写入器发送任务状态事件
   - 支持的事件类型：task_started、task_running、task_completed、task_failed、task_timed_out

### 2.6 工作流程

1. **任务委托**：主代理调用 `task_tool`，指定任务描述、提示和子代理类型
2. **配置准备**：获取子代理配置并应用覆盖设置
3. **上下文准备**：提取父代理的上下文信息
4. **工具选择**：选择适合子代理的工具集，禁用子代理工具
5. **执行器创建**：创建 `SubagentExecutor` 实例
6. **异步执行**：调用 `execute_async` 异步执行任务
7. **状态跟踪**：轮询任务状态，发送实时事件
8. **结果处理**：根据任务状态返回结果或错误信息

### 2.7 使用场景

- **复杂任务**：需要多步骤或多工具的复杂任务
- **冗长输出**：会产生大量输出的任务
- **上下文隔离**：需要与主对话隔离上下文的任务
- **并行处理**：需要并行执行的研究或探索任务

### 2.8 不适用场景

- **简单操作**：单步骤或简单的操作（直接使用工具即可）
- **用户交互**：需要用户交互或澄清的任务

## 3. 工具集成与扩展

### 3.1 工具注册机制

这两个工具都是通过 `@tool` 装饰器注册到系统中的，支持自动解析文档字符串生成工具描述。

### 3.2 扩展性设计

- **ask_clarification_tool**：可以通过扩展 `ClarificationMiddleware` 来增强其功能
- **task_tool**：支持添加新的子代理类型，通过扩展 `get_subagent_config` 函数实现

### 3.3 安全考虑

- **task_tool** 内置了防止子代理嵌套调用的机制
- 两个工具都有严格的参数验证和类型检查
- 任务执行有超时保护，防止资源耗尽

## 4. 总结

`ask_clarification_tool` 和 `task_tool` 是系统中的两个核心内置工具，它们分别解决了不同的问题：

- `ask_clarification_tool` 提供了与用户进行结构化交互的能力，确保代理在缺少信息时能够及时获取用户指导
- `task_tool` 实现了任务分解和委托机制，允许系统将复杂任务分配给更专业的子代理，提高了系统的整体能力和效率

这两个工具的设计都遵循了良好的软件工程原则，包括模块化、可扩展性和安全性，为系统的健壮性和灵活性提供了有力支持。