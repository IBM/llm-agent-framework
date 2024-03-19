from typing import Any, Dict

from ..constrained_decoding import DecodingMonitor
from ..config import Config


# common names for states
ACT_SN, ACT_INP_SN, PLAN_SN, ACT_LBL_SN = 'action', 'action-input', 'plan', 'action-label'


class StateHandler:

    name: str = None

    def __init__(self, config: Config): self.config = config

    def __call__(self, *args: Any, **kwds: Any) -> str: 
        raise NotImplementedError(f'Method __call__ for {self.__class__} is not implemented!')

    def adjust_prompt_args(self, *args: Any, **kwargs: Dict): return NotImplemented

    def adjust_monitor(self, *args: Any, **kwargs: Dict): return NotImplemented
