# Standard
from dataclasses import asdict
from typing import Optional

# Local
from lm_agent.models.interface import ModelConfig, ModelInterface


class DecodingState:
    def __init__(
        self,
        name: str,
        text: str,
        model: Optional[dict] = None,
        env_input: Optional[bool] = False,
    ):
        self._name = name
        self._text = text
        self._model = (
            ModelInterface(ModelConfig(**model)) if model is not None else None
        )
        self._is_env = env_input

    @property
    def name(self):
        return self._name

    @property
    def text(self):
        return self._text

    @property
    def is_env(self):
        return self._is_env

    @property
    def model(self):
        return self._model

    def __repr__(self):
        return self._name

    def is_equiv_gen(self, other_obj: object):
        other_obj: DecodingState = other_obj
        return (not other_obj.is_env) and list(
            asdict(self.model.config).items()
        ) == list(asdict(other_obj.model.config).items())
