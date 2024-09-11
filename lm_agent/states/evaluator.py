# Standard
from typing import Any, Callable

# Local
from lm_agent.base.registry import register_state_handler
from lm_agent.base.state_handler import BaseStateHandler


@register_state_handler("evaluator")
class EvaluatorHandler(BaseStateHandler):
    def __init__(self, answer: Any = None, *args: Any, **kwargs):
        super().__init__(*args, **kwargs)
        self._answer = answer

    def __call__(self, monitor, *args: Any, **kwds: Any) -> str:
        return "Correct" if self._check_equiv(monitor.history[-1][1]) else "Incorrect"

    def _check_equiv(self, x, equiv_func: Callable):
        em_sc = equiv_func(x, self._answer)
        return em_sc
