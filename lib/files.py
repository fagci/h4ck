import os
from pathlib import Path

DATA_PATH = Path(os.path.dirname(__file__)).parent / 'data'

FUZZ_DIR = DATA_PATH / 'fuzz'
BRUTE_DIR = DATA_PATH / 'brute'
