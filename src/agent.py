from collections import defaultdict
import logging
from typing import Dict, Tuple, Union
import torch

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
from peft import PeftModel

from transformers import GenerationConfig, PreTrainedModel
from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING, MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING
from genai.schema import TextGenerationParameters

from .constrained_decoding import DecodingMonitor, ApiDecodingMonitor, LocalDecodingMonitor
from .prompt import Prompt
from .config import Config
from .utils import *
from .decoding_state import DecodingState, extract_states
from .api_models import ApiModel
from .states.state_handler import StateHandler
from .states import *
from .tools import *

logger = logging.getLogger(__name__)

###
#
###

class AgentOutput:

    def __init__(self, text : str, history : List[Tuple[DecodingState, str]]):
        self.text = text
        self._history = history

    def get_history(self, accessor : str='name'):
        history = [(getattr(state, accessor), resp) for state, resp in self._history]
        return history

###
#
###

class LLMAgent:

    def __init__(self, config : Config, custom_state_handlers : Dict=None):

        self.config = config
        self.prompt_obj = Prompt(config)

        if self.config.is_local:
            self.device = ('cuda' if torch.cuda.is_available() else 'cpu')
            self.model = self._get_auto_model()
            self.tokenizer = AutoTokenizer.from_pretrained(config.model, truncation_side='left')
        else:
            self.model = ApiModel(self.config)
            self.tokenizer = None

        self.specification = parse_specification_to_tuple(config.specification)
        self.states = extract_states(self.specification, self.tokenizer)
        self.custom_state_handlers = custom_state_handlers
        self._reset_state_handlers()

    def _reset_state_handlers(self, state_handler_kwargs : Dict=None):
        if state_handler_kwargs is None: state_handler_kwargs = defaultdict(dict)
        if type(state_handler_kwargs) != defaultdict: state_handler_kwargs = defaultdict(dict, state_handler_kwargs)

        state_handlers: Dict[str, StateHandler] = { state_subclass.name : state_subclass for state_subclass in all_subclasses(StateHandler) }
        self.state_handlers : Dict[str, StateHandler] = { 
            state.name : state_handlers[state.name](self.config, **state_handler_kwargs[state.name]) for state in self.states.values() if state.defer_to_env 
        }

        if self.custom_state_handlers is not None:
            for state_name, state_handler in self.custom_state_handlers.items():
                self.state_handlers[state_name] = state_handler(self.config)

    def predict(self, prompt_inputs : Dict, state_handler_args : Dict=None, output_all : bool=False, **kw_args):

        def _canon_answer(x : str):
            return normalize_answer(x).strip()

        answers = dict()
        for _ in range(self.config.self_consistency_k):
            resp = self._predict(prompt_inputs, state_handler_args=state_handler_args, **kw_args)
            _, final_resp = resp.get_history()[-1]
            key_in = _canon_answer(final_resp)
            if key_in not in answers: answers[key_in] = []
            answers[key_in].append(resp)

        return (list(answers.values()) if output_all else max(answers.values(), key=len)[0])

    def _predict(self, prompt_inputs : Dict, state_handler_args : Dict=None, **kw_args):

        def _get_response(monitor : DecodingMonitor):
            curr_state = monitor.get_current_state()
            return self.state_handlers[curr_state.name](monitor)

        self._reset_state_handlers(state_handler_args)

        with torch.no_grad():

            logger.debug(f'Beginning prediction for input \"{prompt_inputs}\"')

            monitor = self._init_monitor(prompt_inputs, **kw_args)

            # first we handle the case where the first state is a env-response state
            if monitor.in_env_response_state():
                response = _get_response(monitor)
                monitor.submit_input(response)
            else: 
                monitor.generate()

            while not monitor.finished_generating():
                response = _get_response(monitor)
                monitor.submit_input(response)

            final_resp = monitor.get_generated_response()

            return AgentOutput(final_resp, monitor.history)

    def _init_prompt(self, prompt_inputs : Dict, **kw_args):
        # now add state-specific inclusions
        prompt_kw_args = dict(prompt_inputs)

        for state_handler in self.state_handlers.values():
            state_handler.adjust_prompt_args(prompt_kw_args)

        for k, v in prompt_kw_args.items(): 
            if type(v) == list: prompt_kw_args[k] = ', '.join([str(x) for x in v])
            else: prompt_kw_args[k] = str(v)

        self.prompt_obj.fill_prompt(**prompt_kw_args)

    def _init_monitor(self, prompt_inputs : Dict, **kw_args):
        
        self._init_prompt(prompt_inputs, **kw_args)
        
        monitor = monitor_factory(
            self.model, 
            self.prompt_obj,
            self.specification, 
            self.config, 
            self.tokenizer, 
            self.states
        )
        for state_handler in self.state_handlers.values():
            state_handler.adjust_monitor(monitor)

        return monitor

    def _get_auto_model(self):
        assert not any([restr_model in self.config.model for restr_model in ['llama']]), f'Not allowed to download {self.config.model_type} locally!'

        kw_args = dict(trust_remote_code=True)

        auto_config = AutoConfig.from_pretrained(self.config.model, **kw_args)
        
        if type(auto_config) in MODEL_FOR_SEQ_TO_SEQ_CAUSAL_LM_MAPPING:
            auto_model = AutoModelForSeq2SeqLM
        elif type(auto_config) in MODEL_FOR_CAUSAL_LM_MAPPING or any([out_model in self.config.model for out_model in ['falcon', 'mosaic']]):
            auto_model = AutoModelForCausalLM
        else: raise ValueError(f'Unhandled model type {self.config.model}')
        
        if self.config.model in ['t5-base']:
            # this will be for all marble-rolling models, e.g., small ones like t5-base to check
            model = auto_model.from_pretrained(self.config.model, device_map='auto', config=auto_config, **kw_args)
        else:
            model = self.load_local_model(auto_model)

        model.eval()

        return model

    def load_local_model(self, auto_model : Union[AutoModelForCausalLM, AutoModelForSeq2SeqLM], qlora=False):

        logger.info(f'Loading a local model from {self.config.model}')

        adapters_name = self.config.model
        model = auto_model.from_pretrained(
            self.config.model,
            load_in_4bit=True,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            max_memory={i: '24000MB' for i in range(torch.cuda.device_count())},
            quantization_config=BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type='nf4'
            ),
            trust_remote_code=True
        )
        if qlora:
            model = PeftModel.from_pretrained(model, adapters_name)
        return model

def monitor_factory(model : Union[PreTrainedModel, ApiModel], *args, **kw_args):
    if isinstance(model, PreTrainedModel):
        return LocalDecodingMonitor(model, *args, **kw_args)
    elif isinstance(model, ApiModel):
        return ApiDecodingMonitor(model, *args, **kw_args)
    else: raise ValueError(f'Unknown model type {type(model)}')