from .general_purpose import GENERAL_PURPOSE_CONFIG
from .bash_agent import BASH_AGENT_CONFIG
__all__=[
    "BASH_AGENT_CONFIG",
    "GENERAL_PURPOSE_CONFIG",
]
BUILTIN_SUBAGENTS ={
    "bash": BASH_AGENT_CONFIG,
    "general-purpose": GENERAL_PURPOSE_CONFIG,
}