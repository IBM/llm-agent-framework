import copy
from typing import Any, Dict

from .state_handler import *
from .tool import ToolStateHandler
from ..constrained_decoding import DecodingMonitor
from ..tools.llm import LlmGenerationTool

_PREFIX = 'Solve the provided problems as best you can. To assist you, we have provided some plans and evidence that might be helpful. Notice that some of the information may contain noise so you should trust them with caution. The format of your output should be as follows:'
_FORMAT = 'Question: your question to solve\nPlan: a relevant step towards answering the question\nEvidence: evidence resulting from executing the previous plan step\n(... you can have up to N plan / evidence steps)\nAnswer: the answer to the question'
_SUFFIX = 'Now begin to solve the task or problem. Respond with the answer directly with no extra words.'

class SolverHandler(ToolStateHandler):

    name: str = 'solver'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = copy.deepcopy(self.config)
        config.tool_model = self.config.model
        self.llm_solver = LlmGenerationTool(config)

    def __call__(self, monitor: DecodingMonitor, *args: Any, **kwds: Any) -> str:

        def _sub_results(inp_str: str, results: Dict):
            for k in results:
                if k in inp_str: 
                    inp_str = inp_str.replace(k, results[k])
            return inp_str

        question_text = monitor.history[0][1]

        rel_history = monitor.history + []
        while rel_history[0][0].name != PLAN_SN: rel_history.pop(0)
        # assumes correct formatting of inputs
        to_execute = []
        for label, content in rel_history:
            if label.name == PLAN_SN: to_execute.append([])
            else: to_execute[-1].append((label.name, content))

        label_dict = dict()
        for plan in to_execute:
            action, action_label, action_input = [next(x for x in plan if x[0] == type_of)[1] for type_of in [ACT_SN, ACT_LBL_SN, ACT_INP_SN]]
            label_dict[action_label] = (action, action_input)

        results = dict()
        for label, (action, action_input) in sorted(label_dict.items(), key=lambda x : int(''.join([c for c in x[0] if c.isdigit()]))):
            action_input = _sub_results(action_input, results)
            obs = self._get_observation(action, action_input)
            results[label] = obs

        adj_history = []
        for state, content in rel_history:
            if state.name in [PLAN_SN, ACT_LBL_SN]:
                label = 'Plan:' if state.name == PLAN_SN else 'Evidence:'
                adj_history.append((label, _sub_results(content, results)))
        plan_text = f'Question: {question_text}\n' + '\n'.join([f'{label} {content}' for label, content in adj_history]) + f'\nAnswer:'

        prompt = []
        prompt.append(_PREFIX)
        prompt.append(_FORMAT)
        prompt.append(_SUFFIX)
        prompt.append('{{' + self.llm_solver.INP_VAR + '}}')
        prompt = '\n\n'.join(prompt)

        resp = self.llm_solver(plan_text, prompt=prompt)

        return resp
