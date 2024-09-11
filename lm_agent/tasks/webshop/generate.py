# Standard
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple
import copy
import time

# Third Party
from scale_sdg.base.databuilder import DataBuilder
from scale_sdg.base.instance import Instance
from scale_sdg.base.instruct_data import InstructData
from scale_sdg.base.registry import register_data_builder
from scale_sdg.databuilders.api.prompts import ApiGenIntentPrompt, ApiGenSequencePrompt
from scale_sdg.generators.llm import LMGenerator
from scale_sdg.utils import sdg_logger
from scale_sdg.validators.api import (
    API_NAME,
    DESCR_NAME,
    PARAM_NAME,
    SLOT_LIST,
    ApiGenSpecIntentValidation,
    ApiGenSpecSequencingValidation,
    ApiGenSpecSlotFillingValidation,
)


@register_data_builder("api_yes_no_detection")
class ApiYesNoDataBuilder(DataBuilder):
    """Class for API Sequence task"""

    # llm1 is the main generator that will produce the synthetic examples
    llm1: LMGenerator

    def __call__(
        self,
        request_idx: int,
        instruction_data: List[InstructData],
        all_generated_instructions: List[InstructData],
    ) -> Tuple[List[InstructData], int]:

        inputs: List[Instance] = []
        for instr in instruction_data:
            prompt = f"{instr.input}\n\nQ: {instr.instruction}\nA: {instr.output}\n\nQ:"
            args = [prompt]
            kwargs = {"stop_sequences": [f"Q:"]}
            inputs.append(Instance(args, kwargs, data=instr))

        request_start = time.time()
        self.llm1.generate_batch(inputs)
        request_duration = time.time() - request_start

        post_process_start = time.time()
        discarded = 0
        outputs = []
        for gen_inp in inputs:
            instr: InstructData = gen_inp.data
            components = gen_inp.result.split("A:")
            if len(components) == 2:
                question, answer = [x.strip() for x in components]
            else:
                discarded += 1

            new_instr = copy.deepcopy(instr)
            new_instr.instruction = question
            new_instr.output = answer
            outputs.append(new_instr)

        post_process_duration = time.time() - post_process_start
        sdg_logger.debug(
            f"Request {request_idx} took {request_duration:.2f}s, "
            f"post-processing took {post_process_duration:.2f}s"
        )

        return outputs, discarded


@register_data_builder("api_detection")
class ApiDetectionDataBuilder(DataBuilder):
    """Class for API Sequence task"""

    # llm1 is the main generator that will produce the synthetic examples
    llm1: LMGenerator

    def __call__(
        self,
        request_idx: int,
        instruction_data: List[InstructData],
        all_generated_instructions: List[InstructData],
    ) -> Tuple[List[InstructData], int]:
        raise NotImplementedError


@register_data_builder("api_sequencing")
class ApiSequencingDataBuilder(DataBuilder):
    """Class for API Sequence task"""

    # llm1 is the main generator that will produce the synthetic examples
    llm1: LMGenerator

    def __call__(
        self,
        request_idx: int,
        instruction_data: List[InstructData],
        all_generated_instructions: List[InstructData],
    ) -> Tuple[List[InstructData], int]:
        raise NotImplementedError


@register_data_builder("api_slot_filling")
class ApiSlotFillingDataBuilder(DataBuilder):
    """Class for API task"""

    # llm1 is the main generator that will produce the synthetic examples
    llm1: LMGenerator

    def __call__(
        self,
        request_idx: int,
        instruction_data: List[InstructData],
        all_generated_instructions: List[InstructData],
    ) -> Tuple[List[InstructData], int]:
        raise NotImplementedError
