from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
_spec = spec_from_file_location(__name__, Path(__file__).resolve().parents[1] / 'tests' / 'assistant_eval_run.py')
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
import sys
sys.modules[__name__] = _module
