# Standard
from typing import Any, Dict, Type
import logging
import os

# Local
from lm_agent.base.model import BaseModel, CachingLM
from lm_agent.base.resource import BaseResource
from lm_agent.base.state_handler import BaseStateHandler
from lm_agent.base.tool_handler import BaseToolHandler
from lm_agent.utils import lma_logger

# TODO: agent registry, state registry, tool registry, resource registry


STATE_HANDLER_REGISTRY = {}


def register_state_handler(*names) -> None:
    # either pass a list or a single alias.
    # function receives them as a tuple of strings

    def decorate(cls):
        for name in names:
            assert issubclass(
                cls, BaseStateHandler
            ), f"State handler '{name}' ({cls.__name__}) must extend BaseStateHandler class"

            assert (
                name not in STATE_HANDLER_REGISTRY
            ), f"State handler named '{name}' conflicts with existing state handler! Please register with a non-conflicting alias instead."

            STATE_HANDLER_REGISTRY[name] = cls
        return cls

    return decorate


def get_state_handler(obj_name) -> Type[BaseStateHandler]:
    try:
        return STATE_HANDLER_REGISTRY[obj_name]
    except KeyError:
        raise ValueError(
            f"Attempted to load state handler '{obj_name}', but no state handler for this name found! Supported state handler names: {', '.join(STATE_HANDLER_REGISTRY.keys())}"
        )


TOOL_HANDLER_REGISTRY = {}


def register_tool_handler(*names) -> None:
    # either pass a list or a single alias.
    # function receives them as a tuple of strings

    def decorate(cls):
        for name in names:
            assert issubclass(
                cls, BaseToolHandler
            ), f"Tool handler '{name}' ({cls.__name__}) must extend BaseToolHandler class"

            assert (
                name not in TOOL_HANDLER_REGISTRY
            ), f"Tool handler named '{name}' conflicts with existing tool handler! Please register with a non-conflicting alias instead."

            TOOL_HANDLER_REGISTRY[name] = cls
        return cls

    return decorate


def get_tool_handler(obj_name) -> Type[BaseToolHandler]:
    try:
        return TOOL_HANDLER_REGISTRY[obj_name]
    except KeyError:
        raise ValueError(
            f"Attempted to load tool handler '{obj_name}', but no tool handler for this name found! Supported tool handler names: {', '.join(TOOL_HANDLER_REGISTRY.keys())}"
        )


RESOURCE_REGISTRY = {}
resource_index: Dict[str, BaseResource] = {}


def register_resource(*names) -> None:
    # either pass a list or a single alias.
    # function receives them as a tuple of strings
    def decorate(cls):
        for name in names:
            assert issubclass(
                cls, BaseResource
            ), f"Resource '{name}' ({cls.__name__}) must extend BaseResource class"
            assert (
                name not in RESOURCE_REGISTRY
            ), f"Resource named '{name}' conflicts with existing resource! Please register with a non-conflicting alias instead."

            RESOURCE_REGISTRY[name] = cls
        return cls

    return decorate


def get_resource(obj_name, *args, **kwargs) -> Type[BaseResource]:
    try:
        if not obj_name in resource_index:
            ret_resource = RESOURCE_REGISTRY[obj_name](*args, **kwargs)
            resource_index[obj_name] = ret_resource
            if isinstance(ret_resource, BaseModel) and ret_resource.config.lm_cache:
                lma_logger.info(f"Using cache at {ret_resource.config.lm_cache}")
                resource_index[obj_name] = CachingLM(
                    resource_index[obj_name],
                    ret_resource.config.lm_cache
                    # each rank receives a different cache db.
                    # necessary to avoid multiple writes to cache at once
                    + f"_model{os.path.split(ret_resource.model_id_or_path)[-1]}_rank{ret_resource.rank}.db",
                )
        ret_resource = resource_index[obj_name]
        assert not ret_resource.is_conflicting(*args, **kwargs)
        return ret_resource
    except KeyError:
        raise ValueError(
            f"Attempted to load resource '{obj_name}', but no resource for this name found! Supported resource names: {', '.join(RESOURCE_REGISTRY.keys())}"
        )


TASK_REGISTRY = {}
ALL_TASKS = set()
func2task_index = {}


def register_task(name) -> None:
    def decorate(fn):
        assert (
            name not in TASK_REGISTRY
        ), f"task named '{name}' conflicts with existing registered task!"

        TASK_REGISTRY[name] = fn
        ALL_TASKS.add(name)
        func2task_index[fn.__name__] = name
        return fn

    return decorate


def get_task(name):
    try:
        return TASK_REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Attempted to load task '{name}', but no task for this name found! Supported task names: {', '.join(TASK_REGISTRY.keys())}"
        )
