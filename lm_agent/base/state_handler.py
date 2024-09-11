# Standard
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

# Local
from lm_agent.base.tool_handler import BaseToolHandler


@dataclass
class StateHandlerConfig(dict):
    name: Optional[str] = None
    text: Optional[str] = None
    tools: Optional[dict] = None
    env_input: Optional[bool] = False
    model: Optional[Dict] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []


class BaseStateHandler(ABC):
    def __init__(
        self,
        config: StateHandlerConfig,
        tools: Optional[Dict[str, BaseToolHandler]] = None,
    ):
        self._config = config
        self._name = config.name
        self._tools = tools

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    @property
    def tools(self):
        return self._tools

    async def __call__(self, history: List) -> str:
        raise NotImplementedError(
            f"Method __call__ for {self.__class__} is not implemented!"
        )
