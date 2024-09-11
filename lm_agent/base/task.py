# Standard
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Union
import abc
import asyncio
import json
import os

# Third Party
import yaml

# Local
from lm_agent.agent.agent import Agent, AgentConfig
from lm_agent.utils import lma_logger
import lm_agent.utils as utils


@dataclass
class TaskConfig(dict):
    task: str
    model: dict
    tools: Optional[dict] = None
    agents: Optional[dict] = None
    input_source: Optional[dict] = None
    metadata: Optional[
        dict
    ] = None  # by default, not used in the code. allows for users to pass arbitrary info to tasks


TYPE_KEY = "type"
DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_PROMPT_DIR = "prompts"


class Task(ABC):
    """A task represents"""

    VERSION: Optional[Union[int, str]] = None

    def __init__(
        self,
        config: TaskConfig,
        agents: List[str],
        model_kwargs: Dict,
        output_dir: Optional[str] = None,
        dataset_size: Optional[int] = -1,
        prompt_path: Optional[str] = None,
    ) -> None:
        """ """
        self._config = config

        # optional args
        self._dataset_size = dataset_size

        if agents is not None:
            self._config.agents = {
                agent: self._config.agents[agent] for agent in agents
            }

        model_config = utils.merge_dicts(config.model, model_kwargs)

        if prompt_path is None:
            prompt_path = os.path.join(
                self.config.metadata["task_dir"],
                DEFAULT_PROMPT_DIR,
                self.name + ".yaml",
            )
        with open(prompt_path, "rb") as file:
            yaml_prompt = yaml.full_load(file)

        self._agents: Dict[str, Agent] = dict()
        for agent_name, agent_cfg_dict in self._config.agents.items():
            agent_cfg = AgentConfig(**{"name": agent_name, **agent_cfg_dict})

            assert (
                not agent_cfg.name in self._agents
            ), f"Cannot have duplicate agents: {agent_cfg.name}!"

            agent_cfg.model = utils.merge_dicts(
                model_config,
                (agent_cfg.model if agent_cfg.model is not None else {}),
            )

            agent_obj = Agent(agent_cfg, yaml_prompt[agent_cfg.name])
            self._agents[agent_cfg.name] = agent_obj

        self._output_dir = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR
        self._output_path = getattr(
            self._config, "output_path", self._get_default_output_path()
        )

    @property
    def config(self) -> TaskConfig:
        """Returns the TaskConfig associated with this class."""
        return self._config

    @property
    def name(self) -> str:
        return self.config.task

    @property
    def output_path(self) -> str:
        return self._output_path

    @property
    def output_dir(self) -> str:
        return self._output_dir

    @property
    def agents(self) -> Dict[str, Agent]:
        return self._agents

    def _get_default_output_path(self):
        path_components = []
        path_components.append(self._output_dir)
        path_components.append(self.config.task)
        return os.path.join(*path_components)

    def save_result(self, agent: Agent, result: List, output_path: str = None) -> None:
        output_path = (
            os.path.join(
                self._output_path,
                agent.name,
                utils.make_file_str(agent.config.model["model_id_or_path"]),
                "output.jsonl",
            )
            if output_path is None
            else output_path
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "a") as f:
            f.write(json.dumps(result) + "\n")

    def load_output(self, agent: Agent, output_path: str = None) -> List:
        output_path = (
            os.path.join(
                self._output_path,
                agent.name,
                utils.make_file_str(agent.config.model["model_id_or_path"]),
                "output.jsonl",
            )
            if output_path is None
            else output_path
        )
        if not os.path.isfile(output_path):
            return []
        outputs = []
        with open(output_path, "r") as f:
            try:
                for line in f.readlines():
                    outputs.append(json.loads(line))
            except ValueError as e:
                raise e
            return outputs

    def clear_previous_outputs(self, agent: Agent, output_path: str = None) -> None:
        output_path = (
            os.path.join(
                self._output_path,
                agent.name,
                utils.make_file_str(agent.config.model["model_id_or_path"]),
                "output.jsonl",
            )
            if output_path is None
            else output_path
        )
        if os.path.exists(output_path):
            os.remove(output_path)

    def get_task_calls(self, agent: Agent, to_exclude: List = None):
        examples = self.get_task_inputs(to_exclude)
        calls = set()
        for example in examples:
            task = asyncio.create_task(self(agent, *example))
            calls.add(task)
            task.add_done_callback(calls.discard)
        return calls

    @abc.abstractmethod
    def get_task_inputs(self, to_exclude: List = None):
        raise NotImplementedError

    @abc.abstractmethod
    async def __call__(self, *args: Any, **kwargs: Any):
        """In this function..."""
        raise NotImplementedError


class ConfigurableTask(Task):
    VERSION = "Yaml"
    OUTPUT_TYPE = None
    CONFIG = None

    def __init__(
        self,
        config: Optional[dict] = None,
    ) -> None:  # TODO no super() call here
        # Get pre-configured attributes
        self._config = self.CONFIG

        # Use new configurations if there was no preconfiguration
        if self.config is None:
            self._config = TaskConfig(**config)
        # Overwrite configs
        else:
            if config is not None:
                self._config.__dict__.update(config)

        if self.config is None:
            raise ValueError(
                "Must pass a config to ConfigurableTask, either in cls.CONFIG or `config` kwarg"
            )

        if isinstance(self.config.metadata, dict):
            if "version" in self.config.metadata:
                self.VERSION = self.config.metadata["version"]

    def get_task_inputs(self, to_exclude: List = None):
        raise NotImplementedError

    def get_task_calls(self):
        raise NotImplementedError

    async def __call__(self, *args: Any, **kwargs: Any):
        """In this function..."""
        raise NotImplementedError
