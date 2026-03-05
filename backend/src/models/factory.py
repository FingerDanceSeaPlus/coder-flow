from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
def create_agent_model():
    """
    创建并返回一个智能体模型。
    """
    return ChatOpenAI(
        model_name="deepseek-chat",
        base_url="https://api.deepseek.cn/v1",
        api_key=deepseek_api_key,
        temperature=0.7,
    )
