"""Unified extensions configuration for MCP servers and skills."""

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class McpOAuthConfig(BaseModel):
    """OAuth configuration for an MCP server (HTTP/SSE transports)."""

    enabled: bool = Field(default=True, description="Whether OAuth token injection is enabled")#控制是否启用OAuth令牌注入功能
    token_url: str = Field(description="OAuth token endpoint URL")#OAuth令牌端点URL
    grant_type: Literal["client_credentials", "refresh_token"] = Field(#OAuth授权类型，支持客户端凭证和刷新令牌两种模式
        default="client_credentials",
        description="OAuth grant type",
    )
    client_id: str | None = Field(default=None, description="OAuth client ID")#OAuth客户端ID
    client_secret: str | None = Field(default=None, description="OAuth client secret")#OAuth客户端密钥
    refresh_token: str | None = Field(default=None, description="OAuth refresh token (for refresh_token grant)")#OAuth刷新令牌（仅用于刷新令牌授权模式）
    scope: str | None = Field(default=None, description="OAuth scope")#OAuth作用域
    audience: str | None = Field(default=None, description="OAuth audience (provider-specific)")#OAuth受众（根据OAuth提供程序而异）
    token_field: str = Field(default="access_token", description="Field name containing access token in token response")#令牌响应中包含访问令牌的字段名
    token_type_field: str = Field(default="token_type", description="Field name containing token type in token response")#令牌响应中包含令牌类型的字段名
    expires_in_field: str = Field(default="expires_in", description="Field name containing expiry (seconds) in token response")#令牌响应中包含过期时间（秒）的字段名
    default_token_type: str = Field(default="Bearer", description="Default token type when missing in token response")#令牌响应中缺失令牌类型时的默认值
    refresh_skew_seconds: int = Field(default=60, description="Refresh token this many seconds before expiry")  #刷新令牌提前多少秒刷新
    extra_token_params: dict[str, str] = Field(default_factory=dict, description="Additional form params sent to token endpoint")#令牌端点额外的表单参数
    model_config = ConfigDict(extra="allow")


class McpServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    enabled: bool = Field(default=True, description="Whether this MCP server is enabled")#控制是否启用此MCP服务器
    type: str = Field(default="stdio", description="Transport type: 'stdio', 'sse', or 'http'")#MCP服务器传输类型，支持标准输入输出、Server-Sent Events（SSE）和HTTP/HTTPS
    command: str | None = Field(default=None, description="Command to execute to start the MCP server (for stdio type)")#启动MCP服务器的命令（仅适用于stdio类型）
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the command (for stdio type)")#传递给命令的参数（仅适用于stdio类型）
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables for the MCP server")#MCP服务器的环境变量
    url: str | None = Field(default=None, description="URL of the MCP server (for sse or http type)")#MCP服务器的URL（仅适用于SSE或HTTP/HTTPS类型）
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers to send (for sse or http type)")#发送到MCP服务器的HTTP头（仅适用于SSE或HTTP/HTTPS类型）
    oauth: McpOAuthConfig | None = Field(default=None, description="OAuth configuration (for sse or http type)")#MCP服务器的OAuth配置（仅适用于SSE或HTTP/HTTPS类型）
    description: str = Field(default="", description="Human-readable description of what this MCP server provides")#MCP服务器的人类可读描述，用于说明服务器提供的功能
    model_config = ConfigDict(extra="allow")


class SkillStateConfig(BaseModel):
    """Configuration for a single skill's state."""

    enabled: bool = Field(default=True, description="Whether this skill is enabled")#控制是否启用此技能


class ExtensionsConfig(BaseModel):
    """Unified configuration for MCP servers and skills."""

    mcp_servers: dict[str, McpServerConfig] = Field(
        default_factory=dict,
        description="Map of MCP server name to configuration",
        alias="mcpServers",
    )
    skills: dict[str, SkillStateConfig] = Field(
        default_factory=dict,
        description="Map of skill name to state configuration",
    )
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @classmethod
    def resolve_config_path(cls, config_path: str | None = None) -> Path | None:
        """Resolve the extensions config file path.

        Priority:
        1. If provided `config_path` argument, use it.
        2. If provided `DEER_FLOW_EXTENSIONS_CONFIG_PATH` environment variable, use it.
        3. Otherwise, check for `extensions_config.json` in the current directory, then in the parent directory.
        4. For backward compatibility, also check for `mcp_config.json` if `extensions_config.json` is not found.
        5. If not found, return None (extensions are optional).

        Args:
            config_path: Optional path to extensions config file.

        Returns:
            Path to the extensions config file if found, otherwise None.
        """
        if config_path:
            path = Path(config_path)
            if not path.exists():
                raise FileNotFoundError(f"Extensions config file specified by param `config_path` not found at {path}")
            return path
        elif os.getenv("DEER_FLOW_EXTENSIONS_CONFIG_PATH"):
            path = Path(os.getenv("DEER_FLOW_EXTENSIONS_CONFIG_PATH"))
            if not path.exists():
                raise FileNotFoundError(f"Extensions config file specified by environment variable `DEER_FLOW_EXTENSIONS_CONFIG_PATH` not found at {path}")
            return path
        else:
            # Check if the extensions_config.json is in the current directory
            path = Path(os.getcwd()) / "extensions_config.json"
            if path.exists():
                return path

            # Check if the extensions_config.json is in the parent directory of CWD
            path = Path(os.getcwd()).parent / "extensions_config.json"
            if path.exists():
                return path

            # Backward compatibility: check for mcp_config.json
            path = Path(os.getcwd()) / "mcp_config.json"
            if path.exists():
                return path

            path = Path(os.getcwd()).parent / "mcp_config.json"
            if path.exists():
                return path

            # Extensions are optional, so return None if not found
            return None

    @classmethod
    def from_file(cls, config_path: str | None = None) -> "ExtensionsConfig":
        """Load extensions config from JSON file.

        See `resolve_config_path` for more details.

        Args:
            config_path: Path to the extensions config file.

        Returns:
            ExtensionsConfig: The loaded config, or empty config if file not found.
        """
        resolved_path = cls.resolve_config_path(config_path)
        if resolved_path is None:
            # Return empty config if extensions config file is not found
            return cls(mcp_servers={}, skills={})

        try:
            with open(resolved_path, encoding="utf-8") as f:
                config_data = json.load(f)
            cls.resolve_env_variables(config_data)
            return cls.model_validate(config_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Extensions config file at {resolved_path} is not valid JSON: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load extensions config from {resolved_path}: {e}") from e

    @classmethod
    def resolve_env_variables(cls, config: dict[str, Any]) -> dict[str, Any]:
        """Recursively resolve environment variables in the config.

        Environment variables are resolved using the `os.getenv` function. Example: $OPENAI_API_KEY

        Args:
            config: The config to resolve environment variables in.

        Returns:
            The config with environment variables resolved.
        """
        for key, value in config.items():
            if isinstance(value, str):
                if value.startswith("$"):
                    env_value = os.getenv(value[1:])
                    if env_value is None:
                        # Unresolved placeholder — store empty string so downstream
                        # consumers (e.g. MCP servers) don't receive the literal "$VAR"
                        # token as an actual environment value.
                        config[key] = ""
                    else:
                        config[key] = env_value
                else:
                    config[key] = value
            elif isinstance(value, dict):
                config[key] = cls.resolve_env_variables(value)
            elif isinstance(value, list):
                config[key] = [cls.resolve_env_variables(item) if isinstance(item, dict) else item for item in value]
        return config

    def get_enabled_mcp_servers(self) -> dict[str, McpServerConfig]:
        """Get only the enabled MCP servers.

        Returns:
            Dictionary of enabled MCP servers.
        """
        return {name: config for name, config in self.mcp_servers.items() if config.enabled}

    def is_skill_enabled(self, skill_name: str, skill_category: str) -> bool:
        """Check if a skill is enabled.

        Args:
            skill_name: Name of the skill
            skill_category: Category of the skill

        Returns:
            True if enabled, False otherwise
        """
        skill_config = self.skills.get(skill_name)
        if skill_config is None:
            # Default to enable for public & custom skill
            return skill_category in ("public", "custom")
        return skill_config.enabled


_extensions_config: ExtensionsConfig | None = None


def get_extensions_config() -> ExtensionsConfig:
    """Get the extensions config instance.

    Returns a cached singleton instance. Use `reload_extensions_config()` to reload
    from file, or `reset_extensions_config()` to clear the cache.

    Returns:
        The cached ExtensionsConfig instance.
    """
    global _extensions_config
    if _extensions_config is None:
        _extensions_config = ExtensionsConfig.from_file()
    return _extensions_config


def reload_extensions_config(config_path: str | None = None) -> ExtensionsConfig:
    """Reload the extensions config from file and update the cached instance.

    This is useful when the config file has been modified and you want
    to pick up the changes without restarting the application.

    Args:
        config_path: Optional path to extensions config file. If not provided,
                     uses the default resolution strategy.

    Returns:
        The newly loaded ExtensionsConfig instance.
    """
    global _extensions_config
    _extensions_config = ExtensionsConfig.from_file(config_path)
    return _extensions_config


def reset_extensions_config() -> None:
    """Reset the cached extensions config instance.

    This clears the singleton cache, causing the next call to
    `get_extensions_config()` to reload from file. Useful for testing
    or when switching between different configurations.
    """
    global _extensions_config
    _extensions_config = None


def set_extensions_config(config: ExtensionsConfig) -> None:
    """Set a custom extensions config instance.

    This allows injecting a custom or mock config for testing purposes.

    Args:
        config: The ExtensionsConfig instance to use.
    """
    global _extensions_config
    _extensions_config = config
