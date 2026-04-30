from dataclasses import dataclass
from pathlib import Path

@dataclass
class Skill:
    name: str                    # 技能名称（唯一标识）
    description: str             # 技能描述（用于 LLM 选择）
    license: str | None          # 许可证信息
    skill_dir: Path              # 技能目录路径
    skill_file: Path             # SKILL.md 文件路径
    relative_path: Path          # 相对于分类根目录的路径
    category: str                # 分类：'public' 或 'custom'
    enabled: bool = False        # 是否启用

    @property
    def skill_path(self) -> str:
        """返回技能相对路径"""
        path = self.relative_path.as_posix()
        return "" if path == "." else path

    def get_container_path(self, container_base_path: str = "/mnt/skills") -> str:
        """
        Get the full path to this skill in the container.

        Args:
            container_base_path: Base path where skills are mounted in the container

        Returns:
            Full container path to the skill directory
        """
        category_base = f"{container_base_path}/{self.category}"
        skill_path = self.skill_path
        if skill_path:
            return f"{category_base}/{skill_path}"
        return category_base

    def get_container_file_path(self, container_base_path: str = "/mnt/skills") -> str:
        """
        Get the full path to this skill's main file (SKILL.md) in the container.

        Args:
            container_base_path: Base path where skills are mounted in the container

        Returns:
            Full container path to the skill's SKILL.md file
        """
        return f"{self.get_container_path(container_base_path)}/SKILL.md"

    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, description={self.description!r}, category={self.category!r})"