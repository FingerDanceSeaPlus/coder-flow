from langchain.tools import BaseTool
from src.config.app_config import get_app_config
from src.reflection.resolvers import resolve_variable
from src.tools.builtiins import ask_clarification_tool
from src.tools.builtiins import present_file_tool

import logging
logger = logging.getLogger(__name__)#创建一个与当前模块同名的日志记录器实例 ，用于在该模块中记录各种级别的日志信息。
from src.tools.builtiins import task_tool
# 内建工具
BUILTIN_TOOLS = [
    present_file_tool,
    ask_clarification_tool,
]
# 子代理工具
SUBAGENT_TOOLS = [
    task_tool,
]
def get_available_tools(
    groups: list[str] | None = None,
    include_mcp: bool = True,
    model_name: str | None = None,#TODO: 有些参数尚未使用
    subagent_enabled: bool = True,
)->list[BaseTool]:
    """
    返回可用的工具列表。

    参数：
        groups (list[str] | None): 工具组列表。
        include_mcp (bool): 是否包含MCP工具。
        subagent_enabled (bool): 是否启用子智能体。
    返回：
        tools (list[Tool]): 可用的工具列表。
    """
    config=get_app_config()
     # 处理字典类型的工具配置
    loaded_tools = []
    for tool in config.tools:
        if isinstance(tool, dict):
            # 从字典中获取use属性
            use_value = tool.get('use')
            if use_value:
                loaded_tools.append(resolve_variable(use_value, BaseTool))
        else:
            # 处理对象类型的工具配置
            loaded_tools.append(resolve_variable(tool.use, BaseTool))
    
    # TODO: 添加MCP工具
    builtin_tools=BUILTIN_TOOLS.copy()
    if subagent_enabled:
        builtin_tools.extend(SUBAGENT_TOOLS)
        logger.info(f"Enabled subagent tools: {SUBAGENT_TOOLS}")

    return loaded_tools+builtin_tools