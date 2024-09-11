# Standard
from typing import Any

# Local
from lm_agent.base.registry import register_tool_handler
from lm_agent.base.tool_handler import BaseToolHandler, ToolConfig


@register_tool_handler("UserResponse")
class UserResponseTool(BaseToolHandler):
    description: str = "a tool you can use to get further clarification from a user"

    def __init__(self, config: ToolConfig):
        super().__init__(config)

    async def __call__(self, action_input: str, *args: Any, **kwds: Any) -> Any:
        response = input(
            f"{action_input}. Type your response below and press 'Enter' once your response is complete.\n"
        ).strip()
        return response
