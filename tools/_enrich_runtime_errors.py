"""Enrich except Exception: _runtime_error('? X error') with exception detail."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "mini_basic" / "runtime_parts" / "execution.py"

# except Exception:\n ... self._runtime_error('? Something error'
# -> except Exception as exc:\n ... self._runtime_error(self._error_message('? Something error', exc)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"except Exception:\n"
        r"([ \t]*)self\._runtime_error\(\s*'(?P<msg>\?[^']*error[^']*)'",
    )

    def repl(m: re.Match[str]) -> str:
        indent = m.group(1)
        msg = m.group("msg")
        return (
            f"except Exception as exc:\n"
            f"{indent}self._runtime_error(\n"
            f"{indent}    self._error_message('{msg}', exc),"
        )

    new, n = pattern.subn(repl, text)
    # Fix trailing: originally was self._runtime_error('? X error', line_num...
    # After sub: self._runtime_error(\n    self._error_message('? X error', exc), line_num...
    # But we may have broken `self._runtime_error(\n    self._error_message('...', exc), line_num` 
    # if original was single-line. Check pattern carefully.

    # Alternative simpler approach: only simple single-line forms
    text2 = PATH.read_text(encoding="utf-8")
    pattern2 = re.compile(
        r"except Exception:\n"
        r"([ \t]*)self\._runtime_error\("
        r"'(?P<msg>\?[^']*)'"
        r"(?P<rest>,[^)]*)\)"
    )

    def repl2(m: re.Match[str]) -> str:
        indent = m.group(1)
        msg = m.group("msg")
        rest = m.group("rest")
        return (
            f"except Exception as exc:\n"
            f"{indent}self\._runtime_error(\n"
            f"{indent}    self._error_message('{msg}', exc){rest})"
        )

    new2, n2 = pattern2.subn(repl2, text2)
    PATH.write_text(new2, encoding="utf-8")
    print(f"enriched {n2} sites")


if __name__ == "__main__":
    main()
