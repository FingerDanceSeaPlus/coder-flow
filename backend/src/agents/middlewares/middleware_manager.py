from langchain_core.runnables import RunnableConfig
from langchain.agents.middleware import AgentMiddleware, SummarizationMiddleware, TodoListMiddleware
from src.agents.middlewares.clarification_middleware import ClarificationMiddleware
from src.agents.middlewares.subagent_limit_middleware import SubagentLimitMiddleware

class MiddlewareManager:
    """
    中间件管理器，用于管理和应用中间件。
    """
    def __init__(self,config: RunnableConfig):
        self.config = config
        self.middlewares = []

    def build_middlewares(self)->list[AgentMiddleware]:
        """
        构建并返回中间件列表。
        """
        self.middlewares=_build_runtime_middlewares(
            include_uploads=True,
            include_dangling_tool_call_patch=True,
            lazy_init=True,
        )
        self.middlewares.append(self._create_summarization_middleware())
        self.middlewares.append(self._create_todo_list_middleware())
        
        subagent_enabled = self.config.get("configurable", {}).get("subagent_enabled", False)
        if subagent_enabled:
            max_concurrent_subagents = self.config.get("configurable", {}).get("max_concurrent_subagents", 3)
            self.middlewares.append(SubagentLimitMiddleware(max_concurrent=max_concurrent_subagents))

        # ClarificationMiddleware should always be last
        self.middlewares.append(ClarificationMiddleware())
        return self.middlewares

    def _create_summarization_middleware(self)->SummarizationMiddleware:
        """
        创建并返回摘要中间件。
        TODO: 先写死，不考虑复杂的配置问题
        """
        model="deepseek-chat"
        trigger=[
                ("messages", 20),
            ]
        keep=("messages", 20)
        self.config
        kwargs = {
            "model": model,
            "trigger": trigger,
            "keep": keep
        }

        return SummarizationMiddleware(**kwargs)

    def _create_todo_list_middleware(self)->TodoListMiddleware:
        """
        创建并返回Todo列表中间件。
        TODO: 先写死，不考虑复杂的配置问题
        """
        system_prompt = """
<todo_list_system>
You have access to the `write_todos` tool to help you manage and track complex multi-step objectives.

**CRITICAL RULES:**
- Mark todos as completed IMMEDIATELY after finishing each step - do NOT batch completions
- Keep EXACTLY ONE task as `in_progress` at any time (unless tasks can run in parallel)
- Update the todo list in REAL-TIME as you work - this gives users visibility into your progress
- DO NOT use this tool for simple tasks (< 3 steps) - just complete them directly

**When to Use:**
This tool is designed for complex objectives that require systematic tracking:
- Complex multi-step tasks requiring 3+ distinct steps
- Non-trivial tasks needing careful planning and execution
- User explicitly requests a todo list
- User provides multiple tasks (numbered or comma-separated list)
- The plan may need revisions based on intermediate results

**When NOT to Use:**
- Single, straightforward tasks
- Trivial tasks (< 3 steps)
- Purely conversational or informational requests
- Simple tool calls where the approach is obvious

**Best Practices:**
- Break down complex tasks into smaller, actionable steps
- Use clear, descriptive task names
- Remove tasks that become irrelevant
- Add new tasks discovered during implementation
- Don't be afraid to revise the todo list as you learn more

**Task Management:**
Writing todos takes time and tokens - use it when helpful for managing complex problems, not for simple requests.
</todo_list_system>
"""

        tool_description = """Use this tool to create and manage a structured task list for complex work sessions.

**IMPORTANT: Only use this tool for complex tasks (3+ steps). For simple requests, just do the work directly.**

## When to Use

Use this tool in these scenarios:
1. **Complex multi-step tasks**: When a task requires 3 or more distinct steps or actions
2. **Non-trivial tasks**: Tasks requiring careful planning or multiple operations
3. **User explicitly requests todo list**: When the user directly asks you to track tasks
4. **Multiple tasks**: When users provide a list of things to be done
5. **Dynamic planning**: When the plan may need updates based on intermediate results

## When NOT to Use

Skip this tool when:
1. The task is straightforward and takes less than 3 steps
2. The task is trivial and tracking provides no benefit
3. The task is purely conversational or informational
4. It's clear what needs to be done and you can just do it

## How to Use

1. **Starting a task**: Mark it as `in_progress` BEFORE beginning work
2. **Completing a task**: Mark it as `completed` IMMEDIATELY after finishing
3. **Updating the list**: Add new tasks, remove irrelevant ones, or update descriptions as needed
4. **Multiple updates**: You can make several updates at once (e.g., complete one task and start the next)

## Task States

- `pending`: Task not yet started
- `in_progress`: Currently working on (can have multiple if tasks run in parallel)
- `completed`: Task finished successfully

## Task Completion Requirements

**CRITICAL: Only mark a task as completed when you have FULLY accomplished it.**

Never mark a task as completed if:
- There are unresolved issues or errors
- Work is partial or incomplete
- You encountered blockers preventing completion
- You couldn't find necessary resources or dependencies
- Quality standards haven't been met

If blocked, keep the task as `in_progress` and create a new task describing what needs to be resolved.

## Best Practices

- Create specific, actionable items
- Break complex tasks into smaller, manageable steps
- Use clear, descriptive task names
- Update task status in real-time as you work
- Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
- Remove tasks that are no longer relevant
- **IMPORTANT**: When you write the todo list, mark your first task(s) as `in_progress` immediately
- **IMPORTANT**: Unless all tasks are completed, always have at least one task `in_progress` to show progress

Being proactive with task management demonstrates thoroughness and ensures all requirements are completed successfully.

**Remember**: If you only need a few tool calls to complete a task and it's clear what to do, it's better to just do the task directly and NOT use this tool at all.
"""
        return TodoListMiddleware(system_prompt=system_prompt, tool_description=tool_description)


def _build_runtime_middlewares(
    *,
    include_uploads: bool,
    include_dangling_tool_call_patch: bool,
    lazy_init: bool = True,
) -> list[AgentMiddleware]:
    """Build shared base middlewares for agent execution."""
    from src.agents.middlewares.thread_data_middleware import ThreadDataMiddleware
    from src.sandbox.middleware import SandboxMiddleware
    from src.agents.middlewares.tool_error_handling_middleware import ToolErrorHandlingMiddleware

    middlewares: list[AgentMiddleware] = [
        ThreadDataMiddleware(lazy_init=lazy_init),
        SandboxMiddleware(lazy_init=lazy_init),
    ]
    """
    TODO: 暂时先忽略上传文件之类的中间件
    if include_uploads:
        from deerflow.agents.middlewares.uploads_middleware import UploadsMiddleware

        middlewares.insert(1, UploadsMiddleware())

    if include_dangling_tool_call_patch:
        from deerflow.agents.middlewares.dangling_tool_call_middleware import DanglingToolCallMiddleware

        middlewares.append(DanglingToolCallMiddleware())
    """
    middlewares.append(ToolErrorHandlingMiddleware())
    return middlewares