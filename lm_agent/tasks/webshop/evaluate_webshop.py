# Standard
from argparse import Namespace
from contextlib import nullcontext
from itertools import repeat
from multiprocessing.pool import Pool
import argparse
import copy
import logging
import sys
import time

# Third Party
from bs4 import BeautifulSoup
from bs4.element import Comment
from src.agent import LLMAgent
from src.constants import *
from src.states.webshop import WebshopObservationHandler
from src.utils import *
from tqdm import tqdm
import requests

logger = logging.getLogger(__name__)


def _write_json(data: Dict, path: str):
    with open(path, mode="a", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def _eval(idx, config, prior_predictions):
    config = copy.deepcopy(config)
    config.webshop_idx = idx
    agent = LLMAgent(config)

    obs_key = (
        "webshop-observation"
        if "webshop-observation" in agent.state_handlers
        else "webshop-summarize"
    )
    obs_state: WebshopObservationHandler = agent.state_handlers[obs_key]
    # reset the environments

    if idx in prior_predictions:
        response = prior_predictions[idx]["generated_response"]
        reward = prior_predictions[idx]["reward"]
    else:
        prompt_args = {"input": obs_state.input_text}
        try:
            agent.predict(prompt_args, output_all=True)
        except AssertionError as e:
            pass
        except Exception as e:
            print(json.dumps(obs_state.trajectory, indent=4))
            raise e
        obs_state: WebshopObservationHandler = agent.state_handlers[obs_key]
        reward = obs_state.observed_reward
        response = obs_state.trajectory

    json_data = {
        "id": idx,
        "input_text": obs_state.input_text,
        "reward": reward,
        "generated_response": response,
    }

    return json_data


def chunk(seq, size):
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


def main(args: Namespace):

    config = setup_experiment_files(args)
    up_to = getattr(args, "dataset_size", 900)
    if up_to <= 0:
        up_to = 900
    dataset = list(range(0, up_to))

    metrics = {"reward": 0}

    prior_predictions = extract_predictions(config.predictions_file)

    parallel_exec = args.chunk_size > 1
    with (Pool(args.process_ct) if parallel_exec else nullcontext()) as p, tqdm(
        total=len(dataset), desc="evaluation"
    ) as pbar:
        for dataset_chunk in chunk(dataset, args.chunk_size):
            if parallel_exec:
                iterator = p.starmap(
                    _eval, zip(dataset_chunk, repeat(config), repeat(prior_predictions))
                )
            else:
                iterator = map(
                    _eval, dataset_chunk, repeat(config), repeat(prior_predictions)
                )
            for json_data in iterator:
                idx, input_text, reward, response = (
                    json_data["id"],
                    json_data["input_text"],
                    json_data["reward"],
                    json_data["generated_response"],
                )

                if idx not in prior_predictions:

                    json_data = {
                        "id": idx,
                        "input_text": input_text,
                        "generated_response": response,
                        "reward": reward,
                    }

                    _write_json(json_data, config.predictions_file)

                metrics["reward"] += reward

                pbar.update()

    metrics["avg"] = metrics["reward"] / len(dataset)
    with open(config.results_file, "w") as rf:
        keys = list(metrics)
        wr_keys, wr_vals = ["total"] + keys, [str(len(dataset))] + [
            str(metrics[k]) for k in keys
        ]
        rf.write("\t".join(wr_keys) + "\n")
        rf.write("\t".join(wr_vals) + "\n")


if __name__ == "__main__":

    """
    How to call:
        python -m evaluate_webshop --model <model-type>

    Example:
        python -m evaluate_webshop --model meta-llama/llama-2-70b --agent_type webshop_react --dataset_size -1 --debug --restart
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="Model to use")
    parser.add_argument(
        "--agent_type", type=str, required=True, help="Agent type to use"
    )
    parser.add_argument("--run_local", action="store_true", help="Run with local model")
    parser.add_argument("--model_name", default=None, help="Save model with name")
    parser.add_argument(
        "--dataset_size", default=-1, type=int, help="Dataset size to evaluate on"
    )
    parser.add_argument("--few_shot_k", type=int, help="K few-shot examples")

    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart experiment even if partial results exist",
    )
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    # hyperparams
    parser.add_argument(
        "--temperature", type=float, default=-1, help="Temperature for decoding"
    )

    parser.add_argument(
        "--process_ct", type=int, default=5, help="Amount of parallelism"
    )
    parser.add_argument(
        "--chunk_size", type=int, default=5, help="Amount of parallelism"
    )

    args = parser.parse_args()

    setattr(args, "dataset", "webshop")

    # set up logging
    logging.basicConfig(
        format=" %(name)s :: %(levelname)s :: %(message)s",
        # level=logging.DEBUG if args.debug else logging.INFO
    )
    for name in logging.root.manager.loggerDict:
        if name.strip().startswith("src"):
            logging.getLogger(name).setLevel(
                logging.DEBUG if args.debug else logging.INFO
            )

    if args.model_name is None:
        args.model_name = canon_model_name(args.model)

    main(args)
