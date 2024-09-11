# Standard
from typing import Any, Dict, List, Tuple, Union
import copy

# Third Party
import numpy as np

# Local
from lm_agent.base.registry import register_state_handler
from lm_agent.base.state_handler import BaseStateHandler
from lm_agent.base.tool_handler import RecoverableToolError
from lm_agent.models.interface import ModelConfig, ModelInterface
from lm_agent.states.observation import ToolStateHandler

_PLAN_SN, _ACT_SN, _ACT_INP_SN = (
    "plan",
    "action",
    "action-input",
)


@register_state_handler("summarize")
class ToolSetHandler(ToolStateHandler):
    async def _get_observations(
        self, history: List, *args, **kwargs
    ) -> List[Tuple[bool, Any]]:

        i = len(history) - 1
        while history[i][0].name != _PLAN_SN:
            i -= 1
        rel_history = history[i + 1 :]

        obs_lst = [
            (act_name, act_input)
            for (_, act_name), (_, act_input) in zip(
                filter(lambda x: x[0].name == _ACT_SN, rel_history),
                filter(lambda x: x[0].name == _ACT_INP_SN, rel_history),
            )
        ]

        observations = []
        for action_name, action_input in obs_lst:
            try:
                obs = await self._get_observation(
                    action_name,
                    action_input,
                    *args,
                    squash_recoverable_error=False,
                    **kwargs,
                )
                observations.append((True, obs))
            except RecoverableToolError as e:
                observations.append((False, str(e)))

        return observations

    async def __call__(self, history, *args: Any, **kwargs: Any) -> str:
        observations = await self._get_observations(history, *args, **kwargs)
        obs_str = "\n".join([x.replace("\n", "") for _, x in observations])
        return obs_str


_PREFIX = "Solve the following task or problem. To assist you, we have provided background information. Note that the provided background information may contain noise so you should trust it with caution."
_SUFFIX = "Now begin to solve the task or problem. Respond with the answer directly with no extra words."


@register_state_handler("post_action_solve")
class PostActionSolveHandler(BaseStateHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._model = ModelInterface(ModelConfig(**self.config.model))

    async def __call__(self, history, *args: Any, **kwargs: Any) -> str:

        question_text = history[0][1]

        # assumes correct formatting of inputs
        trajectory = []
        for label, content in history[1:]:
            if label.name not in [_PLAN_SN, _ACT_SN, _ACT_INP_SN]:
                for line in content.split("\n"):
                    trajectory.append((f"({len(trajectory)+1})", line.strip()))
        trajectory = [
            ("Background Information:", ""),
        ] + trajectory

        prompt = []
        prompt.append(_PREFIX)
        prompt.append(
            "\n".join([f"{label} {content}" for label, content in trajectory])
        )
        prompt.append(_SUFFIX)
        prompt.append("Question: " + question_text)

        prompt = "\n\n".join(prompt) + "\nAnswer:"

        resp = await self._model.generate(prompt, *args, **kwargs)
        resp = resp.generated_text.strip().split("\n")[0].strip()

        # print(prompt)
        # print("--")
        # print(resp)
        # input("==")

        return resp
