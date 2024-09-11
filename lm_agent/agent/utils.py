# Standard
from typing import Dict
import re

# Local
from lm_agent.base.tool_handler import BaseToolHandler


def tool_list_to_string(tool_dict: Dict[str, BaseToolHandler]):
    tool_list = [
        f"({ind+1}) {k} {v.description}"
        for ind, (k, v) in enumerate(sorted(tool_dict.items(), key=lambda x: x[0]))
    ]
    return "\n".join(tool_list)
