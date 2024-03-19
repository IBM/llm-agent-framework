import logging
import argparse
from argparse import Namespace
from tqdm import tqdm

from .eval_utils import get_init_metrics

from .constants import *
from .utils import *
from .agent import LLMAgent

logger = logging.getLogger(__name__)

_ANS = '[Answer]'

def _extract_predictions(pred_file : str):
    predictions = dict()
    if os.path.exists(pred_file):
        with open(pred_file, 'r') as f:
            content = json.loads('[' + str(f.read()).replace('}\n{', '},\n{') + ']')
        for ex in content: 
            if ex: predictions[ex['id']] = ex
    return predictions

def _extract_ans(prediction : str):
    return prediction.split(_ANS)[-1].split('\n')[0]

def _take_fallback(alt_ans : List[str], fallback_ans : List[str]):

    def _canon_answer(x : str):
        x = x.split(_ANS)[-1]
        return normalize_answer(x).strip()

    def _get_max(ans_lst : List):
        lengths = [len(v) for v in ans_lst]
        max_lengths = [ans for ans in ans_lst if len(ans) == max(lengths)]
        return max_lengths

    max_lengths = _get_max(alt_ans)
    if len(max_lengths) == 1: return max_lengths[0][0]

    plus_fallback = []
    for ans in max_lengths:
        matching_fallbacks = [f_ans for f_ans in fallback_ans if _canon_answer(f_ans[0]) == _canon_answer(ans[0])]
        for match in matching_fallbacks: ans = ans + match
        plus_fallback.append(ans)

    max_lengths = _get_max(plus_fallback)
    if any([len(ans) > 1 for ans in max_lengths]): return max_lengths[0][0]

    return fallback_ans[0][0]

def main(args : Namespace):
    
    config = setup_experiment_files(args)

    dataset = load_data(args)

    agent = LLMAgent(config)

    metrics = get_init_metrics() if any([args.dataset.startswith(opt) for opt in ['hotpot', 'trivia']]) else { 'correct' : 0 }

    prior_predictions = _extract_predictions(config.predictions_file)
    fallback_predictions = _extract_predictions(config.fallback_predictions_file)

    for input_text, answer, idx in tqdm(dataset, desc='evaluation'):
        if idx in prior_predictions:
            responses = prior_predictions[idx]['generated_responses']
        else:
            # for reflexion specifically
            state_handler_args = { 'evaluator' : { 'answer' : answer } }
            #

            prompt_args = { 'input' : input_text }
            responses = agent.predict(prompt_args, state_handler_args, output_all=True)
            responses = [[resp_obj.text for resp_obj in resp_lst] for resp_lst in responses]

        check_responses = responses
        if idx in fallback_predictions:
            fallback_responses = fallback_predictions[idx]['generated_responses']
            prediction = _take_fallback(responses, fallback_responses)
        else:
            prediction = max(check_responses, key=len)[0]

        gen_ans = _extract_ans(prediction)

        is_correct, extracted_answer = check_correctness(gen_ans, prediction, answer, metrics, config)

        if idx not in prior_predictions:
            
            json_data = {
                "id": idx,
                "input_text": input_text,
                "generated_responses": responses,
                "prediction": extracted_answer,
                "answer": answer,
                "is_correct": is_correct,
            }

            write_json(json_data, config.predictions_file)

    with open(config.results_file, 'w') as rf:
        keys = list(metrics)
        wr_keys, wr_vals = ['total'] + keys, [str(len(dataset))] + [str(metrics[k]) for k in keys]
        rf.write('\t'.join(wr_keys) + '\n')
        rf.write('\t'.join(wr_vals) + '\n')

if __name__ == '__main__':

    """
    How to call:
        python -m src.evaluate --model <model-type> --dataset <dataset-name>

    Example:
        python -m src.evaluate --model meta-llama/llama-2-70b --agent_type pass --dataset hotpot_qa --debug --restart
        python -m src.evaluate --model meta-llama/llama-2-70b --agent_type react --dataset hotpot_qa --debug --restart
        python -m src.evaluate --model meta-llama/llama-2-70b --agent_type rewoo --dataset hotpot_qa --debug --restart
        python -m src.evaluate --model meta-llama/llama-2-70b --agent_type cot --self_consistency_k 5 --dataset hotpot_qa --debug --restart
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="Model to use")
    parser.add_argument("--agent_type", type=str, required=True, help="Agent type to use")
    parser.add_argument("--run_local", action="store_true", help="Run with local model")
    parser.add_argument("--dataset", type=str, required=True, choices=['gsm8k_main', 'gsm8k_socratic', 'fever_v1.0', 'hotpot_qa', 'trivia_qa'], help=" Name of dataset you are training")
    parser.add_argument("--model_name", default=None, help="Save model with name")
    parser.add_argument("--split", default="validation", help="Split to test prompting on")
    parser.add_argument("--dataset_size", default=1000, type=int, help="Dataset size to evaluate on")
    parser.add_argument("--few_shot_k", type=int, help="K few-shot examples")
    parser.add_argument("--dataset_range", default=None, type=str, help="Dataset size to evaluate on")
    parser.add_argument("--fallback", default=None, type=str, help="Fallback agent to use if no answer is provided by specified agent")

    parser.add_argument("--self_consistency_k", default=1, type=int, help="K retries for self-consistency")

    parser.add_argument("--restart", action="store_true", help="Restart experiment even if partial results exist")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    # hyperparams
    parser.add_argument("--max_tokens", type=int, default=1024, help="Maximum number of tokens to generate")
    parser.add_argument("--max_state_tokens", type=int, default=50, help="Maximum number of tokens to generate in a state")
    parser.add_argument("--temperature", type=float, default=-1, help="Temperature for decoding")

    args = parser.parse_args()
    
    assert args.dataset_range is None or (len(args.dataset_range.split('-')) == 2 and [int(x) for x in args.dataset_range.split('-')]), \
        f'Malformed dataset_range argument {args.dataset_range}'

    # set up logging
    logging.basicConfig(
        format=' %(name)s :: %(levelname)s :: %(message)s', 
        # level=logging.DEBUG if args.debug else logging.INFO
    )
    for name in logging.root.manager.loggerDict:
        if name.strip().startswith('src'): 
            logging.getLogger(name).setLevel(logging.DEBUG if args.debug else logging.INFO)

    if args.model_name is None: args.model_name = canon_model_name(args.model)

    main(args)
