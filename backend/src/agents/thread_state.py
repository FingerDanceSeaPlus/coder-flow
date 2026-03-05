from typing import NotRequired,TypedDict
from langchain.agents import AgentState

class ThreadState(AgentState):
    title: NotRequired[str | None]#线程标题，为对话提供有意义的话题，便于用户识别
    todos: NotRequired[list | None]#存储待办事项列表
    #TODO: 研究是否有必要为算法题额外添加一个状态类