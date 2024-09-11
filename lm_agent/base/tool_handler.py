# Standard
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import abc
import copy


@dataclass
class ToolConfig(dict):
    name: Optional[str] = None
    model: Optional[Dict] = None


class RecoverableToolError(Exception):
    def __init__(self, message: str, original_error: Exception):
        super().__init__(message)
        self._original_error = original_error

    @property
    def original_error(self):
        return self._original_error


class BaseToolHandler(ABC):
    description: str = None

    def __init__(self, config: ToolConfig):
        self._config = config
        self._name = config.name

    @property
    def config(self):
        return self._config

    @property
    def name(self):
        return self._name

    def update_state(self, action: object, action_result: str):
        pass

    @abc.abstractmethod
    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError(
            f"Action type {self.__class__} does not have action execution implemented!"
        )
