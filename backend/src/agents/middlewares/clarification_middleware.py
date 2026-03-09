from langchain.agents.middleware import AgentMiddleware
from collections.abc import Callable
from typing import override
from langchain.agents import AgentState
from langchain_core.messages import ToolMessage
from langgraph.graph import END
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

class ClarificationMiddlewareState(AgentState):
    """
    ClarificationMiddlewareState类，用于存储 ClarificationMiddleware 的状态,继承了AgentState
    """
    # TODO: 目前没有添加新的状态字段，后续也许能根据实际任务做一些个性化定制
    pass

class ClarificationMiddleware(AgentMiddleware[ClarificationMiddlewareState]):
    """
    拦截clarification工具的调用，中断执行以向用户提出问题

    当模型调用'ask_clarification'工具时，会触发该中间件，向用户提出问题：
    1.在执行前拦截工具调用
    2.提取需要澄清的问题和元数据
    3.生成一条用户友好的信息
    4.返回一条打断执行并展示问题的命令
    5.在继续之前等待用户回答
    """
    state_schema = ClarificationMiddlewareState
    def _format_clarification_message(self, args: dict) -> str:
        """Format the clarification arguments into a user-friendly message.

        Args:
            args: The tool call arguments containing clarification details

        Returns:
            Formatted message string
        """
        question = args.get("question", "")
        clarification_type = args.get("clarification_type", "missing_info")
        context = args.get("context")
        options = args.get("options", [])

        # Type-specific icons
        type_icons = {
            "missing_info": "❓",
            "ambiguous_requirement": "🤔",
            "approach_choice": "🔀",
            "risk_confirmation": "⚠️",
            "suggestion": "💡",
        }

        icon = type_icons.get(clarification_type, "❓")

        # Build the message naturally
        message_parts = []

        # Add icon and question together for a more natural flow
        if context:
            # If there's context, present it first as background
            message_parts.append(f"{icon} {context}")
            message_parts.append(f"\n{question}")
        else:
            # Just the question with icon
            message_parts.append(f"{icon} {question}")

        # Add options in a cleaner format
        if options and len(options) > 0:
            message_parts.append("")  # blank line for spacing
            for i, option in enumerate(options, 1):
                message_parts.append(f"  {i}. {option}")

        return "\n".join(message_parts)
    def _handle_clarification(self, request:ToolCallRequest)-> Command:
        """_处理ask_clarification工具调用的方法_

        Args:
            request (ToolCallRequest): _工具调用请求_

        Returns:
            Command: _打断执行并展示问题的命令_
        """
        args=request.tool_call.get("args",{})
        question = args.get("question","")
        tool_call_id = request.tool_call.get("id", "")
        print("[ClarificationMiddleware] Intercepted clarification request")
        print(f"[ClarificationMiddleware] Question: {question}")

        # 格式化问题信息
        formatted_message = self._format_clarification_message(args)
        
        #创建一条包含格式化问题的工具信息
        tool_message = ToolMessage(
            content=formatted_message,
            tool_call_id=tool_call_id,
            name="ask_clarification",
        )
        # 返回一条打断执行并展示问题的命令
        return Command(
            update={"messages": [tool_message]},
            goto=END,
        )


    @override
    def wrap_tool_call(
        self,
        request:ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    )-> Command | ToolMessage:
        """_summary_

        Args:
            request (ToolCallRequest): _工具调用请求_
            handler (Callable[[ToolCallRequest], ToolMessage  |  Command]): _原始的工具处理_

        Returns:
            Command | ToolMessage: _以格式化的澄清信息中断执行的命令_
        """
        if request.tool_call.get("name") != "ask_clarification":
            return handler(request)# 不是ask_clarification工具，直接调用原处理函数
        return self._handle_clarification(request)
    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercept ask_clarification tool calls and interrupt execution (async version).

        Args:
            request: Tool call request
            handler: Original tool execution handler (async)

        Returns:
            Command that interrupts execution with the formatted clarification message
        """
        # Check if this is an ask_clarification tool call
        if request.tool_call.get("name") != "ask_clarification":
            # Not a clarification call, execute normally
            return await handler(request)

        return self._handle_clarification(request)

