from langchain_core.runnables import RunnableConfig
from langchain.agents.middleware import AgentMiddleware, SummarizationMiddleware, TodoListMiddleware

class MiddlewareManager:
    """
    中间件管理器，用于管理和应用中间件。
    """
    def __init__(self,config: RunnableConfig):
        config = config
        self.middlewares = []

    def build_middlewares(self)->list[AgentMiddleware]:
        """
        构建并返回中间件列表。
        """
        self.middlewares.append(self._create_summarization_middleware())
        self.middlewares.append(self._create_todo_list_middleware())
        return self.middlewares

    def _create_summarization_middleware(self)->SummarizationMiddleware:
        """
        创建并返回摘要中间件。
        TODO: 先写死，不考虑复杂的配置问题
        """
        model="deepseek-chat"
        trigger=[
                ("tokens", 30000),
                ("messages", 20),
            ]
        keep=("messages", 10)
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
        return TodoListMiddleware()