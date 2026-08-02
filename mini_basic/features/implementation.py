from __future__ import annotations

from typing import List

from .types import TopicRow


def implementation_status_rows() -> List[TopicRow]:
    return [
        ('soccerball.txt', 'graphics corpus', 'runs 0 errors', 'yes', 'rotation tmp vs xyz'),
        ('wheel.txt', 'graphics corpus', 'runs 0 errors', 'yes', 'spoke coords verified'),
        ('PRINT array subscript', 'PRINT a(i)', 'not expanded', 'no', 'use ; or separate PRINT'),
        ('Corpus ALL runnable 24', 'audit list', 'auditing', 'partial', 'corpus_audit_probe'),
    ]
