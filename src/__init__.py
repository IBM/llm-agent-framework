import os

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
if BASE_PATH.endswith('src'): BASE_PATH = os.path.split(BASE_PATH)[0]

os.environ['HF_HOME'] = os.path.join(BASE_PATH, '.cache', 'huggingface', 'transformers')
os.environ['HF_DATASETS_CACHE'] = os.path.join(BASE_PATH, '.cache', 'huggingface', 'datasets')
