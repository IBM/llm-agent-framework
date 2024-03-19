import logging
from typing import Dict, List, Tuple, Union, Set
import copy

from .utils import all_subclasses

from .constants import *
from .utils import *
from .decoding_state import *

logger = logging.getLogger(__name__)

###
#
###

class Operator:
    def __init__(self): self.content = None

class TrueState: 
    def __init__(self): self.name = 'true'
    def __str__(self): return f'{self.name}'

class FalseState: 
    def __init__(self): self.name = 'false'
    def __str__(self): return f'{self.name}'

class MatchCondition(Operator):
    def __init__(self, condition : DecodingState, bounds : List):
        self.content = condition
        self._min_ct, self._max_ct, self._ct = 0, 1000, 0
        if bounds:
            if len(bounds) > 1: self._min_ct = bounds[0]
            self._max_ct = bounds[-1]
        assert self._max_ct >= self._min_ct, f'Cannot have min loop count {self._min_ct} be greater than max loop count {self._max_ct}'
    
    def clear_bounds(self): self._min_ct, self._max_ct = 0, 1000

    def min_ct_reached(self): return self._min_ct - self._ct <= 0

    def max_ct_reached(self): return self._max_ct - self._ct <= 0

    def increment_ct(self): self._ct += 1

    def matches(self, state : DecodingState):
        return type(self.content) == TrueState or self.content.name == state.name

    def reset(self): self._ct = 0

class Until(Operator):
    NAME = 'until'
    def __init__(self, op_type : str, args : List):
        assert len(args) == 2, f'Unparseable structure'
        assert isinstance(args[1], (DecodingState, TrueState, FalseState)), f'Exit condition for {type(self)} must be DecodingState'
        self.content = args[0]
        self.condition = MatchCondition(args[1], bounds=[int(x) for x in op_type.split('_')[1:]])
    
class Always(Until):
    NAME = 'always'
    def __init__(self, op_type : str, args : List):
        assert len(args) == 1, f'Unparseable structure'
        super().__init__(op_type, args + [TrueState()])

class Next(Operator):
    NAME = 'next'
    def __init__(self, args : List):
        super().__init__()
        self.content = args[0]
        self.next = Next(args[1:]) if len(args) > 1 else None

class Disjunction(Operator):
    NAME = 'or'
    def __init__(self, args : List):
        super().__init__()
        self.content = args

def _make_operator(op_type : str, args : List):
    if op_type.startswith(Always.NAME): return Always(op_type, args)
    elif op_type.startswith(Until.NAME): return Until(op_type, args)
    elif op_type == Next.NAME: return Next(args)
    elif op_type == Disjunction.NAME: return Disjunction(args)
    else: raise ValueError(f'Unknown operator type {op_type}')

###
#
###

class TransitionMonitor:

    """
    The transition monitor executes timesteps. It maintains the current state
    """

    def __init__(self, specification : tuple, states : Dict[str, DecodingState], termination_states : List[DecodingState]):
        self.specification = specification
        self.termination_states = copy.deepcopy(termination_states)
        self.states = { **copy.deepcopy(states), **dict([(s.name, s) for s in termination_states]) }
        self._extract_transition_monitor()

    def _extract_transition_monitor(self):

        operator_classes = list(sorted(set([subcls.NAME for subcls in all_subclasses(Operator) if getattr(subcls, 'NAME', False)])))

        def _make_graph(curr_expr):
            if type(curr_expr) == tuple:
                assert curr_expr[0].split('_')[0] in operator_classes and len(curr_expr) > 1, f'Malformed behavior at {curr_expr}'
                proc_args = [_make_graph(arg) for arg in curr_expr[1:]]
                new_operator = _make_operator(curr_expr[0], proc_args)
                self._operators.add(new_operator)
                return new_operator
            else:
                assert curr_expr in self.states, f'Unknown state {curr_expr}'
                return self.states[curr_expr]
        
        self._operators = set()
        behavior = get_components_type(self.specification, BEHAVIOR_KEY)
        assert len(behavior) == 2, f'{BEHAVIOR_KEY} formatted incorrectly'
        behavior = behavior[1]
        top_level_node = _make_graph(behavior)

        self._stack = []

        # add termination states
        init_states = self.get_valid_states(from_state=top_level_node)
        self.termination_states += init_states
        terminal_nodes = Disjunction(self.termination_states)
        termination_node = Next([top_level_node, terminal_nodes])
        self._operators.update([terminal_nodes, termination_node])

        self._stack.append(termination_node)

    def make_copy(self):
        return TransitionMonitor(self.specification, self.states, self.termination_states)

    def disable_count_limits(self):
        for op in self._operators:
            if getattr(op, 'condition', None):
                getattr(op, 'condition').clear_bounds()

    def exit_reached(self):
        return self._stack == []

    def matches_state(self, input_tokens : List):
        matches = []
        for state in self.states.values():
            matched_seq = state.matches(input_tokens)
            if matched_seq is not None:
                matches.append((state, matched_seq))
        if matches:
            state, matched_seq = max(matches, key=lambda x : len(x[1]))
            return state, matched_seq
        return None, None

    def accept_state(self, proposed_state : DecodingState, from_state : Union[Operator, DecodingState]=None):
        valid_states = self.get_valid_states(from_state=from_state)
        return proposed_state in valid_states

    def get_valid_states(self, from_state : Union[Operator, DecodingState]=None, from_stack : List=None, valid_states : List=None) -> List[DecodingState]:
        if valid_states is None: valid_states = []

        if from_stack is None: from_stack = self._stack + []
        if from_state is None and from_stack == []: return []
        current = from_stack.pop() if from_state is None else from_state

        if isinstance(current, DecodingState):
            valid_states.append(current)
        elif isinstance(current, Disjunction):
            for opt in current.content:
                self.get_valid_states(from_state=opt, from_stack=from_stack, valid_states=valid_states)
            return valid_states
        elif isinstance(current, Until) and current.condition.min_ct_reached():
            if type(current.condition.content) == TrueState:
                assert from_stack, 'Must have a stack of operations remaining, is there a bug in the specification or termination states?'
                self.get_valid_states(from_stack=from_stack, valid_states=valid_states)
            else:
                valid_states.append(current.condition.content)

        if isinstance(current, Until) and current.condition.max_ct_reached():
            return valid_states

        return self.get_valid_states(from_state=current.content, from_stack=from_stack, valid_states=valid_states) if isinstance(current, Operator) else valid_states

    def step(self, state : DecodingState):
        # gets next element of stack, this ASSUMES state is valid (e.g., was provided by get_valid_states)
        current = self._stack.pop()
        if isinstance(current, DecodingState):
            assert current == state, f'Verification of state failed, expected [{current.name}] but received [{state.name}]'
            return current
        elif isinstance(current, Disjunction):
            # this will replace the disjunction with its appropriate child
            for opt in current.content:
                if state in self.get_valid_states(from_state=opt):
                    self._push(opt)
                    return self.step(state)
            assert f'Verification of disjunction failed, could not match with [{current.name}]'
        elif isinstance(current, Until):
            if current.condition.matches(state) and current.condition.min_ct_reached():
                # when we have a true condition, that MUST match to the next state, so we thus skip the true condition
                if type(current.condition.content) == TrueState:
                    # if we can keep looping, we just do that, otherwise, we will execute a skip state step with self.step(state)
                    if current.condition.max_ct_reached() or not self.accept_state(state, current.content):
                        # when we exit the until loop, we reset its conditions since, if we revisit the loop, it will be the exact same object
                        current.condition.reset()
                        return self.step(state)
                else:
                    # when we exit the until loop, we reset its conditions since, if we revisit the loop, it will be the exact same object
                    current.condition.reset()
                    return current.condition.content
            assert not current.condition.max_ct_reached(), f'Loop limit reached, expected [{current.condition.content.name}] but received [{state.name}]'
        self._push(current)
        return self.step(state)

    def _push(self, to_add : Union[Operator, DecodingState]):
        if isinstance(to_add, Next):
            if to_add.next: self._stack.append(to_add.next)
            self._stack.append(to_add.content)
        elif isinstance(to_add, Until):
            self._stack.append(to_add)
            if not to_add.condition.max_ct_reached():
                to_add.condition.increment_ct()
                self._stack.append(to_add.content)
        else:
            self._stack.append(to_add)

    def validate_sequence_from_string(self, string : str):
        state_texts = [v.text for v in self.states.values()]
        steps = collect_states(string, state_texts)
        return self.validate_sequence(steps)

    def validate_sequence(self, state_history : List[Tuple[str, str]]):
        monitor = self.make_copy()
        monitor.disable_count_limits()
        state_dict = { state.text : state for state in monitor.states.values() }
        for dec_str, _ in state_history:
            
            try:
                assert not monitor.exit_reached(), f'Exit state reached but there are still state transitions occurring!'
                matched_state = state_dict[dec_str]
                logger.debug(f'Acceptable states [{", ".join([state.name for state in monitor.get_valid_states()])}]')
                step_state = monitor.step(matched_state)
                logger.debug(f'Step [{matched_state.name}] was matched by monitor with [{step_state.name}]')

            except AssertionError as e: logger.error(str(e))

        if not (monitor.exit_reached() or not self.termination_states):
            logger.warning(f'Exit state not reached for prompt example, ended at [{monitor._stack[-1].name if isinstance(monitor._stack[-1], DecodingState) else type(monitor._stack[-1])}]. Example may be malformed!')
        else: logger.debug(f'Prompt met specifications!')

        return True
