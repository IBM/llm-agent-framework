# Standard
from dataclasses import dataclass
from typing import List, Optional
import abc

# Local
from lm_agent.base.model import BaseModel, ModelResourceConfig, ModelResult
from lm_agent.base.registry import get_resource
from lm_agent.utils import lma_logger


@dataclass
class ModelConfig(dict):
    model_backend: Optional[str] = None
    model_id_or_path: Optional[str] = None
    temperature: Optional[float] = None
    max_new_tokens: Optional[int] = None
    min_new_tokens: Optional[int] = None
    lm_cache: Optional[str] = None


class ModelInterface:
    """Class for LLMs"""

    def __init__(self, config: ModelConfig):
        self._config = config
        resource_config = ModelResourceConfig.from_model_config(config)
        self._model: BaseModel = get_resource(
            resource_config.model_backend, resource_config
        )

    @property
    def config(self):
        return self._config

    @property
    def model(self):
        return self._model

    async def loglikelihood(self, text: str, prefix: str = "", **kwargs) -> List:
        kwargs = {
            "model_id_or_path": self._config.model_id_or_path,
            **kwargs,
        }
        resp = await self._model.loglikelihood(text, prefix=prefix, **kwargs)
        return resp

    @abc.abstractmethod
    async def generate(self, text: str, **kwargs) -> ModelResult:
        kwargs = {
            "model_id_or_path": self._config.model_id_or_path,
            "temperature": self._config.temperature,
            "max_new_tokens": self._config.max_new_tokens,
            "min_new_tokens": self._config.min_new_tokens,
            **kwargs,
        }
        kwargs["decoding_method"] = kwargs.get(
            "decoding_method", "greedy" if kwargs["temperature"] <= 0.0 else "sample"
        )
        resp = await self._model.generate(text, **kwargs)
        return resp
