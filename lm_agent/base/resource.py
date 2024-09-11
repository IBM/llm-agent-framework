# Standard
from abc import ABC
from typing import Any
import abc


class BaseResource(ABC):
    """Base Class for all shared Resources"""

    @abc.abstractmethod
    def is_conflicting(self, *args: Any, **kwargs: Any):
        raise NotImplementedError
