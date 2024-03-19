from typing import Any

from ..config import Config
from .tool_handler import Tool

class CalculatorTool(Tool):

    name: str = 'Calculator'
    description: str = 'which performs numerical computations'

    def __init__(self, config : Config):
        super().__init__(config)

    def __call__(self, action_input : str, *args: Any, **kwds: Any) -> Any:
        action_input = action_input.replace('x', '*')
        only_formula = ''.join([c for c in action_input if c in "0123456789*+-/.()"])
        try:
            res = eval(only_formula)
            if type(res) == float and res.is_integer(): res = int(res)
            return str(res)
        except SyntaxError as e:
            return '<<SYNTAX ERROR>>'
        except TypeError as e:
            return '<<TYPE ERROR>>'
        except ZeroDivisionError as e:
            return 'Cannot divide by zero'
        except OverflowError as e:
            return '<<OVERFLOW ERROR>>'
