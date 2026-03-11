from pydantic import BaseModel, Field

from backend.src import subagents
class SubagentsAppConfig(BaseModel):
    """Configuration for subagents application.
    子代理应用配置。

    Attributes:
        default_timeout_seconds: Default timeout in seconds for subagents (default: 900 = 15 minutes).
        timeout_overrides: Dictionary mapping subagent names to their timeout overrides in seconds.
    """
    timeout_seconds: int = Field(
        default=900, 
        ge=1,# >= 1必须至少为1
        description="Default timeout in seconds for subagents (default: 900 = 15 minutes).")
    agents: dict[str, SubagentOverrideConfig] = Field(
        default_factory=dict,
        description="每个子代理的配置",
    )
    def get_timeout_for(self, agent_name: str) -> int:
        """为特定的子代理获取超时时间。

        Args:
            agent_name: 子代理名称。

        Returns:
            The timeout in seconds, using per-agent override if set, otherwise global default.
        """
        override = self.agents.get(agent_name)
        if override is not None and override.timeout_seconds is not None:
            return override.timeout_seconds
        return self.timeout_seconds

_subagents_config:SubagentsAppConfig = SubagentsAppConfig()
def get_subagents_app_config() -> SubagentsAppConfig:
    """Get the subagents application configuration.
    获取子代理应用配置。

    Returns:
        SubagentsAppConfig instance.
    """
    return _subagents_config