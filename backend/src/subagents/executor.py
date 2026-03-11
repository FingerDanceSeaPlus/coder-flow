import logging
from os import name
import uuid
logger=logging.getLogger(__name__)
from typing import Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import Future, ThreadPoolExecutor
from src.subagents.config import SubagentConfig
from langchain.tools import BaseTool
from src.agents.thread_state import ThreadDataState, ThreadState, SandboxState
from src.models import create_chat_model
class SubagentStatus(Enum):
    """Status of a subagent execution."""

    PENDING = "pending"# 待执行
    RUNNING = "running"# 运行中
    COMPLETED = "completed"# 已完成
    FAILED = "failed"# 失败
    TIMED_OUT = "timed_out"# 超时

@dataclass
class SubagentResult:
    """Result of a subagent execution."""

    task_id: str
    trace_id: str
    status: SubagentStatus
    result: str | None = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    ai_messages: list[dict[str, Any]] | None = None

    def __post_init__(self):
        if self.ai_messages is None:
            self.ai_messages = []

# Global storage for background task results
_background_tasks: dict[str, SubagentResult] = {}
_background_tasks_lock = threading.Lock()

# 背景任务规划和编排的线程池
_scheduler_pool = ThreadPoolExecutor(max_workers=3,thread_name_prefix="subagent-scheduler")
# 子代理实际执行的线程池
# 构建更大的线程池防止规划者提交执行任务时发生阻塞
_executor_pool = ThreadPoolExecutor(max_workers=10,thread_name_prefix="subagent-executor")



def _filter_tools(
    all_tools: list[str], 
    allowed_tools: list[str] | None,
    disallowed_tools: list[str] | None
)->list[BaseTool]:
    """Filter tools based on allowed and disallowed lists.

    Args:
        all_tools: All available tools.
        allowed_tools: List of allowed tools (None means all are allowed).
        disallowed_tools: List of disallowed tools (None means none are disallowed).

    Returns:
        List of filtered tools.
    """
    filtered=all_tools
    if allowed_tools is not None:
        all_allowed = set(allowed_tools)
        filtered = [tool for tool in filtered if tool in all_allowed]
    if disallowed_tools is not None:
        all_disallowed = set(disallowed_tools)
        filtered = [tool for tool in filtered if tool not in all_disallowed]
    return filtered


def _get_model_name(config: SubagentConfig, parent_model: str | None) -> str | None:
    """为子代理获取模型名称

    Args:
        config: Subagent configuration.
        parent_model: The parent agent's model name.

    Returns:
        Model name to use, or None to use default.
    """
    if config.model == "inherit":
        return parent_model
    return config.model

class SubagentExecutor:
    """Executor for subagents."""

    def __init__(
        self,
        config: SubagentConfig,
        tools:list[BaseTool],
        parent_model: str | None = None,
        sandbox_state:SandboxState | None = None,
        thread_data:ThreadDataState | None = None,
        thread_id:str | None = None,
        trace_id:str | None = None,
    ):
        """Initialize the executor.

        Args:
            config: Subagent configuration.
            tools: Tools to use.
            parent_model: The parent agent's model name.
            sandbox_state: Sandbox state.
            thread_data: Thread data.
            thread_id: Thread ID.
            trace_id: Trace ID.
        """
        self.config = config
        self.parent_model = parent_model
        self.sandbox_state = sandbox_state
        self.thread_data = thread_data
        self.thread_id = thread_id
        self.trace_id = trace_id or str(uuid.uuid4())[:8]

        self.tools = _filter_tools(
            all_tools=tools,
            allowed_tools=config.tools,
            disallowed_tools=config.disallowed_tools,
        )
        
        logger.info(f"[trace={self.trace_id}] SubagentExecutor initialized: {config.name} with {len(self.tools)} tools")

    def _create_agent(self):
        """创建agent实例"""
        model_name = _get_model_name(self.config, self.parent_model)
        model = create_chat_model(name=model_name,thinking_enabled=False)

        from src.agents.middlewares.thread_data_middleware import ThreadDataMiddleware
        from src.sandbox.middleware import SandboxMiddleware

        