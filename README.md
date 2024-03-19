## Overview

This repo is associated with our paper "Formally Specifying the High-Level Behavior of LLM-Based Agents" (https://arxiv.org/pdf/2310.08535.pdf). It is an llm-based agent design framework that aims to make defining your own custom agents much more straightforward.

## Setup

First we'll get our environment set up

```
conda create --prefix ./llm_agents_env python=3.9
conda activate ./llm_agents_env
pip install -r ./requirements.txt
```

We have (of course...) primarily used IBM watsonx. To set that up, follow the instructions from https://github.com/IBM/ibm-generative-ai. After you have done that, make sure you have a .env file in the base of this repo with your GENAI key (look to .env.example to see what it should look like)

```
GENAI_KEY=<watsonx key goes here>
GENAI_API=https://bam-api.res.ibm.com
```

In addition, we also support OpenAI models. To use those, add to your .env file an OpenAI api key

```
OPENAI_API_KEY=<openai api key goes here>
```

We can test out the install just to make sure by running any of the following

```
python -m src.evaluate --model meta-llama/llama-2-70b --agent_type pass --dataset hotpot_qa --split validation --debug --restart
python -m src.evaluate --model meta-llama/llama-2-70b --agent_type react --dataset hotpot_qa --split validation --debug --restart
python -m src.evaluate --model meta-llama/llama-2-70b --agent_type rewoo --dataset hotpot_qa --split validation --debug --restart
python -m src.evaluate --model meta-llama/llama-2-70b --agent_type cot --self_consistency_k 5 --dataset hotpot_qa --split validation --debug --restart
```

If you use this work, please cite it with the following

```
@article{crouse2023formally,
  title={Formally specifying the high-level behavior of LLM-based agents},
  author={Crouse, Maxwell and Abdelaziz, Ibrahim and Basu, Kinjal and Dan, Soham and Kumaravel, Sadhana and Fokoue, Achille and Kapanipathi, Pavan and Lastras, Luis},
  journal={arXiv preprint arXiv:2310.08535},
  year={2023}
}
```
