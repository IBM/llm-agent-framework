from typing import Any
import copy
from openai import OpenAI
import logging

from ..api_models import ApiModel
from ..prompt import sub_in_kv
from ..config import Config
from .tool_handler import Tool


logger = logging.getLogger(__name__)


class LlmGenerationTool(Tool):

    name: str = 'LLM'
    description: str = "a pretrained LLM like yourself. Useful when you need to act with general world knowledge and common sense. Prioritize it when you are confident in solving the problem yourself. Input can be any instruction."
    INP_VAR = 'action_input'
    _PROMPT = 'Respond in short directly with no extra words.\n\n{{' + INP_VAR + '}}'
    
    def __init__(self, config: Config, prompt: str=None):
        config = copy.deepcopy(config)
        config.model = config.tool_model
        super().__init__(config)

        self._prompt = prompt
        if self._prompt is None: self._prompt = self._PROMPT

        config.max_tokens = 128
        self.llm = ApiModel(config)
        self.llm.add_stop_sequences(['\n'])

    def __call__(self, action_input : str, *args: Any, prompt=None, attempts=3, **kwds: Any) -> str:
        prompt = self._prompt if prompt is None else prompt
        input_text = sub_in_kv(prompt, self.INP_VAR, action_input)
        resp = self.llm.generate(input_text)
        return resp.generated_text.strip()

class LlmScoringTool(Tool):

    name: str = 'LlmScorer'

    def __init__(self, config: Config, prompt : str=None):
        config = copy.deepcopy(config)
        config.model = config.tool_model
        super().__init__(config)
        self.llm = ApiModel(config)
        self.llm.add_stop_sequences(['\n'])

    def __call__(self, action_input : str, to_score : str, *args: Any, **kwds: Any) -> str:
        
        # TODO: figure out scoring for OpenAI model
        if isinstance(self.llm._model, OpenAI):
            logger.warning(f'Scoring has not yet been implemented for model type {self.config.model}, defaulting to length!')
            return -len(to_score)

        return self.llm.score(prompt=action_input, to_score=to_score)
        