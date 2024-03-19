import logging
import inspect
from typing import List
import torch
import torch.nn as nn
from transformers.generation.configuration_utils import GenerationConfig
from transformers.tokenization_utils import PreTrainedTokenizer
from transformers import PreTrainedModel
from transformers.generation.logits_process import LogitsProcessorList
from genai.schema import TextGenerationParameters

from .config import Config
from .constants import *
from .monitor import *
from .utils import *
from .prompt import Prompt
from .api_models import ApiModel, ApiGenerateResult
from .decoding_state import DecodingState

"""
The rules for monitors are
    1) can only be in one state at a time
    2) any user-input state is also a state that the user can cancel from
"""

logger = logging.getLogger(__name__)

###
#
###

class DecodingMonitor:

    INPUT_SN = 'input'

    def __init__(self, 
            model: PreTrainedModel, 
            prompt_obj: Prompt,
            specification: tuple, 
            config: Config, 
            tokenizer: PreTrainedTokenizer,
            states: Dict[str, DecodingState],
            **kwargs
        ):

        self.model = model
        self.tokenizer = tokenizer

        self._forced_exit = False

        self.config = config
        self.max_new_tokens, self.max_state_length = config.max_tokens, config.max_state_tokens

        self._monitor_name = specification[1]
        hard_stop_sequences = [prompt_obj.stop_text] if prompt_obj.stop_text else []
        termination_states = [DecodingState((f'term-state-{i}', (DecodingState._TEXT_KEY, seq)), tokenizer) for i, seq in enumerate(hard_stop_sequences)]
        self._transition_monitor = TransitionMonitor(specification, states, termination_states)
        self.states = self._transition_monitor.states

        # validate that prompt examples match decoding monitor specification
        for ex in prompt_obj.examples:
            self.validate_sequence_from_string(ex)

        # now can initialize texts
        state_texts = dict([(v.text, v) for v in self.states.values()])
        steps = collect_states(prompt_obj.initial, state_texts.keys())

        self.history : List[Tuple[DecodingState, str]] = []

        for state, state_content in steps[:-1]:
            matched_state = state_texts[state]
            assert matched_state in self._transition_monitor.get_valid_states(), f'Input to prompt does not follow specification!'
            self._transition_monitor.step(matched_state)
            self.history.append((matched_state, state_content.strip()))
        init_state_text, init_state_content = steps[-1]
        init_state = state_texts[init_state_text]

        self._transition_monitor.step(init_state)

        self._in_progress: DecodingState = init_state
        self._init_text = init_state_content if init_state_content else None
        self._tgen_ct = 0

        input_text = [prompt_obj.instructions, '\n\n'.join(prompt_obj.examples)]
        self.input_text = '\n\n'.join(input_text) + '\n'

    ###
    #
    ###

    def _init_generation(self):
        if self._init_text is not None:
            to_submit = self._init_text
            self._init_text = None
            self.submit_input(to_submit)
            return self._in_progress.defer_to_env

    def _in_terminal_state(self):
        return len(self.history) > 1 and self._in_progress in self._transition_monitor.termination_states

    def get_generated_response(self):
        hist_str = '\n'.join([f'{state.text} {content}' for state, content in self.history])
        return hist_str
        
    def submit_input(self, text : str): raise NotImplementedError

    def get_current_state(self):
        return self._in_progress

    def in_env_response_state(self):
        return self.get_current_state().defer_to_env

    def finished_generating(self):
        if self._init_text: return False
        return self._forced_exit or self._tgen_ct >= self.max_new_tokens or self._transition_monitor.exit_reached() or self._in_terminal_state()

    def get_current_str(self):
        string_components = [self.input_text]
        if self.history: string_components.append(self.get_generated_response())
        string_components.append(self._in_progress.text)
        curr_str = '\n'.join([comp for comp in string_components if comp])
        return curr_str
    
    ###
    # Generate
    ###

    def generate(self): raise NotImplementedError

    ###
    # validate
    ###

    def validate_sequence_from_string(self, string: str):
        return self._transition_monitor.validate_sequence_from_string(string)

    def validate_sequence(self, state_history: List[Tuple[str, str]]):
        return self._transition_monitor.validate_sequence(state_history)

###
#
###

class LocalDecodingMonitor(DecodingMonitor):

    def __init__(self, 
            model : PreTrainedModel, 
            prompt_obj : Prompt,
            specification : tuple, 
            config : Config, 
            tokenizer : PreTrainedTokenizer,
            states : Dict[str, DecodingState],
            **kwargs
        ):
        super().__init__(model, prompt_obj, specification, config, tokenizer, states, **kwargs)

        self.generation_config = GenerationConfig(
            temperature=(self.config.temperature if self.config.temperature > 0 else 1.0),
            output_scores=True,
            return_dict_in_generate=True,
            output_attentions=True,
            max_new_tokens=self.config.max_tokens,
            do_sample=self.config.decoding_strategy == 'sample',
            top_p=self.config.top_p,
        )

        self.device = ('cuda' if torch.cuda.is_available() else 'cpu')

        hard_stop_sequences = [state.text for state in self._transition_monitor.termination_states]
        self._hard_stop_sequences = []
        self._hard_stop_sequences.extend([tokenizer.convert_tokens_to_ids(tokenizer.tokenize(stop_seq.strip())) for stop_seq in hard_stop_sequences])
        self._hard_stop_sequences.extend([tokenizer.convert_tokens_to_ids(tokenizer.tokenize('\n' + stop_seq.strip())) for stop_seq in hard_stop_sequences])
        self._soft_stop_sequences = []
        newline = tokenizer.convert_tokens_to_ids(tokenizer.tokenize('\n'))
        if newline != tokenizer.convert_tokens_to_ids(tokenizer.tokenize(' ')):
            self._soft_stop_sequences.append(newline)

        """
        This next part is taken from the initialization of .generate()
        """
        input_text = self.input_text + '\n'
        if self.history: input_text += self.get_generated_response()
        inputs = self.tokenizer(input_text, return_tensors='pt', truncation=True).to(self.device)['input_ids']

        generation_config = copy.deepcopy(generation_config)
        model_kwargs = generation_config.update(**kwargs)  # All unused kwargs must be model kwargs
        generation_config.validate()
        self.model._validate_model_kwargs(model_kwargs.copy())

        # 3. Define model inputs
        # inputs_tensor has to be defined
        # model_input_name is defined if model-specific keyword input is passed
        # otherwise model_input_name is None
        # all model-specific keyword inputs are removed from `model_kwargs`
        inputs_tensor, model_input_name, model_kwargs = self.model._prepare_model_inputs(
            inputs, generation_config.bos_token_id, model_kwargs
        )
        batch_size = inputs_tensor.shape[0]

        # 4. Define other model kwargs
        model_kwargs["output_attentions"] = generation_config.output_attentions
        model_kwargs["output_hidden_states"] = generation_config.output_hidden_states
        # decoder-only models with inputs_embeds forwarding must use caching (otherwise we can't detect whether we are
        # generating the first new token or not, and we only want to use the embeddings for the first new token)
        if not self.model.config.is_encoder_decoder and model_input_name == "inputs_embeds":
            model_kwargs["use_cache"] = True
        else:
            model_kwargs["use_cache"] = generation_config.use_cache

        accepts_attention_mask = "attention_mask" in set(inspect.signature(self.model.forward).parameters.keys())
        requires_attention_mask = "encoder_outputs" not in model_kwargs

        if model_kwargs.get("attention_mask", None) is None and requires_attention_mask and accepts_attention_mask:
            model_kwargs["attention_mask"] = self.model._prepare_attention_mask_for_generation(
                inputs_tensor, generation_config.pad_token_id, generation_config.eos_token_id
            )

        # decoder-only models should use left-padding for generation
        if not self.model.config.is_encoder_decoder:
            # If `input_ids` was given, check if the last id in any sequence is `pad_token_id`
            # Note: If using, `inputs_embeds` this check does not work, because we want to be more hands-off.
            if (
                generation_config.pad_token_id is not None
                and len(inputs_tensor.shape) == 2
                and torch.sum(inputs_tensor[:, -1] == generation_config.pad_token_id) > 0
            ):
                logger.warning(
                    "A decoder-only architecture is being used, but right-padding was detected! For correct "
                    "generation results, please set `padding_side='left'` when initializing the tokenizer."
                )

        if self.model.config.is_encoder_decoder and "encoder_outputs" not in model_kwargs:
            # if model is encoder decoder encoder_outputs are created
            # and added to `model_kwargs`
            model_kwargs = self.model._prepare_encoder_decoder_kwargs_for_generation(
                inputs_tensor, model_kwargs, model_input_name
            )

        # 5. Prepare `input_ids` which will be used for auto-regressive generation
        if self.model.config.is_encoder_decoder:
            self.input_ids, model_kwargs = self.model._prepare_decoder_input_ids_for_generation(
                batch_size=batch_size,
                model_input_name=model_input_name,
                model_kwargs=model_kwargs,
                decoder_start_token_id=generation_config.decoder_start_token_id,
                bos_token_id=generation_config.bos_token_id,
                device=inputs_tensor.device,
            )
        else:
            self.input_ids = inputs_tensor if model_input_name == "input_ids" else model_kwargs.pop("input_ids")

        self.logits_warper = LogitsProcessorList()
        if generation_config.do_sample:
            self.logits_warper = self.model._get_logits_warper(generation_config)

        self.model_kwargs = model_kwargs

        self.pad_token_id = self.model.generation_config.pad_token_id
        self.eos_token_id = self.model.generation_config.eos_token_id

        """
        This is back to our code
        """
        self.generation_config = generation_config
        self._seq_dims = []

        self._add_text(self._in_progress.text)

        # initialize history
        self._start_idx = self.input_ids.size(1)

    ###
    #
    ###

    def submit_input(self, text : str):
        text = text.strip()
        tokenized = self.tokenizer(' ' + text, return_tensors='pt')['input_ids']
        self._force_decoder(tokenized)
        self._process_state_change(force_change=True)
        self.generate()

    def _add_text(self, text : str):
        tokenized = self.tokenizer(text, return_tensors='pt')['input_ids']
        assert tokenized.size(0) == 1
        if tokenized[0, -1] == self.eos_token_id: tokenized = tokenized[:, :-1]
        self._force_decoder(tokenized)

    ###
    # Generate
    ###

    def generate(self):

        # initialization
        return_to_user = self._init_generation()
        if return_to_user: return

        self._sgen_ct = 0

        # auto-regressive generation
        while not self.finished_generating():

            target_state = self._in_progress

            force_change = False
            if target_state.constraints:
                logger.debug(f'Constraints found for state [{target_state.name}], will decode to one of specified options')
                self._disjunctive_decode(target_state.constraints)
                force_change = True
            else:
                self._generation_step()
                self._sgen_ct += 1

            # now we do state validation
            return_to_user = self._process_state_change(force_change=force_change)
            if return_to_user: return

    def _generation_step(self, forced_dec : List[int]=None):
        assert forced_dec is None or type(forced_dec) == list, 'Forced decoder input invalid'

        # prepare model inputs
        model_inputs = self.model.prepare_inputs_for_generation(self.input_ids, **self.model_kwargs)

        if self.input_ids.size(-1) >= self.tokenizer.model_max_length: 
            self._tgen_ct = self.max_new_tokens + 1
            return

        # forward pass to get next token
        outputs = self.model(
            **model_inputs,
            return_dict=True,
        )

        if type(forced_dec) == list and len(forced_dec) == 1:
            next_tokens = torch.tensor(forced_dec).to(self.input_ids.device)
        else:
            # sample
            next_token_logits = outputs.logits[:, -1, :]

            if type(forced_dec) == list:
                logit_mask = torch.zeros_like(next_token_logits) + float('-inf')
                for dec_id in forced_dec: logit_mask[:, dec_id] = 0.0
                next_token_logits += logit_mask
                                
            if self.eos_token_id is not None and not self._transition_monitor.exit_reached(): 
                next_token_logits[:, self.eos_token_id] = float('-inf')

            next_token_logits = self.logits_warper(self.input_ids, next_token_logits)
            if self.generation_config.do_sample:
                probs = nn.functional.softmax(next_token_logits, dim=-1)
                next_tokens = torch.multinomial(probs, num_samples=1).squeeze(1)
            else:
                next_tokens = torch.argmax(next_token_logits, dim=-1)

        # update generated ids, model inputs, and length for next step
        self.input_ids = torch.cat([self.input_ids, next_tokens[:, None]], dim=-1)
        self.model_kwargs = self.model._update_model_kwargs_for_generation(
            outputs, self.model_kwargs, is_encoder_decoder=self.model.config.is_encoder_decoder
        )

        self._tgen_ct += 1

    def _process_state_change(self, force_change : bool=False):

        def _update_history(next_state : DecodingState=None):
            prior_state, prior_start_ind = self._in_progress, self._start_idx
            prev_tokens = self.input_ids[0, prior_start_ind:]
            history_string = self.tokenizer.decode(prev_tokens, skip_special_tokens=True)
            if next_state is not None: 
                history_string = history_string[:-len(next_state.text)]
                prev_tokens = prev_tokens[:-len(next_state.tokens)]
            self.history.append((prior_state, history_string.strip()))
            logger.debug(f'Adding state [{self.history[-1][0].name}] to history with response \"{self.history[-1][1]}\"')

        def _early_termination():
            # termination criteria
            if self._transition_monitor.exit_reached():
                if self._in_terminal_state():
                    logger.debug(f'Termination state [{self._in_progress.name}] reached with text \"{self._in_progress.text}\", terminating!')
                    return True
                elif seq_matches_any(self._soft_stop_sequences, self.input_ids) is not None:
                    logger.debug(f'Soft stop sequence matched while in exit state, terminating!')
                    _update_history()
                    return True

        if _early_termination():
            return True

        proposed_state, matched_seq = self._transition_monitor.matches_state(self.input_ids)

        if force_change or self._sgen_ct >= self.max_state_length or proposed_state is not None:

            _update_history(proposed_state)

            # reset state token generation count
            self._sgen_ct = 0

            if proposed_state is not None:
                if (not self._transition_monitor.exit_reached()) and self._transition_monitor.accept_state(proposed_state):

                    self._transition_monitor.step(proposed_state)

                    self._in_progress, self._start_idx = proposed_state, self.input_ids.size(1)

                    logger.debug(f'Current state is now [{proposed_state.name}]')

                    return proposed_state.defer_to_env
                else:
                    # roll back decoder predictions
                    logger.debug(f'Predicted state [{proposed_state.name}] violates specification, rolling back prediction')
                    self._roll_back_decoder(matched_seq)
                    if self._transition_monitor.exit_reached():
                        logger.debug(f'Exit reached!')
                        return True

            possible_states = self._transition_monitor.get_valid_states()

            if possible_states:

                logger.debug(f'Possible target states are [{", ".join([ps.name for ps in possible_states])}]')

                proposed_state = self._decode_to_state(possible_states)

                # update decoder to have chosen that state
                self._transition_monitor.step(proposed_state)

                self._in_progress, self._start_idx = proposed_state, self.input_ids.size(1)

                return proposed_state.defer_to_env
            else:
                logger.debug(f'Exit reached!')
                assert self._transition_monitor.exit_reached(), self._transition_monitor._stack
                return True

        return False

    def _decode_to_state(self, possible_states : List[DecodingState]):
        disjunctive_alternatives = [ps.tokens for ps in possible_states]

        if len(possible_states) == 1: logger.debug(f'Constraining decoding to [{possible_states[0]}]')
        else: logger.debug(f'Constraining decoding to one of [{", ".join([ps.name for ps in possible_states])}]')

        self._disjunctive_decode(disjunctive_alternatives)
        proposed_state, _ = self._transition_monitor.matches_state(self.input_ids)
        return proposed_state
    
    def _disjunctive_decode(self, disj_alt : List[List[int]]):
        i = 0
        while i < max([len(x) for x in disj_alt]):
            tokens = [tok_lst[i] for tok_lst in disj_alt if len(tok_lst) > i]
            self._generation_step(tokens)
            chosen_token = self.input_ids[:, -1][0]
            disj_alt = [tok_lst for tok_lst in disj_alt if i < len(tok_lst) and tok_lst[i] == chosen_token]
            i += 1

    def _roll_back_decoder(self, matched_seq : torch.Tensor):

        if 'attention_mask' in self.model_kwargs and self.model_kwargs['attention_mask'] is not None and not self.model.config.is_encoder_decoder:
            self.model_kwargs['attention_mask'] = self.model_kwargs['attention_mask'][..., :-len(matched_seq)]

        self.input_ids = self.input_ids[..., :-len(matched_seq)]

        if 'past_key_values' in self.model_kwargs and self.model_kwargs['past_key_values'] is not None:
            new_pkv = []
            if not self._seq_dims: self._seq_dims = [[None, None] for _ in range(len(self.model_kwargs['past_key_values']))]
            seq_len = self.input_ids.size(-1) + len(matched_seq) - 1
            is_enc_dec = int(self.model.config.is_encoder_decoder)
            # shape of past_key_values is (n_layers, batch_size, num_heads (optional), seq_length, embed_size)
            for i in range(len(self.model_kwargs['past_key_values'])):

                new_pkv.append([])
                
                for j in range(len(self.model_kwargs['past_key_values'][i])):
                    if j > 1: 
                        assert is_enc_dec
                        new_pkv[-1].append(self.model_kwargs['past_key_values'][i][j])
                    else:
                        if self._seq_dims[i][j] is None:
                            self._seq_dims[i][j] = next(iter([k for k in range(len(self.model_kwargs['past_key_values'][i][j].size()))
                                                             if self.model_kwargs['past_key_values'][i][j].size(k) == seq_len]))
                        # Note how 0 is handled differently, this must be a decoder-only setting
                        if self._seq_dims[i][j] == 0: new_pkv[-1].append(self.model_kwargs['past_key_values'][i][j][:-len(matched_seq)])
                        elif self._seq_dims[i][j] == 1: new_pkv[-1].append(self.model_kwargs['past_key_values'][i][j][:, :-len(matched_seq)])
                        elif self._seq_dims[i][j] == 2: new_pkv[-1].append(self.model_kwargs['past_key_values'][i][j][:, :, :-len(matched_seq)])
                        elif self._seq_dims[i][j] == 3: new_pkv[-1].append(self.model_kwargs['past_key_values'][i][j][:, :, :, :-len(matched_seq)])

                if len(new_pkv[-1][0].size()) == 2:
                    # if we haven't included num_heads in this
                    new_pkv[-1] = torch.stack(new_pkv[-1])

            self.model_kwargs['past_key_values'] = new_pkv

    def _force_decoder(self, new_tokens : torch.Tensor):
        if len(new_tokens.size()) > 1: new_tokens = new_tokens[0]
        for tok in new_tokens: self._generation_step([int(tok)])

    ###
    # validate
    ###

    def validate_sequence_from_string(self, string : str):
        return self._transition_monitor.validate_sequence_from_string(string)

    def validate_sequence(self, state_history : List[Tuple[str, str]]):
        return self._transition_monitor.validate_sequence(state_history)

    ###
    # misc
    ###

    def _print_state(self):
        print(self.tokenizer.decode(self.input_ids[0]))

###
#
###


class ApiDecodingMonitor(DecodingMonitor):

    def __init__(self, 
            model : ApiModel, 
            prompt_obj : Prompt,
            specification : tuple, 
            config : Config, 
            tokenizer : PreTrainedTokenizer, 
            states : Dict[str, DecodingState],
            **kwargs
        ):
        super().__init__(model, prompt_obj, specification, config, tokenizer, states, **kwargs)

        model.add_stop_sequences([state.text for state in self.states.values() if state.defer_to_env or state in self._transition_monitor.termination_states])

        self._text_to_add = ''
        self._prompt_token_ct = None

        self._state_change_trigger = '\n' + os.path.commonprefix([state.text for state in self.states.values()])

    ###
    #
    ###

    def submit_input(self, text : str): 
        self._text_to_add = text.strip() + self._get_state_change_trigger()
        self.generate()
        self._text_to_add = ''

    def _get_state_change_trigger(self):
        valid_states = self._transition_monitor.get_valid_states()
        prefix = '\n' + os.path.commonprefix([state.text for state in valid_states])
        return prefix

    def _get_short_circuit_state(self):
        if self.in_env_response_state():
            valid_states = self._transition_monitor.get_valid_states()
            if (len(valid_states) == 1 and valid_states[0].defer_to_env) or all([state in self._transition_monitor.termination_states for state in valid_states]):
                logger.debug(f'Only one valid state available, skipping geneneration to transition to state [{valid_states[0].name}]')
                return valid_states[0]

    ###
    # Generate
    ###

    def generate(self):

        # initialization        
        return_to_user = self._init_generation()
        if return_to_user: return

        while not self.finished_generating():
            
            prev_len = len(self.history)

            for i in range(self.config.k_attempts + 1):

                if i == self.config.k_attempts:
                    logger.warning(f'Could not complete prompt with {self.config.k_attempts} attempts, returning to user')
                    self._forced_exit = True
                    return

                curr_str = self.get_current_str()

                # this is a very specific situation, where we can essentially shortcircuit generation if we are in an env_response state AND the next state is also an env_response state
                short_circuit_state = self._get_short_circuit_state()
                if short_circuit_state is not None:
                    s_trigger = self._get_state_change_trigger()
                    assert self._text_to_add.endswith(s_trigger), f'Something is happening that is unplanned...'
                    resp = ApiGenerateResult.from_str(curr_str)
                else:
                    if self._text_to_add: curr_str += ' ' + self._text_to_add
                    try:
                        resp : ApiGenerateResult = self.model.generate(curr_str)
                    except KeyboardInterrupt as e: raise e
                    except Exception as e:
                        if all([x in str(e) for x in ['input tokens ', 'must be <']]):
                            logger.error(str(e))
                            self._forced_exit = True
                            return
                        else: raise e
                    except Exception as e: raise e
            
                return_to_user = self._process_state_changes(resp)
                if return_to_user: return

                # reset length check when history has been updated
                if len(self.history) != prev_len: break

        exit_msg = 'Generation is complete' if self._tgen_ct < self.max_new_tokens else 'Too many tokens generated, terminating generation'
        logger.debug(exit_msg)

    def _process_state_changes(self, resp : ApiGenerateResult):

        def _normalize_state_string(string : str):
            return string.lower()

        def _choose_state(states : List[DecodingState]):
            # for state in states:
            #     if state not in self._transition_monitor.termination_states:
            #         return state
            return states[0]

        def _validate_and_add(state_resp : str):
            logger.debug(f'Validating content for state [{self._in_progress.name}]')
            state_content = state_resp.strip()
            state_content = self._in_progress.validate_constraints(state_content, enforce_hard_constraints=False)
            if state_content is not None:
                logger.debug(f'Adding content for state [{self._in_progress.name}] to history')
                self.history.append((self._in_progress, state_content))
                if self._prompt_token_ct is None: self._prompt_token_ct = resp.input_token_count
                # self._tgen_ct = resp.input_token_count + resp.generated_token_count - self._prompt_token_ct

            return state_content is not None

        text = self._text_to_add + resp.generated_text

        state_texts = dict([(_normalize_state_string(state.text), state) for state in self.states.values()])
        split_lst = split_states(text, state_texts)
        # skip empty
        if split_lst[0] == '': split_lst = split_lst[1:]

        state_resp, subsequent_predictions = split_lst[0], split_lst[1:]

        if state_resp in state_texts:
            logger.debug(f'Immediate generation failure, state [{state_texts[state_resp].name}] received as initial prediction, retrying generation')
            assert not self._in_progress.defer_to_env, f'Generation failure stems from environment-provided response to state [{self._in_progress.name}]'
            return False

        # adding prediction to history only if it is valid w.r.t. constraints
        is_valid = _validate_and_add(state_resp)
        if not is_valid:
            logger.debug(f'Immediate generation failure, state constraints for [{self._in_progress.name}] not met with input \"{state_resp}\"')
            assert not self._in_progress.defer_to_env, f'Generation failure stems from environment-provided response to state [{self._in_progress.name}]'
            return False

        predicted_steps = []
        if subsequent_predictions and _normalize_state_string(subsequent_predictions[0]) in state_texts:
            # collect transitions
            for entry in subsequent_predictions:
                if _normalize_state_string(entry) in state_texts: predicted_steps.append([])
                if len(predicted_steps[-1]) >= 2: break
                # the above condition will ensure we ONLY collect state-prediction pairs
                predicted_steps[-1].append(entry)

        for state_text, state_content in predicted_steps:

            proposed_state = state_texts[_normalize_state_string(state_text)]

            if (not self._transition_monitor.exit_reached()) and self._transition_monitor.accept_state(proposed_state):

                logger.debug(f'Current state is now [{proposed_state.name}]')

                self._transition_monitor.step(proposed_state)
                self._in_progress = proposed_state

                if self._in_progress.defer_to_env or self._in_terminal_state():
                    return self._in_progress.defer_to_env

                # adding prediction to history only if it is valid w.r.t. constraints
                is_valid = _validate_and_add(state_content)
                if not is_valid:
                    logger.debug(f'State constraints for [{self._in_progress.name}] not met, starting generation from [{self._in_progress.name}]')
                    assert not self._in_progress.defer_to_env, f'Generation failure stems from environment-provided response to state {self._in_progress.name}'
                    return self._in_progress.defer_to_env

            elif self._transition_monitor.exit_reached():
                logger.debug(f'Exit reached!')
                return True
            else:
                # if we get here, the prediction was erroneous
                logger.debug(f'Proposed state [{proposed_state.name}] is rejected')
                break

        possible_states = self._transition_monitor.get_valid_states()
        if possible_states:
            logger.debug(f'Possible target states are [{", ".join([ps.name for ps in possible_states])}]')
            proposed_state = _choose_state(possible_states)
            logger.debug(f'State [{proposed_state.name}] chosen')
            # update decoder to have chosen that state
            self._transition_monitor.step(proposed_state)
            self._in_progress = proposed_state
            return self._in_progress.defer_to_env
        else:
            logger.debug(f'Exit reached!')
            assert self._transition_monitor.exit_reached(), self._transition_monitor._stack
            return True
