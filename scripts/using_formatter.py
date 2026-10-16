"""Backward-compatible re-export of PRINT USING support.

Implementation: ``mini_basic.format.using.UsingFormatter``.
New code should use::

    from mini_basic.format import UsingFormatter
"""
from mini_basic.format import UsingFormatter

__all__ = ['UsingFormatter']