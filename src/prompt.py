import ast, logging
from typing import List

from .config import Config
from .constants import *
from .utils import sub_in_kv

logger = logging.getLogger(__name__)

class Prompt:

    INSTRUCTIONS_KW, EXAMPLES_KW, INPUT_KW, STOP_KW = 'instructions', 'examples', 'input', 'stop_text'

    def __init__(self, config : Config):
        
        self.config = config

        prompt_contents = _load_prompt_contents(config.prompt_file, agent_type=config.agent_type)

        self._instructions = prompt_contents.get(Prompt.INSTRUCTIONS_KW, '').strip()
        self._examples = prompt_contents.get(Prompt.EXAMPLES_KW, [])
        self._initial = prompt_contents.get(Prompt.INPUT_KW, None)
        self.stop_text = prompt_contents.get(Prompt.STOP_KW, '').strip()

        self._examples = [_clean_text_content(ex) for ex in self._examples[:self.config.few_shot_k]]
        self._examples = [ex for ex in self._examples if ex]

        self.initial, self.examples, self.instructions = None, None, None

        assert self._initial is not None, 'Must specify \'initial\' text!'
        var_marker = '{{'
        assert var_marker in self._initial, f'Must specify a variable with {var_marker} in prompt!'

    def update_examples(self, new_examples : List):
        self._examples = new_examples
        
    def fill_prompt(self, **kw_args):
        instructions = self._instructions + ''
        examples = [ex + '' for ex in self._examples]
        initial = self._initial + ''
        for k, v in kw_args.items():
            instructions, examples, initial = sub_in_kv(instructions, k, v), [sub_in_kv(ex, k, v) for ex in examples], sub_in_kv(initial, k, v)
        self.instructions, self.examples, self.initial = str(instructions), [str(ex) for ex in examples], str(initial)

def _clean_text_content(text : str):
    tab_sep = '[TAB_SEP]'
    text = text.strip().replace('\t', tab_sep)
    return '\n'.join(line.strip().replace(tab_sep, '\t') for line in text.split('\n')).strip()

def _load_prompt_contents(prompt_file : str, agent_type : str=None):
    def _proc_content(f_content):
        if type(f_content) == dict:
            new_content = dict()
            for k, v in f_content.items():
                new_content[k] = _proc_content(v)
        elif type(f_content) == list:
            new_content = [_proc_content(v) for v in f_content]
        else:
            new_content = _clean_text_content(f_content)
        return new_content

    with open(prompt_file, 'r') as f:
        return _proc_content(ast.literal_eval(f.read())[agent_type])
