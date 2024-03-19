from argparse import Namespace
import re, random
import shutil
import os, json
import string
from typing import Dict, List
import torch
from datasets import load_dataset

from .config import Config
from .eval_utils import *
from .constants import *
import numpy as np
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge

###
#
###

def calculate_bleu_score(reference, hypothesis):
    return sentence_bleu([reference.split()], hypothesis.split()) # assumes single reference. for multiple reference we will have [reference1.split(), reference2.split(), ...]

def calculate_rouge_l_score(reference, hypothesis):
    rouge = Rouge()
    scores = rouge.get_scores(hypothesis, reference)
    rouge_l_score = scores[0]['rouge-l']['f'] #change to rouge-1 or rouge-2 or rouge-l and 'p','r','f' for precision, recall, f-score
    return rouge_l_score

###
#
###

def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

def split_states(text: str, state_texts: List[str]):
    split_lst = re.split('(' + '|'.join([re.escape(x) for x in state_texts]) + ')', text, flags=re.IGNORECASE)
    if split_lst[0] == '': split_lst.pop(0)
    return split_lst

def collect_states(string: str, state_texts: List[str]):
    split_lst = split_states(string.strip(), state_texts)
    steps = []
    for entry in split_lst:
        if entry in state_texts: steps.append([])
        steps[-1].append(entry)
    assert all([len(step) == 2 for step in steps[:-1]]), f'Malformed step in string:\n{string}'
    assert len(steps[-1]) <= 2, f'Malformed final step in string:\n{string}'
    return steps

###
#
###

def setup_experiment_files(args: Namespace, config_cls: Config=Config):

    config = config_cls(args)

    if getattr(args, 'restart', None) or not os.path.exists(config.exp_dir):
        if os.path.exists(config.exp_dir): shutil.rmtree(config.exp_dir)
        os.makedirs(config.exp_dir)
        config.write_config()
    elif os.path.exists(config.exp_dir):
        config = Config.load_config(config.exp_dir)

    return config

def canon_model_name(model_type : str):
    return model_type.replace("/", "-")

###
#
###

def extract_last_number_in_text(text : str):
    text = text.replace(",", "")
    pred = [s for s in re.findall(r"-?\d+\.?\d*", text)]
    if not pred:
        return None
    num = pred[-1].strip()
    if num[-1] == ".":
        num = num[:-1]
    return num

def extract_answer_from_provided_text(text : str, config : Config):
    if config.dataset.lower().startswith('gsm8k'):
        ans = extract_last_number_in_text(text)
        return ans
    elif config.dataset.lower().startswith('fever'):
        for ans in ['SUPPORTS', 'REFUTES', 'NOT ENOUGH INFO']:
            if ans.lower() in text.lower(): return ans
    elif config.dataset.lower().startswith('hotpot'):
        raise NotImplementedError('Not implemented!')
    else:
        raise ValueError(f'Unknown dataset: {config.dataset}')

def check_correctness(gen_ans : str, full_text : str, gold_ans : str, metrics : Dict, config : Config):
    if config.dataset.lower().startswith('gsm8k'):
        gen_ans = extract_answer_from_provided_text(gen_ans, config)
        if not gen_ans: 
            gen_ans = extract_answer_from_provided_text(full_text, config)
        correct = is_correct(gen_ans, dict(answer=gold_ans)) if gen_ans is not None else False
        metrics['correct'] += int(correct)
        return correct, gen_ans
    elif config.dataset.lower().startswith('fever'):
        gen_ans = extract_answer_from_provided_text(gen_ans, config)
        correct = (gen_ans == gold_ans)
        metrics['correct'] += int(correct)
        return correct, gen_ans
    elif any([config.dataset.lower().startswith(opt) for opt in ['hotpot', 'trivia']]):
        gen_ans = gen_ans.strip()
        update_answer(metrics, gen_ans, gold_ans)
        correct = exact_match_score(gen_ans, gold_ans)
        return correct, gen_ans
    else:
        raise ValueError(f'Unknown dataset: {config.dataset}')

###
#
###

def load_data(args : Namespace):
    if args.dataset.startswith('hotpot'):
        dataset_spec = [args.dataset, 'fullwiki']
    elif args.dataset.startswith('trivia'):
        dataset_spec = [args.dataset, 'rc.nocontext']
    else: dataset_spec = args.dataset.split('_')

    dataset = load_dataset(*dataset_spec)[args.split]
    dataset_range = [int(x) for x in args.dataset_range.split('-')] if args.dataset_range else [0, float('inf')]

    examples = []
    for idx, example in enumerate(dataset):
        if idx < dataset_range[0] or idx >= dataset_range[1]: continue
        if args.dataset.lower() in ['gsm8k_main', 'gsm8k_socratic', 'hotpot_qa']:
            q = example['question']
            a = example['answer']
            idx = f'q_id{idx}'
        elif args.dataset.lower() in ['fever_v1.0']:
            q = example['claim']
            a = example['label']
            idx = str(example['id'])
        elif args.dataset.lower() in ['trivia_qa']:
            q = example['question']
            a = example['answer']['value']
            idx = example['question_id']
        else:
            raise ValueError(f'Unknown dataset: {args.dataset}')
        examples.append((q, a, idx))

    if args.dataset_size > 0: 
        random.Random(0).shuffle(examples)
        examples = examples[:args.dataset_size]

    return examples

def write_json(data, path):
    with open(path, mode='a', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')
    
###
#
###

def seq_matches_any(check_tokens : List[List[int]], input_tokens : torch.Tensor):
    for check_seq in check_tokens:
        input_seq = input_tokens[0, -len(check_seq):]
        if len(input_seq) == len(check_seq) and all(tok1 == tok2 for tok1, tok2 in zip(input_seq, check_seq)):
            return input_seq

###
# String parsing
###

def sub_in_kv(string: str, k: str, v: str):
    return string.replace('{{' + k + '}}', v)

def get_components_type(specification : tuple, component_type : str):
    lst = None
    for component in specification:
        if type(component) == tuple and component[0] == component_type: lst = component
    assert lst, f'{component_type} list must be specified!'
    return lst

def parse_specification_to_tuple(sexpr_str : str) -> tuple:
    toks = re.split('([()])', sexpr_str)
    toks = [x for x in toks if x]

    def _rejoin_strings(tok):
        all_toks = [tok for tok in re.split('([\"\'])', tok) if tok]
        all_toks = [emb_tok for tok in all_toks for emb_tok in tok.split()]
        toks, curr_tok, is_open = [], '', False
        while all_toks:
            new_tok = all_toks.pop(0)
            curr_tok += new_tok
            if is_open and all_toks and all_toks[0] not in ['\'', '\"']: curr_tok += ' '
            if new_tok in ['\'', '\"']:
                if is_open:
                    toks.append(curr_tok)
                    curr_tok, is_open = '', False
                else: is_open = True
            elif not is_open:
                toks.append(curr_tok)
                curr_tok = ''
        return toks

    stack, add_lst = [], []
    for tok in toks:
        if tok == '(':
            stack.append(add_lst)
            add_lst = []
        elif tok == ')':
            assert len(stack) > 0, f'Imbalanced parentheses:\n{sexpr_str}'
            assert add_lst, f'Empty list found:\n{sexpr_str}'
            canon_expr = tuple(add_lst)
            add_lst = stack.pop()
            add_lst.append(canon_expr)
        else:
            add_lst.extend(_rejoin_strings(tok))
    assert len(stack) == 0, 'Imbalanced parentheses:\n' + sexpr_str
    assert len(add_lst) == 1, 'Should only have one specification!'

    ret_tup = add_lst[0]
    assert ret_tup[0] == 'define', 'Must start specification definition with \'define\'!'

    return ret_tup

def evaluator(pred, gold, sort_slots=True):
    def split_intent_slot(input_func): return input_func.split('(')[0], input_func.split('(')[1].split(')')[0]

    pred_intents = [x for x in pred]
    gold_intents = [x for x in gold]

    # pred_slots = [split_intent_slot(x)[1] for x in pred]
    # gold_slots = [split_intent_slot(x)[1] for x in gold]

    # if sort_slots:
    #     pred_slots = [", ".join(sorted(item.split(", "))) for item in sorted(pred_slots)]
    #     gold_slots = [", ".join(sorted(item.split(", "))) for item in sorted(gold_slots)]

    intent_matches = [int(x in gold_intents) for x in pred_intents]
    # overall_matches = [int(x in gold) for x in pred]
    # slot_matches = [int(x in gold_slots) for x in pred_slots]

    normalized_intent_score = np.mean(intent_matches) if intent_matches else 0
    # normalized_overall_score = np.mean(overall_matches) if overall_matches else 0
    # normalized_slot_matches_score = np.mean(slot_matches) if slot_matches else 0

    em_intent = (normalized_intent_score == 1.0)
    # em_overall = (normalized_overall_score == 1.0)
    # em_slot = (normalized_slot_matches_score == 1.0)

    # return normalized_intent_score, normalized_overall_score, normalized_slot_matches_score, em_intent, em_slot, em_overall
    return normalized_intent_score, em_intent
