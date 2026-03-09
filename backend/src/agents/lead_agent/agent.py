import logging
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from src.agents.thread_state import ThreadState
from src.agents.middlewares.middleware_manager import MiddlewareManager
from src.tools import get_available_tools
logger = logging.getLogger(__name__)#创建一个与当前模块同名的日志记录器实例 ，用于在该模块中记录各种级别的日志信息。


def make_lead_agent(config: RunnableConfig):
    """
    创建并返回一个领导智能体。
    """
    from src.models.factory import create_agent_model
    
    middleware_manager = MiddlewareManager(config)
    middlewares = middleware_manager.build_middlewares()

    return create_agent(
        model=create_agent_model(),
        tools=get_available_tools(),
        middleware=middlewares,
        system_prompt="你是一个领导型agent，你需要帮助组织你的工作。",
        state_schema=ThreadState,
    )