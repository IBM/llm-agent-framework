from typing import Any, Dict

from ..constrained_decoding import DecodingMonitor
from ..config import Config

class Tool:

    name: str = None
    description: str = None

    def __init__(self, config: Config):
        self.config = config

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError(f'Action type {self.__class__} does not have action execution implemented!')

    def update_state(self, action_type: Any): pass
