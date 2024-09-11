# Standard
from typing import Any, Dict
import copy

# Local
from lm_agent.base.registry import register_state_handler
from lm_agent.models.interface import ModelConfig, ModelInterface
from lm_agent.states.observation import ToolStateHandler

_PREFIX = "Solve the following task or problem. To assist you, we provide some plans and corresponding evidences that might be helpful. Notice that some of these information contain noise so you should trust them with caution."
_SUFFIX = "Now begin to solve the task or problem. Respond with the answer directly with no extra words."

_PLAN_SN, _ACT_SN, _ACT_LBL_SN, _ACT_INP_SN = (
    "plan",
    "action",
    "action-label",
    "action-input",
)


@register_state_handler("solver")
class SolverHandler(ToolStateHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._model = ModelInterface(ModelConfig(**self.config.model))

    async def __call__(self, history, *args: Any, **kwargs: Any) -> str:
        def _make_int(x: str):
            digits = "".join([c for c in x[0] if c.isdigit()])
            if not digits:
                digits = -1
            return int(digits)

        def _sub_results(inp_str: str, results: Dict):
            for k in results:
                if k in inp_str:
                    inp_str = inp_str.replace(k, results[k])
            return inp_str

        question_text = history[0][1]

        rel_history = history + []
        while rel_history and rel_history[0][0].name != _PLAN_SN:
            rel_history.pop(0)
        if not rel_history:
            return ""

        # assumes correct formatting of inputs
        to_execute = []
        for label, content in rel_history:
            if label.name == _PLAN_SN:
                to_execute.append([])
            else:
                to_execute[-1].append((label.name, content))

        label_dict = dict()
        for plan in to_execute:
            action, action_label, action_input = [
                next(x for x in plan if x[0] == type_of)[1]
                for type_of in [_ACT_SN, _ACT_LBL_SN, _ACT_INP_SN]
            ]
            label_dict[action_label] = (action, action_input)

        results = dict()
        for label, (action, action_input) in sorted(label_dict.items(), key=_make_int):
            action_input = _sub_results(action_input, results)
            obs = await self._get_observation(action, action_input, *args, **kwargs)
            results[label] = obs

        adj_history = []
        for state, content in rel_history:
            if state.name in [_PLAN_SN, _ACT_LBL_SN]:
                label = "Plan:" if state.name == _PLAN_SN else "Evidence:"
                content = _sub_results(content, results).strip()
                if content:
                    adj_history.append((label, content))

        question_text = "Question: " + question_text

        prompt = []
        prompt.append(_PREFIX)
        prompt.append(
            "\n".join(
                [question_text]
                + [f"{label} {content}" for label, content in adj_history]
            )
        )
        prompt.append(_SUFFIX)
        prompt.append(question_text)

        prompt = "\n\n".join(prompt) + "\n" + "Answer:"

        resp = await self._model.generate(prompt, *args, **kwargs)

        resp = resp.generated_text.strip().split("\n")[0].strip()

        return resp
