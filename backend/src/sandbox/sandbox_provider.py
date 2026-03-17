from abc import ABC, abstractmethod

from src.config import get_app_config
from src.reflection import resolve_class
from src.sandbox.sandbox import Sandbox


class SandboxProvider(ABC):
    """Abstract base class for sandbox providers"""

    @abstractmethod
    def acquire(self, thread_id: str | None = None) -> str:
        """Acquire a sandbox environment and return its ID.
        请求一个沙箱环境并返回其ID。

        Returns:
            The ID of the acquired sandbox environment.
        """
        pass

    @abstractmethod
    def get(self, sandbox_id: str) -> Sandbox | None:
        """Get a sandbox environment by ID.
        根据ID获取沙箱环境。

        Args:
            sandbox_id: The ID of the sandbox environment to retain.
        """
        pass

    @abstractmethod
    def release(self, sandbox_id: str) -> None:
        """Release a sandbox environment.
        释放一个沙箱环境。

        Args:
            sandbox_id: The ID of the sandbox environment to destroy.
        """
        pass


_default_sandbox_provider: SandboxProvider | None = None


def get_sandbox_provider(**kwargs) -> SandboxProvider:
    """Get the sandbox provider singleton.

    Returns a cached singleton instance. Use `reset_sandbox_provider()` to clear
    the cache, or `shutdown_sandbox_provider()` to properly shutdown and clear.
    获取沙箱提供程序单例实例。

    Returns:
        A sandbox provider instance.
    """
    global _default_sandbox_provider
    if _default_sandbox_provider is None:
        config = get_app_config()
        cls = resolve_class(config.sandbox.use, SandboxProvider)
        _default_sandbox_provider = cls(**kwargs)
    return _default_sandbox_provider


def reset_sandbox_provider() -> None:
    """Reset the sandbox provider singleton.

    This clears the cached instance without calling shutdown.
    将会清除缓存的实例，但不会调用关闭方法。
    The next call to `get_sandbox_provider()` will create a new instance.
    下一次调用`get_sandbox_provider()`将创建一个新实例。
    Useful for testing or when switching configurations.
    这对于测试或切换配置非常有用。

    Note: If the provider has active sandboxes, they will be orphaned.
    注意：如果提供程序有活动的沙箱环境，它们将成为孤儿环境。
    Use `shutdown_sandbox_provider()` for proper cleanup.
    请使用`shutdown_sandbox_provider()`进行适当的清理。
    """
    global _default_sandbox_provider
    _default_sandbox_provider = None


def shutdown_sandbox_provider() -> None:
    """Shutdown and reset the sandbox provider.

    This properly shuts down the provider (releasing all sandboxes)
    这将正确关闭提供程序（释放所有沙箱环境）。
    before clearing the singleton. Call this when the application
    is shutting down or when you need to completely reset the sandbox system.
    在清理单例之前，确保所有沙箱环境都已释放。
    """
    global _default_sandbox_provider
    if _default_sandbox_provider is not None:
        if hasattr(_default_sandbox_provider, "shutdown"):
            _default_sandbox_provider.shutdown()
        _default_sandbox_provider = None


def set_sandbox_provider(provider: SandboxProvider) -> None:
    """Set a custom sandbox provider instance.

    This allows injecting a custom or mock provider for testing purposes.
    这允许注入自定义或模拟提供程序用于测试目的。

    Args:
        provider: The SandboxProvider instance to use.
    """
    global _default_sandbox_provider
    _default_sandbox_provider = provider