# Standard
from typing import Any

# Local
from lm_agent.base.registry import register_state_handler
from lm_agent.base.state_handler import BaseStateHandler, StateHandlerConfig
from lm_agent.base.tool_handler import BaseToolHandler, RecoverableToolError
from lm_agent.utils import lma_logger


@register_state_handler("observation")
class ToolStateHandler(BaseStateHandler):
    async def __call__(self, history, *args: Any, **kwargs: Any) -> str:
        action_name, action_input = history[-2][1], history[-1][1]

        if action_name not in self.tools:
            lma_logger.info(
                f"Action name {action_name} is not valid, returning to agent!"
            )
            return f"Unhandled action name {action_name}, possible options are [{', '.join(self.tools.keys())}]"

        action_result = await self._get_observation(
            action_name, action_input, *args, **kwargs
        )

        return action_result

    async def _get_observation(
        self,
        action_name,
        action_input,
        *args,
        squash_recoverable_error: bool = True,
        **kwargs,
    ):
        if action_name not in self.tools:
            return (
                f"Selected action must be one of {', '.join(list(self.tools.keys()))}"
            )

        try:
            action = self.tools[action_name]
            action_result = await action(action_input, *args, **kwargs)
        except RecoverableToolError as e:
            if squash_recoverable_error:
                action_result = str(e)
            else:
                raise e

        for tool in self.tools.values():
            tool.update_state(action, action_name)

        return action_result
