from abc import ABC, abstractmethod


class Sandbox(ABC):
    """
    抽象沙箱基类
    """

    _id:str # 沙箱id

    def __init__(self, id: str) -> None:
        self._id = id

    @abstractmethod
    def execute_command(self, command: str) -> str:
        """
        在沙箱中执行命令
        Args:
            command (str): 要执行的命令
        Returns:
            str: 命令执行结果
        """
        pass

    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """
        从沙箱中读取文件内容
        Args:
            file_path (str): 文件绝对路径
        Returns:
            str: 文件内容
        """
        pass

    @abstractmethod
    def list_dir(self, path: str,max_depth: int = 2) -> list[str]:
        """
        列出沙箱中指定路径下的所有文件和目录
        Args:
            path (str): 目录路径
            max_depth (int, optional): 递归深度. Defaults to 2.
        Returns:
            list[str]: 文件和目录列表
        """
        pass

    @abstractmethod
    def write_file(self, path: str, content: str,append: bool = False) -> None:
        """
        向沙箱中写入文件内容
        Args:
            path (str): 文件绝对路径
            content (str): 要写入的内容
            append (bool, optional): 是否追加内容. Defaults to False.如果为True，则在文件末尾追加内容，否则覆盖原有内容。
        """
        pass

    @abstractmethod
    def update_file(self, path: str, content: bytes) -> None:
        """Update a file with binary content.

        Args:
            path: The absolute path of the file to update.
            content: The binary content to write to the file.
        """
        pass

