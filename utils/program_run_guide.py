"""How users actually run corpus programs (interactive / visual verification)."""
from __future__ import annotations

from typing import Dict, List, TypedDict


class ProgramRunGuide(TypedDict):
    command: str
    kind: str
    try_notes: List[str]


_CORPUS = 'test/corpus/bbcsdl'

PROGRAM_USER_RUN: Dict[str, ProgramRunGuide] = {
    'animal.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/games/animal.txt'
        ),
        'kind': 'interactive text (Y/N and INPUT prompts in terminal)',
        'try_notes': [
            'Start: answer N — should list known animals and exit cleanly',
            'Play: answer Y, follow Y/N questions until it guesses your animal',
            'Wrong guess: teach a new animal (name, distinguishing question, Y/N branch)',
            'Run again with the same animal — tree should remember it',
            'Or: python mini_basic.py --dialect bbc examples/games/animal.bbc',
        ],
    },
    'soccerball.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/graphics/soccerball.txt'
        ),
        'kind': 'graphics animation (pygame window; auto-enabled on LOAD)',
        'try_notes': [
            'Ball should spin smoothly; white hex pattern on coloured disc',
            'Let several frames run — rotation should be continuous',
            'Close window or press Escape when done',
        ],
    },
    'wheel.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/graphics/wheel.txt'
        ),
        'kind': 'graphics animation (pygame auto-enabled)',
        'try_notes': [
            'Rotating colour wheel around the centre',
            'Close window or press Escape when done',
        ],
    },
    'hanoi.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'examples/games/hanoi.bbc'
        ),
        'kind': 'graphics text discs (MODE 3; pygame or terminal)',
        'try_notes': [
            'Enter disc count 1–13; press SPACE to start solve',
            'Discs move; finish on middle peg is original program design',
            'No floating colour fragments mid-solve',
        ],
    },
    'jclock.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/graphics/jclock.txt'
        ),
        'kind': 'graphics analog clock (pygame)',
        'try_notes': [
            'Clock face with hands/markers should appear and update',
            'Close window or Escape when done',
        ],
    },
    'filters.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/general/filters.txt'
        ),
        'kind': 'general / graphics filters demo',
        'try_notes': [
            'Should start without ? errors; follow any on-screen prompts',
            'Close window if graphics open',
        ],
    },
    'saucer.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/graphics/saucer.txt'
        ),
        'kind': 'graphics 3D-style flying saucer plot (slow nested FOR)',
        'try_notes': [
            'Expect a long draw — nested FOR over a large range (not a hang)',
            'Should plot a saucer-like point cloud without ? errors',
            'Close window or Escape when finished / tired of waiting',
        ],
    },
    'flier.txt': {
        'command': (
            f'python mini_basic.py --dialect bbc '
            f'{_CORPUS}/graphics/flier.txt'
        ),
        'kind': 'graphics 3D flier (MODE 18; long animation)',
        'try_notes': [
            'Uses _BOX/_LINE arrays; should not die on DIM',
            'Animation can run a long time; Escape/close window to exit',
        ],
    },
}


def _program_key(program: str) -> str:
    """Map 'jclock.txt (graphics)' or bare name to PROGRAM_USER_RUN key."""
    text = program.strip().lower()
    # Drop trailing " — notes"
    text = text.split('—')[0].split('-')[0].strip() if '—' in program else text
    text = program.strip().split('—')[0].strip()
    # Drop " (folder)" suffix
    if '(' in text:
        text = text[: text.index('(')].strip()
    return text.lower() if text.endswith('.txt') or text.endswith('.bbc') else text


def run_command_for(program: str) -> str:
    key = _program_key(program)
    # Prefer original case keys in table
    for name, guide in PROGRAM_USER_RUN.items():
        if name.lower() == key:
            return guide['command']
    base = key if key else program.strip()
    return f'python mini_basic.py --dialect bbc test/corpus/bbcsdl/<folder>/{base}'


def run_guide_for(program: str) -> ProgramRunGuide | None:
    key = _program_key(program)
    for name, guide in PROGRAM_USER_RUN.items():
        if name.lower() == key:
            return guide
    return None