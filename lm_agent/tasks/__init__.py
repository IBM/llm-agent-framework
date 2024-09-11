# Standard
from typing import Dict, Mapping, Optional, Union
import collections
import os

# Local
from lm_agent.base.task import ConfigurableTask
import lm_agent.utils as utils


class TaskIndex:
    """TaskIndex indexes all tasks from the default `lm_agent/tasks/` and an optional directory if provided."""

    def __init__(self, include_path: Optional[str] = None) -> None:
        self.include_path = include_path
        self._index = self.initialize_tasks(include_path=include_path)
        self._all_tasks = sorted(list(self._index.keys()))

    def initialize_tasks(self, include_path: Optional[str] = None) -> Dict[str, Dict]:
        """Creates a dictionary of task index.

        :param include_path: str = None
            An additional path to be searched for task

        :return
            Dictionary of task names as key and task metadata
        """
        all_paths = [os.path.dirname(os.path.abspath(__file__)) + os.path.sep]
        if include_path is not None:
            if isinstance(include_path, str):
                include_path = [include_path]
            all_paths.extend(include_path)

        task_index = {}
        for task_dir in all_paths:
            tasks = self._get_task(task_dir)
            task_index = {**tasks, **task_index}

        return task_index

    @property
    def all_tasks(self):
        return self._all_tasks

    @property
    def index(self):
        return self._index

    def match_tasks(self, task_list):
        return utils.pattern_match(task_list, self.all_tasks)

    def name_is_registered(self, name) -> bool:
        return name in self.all_tasks

    def _get_yaml_path(self, name):
        if name not in self.index:
            raise ValueError
        return self.index[name]["yaml_path"]

    def _get_config(self, name_or_cfg):
        if name_or_cfg not in self.index:
            raise ValueError
        yaml_path = self._get_yaml_path(name_or_cfg)
        return dict() if yaml_path == -1 else utils.load_yaml_config(yaml_path)

    def _load_individual_task(
        self,
        name_or_config: Optional[Union[str, dict]] = None,
        update_config: Optional[dict] = None,
        yaml_path: Optional[str] = None,
    ) -> Mapping:
        def load_task(config, task_name, yaml_path=None):
            if "include" in config:
                if yaml_path is None:
                    raise ValueError
                config.update(
                    utils.load_yaml_config(
                        yaml_path,
                        yaml_config={"include": config.pop("include")},
                    )
                )
            config["metadata"]["task_dir"] = self.index[task_name]["task_dir"]
            task_object = ConfigurableTask(config=config)
            return {task_name: task_object}

        config = self._get_config(name_or_config)
        return load_task(config, task_name=name_or_config, yaml_path=yaml_path)

    def load_tasks(
        self, task_list: Optional[Union[str, list]] = None
    ) -> Dict[str, ConfigurableTask]:
        """Loads a dictionary of task objects from a list

        :param task_list: Union[str, list] = None
            Single string or list of string of task names to be loaded

        :return
            Dictionary of task objects
        """
        if isinstance(task_list, str):
            task_list = [task_list]

        all_loaded_tasks = dict(
            collections.ChainMap(*map(self._load_individual_task, task_list))
        )
        return all_loaded_tasks

    def _get_task(self, task_dir: str):
        """Creates a dictionary of tasks index with the following metadata, ...

        :param task_dir: str
            A directory to check for tasks

        :return
            Dictionary of task names as key and task metadata
        """
        tasks = collections.defaultdict()
        for root, _, file_list in os.walk(task_dir):
            for f in file_list:
                if f.endswith(".yaml"):
                    task_imp = os.path.split(root)[-1]
                    yaml_path = os.path.join(root, f)
                    config = utils.load_yaml_config(yaml_path)

                    # TODO: Clean this up and get rid of it, just load top two levels
                    if not "task" in config or config["task"] not in yaml_path:
                        continue

                    task_name = config["task"]
                    tasks[task_name] = {
                        "yaml_path": yaml_path,
                        "task_dir": root,
                        "task_import": task_imp,
                    }

        return tasks
