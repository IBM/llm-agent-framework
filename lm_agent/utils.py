# Standard
from typing import Any, Dict
import fnmatch
import importlib
import logging
import os

# Third Party
import yaml

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)
lma_logger = logging.getLogger("lm_agent")


def import_task(inp_task: str, fpath: str = None) -> None:
    # TODO: this must be generalized
    import_path = f"lm_agent.tasks.{inp_task}.generate" if fpath is None else fpath
    importlib.import_module(import_path)


def import_tool_or_state(inp: str, inp_type: str, fpath: str = None) -> None:
    # TODO: this must be generalized
    import_path = f"lm_agent.{inp_type}.{inp}" if fpath is None else fpath
    importlib.import_module(import_path)


def load_yaml_config(yaml_path=None, yaml_config=None, yaml_dir=None):
    def load_file(path):
        try:
            if path.endswith(".yaml"):
                data = load_yaml_config(yaml_path=path)
            else:
                with open(path, "r") as f:
                    data = f.read()
            return data
        except Exception as ex:
            # If failed to load, ignore
            raise ex

    def init_include(to_include: Any):
        if type(to_include) == list:
            return [init_include(x) for x in to_include]
        elif type(to_include) == dict:
            return {k: init_include(v) for k, v in to_include.items()}
        elif type(to_include) == str:
            if os.path.isfile(to_include):
                # case where provided include is an absolute path
                add_data = load_file(to_include)
            elif os.path.isfile(os.path.join(yaml_dir, to_include)):
                # case where provided include is a relative path
                add_data = load_file(os.path.join(yaml_dir, to_include))
            else:
                raise ValueError(
                    f"Should not include non-file paths in include directive: {to_include}"
                )
            return add_data
        else:
            raise ValueError(
                f"Unhandled input format in 'include' directive: {to_include}"
            )

    # Add the import_function constructor to the YAML loader
    if yaml_config is None:
        with open(yaml_path, "rb") as file:
            yaml_config = yaml.full_load(file)

    if yaml_dir is None:
        yaml_dir = os.path.dirname(yaml_path)

    assert yaml_dir is not None

    if "include" in yaml_config:
        to_include = yaml_config["include"]
        del yaml_config["include"]

        if isinstance(to_include, str):
            to_include = [to_include]

        final_yaml_config = dict()
        to_add = init_include(to_include)
        if type(to_include) == list:
            for entry in to_add:
                final_yaml_config.update(entry)
        elif type(to_include) == dict:
            final_yaml_config.update(to_add)
        else:
            raise ValueError(
                f"Unhandled input format in 'include' directive: {to_include}"
            )

        final_yaml_config.update(yaml_config)
        return final_yaml_config

    return yaml_config


def pattern_match(patterns, source_list):
    if isinstance(patterns, str):
        patterns = [patterns]

    task_names = set()
    for pattern in patterns:
        for matching in fnmatch.filter(source_list, pattern):
            task_names.add(matching)
    return sorted(list(task_names))


def make_file_str(string: str):
    return string.replace(os.path.sep, "_")


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    ret = dict(dict1)
    for k, v in dict2.items():
        if v is not None:
            ret[k] = v
    return ret
