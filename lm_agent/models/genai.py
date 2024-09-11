# Standard
from functools import partial
from typing import Any, List
import asyncio
import copy
import os

# Local
from lm_agent.base.model import BaseModel, ModelResourceConfig
from lm_agent.base.registry import register_resource
from lm_agent.models.interface import ModelResult

try:
    # Third Party
    from dotenv import load_dotenv
    from genai import Client, Credentials
    from genai.schema import (
        TextGenerationParameters,
        TextGenerationReturnOptions,
        TextTokenizationParameters,
        TextTokenizationReturnOptions,
    )
except ModuleNotFoundError:
    pass


@register_resource("genai")
class GenAIGenerator(BaseModel):
    """GENAI Generator"""

    MAX_CALLS = 10
    MAX_THREADS = 10

    def __init__(self, config: ModelResourceConfig, **kwargs: Any):
        super().__init__(config, **kwargs)

        try:
            # Third Party
            import genai  # noqa: E401
        except ModuleNotFoundError:
            raise Exception(
                "attempted to use 'genai' LM type, but package `genai` not installed. ",
                "please install these via `pip install -r lm_agent[genai]`",
            )

        load_dotenv()
        credentials = Credentials(
            os.getenv("GENAI_KEY", None), api_endpoint=os.getenv("GENAI_API", None)
        )
        self.client = Client(credentials=credentials)

    @property
    def eot_token_id(self):
        return ""

    @property
    def max_length(self) -> int:
        return 2048

    @property
    def max_gen_toks(self) -> int:
        return 256

    @property
    def batch_size(self):
        # Isn't used because we override _loglikelihood_tokens
        raise NotImplementedError()

    @property
    def device(self):
        # Isn't used because we override _loglikelihood_tokens
        raise NotImplementedError()

    def is_conflicting(self, *args: Any, **kwargs: Any):
        return False

    async def loglikelihood(
        self, text: str, prefix: str = "", *args: Any, **kwargs: Any
    ) -> List:
        async with self.semaphore:
            score_params = TextGenerationParameters(
                temperature=1.0,
                decoding_method="greedy",
                max_new_tokens=1,
                min_new_tokens=0,
                return_options=TextGenerationReturnOptions(
                    generated_tokens=True,
                    token_logprobs=True,
                    input_text=True,
                    input_tokens=True,
                ),
            )

            model_id = kwargs.get("model_id_or_path", self.model_id_or_path)
            score_response = (
                next(
                    self.client.text.generation.create(
                        model_id=model_id,
                        inputs=[prefix + text],
                        parameters=score_params,
                    )
                )
                .results[0]
                .input_tokens
            )

            prefix_token_count = 1
            if prefix:
                prefix_token_count = (
                    next(
                        self.client.text.tokenization.create(
                            model_id=model_id,
                            input=[prefix],
                            parameters=TextTokenizationParameters(
                                return_options=TextTokenizationReturnOptions(
                                    tokens=True
                                )
                            ),
                        )
                    )
                    .results[0]
                    .token_count
                )

            s_toks = score_response[-(prefix_token_count - 1) :]
            logprobs = [tok.logprob for tok in s_toks if tok.logprob is not None]

            self.cache_hook.add_partial(
                f"loglikelihood", [text, prefix], kwargs, logprobs
            )

        return logprobs

    async def generate(self, text: str, **kwargs) -> ModelResult:
        async with self.semaphore:
            if isinstance(gen_kwargs := copy.deepcopy(kwargs), dict):
                # start with default params in self.config then overwrite with kwargs
                gen_kwargs = {**self._base_kwargs, **gen_kwargs}
                model_id = gen_kwargs.pop("model_id_or_path", self.model_id_or_path)
            else:
                raise ValueError(
                    f"Expected repr(kwargs) to be of type repr(dict) but got {kwargs}"
                )

            parameters = TextGenerationParameters(
                return_options=TextGenerationReturnOptions(
                    input_text=True,
                ),
                **gen_kwargs,
            )
            resp = await asyncio.get_running_loop().run_in_executor(
                self.executor,
                partial(
                    self.client.text.generation.create,
                    model_id=model_id,
                    inputs=[text],
                    parameters=parameters,
                ),
            )
            res = next(resp).results[0]
            s = ModelResult(
                generated_text=res.generated_text,
                input_token_count=res.input_token_count,
                generated_token_count=res.generated_token_count,
            )

            self.cache_hook.add_partial(f"generate", [text], kwargs, s)

        return s
