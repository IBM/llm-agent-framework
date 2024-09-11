# Standard
from collections import defaultdict
from typing import Dict, List, Optional
import asyncio
import json

# Third Party
from tqdm import tqdm

# Local
from lm_agent.base.registry import get_task
from lm_agent.base.task import Task, TaskConfig


class SessionManager:
    """A session manager will take in a set of tasks"""

    def __init__(
        self,
        tasks: List[TaskConfig],
        agents: List[str],
        model_kwargs: Dict,
        task_kwargs: Dict,
        restart: Optional[bool] = False,
    ):
        self._task_objs: List[Task] = []
        for task_cfg in tasks:
            task_obj: Task = get_task(task_cfg.task)(
                config=task_cfg,
                agents=agents,
                model_kwargs=model_kwargs,
                **task_kwargs,
            )
            self._task_objs.append(task_obj)
        self._restart = restart

    async def execute_tasks(self):
        task_results = defaultdict(list)
        for task_obj in tqdm(self._task_objs, desc="Task Iteration"):
            for agent in tqdm(task_obj.agents.values(), desc="Agent Iteration"):
                if self._restart:
                    task_obj.clear_previous_outputs(agent)
                prev_outputs = task_obj.load_output(agent)
                task_calls = task_obj.get_task_calls(agent, prev_outputs)
                progress_bar = tqdm(total=len(task_calls), desc=f"Task {task_obj.name}")
                for task_result in asyncio.as_completed(task_calls):
                    result = await task_result
                    task_obj.save_result(agent, result)
                    task_results[task_obj.name].append(result)
                    progress_bar.update(1)
