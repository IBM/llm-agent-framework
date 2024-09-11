# Standard
import argparse
import asyncio
import os

# Local
from lm_agent.session_manager import SessionManager
from lm_agent.tasks import TaskIndex
import lm_agent.utils as utils

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH = os.path.split(BASE_PATH)[0]

os.environ["HF_HOME"] = os.path.join(BASE_PATH, ".cache", "huggingface", "transformers")
os.environ["HF_DATASETS_CACHE"] = os.path.join(
    BASE_PATH, ".cache", "huggingface", "datasets"
)


def get_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    add_base_args(parser)
    add_model_args(parser)
    add_task_args(parser)

    return parser


def add_base_args(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("base", "General command-line arguments")

    group.add_argument(
        "--include-path",
        type=str,
        default=None,
        metavar="DIR",
        help="Additional path to include if there are external tasks to include.",
    )
    group.add_argument(
        "--agents",
        "-a",
        default="react",
        type=str,
        metavar="agent1,agent2",
        help="Agents to use for tasks",
    )
    group.add_argument(
        "--tasks",
        "-t",
        default=None,
        type=str,
        metavar="task1,task2",
        help="Tasks to execute",
    )
    group.add_argument(
        "--restart",
        action="store_true",
        help="Restart experiment even if partial results exist",
    )

    return group


def add_model_args(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("model", "General command-line arguments")

    group.add_argument(
        "--lm-cache",
        "-c",
        type=str,
        metavar="DIR",
        help="A path to a sqlite db file for caching model responses. `None` if not caching.",
    )
    group.add_argument(
        "--model-id-or-path",
        "-m",
        type=str,
        help="Name of model e.g. `meta-llama/llama-3-8b`",
    )
    group.add_argument(
        "--model-backend",
        "-mb",
        type=str,
        help="Backend to use for model e.g. `hf`",
    )

    return group


def add_task_args(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("task", "General command-line arguments")

    group.add_argument(
        "--dataset-size",
        "-ds",
        type=int,
        default=-1,
        help="Size of dataset to test on (if testing on dataset)",
    )
    group.add_argument(
        "--output-dir",
        default=None,
        type=str,
        help="Directory to output data",
    )

    return group


def gather_grouped_args(
    args: argparse.Namespace, parser: argparse.ArgumentParser, group_name: str
):
    for g in parser._action_groups:
        if g.title == group_name:
            kwargs = dict()
            for act in g._group_actions:
                if hasattr(args, act.dest) and getattr(args, act.dest) is not None:
                    kwargs[act.dest] = getattr(args, act.dest)
            return kwargs
    raise ValueError(f"Unrecognized group name: {group_name}")


if __name__ == "__main__":

    """
    python -m lm_agent.__main__ --tasks <task-name --agents <agent-list>
    """

    parser = get_parser()

    args = parser.parse_args()

    base_args = gather_grouped_args(args, parser, "base")
    model_kwargs = gather_grouped_args(args, parser, "model")
    task_kwargs = gather_grouped_args(args, parser, "task")

    include_path = base_args.get("include_path", None)
    agent_list = base_args.get("agents").split(",")
    task_list = base_args.get("tasks").split(",")
    restart = base_args.get("restart", False)

    task_manager = TaskIndex(include_path)

    task_names = task_manager.match_tasks(task_list)
    for task in [task for task in task_list if task not in task_names]:
        if os.path.isfile(task):
            config = utils.load_yaml_config(task)
            task_names.append(config)

    task_missing = [
        task for task in task_list if task not in task_names and "*" not in task
    ]

    if task_missing:
        missing = ", ".join(task_missing)
        raise ValueError(f"Tasks not found: [{missing}]")

    task_cfgs = []
    for task_name, task_cfg in task_manager.load_tasks(task_names).items():
        task_info = task_manager.index[task_name]
        # import early to catch issues
        utils.import_task(task_info["task_import"])
        task_cfgs.append(task_cfg.config)

    session_manager = SessionManager(
        tasks=task_cfgs,
        agents=agent_list,
        restart=restart,
        model_kwargs=model_kwargs,
        task_kwargs=task_kwargs,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(session_manager.execute_tasks())
