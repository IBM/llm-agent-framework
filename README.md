## Overview

This repo is associated with our paper "Formally Specifying the High-Level Behavior of LLM-Based Agents" (https://arxiv.org/pdf/2310.08535.pdf). It is an llm-based agent design framework that aims to make defining your own custom agents much more straightforward.

## Getting Started

### Setup

We recommend using a Python virtual environment with Python 3.9+. Here is how to setup a virtual environment using [Python venv](https://docs.python.org/3/library/venv.html):

```
python3 -m venv llm_agents_env
source llm_agents_env/bin/activate
pip install .
```

**Note:** If you have used [pyenv](https://github.com/pyenv/pyenv), [Conda Miniforge](https://github.com/conda-forge/miniforge) or another tool for Python version management, then use the virtual environment with that tool instead. Otherwise, you may have issues with packages installed but modules from that package not found as they are linked to you Python version management tool and not `venv`.

For now, the following LLM inference APIs are supported:

- [IBM Generative AI (GenAI)](https://ibm.github.io/ibm-generative-ai/v3.0.0/index.html)
- [OpenAI](https://github.com/openai/openai-python)
- [vLLM](https://github.com/vllm-project/vllm)

lm_agent uses a `.env` file to specify the configuration for the IBM GenAI and OpenAI APIs. The `.env` file needs to be availabe from where the generate command is run from. There is a template `env` file [here](./.env.example).

The subsections that follow explain how to setup for the different APIs.

#### IBM Generative AI (GenAI)

When using the IBM GenAI API, you need to:

1. Add configuration to `env` file as follows:

```yaml
GENAI_KEY=<genai key goes here>
GENAI_API=<genai api goes here>
```

2. Install GenAI dependencies as follows:

```command
pip install -e ".[genai]"
```

#### OpenAI

When using the OpenAI platform, you need to:

1. Add configuration to `env` file as follows:

```yaml
OPENAI_API_KEY=<openai api key goes here>
```

2. Install OpenAI dependencies as follows:

```command
pip install -e ".[openai]"
```

#### vLLM

When using the vLLM batched inference, you need to:

1. Install vLLM dependencies as follows:

```command
pip install -e ".[vllm]"
```

**Note:** vLLM [requires Linux OS and CUDA](https://docs.vllm.ai/en/latest/getting_started/installation.html#requirements).

### Testing out the Framework

To get started with this example, make sure you have followed the [Setup](#setup) instructions, [configured IBM GenAI](#ibm-generative-ai-genai), and/or [configured vLLM](#vLLM)

In this example, we will use the preloaded data files as the seed data to to generate the synthetic data.

#### Testing with GenAI

The default data builder is set to run with the GenAI api unless overridden. We thus only need to run the following command (run from the root of the repository) to execute data generation with GenAI:

```command
python -m lm_agent.__main__ --task hotpot_qa --dataset-size 5 --agent pass
```

#### Testing with vLLM

TODO

#### Examine Outputs

The generated data will be output to the following directory: `outputs/hotpot_qa/pass/meta-llama_llama-3-70b-instruct/output.jsonl`

## Citation

If you use this work, please cite it with the following

```
@article{crouse2023formally,
  title={Formally specifying the high-level behavior of LLM-based agents},
  author={Crouse, Maxwell and Abdelaziz, Ibrahim and Basu, Kinjal and Dan, Soham and Kumaravel, Sadhana and Fokoue, Achille and Kapanipathi, Pavan and Lastras, Luis},
  journal={arXiv preprint arXiv:2310.08535},
  year={2023}
}
```
