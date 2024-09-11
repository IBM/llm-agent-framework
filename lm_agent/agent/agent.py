# Standard
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import os
import re

# Local
from lm_agent.agent.decoding_state import DecodingState
from lm_agent.agent.monitor import TransitionMonitor
from lm_agent.agent.prompt import AgentPrompt
from lm_agent.base.registry import get_state_handler, get_tool_handler
from lm_agent.base.state_handler import BaseStateHandler, StateHandlerConfig
from lm_agent.base.tool_handler import ToolConfig
import lm_agent.agent.utils as agent_utils
import lm_agent.utils as utils


@dataclass
class AgentConfig(dict):
    name: str
    states: Optional[dict] = None
    behavior: Optional[dict] = None
    tools: Optional[dict] = None
    model: Optional[dict] = None
    max_response_tokens: Optional[int] = None
    self_consistency: Optional[int] = 1

    def __post_init__(self):
        if self.states is None:
            self.states = dict()


DEFAULT_AGENT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "agent_specifications"
)
DEFAULT_TOOL_VAR = "tool_descriptions"


class Agent:
    """Class for LLMs"""

    def __init__(
        self,
        config: AgentConfig,
        base_prompt: Dict,
        agent_path: Optional[str] = None,
    ):
        self._name = config.name
        self._self_consistency = config.self_consistency

        self._max_generation_steps = config.get("max_generation_steps", 5)

        if agent_path is None:
            agent_path = os.path.join(DEFAULT_AGENT_PATH, config.name + ".yaml")

        formal_config = AgentConfig(**utils.load_yaml_config(agent_path))
        assert (
            formal_config.states is not None and formal_config.behavior is not None
        ), f"Must define both states and behavior in agent file {agent_path}"

        for state_name, state_info in formal_config.states.items():
            state_info = {
                "name": state_name,
                "model": config.model,
                **state_info,
            }
            config.states[state_name] = (
                utils.merge_dicts(state_info, config.states[state_name])
                if state_name in config.states
                else state_info
            )

        self._config = config

        self._base_prompt = base_prompt
        self._behavior = formal_config.behavior

    @property
    def name(self):
        return self._name

    @property
    def states(self):
        return self.states

    @property
    def config(self):
        return self._config

    @property
    def self_consistency(self):
        return self._self_consistency

    async def solve(self, return_all: bool = False, **prompt_kwargs: Dict):
        outputs = []
        for _ in range(self.self_consistency):
            output = await self._solve(**prompt_kwargs)
            outputs.append(output)
        return outputs if return_all else outputs[0]

    async def _solve(self, **prompt_kwargs: Dict):
        def get_inp_string():
            return prompt + "\n".join(
                [
                    f"{state.text} " + (content if content else "")
                    for state, content in history
                ]
            )

        def get_state_change_trigger(valid_states):
            prefix = "\n" + os.path.commonprefix(
                [states[state_name].text for state_name in valid_states]
            )
            return prefix

        def get_stop_sequences(dec_state: DecodingState):
            default_stop_sequences = [
                state.text for state in transition_system.entry_states
            ]
            stop_sequences = [
                v.text for v in states.values() if not dec_state.is_equiv_gen(v)
            ] + default_stop_sequences
            return stop_sequences

        def exit_reached():
            return (
                generated_token_count > self._config.max_response_tokens
                or (transition_system.exit_reached() and history[-1][1] is not None)
                or gen_steps > self._max_generation_steps
            )

        def update_history(string_to_parse):
            sc_pairs = _split_on_states(string_to_parse, states)
            for i, (state_name, content) in enumerate(sc_pairs):
                if state_name is None:
                    assert (
                        history[-1][1] is None
                    ), f"Unexpected history format: {history}"
                    history[-1][1] = content
                elif transition_system.is_valid(state_name):
                    transition_system.step(state_name)
                    if states[state_name].is_env:
                        history.append([states[state_name], None])
                        break
                    else:
                        history.append([states[state_name], content])
                else:
                    break

        states, state_handlers, behavior, prompt_obj = self._initialize_agent_run()

        transition_system = TransitionMonitor(behavior, states)

        assert prompt_obj is not None, f"Prompt not set for agent {self.name}!"
        prompt, string_to_parse = prompt_obj.format_input(**prompt_kwargs)

        history: List[Tuple[DecodingState, str]] = []
        initial_token_count = 0
        generated_token_count = 0
        gen_steps = 0

        update_history(string_to_parse)

        while not exit_reached():
            string_to_parse = ""
            current_state, current_content = history[-1]
            if current_state.is_env and current_content is None:
                string_to_parse += await state_handlers[current_state.name](
                    history[:-1]
                )

            valid_next_states = transition_system.get_available_states()
            if valid_next_states and not transition_system.exit_reached():
                string_to_parse += get_state_change_trigger(valid_next_states)
                stop_seq = get_stop_sequences(current_state)
                gen_result = await current_state.model.generate(
                    get_inp_string() + string_to_parse, stop_sequences=stop_seq
                )
                string_to_parse += gen_result.generated_text

                # getting token counts
                if initial_token_count == 0:
                    initial_token_count = gen_result.input_token_count
                generated_token_count = (
                    gen_result.generated_token_count
                    + gen_result.input_token_count
                    - initial_token_count
                )
                gen_steps += 1

            update_history(string_to_parse)

        if history[-1][1] is None:
            history.pop()

        return [(state.text, content) for state, content in history]

    def _initialize_agent_run(self):
        states, state_handlers = _initialize_states(self._config)
        behavior = _initialize_transition_system(self._behavior)
        prompt_obj = _initialize_prompt(self._base_prompt, states, state_handlers)
        return states, state_handlers, behavior, prompt_obj


def _initialize_states(
    config: AgentConfig,
):
    model_config = config.model
    state_configs = config.states
    tool_configs = config.tools

    # initializing states is more involved
    states: Dict[str, DecodingState] = dict()
    state_handlers: Dict[str, BaseStateHandler] = dict()

    for state_name, state_info in state_configs.items():
        state_info["model"] = utils.merge_dicts(
            model_config,
            (state_info["model"] if state_info["model"] is not None else {}),
        )
        new_state = DecodingState(
            **{
                k: v
                for k, v in state_info.items()
                if k in ["name", "text", "env_input", "model"]
            }
        )
        states[state_name] = new_state
        if new_state.is_env:
            state_cfg = StateHandlerConfig(**state_info)
            state_tools = _initialize_tools(model_config, tool_configs)
            state_handlers[new_state.name] = get_state_handler(state_cfg.name)(
                state_cfg, state_tools
            )
    return states, state_handlers


def _initialize_tools(model_config: Dict, tool_configs: List):
    tools = dict()
    for tool_config in tool_configs:
        if type(tool_config) == str:
            tool_config = {"name": tool_config}
        else:
            assert len(tool_config) == 1
            tool_config = {
                "name": next(iter(tool_config.keys())),
                **next(iter(tool_config.values())),
            }

        tool_config = ToolConfig(**tool_config)

        tool_config.model = utils.merge_dicts(
            model_config,
            (tool_config.model if tool_config.model is not None else {}),
        )
        tools[tool_config.name] = get_tool_handler(tool_config.name)(tool_config)
    return tools


def _initialize_transition_system(behavior: List[Dict]):
    def _tuplefy(b):
        if type(b) == dict:
            kv = list(b.items())
            assert len(kv) == 1
            return tuple([kv[0][0]] + _tuplefy(kv[0][1]))
        elif type(b) == list:
            return [_tuplefy(arg) for arg in b]
        else:
            return b

    assert len(behavior) == 1, "Cannot begin with multiple top-level keys!"
    behavior = behavior[0]
    return _tuplefy(behavior)


def _initialize_prompt(prompt_dict, states, state_handlers):
    init_vars = dict()
    tools = {
        tool.name: tool
        for state_handler in state_handlers.values()
        for tool in state_handler.tools.values()
    }
    if tools:
        init_vars[DEFAULT_TOOL_VAR] = agent_utils.tool_list_to_string(tools)

    prompt_obj = AgentPrompt(
        prompt_dict,
        {k: v.text for k, v in states.items()},
        init_vars=init_vars,
    )
    return prompt_obj


def _split_on_states(text: str, states: Dict):
    state_texts = [re.escape(x.text) for x in states.values()]
    state_map = {x.text: x.name for x in states.values()}
    split_lst = [
        x.strip()
        for x in re.split(
            "(" + "|".join(state_texts) + ")",
            text,
            flags=re.IGNORECASE,
        )
    ]
    if split_lst[0] == "":
        split_lst.pop(0)
    if split_lst[-1] == "":
        split_lst.pop()

    ret_lst = [[]]
    for comp in split_lst:
        if comp in state_map:
            ret_lst.append([])
            comp = state_map[comp]
        ret_lst[-1].append(comp)
    if ret_lst[0] == []:
        ret_lst.pop(0)

    if len(ret_lst[0]) == 1:
        ret_lst[0] = [None] + ret_lst[0]

    if len(ret_lst[-1]) == 1:
        ret_lst[-1] = ret_lst[-1] + [None]

    assert all(
        [len(lst) == 2 for lst in ret_lst]
    ), f"Malformed list structure, this is not expected behavior: {ret_lst}"

    return ret_lst
