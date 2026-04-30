import os
from pathlib import Path

from .parser import parse_skill_file
from .types import Skill
def load_skills(skills_path, use_config, enabled_only):
    """
    Load all skills from the skills directory.

    Scans both public and custom skill directories, parsing SKILL.md files
    to extract metadata. The enabled state is determined by the skills_state_config.json file.

    Args:
        skills_path: Optional custom path to skills directory.
                     If not provided and use_config is True, uses path from config.
                     Otherwise defaults to deer-flow/skills
        use_config: Whether to load skills path from config (default: True)
        enabled_only: If True, only return enabled skills (default: False)

    Returns:
        List of Skill objects, sorted by name
    """
    # 1. 确定技能目录路径（配置优先，默认回退）
    # 2. 扫描 public 和 custom 目录
    # 3. 遍历查找 SKILL.md 文件
    # 4. 解析每个 SKILL.md
    # 5. 从配置读取启用状态
    # 6. 可选：仅返回启用的技能
    # 7. 按名称排序返回