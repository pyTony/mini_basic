from __future__ import annotations

from typing import List

from .types import TopicRow


def array_matrix_rows() -> List[TopicRow]:
    return [
        ('b() = v1, v2, ...', 'row-major init (BB4W)', 'yes', 'yes', 'test_matrix_comma_fill'),
        ('c() = a() . b()', 'matrix multiply', 'yes', 'yes', 'in-place dest fix'),
        ('SUM(a())', 'whole 1D array', 'yes', 'partial', '1D only'),
        ('SUM(a(i TO j))', 'slice', 'yes', 'yes', 'test_sum_array_slice'),
        ('a() = b() copy', 'whole array', 'yes', 'yes', 'test_whole_array_copy'),
        ('a() = scalar fill', 'broadcast', 'yes', 'yes', 'binary literal fill test'),
        ('scalar + array same name', 'b and b()', 'coexist', 'yes', 'soccerball pattern'),
        ('array slicing assign', 'a() = b(i TO j)', 'missing', 'no', 'deferred'),
    ]
