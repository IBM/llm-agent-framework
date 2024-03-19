from types import LambdaType
import torch

from transformers.tokenization_utils import PreTrainedTokenizer
from nltk.metrics.distance import edit_distance

from .constants import *
from .utils import *

###
#
###

class DecodingState:

    _TEXT_KEY, _FLAGS_KEY, _CONSTRAINTS_KEY, _ENV_INPUT_KEY = ':text', ':flags', ':output-constrs', ':env-input'

    def __init__(self, state_desc : tuple, tokenizer : PreTrainedTokenizer=None):
        self.name, self.tokenizer = state_desc[0], tokenizer        
        text = None
        constraints = None
        self.defer_to_env = False
        for component in state_desc[1:]:
            if component[0] == DecodingState._TEXT_KEY:
                text = component[1]
            elif component[0] == DecodingState._CONSTRAINTS_KEY:
                constraints = component[1:]
            elif component[0] == DecodingState._FLAGS_KEY:
                for flag in component[1:]:
                    if flag == DecodingState._ENV_INPUT_KEY:
                        self.defer_to_env = True
        
        assert text is not None, f'Must specify :text for state {state_desc}'
        self.text = text.replace('\"', '').replace('\'', '')

        assert not (self.defer_to_env and constraints), 'Cannot enforce output constraints while also being an environment action'

        constraints = [constr.replace('\"', '').replace('\'', '') for constr in constraints] if constraints is not None else []
        self.add_constraints(constraints)

        self._constraint_function = None

        self.tokens = tokenizer.convert_tokens_to_ids(tokenizer.tokenize('\n' + self.text.strip())) if tokenizer else None

        # we separate between what we want to add when we match the criteria (the text) and the list of accepting states
        self._check_tokens = []
        if tokenizer:
            self._check_tokens.append(self.tokens)
            for addit in ['', ' ', '\t']:
                self._check_tokens.append(tokenizer.convert_tokens_to_ids(tokenizer.tokenize(addit + self.text.strip())))

    def clear_constraints(self):
        self._constraint_strings.clear()

    def add_constraints(self, constraints : List[str]):
        self._constraint_strings = constraints + []
        self.constraints = [self._construct_constraint(constr) for constr in constraints]

    def remove_constraints(self, constraints_to_remove : List[str]):
        self._constraint_strings = [constraint_string for constraint_string in self._constraint_strings if constraint_string not in constraints_to_remove]
        self.constraints = [self._construct_constraint(constr) for constr in self._constraint_strings]

    def _construct_constraint(self, constr : str):
        if self.tokenizer:
            return self.tokenizer.convert_tokens_to_ids(self.tokenizer.tokenize(' ' + constr)) 
        return constr

    def set_constraint_function(self, new_func: LambdaType):
        self._constraint_function = new_func

    def validate_constraints(self, text : str, enforce_hard_constraints : bool=False):

        if self._constraint_function is not None:
            if not self._constraint_function(text): return None

        return self._adjust_for_constraints(text, enforce_hard_constraints=enforce_hard_constraints)

    def _adjust_for_constraints(self, text : str, enforce_hard_constraints : bool=False):
        
        _eq, _substr, _lw, _ch, _dist = 'eq', 'substr', 'lower', 'char', 'dist'

        def _transform(text : str, transform : str):
            text = text.strip()
            if transform == _lw:
                text = text.lower()
            elif transform == _ch:
                text = text.replace(' ', '').lower()
            return text

        def _score(constr : str, match_type : str, transform : str):
            constr, check_text = _transform(constr, transform), _transform(text, transform)
            if match_type == _dist:
                return edit_distance(constr, check_text)
            return float('inf')

        def _constr_match(constr : str, match_type : str, transform : str):
            constr, check_text = _transform(constr, transform), _transform(text, transform)
            if match_type == _eq:
                return constr == check_text
            elif match_type == _substr:
                return constr in check_text
            return False

        # hard match
        for match_type, transform in [(_eq, None), (_eq, _lw), (_eq, _ch), (_substr, None), (_substr, _lw), (_substr, _ch)]:
            for constr in self.constraints:
                if _constr_match(constr, match_type, transform):
                    return constr

        # soft match
        for match_type in []:
            scores = sorted([(_score(constr, match_type, _lw), constr) for constr in self.constraints])
            scores = [sc for sc in scores if sc[0] == scores[0][0]]
            if len(scores) == 1: 
                return scores[0][1]

        if self.constraints and enforce_hard_constraints: return None
        elif self.constraints: return self.constraints[0]
        else: return text

    def matches(self, input_tokens : torch.Tensor):
        return seq_matches_any(self._check_tokens, input_tokens)

    def __eq__(self, other):
        return type(other) == DecodingState and self.text == other.text

    def __repr__(self): return self.name

def extract_states(specification : tuple, tokenizer : PreTrainedTokenizer) -> Dict[str, DecodingState]:
    states_lst = get_components_type(specification, STATES_KEY)[1:]
    states = [DecodingState(state, tokenizer) for state in states_lst]
    states_dict = dict()
    for state in states:
        assert state.name not in states_dict, f'Cannot have duplicate state specifications: {state.name}'
        states_dict[state.name] = state
    return states_dict