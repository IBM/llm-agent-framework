# Standard
from typing import Callable, Optional


class RejectionCriteria:
    def __init__(self, lambda_func: Callable):
        self._critiera = lambda_func

    def __call__(self, monitor):
        return False
