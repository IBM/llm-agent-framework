# Standard
from typing import Any, List
import copy
import json
import logging

# Local
from lm_agent.base.registry import register_tool_handler
from lm_agent.base.tool_handler import BaseToolHandler, ToolConfig
from lm_agent.models.interface import ModelConfig, ModelInterface
import lm_agent.utils as utils

logger = logging.getLogger(__name__)


@register_tool_handler("LLM")
class LlmGenerationTool(BaseToolHandler):
    description: str = "a pretrained LLM like yourself. Useful when you need to act with general world knowledge and common sense. Prioritize it when you are confident in solving the problem yourself. Input can be any instruction."
    _INP_VAR = "action_input"
    _PROMPT = "Respond in short directly with no extra words.\n\n{{" + _INP_VAR + "}}\n"

    def __init__(self, config: ToolConfig):
        super().__init__(config)
        self._model = ModelInterface(ModelConfig(**self.config.model))

    async def __call__(
        self, action_input: str, *args: Any, prompt=None, **kwds: Any
    ) -> str:
        prompt = self._PROMPT if prompt is None else prompt
        input_text = prompt.replace("{{" + self._INP_VAR + "}}", action_input)
        result = await self._model.generate(input_text)
        return result.generated_text
