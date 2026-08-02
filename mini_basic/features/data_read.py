from __future__ import annotations

from typing import List

from .types import TopicRow


def data_read_rows() -> List[TopicRow]:
    return [
        ('DATA numeric literal', 'stored at parse', 'yes', 'yes', 'existing READ tests'),
        ('DATA expr at READ', 'deferred eval', 'yes', 'yes', 'test_data_deferred_*'),
        ('DATA quoted string', 'literal str', 'yes', 'yes', 'test_read_string_data'),
        ('READ multi-var', 'comma vars', 'yes', 'yes', 'soccerball DATA lines'),
        ('RESTORE +n', 'relative offset', 'yes', 'partial', 'animal.txt uses'),
    ]
