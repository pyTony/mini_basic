"""showcase/demo_reel.py entries must point at real programs."""
import importlib.util
import os
import sys

from mini_basic import BASICInterpreter, InterpreterConfig

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_reel():
    path = os.path.join(_ROOT, 'showcase', 'demo_reel.py')
    spec = importlib.util.spec_from_file_location('showcase_demo_reel', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass needs the module registered
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module.REEL


def test_every_reel_entry_resolves_to_a_program_file():
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
    interp.working_dir = _ROOT
    for entry in _load_reel():
        resolved = interp.resolve_load_path(entry.path)
        assert os.path.isfile(resolved), f'{entry.key}: {entry.path} not found'
