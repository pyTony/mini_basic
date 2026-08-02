"""Language feature matrices split by topic (package layout).

Deferred areas (WIMP, inline ASM, etc.) are listed in deferred.py — not targets
until corpus and core BBC language features are stable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Tuple

from .arrays import array_matrix_rows
from .bbc_family import bbc_family_rows, format_bbc_family_matrix
from .data_read import data_read_rows
from .deferred import deferred_rows
from .dialect_structure import dialect_structure_rows
from .graphics import graphics_rows
from .implementation import implementation_status_rows
from .render import format_deferred_matrix, format_dialect_matrix, format_topic_matrix
from .trigonometry import trigonometry_rows
from .types import DeferredRow, MatrixRow, TopicRow

__all__ = [
    'DeferredRow',
    'MatrixRow',
    'TopicRow',
    'all_matrix_text',
    'array_matrix_rows',
    'bbc_family_rows',
    'data_read_rows',
    'deferred_rows',
    'dialect_structure_rows',
    'format_bbc_family_matrix',
    'graphics_rows',
    'implementation_status_rows',
    'trigonometry_rows',
    'write_matrix_files',
]


def all_matrix_text() -> str:
    parts = [
        format_dialect_matrix(dialect_structure_rows()),
        '',
        format_bbc_family_matrix(bbc_family_rows()),
        '',
        format_topic_matrix('Trigonometry units', trigonometry_rows()),
        '',
        format_topic_matrix('Graphics statements', graphics_rows()),
        '',
        format_topic_matrix('Array / matrix ops', array_matrix_rows()),
        '',
        format_topic_matrix('DATA / READ', data_read_rows()),
        '',
        format_topic_matrix(
            'Implementation status (user verify)',
            implementation_status_rows(),
            spec_col='Target',
        ),
        '',
        format_deferred_matrix(deferred_rows()),
    ]
    return '\n'.join(parts)


def write_matrix_files(root: Path) -> List[Path]:
    root.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    sections: List[Tuple[str, Callable[[], str]]] = [
        ('01_dialect_structure.txt', lambda: format_dialect_matrix(dialect_structure_rows())),
        ('01b_bbc_family.txt', lambda: format_bbc_family_matrix(bbc_family_rows())),
        ('02_trigonometry.txt', lambda: format_topic_matrix('Trigonometry units', trigonometry_rows())),
        ('03_graphics.txt', lambda: format_topic_matrix('Graphics statements', graphics_rows())),
        ('04_arrays_matrix.txt', lambda: format_topic_matrix('Array / matrix ops', array_matrix_rows())),
        ('05_data_read.txt', lambda: format_topic_matrix('DATA / READ', data_read_rows())),
        ('06_implementation_status.txt', lambda: format_topic_matrix(
            'Implementation status (user verify)',
            implementation_status_rows(),
            spec_col='Target',
        )),
        ('07_deferred.txt', lambda: format_deferred_matrix(deferred_rows())),
        ('ALL_MATRICES.txt', all_matrix_text),
    ]
    for name, builder in sections:
        path = root / name
        path.write_text(builder() + '\n', encoding='utf-8')
        written.append(path)
    return written


def main() -> None:
    doc_root = Path(__file__).resolve().parent.parent.parent / 'documentation' / 'feature_matrices'
    paths = write_matrix_files(doc_root)
    print(all_matrix_text())
    print()
    print(f'Wrote {len(paths)} matrix files to {doc_root}')
