import logging
from dataclasses import replace
from src.subagents.builtins import BUILTIN_SUBAGENTS

from src.subagents.config import SubagentConfig

logger = logging.getLogger(__name__)

def get_subagent_config(name: str) -> SubagentConfig | None:
    """Get a subagent configuration by name, with config.yaml overrides applied.
    通过子代理名称获取子代理配置，同时应用config.yaml中的覆盖。

    Args:
        name: 子代理名称

    Returns:
        子代理配置（如果找到），否则为None。
    """
    config = BUILTIN_SUBAGENTS.get(name)# 从内置子代理中获取配置
    if config is None:
        return None

    # Apply timeout override from config.yaml (lazy import to avoid circular deps)
    from src.config.subagents_config import get_subagents_app_config

    app_config = get_subagents_app_config()
    effective_timeout = app_config.get_timeout_for(name)
    if effective_timeout != config.timeout_seconds:
        logger.debug(f"Subagent '{name}': timeout overridden by config.yaml ({config.timeout_seconds}s -> {effective_timeout}s)")
        config = replace(config, timeout_seconds=effective_timeout)

    return config

def list_subagents() -> list[SubagentConfig]:
    """List all available subagent configurations (with config.yaml overrides applied).

    Returns:
        List of all registered SubagentConfig instances.
    """
    return [get_subagent_config(name) for name in BUILTIN_SUBAGENTS]

def get_subagent_names() -> list[str]:
    """Get all available subagent names.

    Returns:
        List of subagent names.
    """
    return list(BUILTIN_SUBAGENTS.keys())