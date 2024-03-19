import os
from . import BASE_PATH

#
CACHE_DIR = os.path.join(BASE_PATH, '.cache', 'data')

DATA_DIR = os.path.join(BASE_PATH, 'data')
PROMPT_DIR = os.path.join(DATA_DIR, 'prompts')

PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed_data')
EXPERIMENTS_DIR = os.path.join(BASE_PATH, 'experiments')
LOGS_DIR = os.path.join(BASE_PATH, 'logs')
SPEC_DIR = os.path.join(DATA_DIR, 'agent_specifications')

#
STATES_KEY, BEHAVIOR_KEY = ':states', ':behavior'
