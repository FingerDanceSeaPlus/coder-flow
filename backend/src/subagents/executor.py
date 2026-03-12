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
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage
import threading
from concurrent.futures import TimeoutError as FuturesTimeoutError

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
        # TODO： 添加沙盒相关的中间件，目前沙盒尚未实现
        #from src.agents.middlewares.thread_data_middleware import ThreadDataMiddleware
        #from src.sandbox.middleware import SandboxMiddleware
        mideedwares = [
            #ThreadDataMiddleware(self.thread_data),
            #SandboxMiddleware(self.sandbox_state),
        ]
        return create_agent(
            model=model,
            tools=self.tools,
            middlewares=mideedwares,
            system_prompt=self.config.system_prompt,
            state_schema=ThreadState,
        )
    
    def _build_initial_state(self,task:str) -> dict[str, Any]:
        """Build initial state for the agent.

        Args:
            task: The task description.

        Returns:
            Initial state dictionary.
        """
        state: dict[str, Any] = {
            "messages": [HumanMessage(content=task)],
        }

        # Pass through sandbox and thread data from parent
        if self.sandbox_state is not None:
            state["sandbox"] = self.sandbox_state
        if self.thread_data is not None:
            state["thread_data"] = self.thread_data

        return state

    def execute(self, task: str,result_holder: SubagentResult|None = None)->SubagentResult:
        """同步执行一个任务

        Args:
            task: The task description.
            result_holder: 可选的在执行过程中更新的提前构建的结果对象

        Returns:
            SubagentResult containing the output.
        """
        if result_holder is not None:
            result=result_holder
        else:
            task_id = str(uuid.uuid4())[:8]
            result = SubagentResult(
                task_id=task_id,
                trace_id=self.trace_id,
                status=SubagentStatus.RUNNING,
                start_time=datetime.now(),
            )
        try:
            agent = self._create_agent()
            state=self._build_initial_state(task)

            run_config: RunnableConfig = {
                "recursion_limit": self.config.max_turns,
            }

            context={}
            if self.thread_id:
                run_config["configurable"] = {"thread_id": self.thread_id}
                context["thread_id"] = self.thread_id

            logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} starting execution with max_turns={self.config.max_turns}")
            
            # 使用流式输出以获得实时信息
            final_state = None
            for chunk in agent.stream(state, config=run_config, context=context, stream_mode="values"):  # type: ignore[arg-type]
                final_state = chunk

                # 从当前状态中提取AI信息
                messages = chunk.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    # Check if this is a new AI message
                    if isinstance(last_message, AIMessage):
                        # Convert message to dict for serialization
                        message_dict = last_message.model_dump()
                        # Only add if it's not already in the list (avoid duplicates)
                        # Check by comparing message IDs if available, otherwise compare full dict
                        message_id = message_dict.get("id")
                        is_duplicate = False
                        # 假如message_id存在，检查是否已存在相同ID的消息，否则直接比较内容
                        if message_id:
                            is_duplicate = any(msg.get("id") == message_id for msg in result.ai_messages)
                        else:
                            is_duplicate = message_dict in result.ai_messages

                        if not is_duplicate:
                            result.ai_messages.append(message_dict)
                            logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} captured AI message #{len(result.ai_messages)}")
            logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} finished execution")
            
            if final_state is None:
                logger.warning(f"[trace={self.trace_id}] Subagent {self.config.name} did not produce any output")
                result.result="No response generated"
            else:
                # Extract the final message - find the last AIMessage
                messages = final_state.get("messages", [])
                logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} final messages count: {len(messages)}")

                # Find the last AIMessage in the conversation
                last_ai_message = None
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        last_ai_message = msg
                        break
                if last_ai_message is not None:
                    content = last_ai_message.content
                    # Handle both str and list content types for the final result
                    if isinstance(content, str):
                        result.result = content
                    elif isinstance(content, list):
                        # Extract text from list of content blocks for final result only
                        text_parts = []
                        for block in content:
                            if isinstance(block, str):
                                text_parts.append(block)
                            elif isinstance(block, dict) and "text" in block:
                                text_parts.append(block["text"])
                        result.result = "\n".join(text_parts) if text_parts else "No text content in response"
                    else:
                        result.result = str(content)
                elif messages:
                    # Fallback: use the last message if no AIMessage found
                    last_message = messages[-1]
                    logger.warning(f"[trace={self.trace_id}] Subagent {self.config.name} no AIMessage found, using last message: {type(last_message)}")
                    result.result = str(last_message.content) if hasattr(last_message, "content") else str(last_message)
                else:
                    logger.warning(f"[trace={self.trace_id}] Subagent {self.config.name} no messages in final state")
                    result.result = "No response generated"
            result.status=SubagentStatus.COMPLETED
            result.end_time=datetime.now()

        except Exception as e:
            logger.exception(f"[trace={self.trace_id}] Subagent {self.config.name} execution failed")
            result.status = SubagentStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()

        return result
    

    def execute_async(self, task: str,task_id: str|None=None) -> str:
        """_summary_

        Args:
            task (str): _description of the task for subagent_
            task_id (str | None, optional): _description_. Defaults to None.

        Returns:
            str: _Task ID that can be used to check status later._
        """

        if task_id is None:
            task_id = str(uuid.uuid4())[:8]

        # Create initial pending result
        result = SubagentResult(
            task_id=task_id,
            trace_id=self.trace_id,
            status=SubagentStatus.PENDING,
        )

        logger.info(f"[trace={self.trace_id}] Subagent {self.config.name} starting async execution, task_id={task_id}, timeout={self.config.timeout_seconds}s")

        with _background_tasks_lock:
            _background_tasks[task_id] = result

        # 提交到规划线程池
        def run_task():
            with _background_tasks_lock:
                _background_tasks[task_id].status = SubagentStatus.RUNNING
                _background_tasks[task_id].started_at = datetime.now()
                result_holder = _background_tasks[task_id]
            
            try:
                execution_future:Future=_executor_pool.submit(self.execute, task,result_holder)
                try:
                    exec_result = execution_future.result(timeout=self.config.timeout_seconds)# 等待执行完成，返回结果，设置超时
                    with _background_tasks_lock:
                            _background_tasks[task_id].status = exec_result.status
                            _background_tasks[task_id].result = exec_result.result
                            _background_tasks[task_id].error = exec_result.error
                            _background_tasks[task_id].completed_at = datetime.now()
                            _background_tasks[task_id].ai_messages = exec_result.ai_messages
                except FuturesTimeoutError:
                    logger.error(f"[trace={self.trace_id}] Subagent {self.config.name} execution timed out after {self.config.timeout_seconds}s")
                    with _background_tasks_lock:
                        _background_tasks[task_id].status = SubagentStatus.TIMED_OUT
                        _background_tasks[task_id].error = f"Execution timed out after {self.config.timeout_seconds} seconds"
                        _background_tasks[task_id].completed_at = datetime.now()
                    # Cancel the future (best effort - may not stop the actual execution)
                    execution_future.cancel()
            except Exception as e:
                logger.exception(f"[trace={self.trace_id}] Subagent {self.config.name} execution failed")
                with _background_tasks_lock:
                    _background_tasks[task_id].status = SubagentStatus.FAILED
                    _background_tasks[task_id].error = str(e)
                    _background_tasks[task_id].completed_at = datetime.now()

        _scheduler_pool.submit(run_task)
        return task_id

MAX_CONCURRENT_SUBAGENTS = 3

def get_background_task_result(task_id: str) -> SubagentResult | None:
    """Get the result of a background task.

    Args:
        task_id: The task ID returned by execute_async.

    Returns:
        SubagentResult if found, None otherwise.
    """
    with _background_tasks_lock:
        return _background_tasks.get(task_id)

def list_background_tasks() -> list[SubagentResult]:
    """List all background tasks.

    Returns:
        List of all SubagentResult instances.
    """
    with _background_tasks_lock:
        return list(_background_tasks.values())







