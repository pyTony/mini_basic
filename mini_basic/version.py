"""Package version and --version report text."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

# PEP 440 (PyPI). Keep in sync with root pyproject.toml.
# 1.0.0.dev0 = pre-1.0 packaging line; set to 1.0.0 when tagging a release.
__version__ = '1.0.0.dev0'

# Short implementation snapshot (keep in sync with FEATURES_DONE / plan).
_IMPLEMENTATION_STATUS = (
    'multi-dialect interpreter (mini, mits, commodore, tiny, bbc); '
    'BBC control flow (CASE/WHILE/REPEAT/PROC/FN); files OPENIN/PRINT#; '
    'graphics tier A (MODE/GCOL/PLOT/CIRCLE/COLOUR/*REFRESH); '
    'VDU phases A–C (17/20/24/26/28/30/cursor/23 stubs); '
    'MODE 7 teletext (alpha/gfx colours, mosaic sextants, flash/hold/separated/bg; '
    'not full SAA5050 / double-height / conceal completeness); '
    'Russell .bbc detokenize; text-only session skip of auto-pygame; '
    'phase0+phase1 pytest regression. '
    'SOUND/ENVELOPE: silent stubs (optional capped wait on SOUND; no audio engine). '
    'Not RISC OS: SYS/WIMP/assembler/full sound/Ceefax.'
)


def _env_minibasic_dir(scope: Optional[str] = None) -> Optional[str]:
    """Return MINIBASIC_DIR from process env, or Windows User/Machine registry."""
    if scope is None:
        value = os.environ.get('MINIBASIC_DIR')
        return value if value else None
    if sys.platform != 'win32':
        return None
    try:
        import winreg
    except ImportError:
        return None
    root = winreg.HKEY_CURRENT_USER if scope == 'User' else winreg.HKEY_LOCAL_MACHINE
    subkey = r'Environment'
    try:
        with winreg.OpenKey(root, subkey) as key:
            value, _ = winreg.QueryValueEx(key, 'MINIBASIC_DIR')
            return str(value) if value else None
    except OSError:
        return None


def _path_status(path: Optional[str]) -> str:
    if not path:
        return '(not set)'
    p = Path(path)
    if p.is_dir():
        return f'{path}  [exists]'
    if p.exists():
        return f'{path}  [exists, not a directory]'
    return f'{path}  [missing]'


def format_version_report() -> str:
    """Multi-line text for ``--version`` / ``-V``."""
    import mini_basic

    package_root = Path(mini_basic.__file__).resolve().parent
    project_root = package_root.parent
    lines: List[str] = [
        f'mini_basic {__version__}',
        f'Python {sys.version.split()[0]} ({sys.platform})',
        f'Package: {package_root}',
        f'Project tree: {project_root}',
        '',
        'Implementation status:',
        f'  {_IMPLEMENTATION_STATUS}',
        '',
        'MINIBASIC_DIR (install / launcher tree):',
        f'  process env:  {_path_status(os.environ.get("MINIBASIC_DIR"))}',
    ]
    if sys.platform == 'win32':
        user_dir = _env_minibasic_dir('User')
        machine_dir = _env_minibasic_dir('Machine')
        lines.append(f'  User permanent: {_path_status(user_dir)}')
        if machine_dir:
            lines.append(f'  Machine permanent: {_path_status(machine_dir)}')
    lines.extend(
        [
            '',
            'Related env:',
            f'  MINI_BASIC_DIALECT / MINIBASIC_DIALECT: '
            f'{os.environ.get("MINI_BASIC_DIALECT") or os.environ.get("MINIBASIC_DIALECT") or "(not set)"}',
            f'  MINIBASIC_NO_GRAPHICS: {os.environ.get("MINIBASIC_NO_GRAPHICS") or "(not set)"}',
            f'  MINIBASIC_DISPLAY: {os.environ.get("MINIBASIC_DISPLAY") or "(not set)"}',
            f'  DISPLAY / WAYLAND_DISPLAY: '
            f'{os.environ.get("DISPLAY") or "(not set)"} / '
            f'{os.environ.get("WAYLAND_DISPLAY") or "(not set)"}',
        ]
    )
    try:
        from mini_basic.util.session import session_supports_gui

        lines.append(
            f'  session_supports_gui(): {session_supports_gui()}'
        )
    except Exception:
        pass
    return '\n'.join(lines)


def print_version_report() -> None:
    print(format_version_report())
