# Standard
from collections import defaultdict
from typing import Any, List
import asyncio
import random

# Third Party
from datasets import load_dataset

# Local
from lm_agent.agent.agent import Agent
from lm_agent.base.registry import register_task
from lm_agent.base.task import Task
import lm_agent.tasks.qa.utils as qa_utils


class QADatasetTask(Task):
    def get_task_inputs(self, to_exclude: List = None):
        raise NotImplementedError

    async def __call__(self, agent: Agent, question: str, answer: Any, idx: Any):
        responses = await agent.solve(return_all=True, input=question)
        grouped_responses = defaultdict(list)
        for resp in responses:
            grouped_responses[qa_utils.normalize_answer(resp[-1][1])].append(resp)
        best_response = max(grouped_responses.values(), key=len)[0]
        gen_answer = best_response[-1][-1]
        return {
            "question": question,
            "answer": answer,
            "idx": idx,
            "response": [list(x) for x in grouped_responses.values()],
            "generated_answer": gen_answer,
        }


@register_task("gsm8k_main")
class GSM8KTask(QADatasetTask):
    """Class for dataset task"""

    def get_task_inputs(self, to_exclude: List = None):
        dataset = qa_utils.load_hf_dataset(
            self.config.task.split("_"), "test", self._dataset_size
        )
        exclude_idx = set([ex["idx"] for ex in to_exclude])
        examples = [
            (example["question"], example["answer"], idx)
            for idx, example in enumerate(dataset)
            if not idx in exclude_idx
        ]
        return examples

    async def __call__(self, agent: Agent, question: str, answer: Any, idx: Any):
        result = await super().__call__(agent, question, answer, idx)
        is_correct = qa_utils.check_gsm8k(result["generated_answer"], answer)
        return {
            **result,
            "is_correct": is_correct,
        }


@register_task("hotpot_qa")
class HotpotQATask(QADatasetTask):
    """Class for dataset task"""

    def get_task_inputs(self, to_exclude: List = None):
        dataset = qa_utils.load_hf_dataset(
            [self.config.task, "fullwiki"], "validation", self._dataset_size
        )
        exclude_idx = set([ex["idx"] for ex in to_exclude])
        examples = [
            (example["question"], example["answer"], example["id"])
            for example in dataset
            if not example["id"] in exclude_idx
        ]
        return examples

    async def __call__(self, agent: Agent, question: str, answer: Any, idx: Any):
        result = await super().__call__(agent, question, answer, idx)
        is_correct = qa_utils.is_normalized_match(result["generated_answer"], answer)
        return {
            **result,
            "is_correct": is_correct,
        }


@register_task("trivia_qa")
class TriviaQATask(QADatasetTask):
    """Class for dataset task"""

    def get_task_inputs(self, to_exclude: List = None):
        dataset = qa_utils.load_hf_dataset(
            [self.config.task, "rc.nocontext"], "validation", self._dataset_size
        )
        exclude_idx = set([ex["idx"] for ex in to_exclude])
        examples = [
            (example["question"], example["answer"]["value"], example["question_id"])
            for example in dataset
            if not example["question_id"] in exclude_idx
        ]
        return examples

    async def __call__(self, agent: Agent, question: str, answer: Any, idx: Any):
        result = await super().__call__(agent, question, answer, idx)
        is_correct = qa_utils.is_normalized_match(result["generated_answer"], answer)
        return {
            **result,
            "is_correct": is_correct,
        }
