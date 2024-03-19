from typing import Any

from ..config import Config
from .tool_handler import Tool

class UserResponseTool(Tool):

    name: str = 'UserResponse'
    description: str = 'a tool you can use to get further clarification from a user'

    def __init__(self, config : Config):
        super().__init__(config)

    def __call__(self, action_input : str, *args: Any, **kwds: Any) -> Any:
        response = input(f'{action_input}. Type your response below and press \'Enter\' once your response is complete.\n').strip()
        return response

