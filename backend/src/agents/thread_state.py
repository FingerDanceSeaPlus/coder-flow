from typing import Annotated,NotRequired,TypedDict
from langchain.agents import AgentState

class SandboxState(TypedDict):
    sandbox_id: NotRequired[str | None]
    
class ThreadDataState(TypedDict):
    workspace_path: NotRequired[str | None]
    uploads_path: NotRequired[str | None]
    outputs_path: NotRequired[str | None]
class ThreadState(AgentState):
    #sandbox: NotRequired[SandboxState | None]沙盒状态，不懂先注释掉
    thread_data: NotRequired[ThreadDataState | None]#存储线程相关的路径信息
    title: NotRequired[str | None]#线程标题，为对话提供有意义的话题，便于用户识别
    #artifacts: Annotated[list[str], merge_artifacts]存储生成的工件路径列表，不懂
    todos: NotRequired[list | None]#存储待办事项列表
    #uploaded_files: NotRequired[list[dict] | None]暂时不需要上传文件
    #viewed_images: Annotated[dict[str, ViewedImageData], merge_viewed_images]暂时不需要视觉支持
    #TODO: 研究是否有必要为算法题额外添加一个状态类