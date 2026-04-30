import logging
from typing import Any

from src.config.extensions_config import ExtensionsConfig, McpServerConfig

logger = logging.getLogger(__name__)

def build_server_params(sever_name:str,config:McpServerConfig)->dict[str,Any]:
    """
    构建MCP服务器参数。

    Args:
        sever_name: 服务器名称
        config: 服务器配置

    Returns:
        包含服务器参数的字典
    """
    transport_type = config.type or "stdio"
    params: dict[str, Any] = {"transport": transport_type}

    if transport_type == "stdio":
        if not config.command:
            raise ValueError(f"MCP server '{server_name}' with stdio transport requires 'command' field")
        params["command"] = config.command
        params["args"] = config.args
        # Add environment variables if present
        if config.env:
            params["env"] = config.env
    elif transport_type in ("sse", "http"):
        if not config.url:
            raise ValueError(f"MCP server '{server_name}' with {transport_type} transport requires 'url' field")
        params["url"] = config.url
        # Add headers if present
        if config.headers:
            params["headers"] = config.headers
    else:
        raise ValueError(f"MCP server '{server_name}' has unsupported transport type: {transport_type}")

    return params

def build_servers_config(extensions_config: ExtensionsConfig) -> dict[str, dict[str, Any]]:
    """
    构建MCP服务器配置。

    Args:
        extensions_config: 扩展配置

    Returns:
        包含服务器配置的字典
    """
    enabled_servers = extensions_config.get_enabled_mcp_servers()

    if not enabled_servers:
        logger.info("No enabled MCP servers found")
        return {}

    servers_config = {}
    for server_name, server_config in enabled_servers.items():
        try:
            servers_config[server_name] = build_server_params(server_name, server_config)
            logger.info(f"Configured MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to configure MCP server '{server_name}': {e}")

    return servers_config




