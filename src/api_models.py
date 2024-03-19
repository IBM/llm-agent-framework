import os
from typing import List
from dotenv import load_dotenv

import numpy as np

# IBM genai
from genai import Credentials
from genai import Credentials, Client
from genai.schema import TextGenerationParameters, TextGenerationReturnOptions, TextGenerationResult, TextTokenizationParameters, TextTokenizationReturnOptions

# OpenAI
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

# 
from .config import Config

class ApiGenerateResult:

    def __init__(self, response: TextGenerationResult):
        # setting this up for abstraction
        self._resp_obj = response
        if isinstance(response, TextGenerationResult):
            self.generated_text = response.generated_text
            self.input_token_count = response.input_token_count
            self.generated_token_count = response.generated_token_count
        elif isinstance(response, ChatCompletion):
            self.generated_text = response.choices[0].message.content
            self.input_token_count = response.usage.prompt_tokens
            self.generated_token_count = response.usage.completion_tokens
        else:
            raise ValueError(f'Unknown response type {type(response)}')
        
    @classmethod
    def from_str(cls, string : str):
        return cls(TextGenerationResult(generated_text=string, input_token_count=0, generated_token_count=0, stop_reason='cancelled'))

class ApiModel:

    def __init__(self, config: Config):

        self.config = config
        self.temperature = config.temperature
        self._stop_sequences = []

        if config.model in ['gpt-3.5-turbo', 'gpt-3.5-turbo-instruct', 'babbage-002', 'davinci-002', 'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']:
            self._get_openai_model()
        else:
            self._get_bam_model()

    def _get_openai_model(self):
        load_dotenv()
        self._model = OpenAI(api_key=os.getenv("OPENAI_API_KEY", None))

    def _get_bam_model(self):
        load_dotenv()
        credentials = Credentials(os.getenv("GENAI_KEY", None), api_endpoint=os.getenv("GENAI_API", None))
        self._model = Client(credentials=credentials)

    def add_stop_sequences(self, sequences : List[str]):
        if self._stop_sequences:
             self._stop_sequences.extend([seq for seq in sequences if not seq in self._stop_sequences])
        else: self._stop_sequences = sequences

    def generate(self, input_text : str):

        gen_params = TextGenerationParameters(
                temperature=(self.temperature if self.temperature > 0 else 1.0),
                decoding_method=('greedy' if self.temperature <= 0. else 'sample'), 
                max_new_tokens=self.config.max_tokens,
                min_new_tokens=1,
                stop_sequences=self._stop_sequences,
                # random_seed=42, 
            )

        if isinstance(self._model, Client):
            resp = next(
                self._model.text.generation.create(
                    model_id=self.config.model,
                    inputs=[input_text],
                    parameters=gen_params,
                )
            ).results[0]
        elif isinstance(self._model, OpenAI):
            resp = self._model.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": input_text}],
                temperature=gen_params.temperature,
                max_tokens=gen_params.max_new_tokens,
                stop=gen_params.stop_sequences,
                seed=42,
            )
        else: raise NotImplementedError()
        return ApiGenerateResult(resp)

    def score(self, prompt: str, to_score: str, reduction : str='mt', alpha=0.3):

        score_params = TextGenerationParameters(
            temperature=1.0, decoding_method='greedy', max_new_tokens=1, min_new_tokens=0, 
            return_options=TextGenerationReturnOptions(generated_tokens=True, token_logprobs=True, input_text=True, input_tokens=True)
            )

        input_text = prompt + to_score

        if isinstance(self._model, Client):
            scored_tokens = next(self._model.text.generation.create(
                model_id=self.config.model,
                inputs=[input_text],
                parameters=score_params,
            )).results[0].input_tokens

            tokenized_to_score = next(self._model.text.tokenization.create(
                model_id=self.config.model,
                input=to_score,
                parameters=TextTokenizationParameters(return_options=TextTokenizationReturnOptions(tokens=True)),
                # parameters=score_params,
            )).results[0].tokens

            logprobs = []
            for tok, tok_data in zip(reversed(tokenized_to_score), reversed(scored_tokens)):
                if tok_data.logprob is not None and tok_data.text == tok:
                    logprobs.append(tok_data.logprob)

        elif isinstance(self._model, OpenAI):
            #
            # TODO: need to figure out how to do this...
            # 
            raise NotImplementedError()
        else: raise NotImplementedError()

        if reduction == 'mean': score = np.mean(logprobs)
        elif reduction == 'sum': score = np.sum(logprobs)
        elif reduction == 'mt': score = np.sum(logprobs) / (((5 + len(logprobs)) ** alpha) / (6 ** alpha))
        else: raise ValueError(f'Unknown reduction type [{reduction}]!')

        return score