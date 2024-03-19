from typing import Any, Callable

from ..constrained_decoding import DecodingMonitor
from ..utils import exact_match_score
from .state_handler import StateHandler

class EvaluatorHandler(StateHandler):

    name: str = 'evaluator'

    def __init__(self, answer: Any=None, *args: Any, **kwargs):
        super().__init__(*args, **kwargs)
        self._answer = answer

    def __call__(self, monitor: DecodingMonitor, *args: Any, **kwds: Any) -> str:
        return 'Correct' if self._check_equiv(monitor.history[-1][1]) else 'Incorrect'

    def _check_equiv(self, x, equiv_func: Callable=exact_match_score):
        em_sc = equiv_func(x, self._answer)
        return em_sc
