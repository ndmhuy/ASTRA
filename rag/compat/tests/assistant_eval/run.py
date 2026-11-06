from pathlib import Path
from tests_snapshot_eval import *
import tests_snapshot_eval

tests_snapshot_eval.QUESTIONS = Path(__file__).resolve().parents[3] / 'tests' / 'assistant_eval_curriculum.json'
