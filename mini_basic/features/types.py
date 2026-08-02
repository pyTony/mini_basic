"""Shared types for dialect / implementation feature matrices."""
from __future__ import annotations

from typing import Tuple

MatrixRow = Tuple[str, str, str, str, str, str]
TopicRow = Tuple[str, str, str, str, str]  # feature, spec, mini, tested, notes
DeferredRow = Tuple[str, str, str]  # area, feature, reason deferred
