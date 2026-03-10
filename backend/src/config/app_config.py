from typing import Self
from src.config.model_config import ModelConfig
from src.config.tool_config import ToolConfig, ToolGroupConfig
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, ConfigDict


class AppConfig(BaseModel):
    """Config for the DeerFlow application"""

    models: list[ModelConfig] = Field(default_factory=list, description="Available models")
    # TODO: 不太懂沙盒，暂时跳过
    #sandbox: SandboxConfig = Field(description="Sandbox configuration")
    tools: list[ToolConfig] = Field(default_factory=list, description="Available tools")
    tool_groups: list[ToolGroupConfig] = Field(default_factory=list, description="Available tool groups")
    # TODO: 不太懂技能，暂时跳过
    #skills: SkillsConfig = Field(default_factory=SkillsConfig, description="Skills configuration")
    #extensions: ExtensionsConfig = Field(default_factory=ExtensionsConfig, description="Extensions configuration (MCP servers and skills state)")
    model_config = ConfigDict(extra="allow", frozen=False)

    def from_file(cls, config_path: str|None=None)->Self:
        """
        从文件加载应用配置。

        参数：
            config_path (str): 配置文件路径。
        返回：
            config (AppConfig): 应用配置。
        """
        path=Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(path,  encoding="utf-8") as f:
            config_data=yaml.safe_load(f)
        # 处理 None 值，确保所有列表字段都有默认值
        if config_data is None:
            config_data = {}
        if config_data.get("tools") is None:
            config_data["tools"] = []
        if config_data.get("models") is None:
            config_data["models"] = []
        if config_data.get("tool_groups") is None:
            config_data["tool_groups"] = []
        reseult=cls.model_validate(config_data) 
        return reseult
    
    def get_model_config(self, name: str) -> ModelConfig | None:
        """
        获取指定名称的模型配置。

        参数：
            name (str): 模型名称。
        返回：
            config (ModelConfig | None): 模型配置，如果不存在则返回 None。
        """
        for model in self.models:
            if model.name == name:
                return model
        return None


def get_app_config() -> AppConfig:
    """
    获取应用配置。

    返回：
        config (AppConfig): 应用配置。
    """
    #TODO: 配置文件路径暂时使用硬编码
    _app_config = AppConfig().from_file("config.yaml")
    return _app_config
