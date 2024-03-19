from argparse import Namespace
import copy
import json, logging
import os

from .constants import *

logger = logging.getLogger(__name__)

class Config:
    
    CONFIG_FNAME = 'config.json'

    def __init__(self, args : Namespace=None):

        #
        self.task_type = getattr(args, 'task_type', 'prediction')
        self.max_tokens = getattr(args, 'max_tokens', 1024)
        self.max_state_tokens = getattr(args, 'max_state_tokens', 128)
        self.top_p = getattr(args, 'top_p', -1)
        self.temperature = getattr(args, 'temperature', -1)

        self.is_local = getattr(args, 'run_local', False)

        self.few_shot_k = getattr(args, 'few_shot_k', None)
        if self.few_shot_k is None: self.few_shot_k = 1000

        self.model = getattr(args, 'model', None)
        self.agent_type = getattr(args, 'agent_type', None)
        self.model_name = getattr(args, 'model_name', None)
        self.fallback_agent = getattr(args, 'fallback', None)

        self.tool_model = getattr(args, 'tool_model', 'google/flan-t5-xxl')

        self.self_consistency_k = getattr(args, 'self_consistency_k', 1)
        if self.agent_type in ['cot', 'direct'] and self.self_consistency_k > 1:
            if self.temperature <= 0:
                logger.warning('Cannot have multiple self-consistency attempts with greedy strategy! Switching decoding strategy to sampling...')
                self.temperature = 0.7
        elif self.agent_type not in ['cot', 'direct']:
            if self.self_consistency_k != 1:
                logger.warning('Cannot use self-consistency with other agent types than CoT! Disabling self-consistency...')
                self.self_consistency_k = 1

        self.k_attempts = getattr(args, 'k_attempts', 3)

        if not args: return

        self.dataset = getattr(args, 'dataset', None)
        self.dataset_range = getattr(args, 'dataset_range', None)
        self.profile_path = getattr(args, 'profile_path', None)
        self.chromadb_index =  getattr(args, 'chromadb_index', None)

        self.action_types = _get_actions(self.agent_type, self.dataset)
        
        self.dataset_name = self.dataset.split('/')[-1]
        self.dataset_split = getattr(args, 'split', None)

        self.exp_id = self._get_experiment_id()
        self.exp_dir = os.path.join(EXPERIMENTS_DIR, self.dataset_name, self.exp_id)
        self._file_path = os.path.join(self.exp_dir, Config.CONFIG_FNAME)
        self.results_file = os.path.join(self.exp_dir, 'results.tsv')
        self.predictions_file = os.path.join(self.exp_dir, 'predictions.out')

        self.prompt_file = getattr(args, 'prompt_file', os.path.join(PROMPT_DIR, self.dataset + '.py'))
        self.agent_file = getattr(args, 'agent_file', os.path.join(SPEC_DIR, self.agent_type + '.txt'))

        if self.fallback_agent:
            dup_args = copy.deepcopy(args)
            dup_args.fallback, dup_args.agent_type = None, args.fallback
            dup_config = Config(dup_args)
            self.fallback_predictions_file = dup_config.predictions_file
        else:
            self.fallback_predictions_file = self.predictions_file

        self._set_dependent_fields()
        
    def _get_experiment_id(self):
        ret_str = []
        ret_str.append(self.dataset)
        ret_str.append(self.agent_type)
        if self.fallback_agent is not None: ret_str.append(self.fallback_agent)
        ret_str.append(self.task_type)
        ret_str.append(self.model_name)
        if self.dataset_range: ret_str.append(self.dataset_range)
        if self.dataset_split is not None: ret_str.append(self.dataset_split)
        ret_str = '_'.join([str(x) for x in ret_str])
        return ret_str

    def write_config(self):
        with open(self._file_path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)
            
    @classmethod
    def load_config(cls, exp_dir):
        file_path = os.path.join(exp_dir, Config.CONFIG_FNAME)
        with open(file_path, 'r') as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_dict(cls, load_dict):
        self = cls()
        for field, value in load_dict.items():
            setattr(self, field, value)
        self._set_dependent_fields()
        return self

    def _set_dependent_fields(self):
        self.specification = _load_spec_from_config(self.agent_file)
        self.decoding_strategy = 'sample' if self.temperature > 0 else 'greedy'
        self.k_attempts = 1 if self.decoding_strategy == 'greedy' else self.k_attempts
        

def _get_actions(agent_type : str, dataset : str):
    if dataset.startswith('gsm8k'):
        return ['Calculator']
    elif any([dataset.startswith(d) for d in ['fever', 'hotpot', 'trivia', 'chat']]):
        tool_lst = ['Search', 'Lookup']
        if 'rewoo' in agent_type: tool_lst.append('LLM')
        if 'chat' in agent_type: tool_lst.append('UserResponse')
        return tool_lst
    else: return []

def _load_spec_from_config(agent_file):
    with open(agent_file, 'r') as f: lines = list(f.readlines())
    lines = [line.strip().split('#')[0] for line in lines]
    lines = [line for line in lines if line]
    content = '\n'.join(lines)
    return content
