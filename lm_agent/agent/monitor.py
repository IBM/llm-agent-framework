# Standard
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union
import copy

# Local
from lm_agent.agent.decoding_state import DecodingState
from lm_agent.utils import lma_logger

###
#
###

_INIT_SN = DecodingState("tm-init-state", None)
_TERMINAL_SN = DecodingState("tm-terminal-state", None)
_NEXT, _UNTIL = "next", "until"


class Edge:
    def __init__(self, node: str, limit: Optional[int] = None):
        self.node = node
        self._limit = limit + 1 if limit is not None else 1000
        self._ct = 1

    def is_available(self):
        return self._ct % self._limit != 0

    def walk(self):
        self._ct += 1
        return self.node


class TransitionMonitor:
    """
    The transition monitor executes timesteps. It maintains the current state
    """

    def __init__(
        self,
        specification: Tuple,
        states: Dict[str, DecodingState],
        # termination_states: List[DecodingState],
    ):
        specification = (_NEXT, _INIT_SN.name, specification, _TERMINAL_SN.name)
        self._specification = specification
        self._base_states = {
            **states,
            **{_INIT_SN.name: _INIT_SN, _TERMINAL_SN.name: _TERMINAL_SN},
        }
        self._states: Dict[str, DecodingState] = dict()

        self._edges: Dict[str, List[Edge]] = defaultdict(list)
        entry_node, terminal_node = self._make_graph(specification)
        self._entry_states = [
            self._states[edge.node] for edge in self._edges[entry_node]
        ]

        assert entry_node.startswith(_INIT_SN.name) and terminal_node.startswith(
            _TERMINAL_SN.name
        )

        self._trajectory = [
            next(iter(k for k in self._states if k.startswith(_INIT_SN.name)))
        ]

    @property
    def entry_states(self):
        return self._entry_states

    def _make_graph(self, curr_expr, parent=None):
        if type(curr_expr) == str:
            new_str = (
                curr_expr
                + f"_{len([s for s in self._states if '_'.join(s.split('_')[:-1]) == curr_expr])}"
            )
            self._states[new_str] = self._base_states[curr_expr]

            if parent is not None:
                self._edges[parent].append(Edge(new_str))

            return new_str, new_str
        else:
            operator, args = curr_expr[0], curr_expr[1:]
            if operator.startswith(_NEXT):
                for i in range(len(args)):
                    start_arg, exit_arg = self._make_graph(
                        args[i], (parent if i == 0 else exit_arg)
                    )
                    if i == 0:
                        entry_arg = start_arg
                return entry_arg, exit_arg
            elif operator.startswith(_UNTIL):
                limit = int(operator.split("_")[-1]) if "_" in operator else None
                arg, cond = args
                entry_arg, exit_arg = self._make_graph(arg, parent)
                entry_cond, exit_cond = self._make_graph(cond, exit_arg)
                self._edges[exit_arg].append(Edge(entry_arg, limit=limit))
                return entry_arg, exit_cond
            else:
                raise ValueError(f"Unhandled expression: {curr_expr}")

    def exit_reached(self):
        return any(
            [
                state.startswith(_TERMINAL_SN.name)
                for state in self.get_available_states()
            ]
        )

    def is_valid(self, state_name: str):
        return state_name in self.get_available_states()

    def get_available_states(self):
        return [
            self._states[edge.node].name
            for edge in self._edges[self._trajectory[-1]]
            if edge.is_available()
        ]

    def step(self, state_name: str):
        def _step(state, curr_expr, is_init=False):
            if is_init:
                return [
                    ext for node in self._edges[curr_expr] for ext in _step(state, node)
                ]
            elif type(curr_expr) == str:
                return [[curr_expr] if self._states[curr_expr].name == state else []]
            else:
                5 / 0
                return [
                    [curr_expr] + ext
                    for node in self._edges[curr_expr]
                    for ext in _step(state, node)
                ]

        in_edges = [
            edge
            for edge in self._edges[self._trajectory[-1]]
            if edge.is_available() and self._states[edge.node].name == state_name
        ]
        assert (
            len(in_edges) <= 1
        ), f"Ambiguous trajectory detected!\nState: {state_name}\nPossible matching states: {[in_edge.node for in_edge in in_edges]}"
        assert (
            in_edges
        ), f"No edges found transitioning to state [{state_name}] with trajectory [{', '.join([str(x) for x in self._trajectory])}], was validity checker not used?"

        out_edge = in_edges[0]
        self._trajectory.append(out_edge.walk())


if __name__ == "__main__":
    # react test
    specification = (
        "next",
        "question",
        (
            "until_2",
            ("next", "thought", "action", "action-input", "observation"),
            "final-thought",
        ),
        "answer",
    )
    states = {
        state_name: DecodingState(state_name, state_name)
        for state_name in [
            "question",
            "thought",
            "action",
            "action-input",
            "observation",
            "final-thought",
            "answer",
        ]
    }
    trajectories = [
        [
            "question",
            "thought",
            "action",
            "action-input",
            "observation",
            "final-thought",
            "answer",
        ],
        [
            "question",
            "thought",
            "action",
            "action-input",
            "final-thought",
            "answer",
        ],
        [
            "question",
            "thought",
            "action",
            "action-input",
            "observation",
            "thought",
            "action",
            "action-input",
            "observation",
            "thought",
            "action",
            "action-input",
            "observation",
            "final-thought",
            "answer",
        ],
    ]
    for trajectory in trajectories:
        monitor = TransitionMonitor(specification, states)
        try:
            for step in trajectory:
                monitor.step(step)
        except AssertionError as e:
            print(e)
