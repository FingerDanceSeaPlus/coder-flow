import pytest
from langchain_core.runnables import RunnableConfig
from src.agents.lead_agent.agent import make_lead_agent
from src.agents.thread_state import ThreadState
from src.agents.middlewares.middleware_manager import MiddlewareManager


def test_make_lead_agent_creation():
    """测试创建lead_agent是否成功"""
    config = RunnableConfig()
    agent = make_lead_agent(config)
    assert agent is not None
    assert hasattr(agent, "invoke")


def test_middleware_manager_build_middlewares():
    """测试中间件管理器是否正确构建中间件"""
    config = RunnableConfig()
    manager = MiddlewareManager(config)
    middlewares = manager.build_middlewares()
    assert len(middlewares) == 2  # 应该包含摘要和待办事项中间件


def test_thread_state_structure():
    """测试ThreadState结构是否包含todos字段"""
    # 创建一个ThreadState实例
    state = ThreadState(
        messages=[],
        todos=[],
        title="Test Thread"
    )
    assert "todos" in state
    assert isinstance(state["todos"], list)
    assert "title" in state


def test_thread_state_with_todos():
    """测试ThreadState是否能正确处理todos"""
    test_todos = [
        {"content": "Test task 1", "status": "pending"},
        {"content": "Test task 2", "status": "in_progress"}
    ]
    state = ThreadState(
        messages=[],
        todos=test_todos,
        title="Test Thread with Todos"
    )
    assert len(state["todos"]) == 2
    assert state["todos"][0]["content"] == "Test task 1"
    assert state["todos"][1]["status"] == "in_progress"
