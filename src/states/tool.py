from typing import Any, Dict
import logging

from ..tools.tool_handler import Tool
from ..tools import *
from ..constrained_decoding import DecodingMonitor
from ..config import Config
from ..utils import all_subclasses
from .state_handler import ACT_SN, StateHandler

logger = logging.getLogger(__name__)

class ToolStateHandler(StateHandler):

    name: str = 'observation'

    def __init__(self, config : Config):
        super().__init__(config)
        self._action_types = dict([(action_type, self.get_tool(action_type)) for action_type in config.action_types])
        self._action_names = [self._action_types[action_type].name.strip() for action_type in config.action_types]

    def __call__(self, monitor : DecodingMonitor, *args: Any, **kwds: Any) -> str:
        history = monitor.history
        action_name, action_input = history[-2][1], history[-1][1]
        return self._get_observation(action_name, action_input, *args, **kwds)

    def _get_observation(self, action_name : str, action_input : str, *args: Any, **kwds: Any):

        assert action_name in self._action_types, f'Action type {action_name} is not valid!'
        action = self._action_types[action_name]

        action_result = action(action_input, *args, **kwds)
        for action_obj in self._action_types.values():
            action_obj.update_state(action)

        return action_result

    def adjust_prompt_args(self, prompt_kwargs: Dict):
        if self._action_names:
            prompt_kwargs['tool_labels'] = '[' + ', '.join(sorted(self._action_names)) + ']'
            prompt_kwargs['tool_descriptions'] = '\n'.join([f'{act}: {self._action_types[act].description}' for act in sorted(self._action_names)])
            return prompt_kwargs

    def adjust_monitor(self, monitor: DecodingMonitor):
        if self._action_names:
            monitor_states = monitor.states
            if ACT_SN in monitor_states:
                logger.debug(f'Adding output constraints [{", ".join(self._action_names)}] to state {ACT_SN}')
                monitor_states[ACT_SN].add_constraints(self._action_names)

    def get_tool(self, action_type: str) -> Tool:
        for subclass in all_subclasses(Tool):
            if action_type == subclass.name:
                return subclass(self.config)
        raise ValueError(f'Unknown tool type {action_type}')
