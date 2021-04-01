import os
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(__file__)).parent
DATA_DIR = ROOT_DIR / 'data'
LOCAL_DIR = ROOT_DIR / 'local'
CFG_DIR = ROOT_DIR / 'config'

FUZZ_DIR = DATA_DIR / 'fuzz'
BRUTE_DIR = DATA_DIR / 'brute'
