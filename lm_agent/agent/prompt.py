# Standard
from typing import Any, List, Optional, Tuple
import re

# Third Party
import yaml


class AgentPrompt:
    """Base Class for all Prompts"""

    """These are the input variables that need to be filled for the particular prompt"""
    input_variables: List[str]

    """The stop sequences needed to end generation for a particular prompt"""
    stop_sequences: List[str]

    def __init__(
        self,
        prompt_dict: dict,
        state_assignments: dict[str, str],
        init_vars: Optional[dict] = None,
    ):
        instructions = prompt_dict["instructions"]
        examples = _update_examples(prompt_dict["examples"], state_assignments)
        self._prompt = "\n\n".join([instructions, examples]) + "\n\n"
        self._input = _update_list(prompt_dict["input"], state_assignments)

        if init_vars is not None:
            self._prompt = _format(self._prompt, **init_vars)
            self._input = _format(self._input, **init_vars)

        self._input_variables = re.findall("\{\{(.*?)\}\}", self._prompt)

    def format_input(self, **kwargs: Any) -> Tuple[str, str]:
        return _format(self._prompt, **kwargs), _format(self._input, **kwargs)

    def all_variables_matched(self, formatted_prompt: str):
        return all(
            [
                "{{" + inp_var + "}}" in formatted_prompt
                for inp_var in self._input_variables
            ]
        )

    @classmethod
    def from_yaml(cls, path: str, state_assignments: dict, **kwargs: Any):
        """Load the corresponding yaml files and return the prompt"""
        with open(path, "rb") as file:
            yaml_prompt = yaml.full_load(file)
        return cls(yaml_prompt, state_assignments)


def _update_examples(example_lists, state_assignments):
    new_examples = [
        _update_list(example, state_assignments) for example in example_lists
    ]
    return "\n\n".join(new_examples)


def _update_list(lst, state_assignments):
    new_list = []
    for kv_pair in lst:
        assert len(kv_pair) == 1, f"Malformed example pair: {kv_pair}"
        key, val = next(iter(kv_pair.items()))
        new_list.append(state_assignments[key] + " " + val)
    return "\n".join(new_list).strip()


def _format(input_text: str, **kwargs: Any) -> str:
    """Format the prompt to string with the optional variables and return"""
    string = input_text
    for k, v in kwargs.items():
        string = string.replace("{{" + k + "}}", v)
    return string
