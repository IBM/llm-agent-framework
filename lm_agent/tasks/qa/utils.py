# Standard
import random
import re
import string

# Third Party
from datasets import load_dataset


def load_hf_dataset(dataset_spec, split, dataset_size):
    dataset = list(load_dataset(*dataset_spec, trust_remote_code=True)[split])
    if dataset_size > 0:
        random.Random(0).shuffle(dataset)
        dataset = dataset[:dataset_size]
    return dataset


def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def is_normalized_match(prediction, ground_truth):
    return normalize_answer(prediction) == normalize_answer(ground_truth)


# GSM8k


def extract_last_number_in_text(text: str):
    text = text.replace(",", "")
    pred = [s for s in re.findall(r"-?\d+\.?\d*", text)]
    if not pred:
        return None
    num = pred[-1].strip()
    if num[-1] == ".":
        num = num[:-1]
    return num


def check_gsm8k(gen_ans, gold_ans):
    gen_ans = extract_last_number_in_text(gen_ans)
    gold_ans = extract_last_number_in_text(gold_ans)
    return round(float(gen_ans), 3) == round(float(gold_ans), 3)
