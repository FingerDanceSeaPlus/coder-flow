import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath

from src.sandbox.local.list_dir import list_dir
from src.sandbox.sandbox import Sandbox

class LocalSandboxWindows(Sandbox):
    def __init__(self, id: str, path_mappings: dict[str, str] | None = None):
        """
        Initialize local sandbox with optional path mappings.

        Args:
            id: Sandbox identifier
            path_mappings: Dictionary mapping container paths to local paths
                          Example: {"/mnt/skills": "/absolute/path/to/skills"}
        """
        super().__init__(id)
        self.path_mappings = path_mappings or {}

    def _resolve_path(self, path: str) -> str:
        """
        Resolve container path to actual local path (Windows-safe).
        """

        if not path:
            return path

        # ---- 1. 统一输入路径为 POSIX 风格 ----
        path_norm = str(PurePosixPath(str(path)))

        # ---- 2. 排序（最长前缀优先）----
        mappings = sorted(
            self.path_mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for container_path, local_path in mappings:
            # ---- 3. 统一 container_path ----
            container_norm = str(PurePosixPath(container_path))

            # ---- 4. Windows：大小写不敏感匹配 ----
            if os.name == "nt":
                match = path_norm.lower().startswith(container_norm.lower())
            else:
                match = path_norm.startswith(container_norm)

            if match:
                # ---- 5. 计算相对路径 ----
                relative = path_norm[len(container_norm):].lstrip("/")

                # ---- 6. 使用 Path 拼接（自动处理 \ 和 /）----
                if relative:
                    resolved = Path(local_path) / Path(relative)
                else:
                    resolved = Path(local_path)

                # ---- 7. 返回标准化字符串 ----
                return str(resolved)

        return path



    def _reverse_resolve_path(self, path: str) -> str:
        """
        Reverse resolve local path back to container path using mappings.将本地路径解析为容器路径

        Args:
            path: Local path that might need to be mapped to container path

        Returns:
            Container path if mapping exists, otherwise original path
        """
        path_str = str(Path(path).resolve())

        # Try each mapping (longest local path first for more specific matches)
        for container_path, local_path in sorted(self.path_mappings.items(), key=lambda x: len(x[1]), reverse=True):
            local_path_resolved = str(Path(local_path).resolve())
            if path_str.startswith(local_path_resolved):
                # Replace the local path prefix with container path
                relative = path_str[len(local_path_resolved) :].lstrip("/")
                resolved = f"{container_path}/{relative}" if relative else container_path
                return resolved

        # No mapping found, return original path
        return path_str

    def _reverse_resolve_paths_in_output(self, output: str) -> str:
        """
        Reverse resolve local paths back to container paths in output string.

        Args:
            output: Output string that may contain local paths

        Returns:
            Output with local paths resolved to container paths
        """
        import re

        # Sort mappings by local path length (longest first) for correct prefix matching
        sorted_mappings = sorted(self.path_mappings.items(), key=lambda x: len(x[1]), reverse=True)

        if not sorted_mappings:
            return output

        # Create pattern that matches absolute paths
        # Match paths like /Users/... or other absolute paths
        result = output
        for container_path, local_path in sorted_mappings:
            local_path_resolved = str(Path(local_path).resolve())
            # Escape the local path for use in regex
            escaped_local = re.escape(local_path_resolved)
            # Match the local path followed by optional path components
            pattern = re.compile(escaped_local + r"(?:/[^\s\"';&|<>()]*)?")

            def replace_match(match: re.Match) -> str:
                matched_path = match.group(0)
                return self._reverse_resolve_path(matched_path)

            result = pattern.sub(replace_match, result)

        return result

    def _resolve_paths_in_command(self, command: str) -> str:
        """
        Resolve container paths in command string (Windows-compatible).
        """

        if not self.path_mappings:
            return command

        # ---- 1. 排序（最长匹配优先）----
        sorted_mappings = sorted(
            self.path_mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        # ---- 2. 构造 regex（支持 / 和 \）----
        patterns = []
        for container_path, _ in sorted_mappings:
            # 统一为 POSIX 风格
            container_norm = str(PurePosixPath(container_path))

            # 把 "/" 替换为 "(/|\\)" → 同时匹配两种分隔符
            flexible = re.escape(container_norm).replace(r"/", r"[\\/]")
            
            # 匹配路径（后面可以跟路径组件）
            p = rf"{flexible}(?:[\\/][^\s\"';&|<>()]*)?"
            patterns.append(p)

        # ---- 3. 合并 pattern ----
        pattern = re.compile(
            "|".join(f"({p})" for p in patterns),
            re.IGNORECASE if os.name == "nt" else 0
        )

        # ---- 4. 替换函数 ----
        def replace_match(match: re.Match) -> str:
            matched_path = match.group(0)

            # 统一为 POSIX 再处理
            normalized = str(PurePosixPath(matched_path.replace("\\", "/")))

            return self._resolve_path(normalized)

        return pattern.sub(replace_match, command)

    @staticmethod
    def _get_shell() -> str:
        """Detect available shell executable with fallback.

        Returns the first available shell in order of preference:
        /bin/zsh → /bin/bash → /bin/sh → first `sh` found on PATH.
        Raises a RuntimeError if no suitable shell is found.
        """
        import os
    
        # 优先查找 Git Bash
        git_bash_paths = [
            r"C:\Program Files\Git\bin\bash.exe",
        ]
        
        for path in git_bash_paths:
            if os.path.exists(path):
                # 返回 Windows 风格的路径
                return path
        for shell in ("/bin/zsh", "/bin/bash", "/bin/sh"):
            if os.path.isfile(shell) and os.access(shell, os.X_OK):
                return shell
        shell_from_path = shutil.which("sh")
        if shell_from_path is not None:
            return shell_from_path
        raise RuntimeError("No suitable shell executable found. Tried /bin/zsh, /bin/bash, /bin/sh, and `sh` on PATH.")

    def execute_command(self, command: str) -> str:
            # Resolve container paths in command before execution
            resolved_command = self._resolve_paths_in_command(command)

            shell_path = self._get_shell()

            result = subprocess.run(
                [shell_path, "-c", resolved_command],
                capture_output=True,
                text=True,
                timeout=600,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nStd Error:\n{result.stderr}" if output else result.stderr
            if result.returncode != 0:
                output += f"\nExit Code: {result.returncode}"

            final_output = output if output else "(no output)"
            # Reverse resolve local paths back to container paths in output
            return self._reverse_resolve_paths_in_output(final_output)

    def list_dir(self, path: str, max_depth=2) -> list[str]:
        resolved_path = self._resolve_path(path)
        entries = list_dir(resolved_path, max_depth)
        # Reverse resolve local paths back to container paths in output
        return [self._reverse_resolve_paths_in_output(entry) for entry in entries]

    def read_file(self, path: str) -> str:
        resolved_path = self._resolve_path(path)
        try:
            with open(resolved_path) as f:
                return f.read()
        except OSError as e:
            # Re-raise with the original path for clearer error messages, hiding internal resolved paths
            raise type(e)(e.errno, e.strerror, path) from None

    def write_file(self, path: str, content: str, append: bool = False) -> None:
        resolved_path = self._resolve_path(path)
        try:
            dir_path = os.path.dirname(resolved_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            mode = "a" if append else "w"
            with open(resolved_path, mode) as f:
                f.write(content)
        except OSError as e:
            # Re-raise with the original path for clearer error messages, hiding internal resolved paths
            raise type(e)(e.errno, e.strerror, path) from None

    def update_file(self, path: str, content: bytes) -> None:
        resolved_path = self._resolve_path(path)
        try:
            dir_path = os.path.dirname(resolved_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(resolved_path, "wb") as f:
                f.write(content)
        except OSError as e:
            # Re-raise with the original path for clearer error messages, hiding internal resolved paths
            raise type(e)(e.errno, e.strerror, path) from None
