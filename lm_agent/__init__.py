# Standard
import os

# Local
import lm_agent.models
import lm_agent.states
import lm_agent.tools

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
if BASE_PATH.endswith("lm_agent"):
    BASE_PATH = os.path.split(BASE_PATH)[0]

os.environ["HF_HOME"] = os.path.join(BASE_PATH, ".cache", "huggingface", "transformers")
os.environ["HF_DATASETS_CACHE"] = os.path.join(
    BASE_PATH, ".cache", "huggingface", "datasets"
)
