# Standard
from typing import Any
import datetime

# Third Party
import dateparser
import numpy as np

# Local
from lm_agent.base.registry import register_tool_handler
from lm_agent.base.tool_handler import BaseToolHandler, ToolConfig


@register_tool_handler("CalendarTodayDate")
class CalendarTodayDateTool(BaseToolHandler):
    description: str = "which gets the current date"

    def __init__(self, config: ToolConfig):
        super().__init__(config)

    async def __call__(self, action_input: str, *args: Any, **kwds: Any) -> Any:
        return datetime.today().strftime("%m/%d/%Y")


@register_tool_handler("CalendarNumberBusinessdaysBetween")
class CalendarNumberBusinessdaysBetweenTool(BaseToolHandler):
    description: str = "which gets the number of business days between two dates"

    def __init__(self, config: ToolConfig):
        super().__init__(config)

    async def __call__(self, action_input: str, *args: Any, **kwds: Any) -> Any:
        """
        This is going to assume the format will be "<date1> to <date2>"
        """
        date_components = action_input.split("to")
        try:
            if len(date_components) != 2:
                raise ValueError(f"Date provided is malformed!")
            date1, date2 = (
                dateparser.parse(date_components[0]),
                dateparser.parse(date_components[1]),
            )
            if date1 is None or date2 is None:
                raise ValueError(f"Date provided is malformed!")
            return np.busday_count(date1, date2)
        except ValueError as e:
            return "<<ERROR>>"


@register_tool_handler("CalendarNumberDaysBetween")
class CalendarNumberDaysBetweenTool(BaseToolHandler):
    description: str = "which gets the number of days between two dates"

    def __init__(self, config: ToolConfig):
        super().__init__(config)

    async def __call__(self, action_input: str, *args: Any, **kwds: Any) -> Any:
        """
        This is going to assume the format will be "<date1> to <date2>"
        """
        date_components = action_input.split("to")
        try:
            if len(date_components) != 2:
                raise ValueError(f"Date provided is malformed!")
            date1, date2 = (
                dateparser.parse(date_components[0]),
                dateparser.parse(date_components[1]),
            )
            if date1 is None or date2 is None:
                raise ValueError(f"Date provided is malformed!")
            delta = date2 - date1
            return abs(delta.days)
        except ValueError as e:
            return "<<ERROR>>"
