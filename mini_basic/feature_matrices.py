"""Backward-compatible entry point; implementation lives in mini_basic.features."""
from __future__ import annotations

from mini_basic.features import (
    all_matrix_text,
    array_matrix_rows,
    bbc_family_rows,
    data_read_rows,
    deferred_rows,
    dialect_structure_rows,
    format_bbc_family_matrix,
    graphics_rows,
    implementation_status_rows,
    trigonometry_rows,
    write_matrix_files,
)

__all__ = [
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
    'main',
]


def main() -> None:
    from mini_basic.features import main as _features_main

    _features_main()


if __name__ == '__main__':
    main()
