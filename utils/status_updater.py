"""Generate status.html dashboard for phone/tablet monitoring."""
from __future__ import annotations

import datetime
import html
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def project_root() -> Path:
    return _PROJECT_ROOT


def default_status_path() -> Path:
    return _PROJECT_ROOT / 'status.html'


def _read_heartbeat_counter() -> int:
    path = _PROJECT_ROOT / '.heartbeat_counter'
    try:
        return int(path.read_text(encoding='utf-8').strip())
    except (OSError, ValueError):
        return 0


class StatusUpdater:
    def __init__(
        self,
        status_file: str | Path | None = None,
        *,
        heartbeat: int | None = None,
    ) -> None:
        if status_file is None:
            self.status_file = default_status_path()
        else:
            self.status_file = Path(status_file)
            if not self.status_file.is_absolute():
                self.status_file = _PROJECT_ROOT / self.status_file
        self.heartbeat = (
            _read_heartbeat_counter() if heartbeat is None else heartbeat
        )

    def update(
        self,
        current_program: str = '',
        focus: str = '',
        todos: Optional[List[str]] = None,
        confirmed: Optional[List[str]] = None,
        pending: Optional[List[str]] = None,
        recent_log: Optional[List[str]] = None,
        issues: Optional[List[str]] = None,
        extra_info: str = '',
        workload_report: Optional[Mapping[str, Any]] = None,
        user_approval: Optional[Mapping[str, Any]] = None,
        debug_step: Optional[Mapping[str, str]] = None,
        *,
        heartbeat_id: Optional[int] = None,
        sync_id: Optional[int] = None,
        stamp: Optional[str] = None,
        started: Optional[str] = None,
        confirmed_more: int = 0,
        is_heartbeat: bool = True,
    ) -> str:
        """Update status.html with clean structure. Returns rendered HTML."""
        if todos is None:
            todos = []
        if confirmed is None:
            confirmed = []
        if pending is None:
            pending = []
        if recent_log is None:
            recent_log = []
        if issues is None:
            issues = []

        now = datetime.datetime.now()
        if heartbeat_id is not None:
            display_counter = heartbeat_id
        else:
            self.heartbeat += 1
            display_counter = self.heartbeat

        if stamp is None:
            stamp = now.strftime('%Y-%m-%d %H:%M:%S')
        if started is None:
            started = now.strftime('%Y-%m-%d %H:%M')

        esc = html.escape
        counter_meta = (
            f'heartbeat #{display_counter}'
            if is_heartbeat
            else f'work sync #{sync_id or display_counter}'
        )
        program = current_program or 'None'
        focus_text = focus or 'No active focus'

        body = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>mini_basic • Status</title>
<style>
    body {{ font-family: system-ui, sans-serif; margin: 1.5rem; background: #f8f9fa; color: #111; line-height: 1.5; }}
    h1 {{ margin: 0 0 0.5rem; font-size: 1.4rem; }}
    .meta {{ color: #555; font-size: 0.95rem; margin-bottom: 1rem; }}
    section {{ margin-bottom: 2rem; background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    h2 {{ margin: 0 0 0.8rem; font-size: 1.1rem; border-bottom: 2px solid #ddd; padding-bottom: 0.4rem; }}
    h3 {{ margin: 1rem 0 0.5rem; font-size: 0.95rem; color: #444; }}
    .current {{ background: #e6f3ff; border-left: 5px solid #0066cc; }}
    .success {{ background: #e6f7e6; border-left: 5px solid #0a5; }}
    .pending {{ background: #fff3e0; border-left: 5px solid #c90; }}
    .workload-ok {{ background: #eef9ee; border-left: 5px solid #0a5; }}
    .workload-warn {{ background: #fff8e6; border-left: 5px solid #c90; }}
    .workload-crit {{ background: #fdecea; border-left: 5px solid #c30; }}
    .workload-action {{ font-weight: 600; margin: 0.4rem 0; }}
    .workload-stop {{ color: #a00; }}
    .workload-reduce {{ color: #c60; }}
    .workload-ok-text {{ color: #0a5; }}
    .approval {{ background: #f3f0ff; border-left: 5px solid #6a3fc7; }}
    .approval-pending {{ color: #6a3fc7; font-weight: 600; }}
    .approval-done {{ color: #0a5; }}
    .verify-cmd {{ background: #f5f5f5; padding: 0.5rem 0.6rem; border-radius: 4px; margin: 0.35rem 0; font-size: 0.9rem; word-break: break-all; }}
    .line {{ padding: 0.25rem 0; font-family: Consolas, monospace; font-size: 0.95rem; }}
    .stamp {{ color: #333; font-weight: 600; }}
    .done {{ color: #0a5; }}
    .todo {{ color: #c30; }}
    .active {{ color: #0066cc; font-weight: 600; }}
    .muted {{ color: #888; font-size: 0.9rem; }}
    ul {{ padding-left: 1.5rem; margin: 0.25rem 0 0; }}
</style>
</head>
<body>
<h1>mini_basic Progress Dashboard</h1>
<p class="meta">{esc(counter_meta)} • Updated: {esc(stamp)}</p>

<section class="current">
    <h2> Currently Working On</h2>
    <div class="line active">Program: <strong>{esc(program)}</strong></div>
    <div class="line">{esc(focus_text)}</div>
    <div class="line stamp">Started: {esc(started)}</div>

    <h3>TODOs for this program</h3>
    <ul>
'''
        if todos:
            for todo in todos:
                body += f'        <li class="todo">{esc(todo)}</li>\n'
        else:
            body += '        <li class="muted">(none)</li>\n'

        body += '''    </ul>
</section>

'''
        body += self._render_workload_section(workload_report, esc)
        body += self._render_debug_step_section(debug_step, esc)
        body += self._render_user_approval_section(user_approval, esc, program)

        body += '''<section class="success">
    <h2>✅ Confirmed Working</h2>
'''
        if confirmed:
            for item in confirmed:
                body += f'    <div class="line done">{esc(item)}</div>\n'
            if confirmed_more:
                body += (
                    f'    <div class="line">... ({confirmed_more} more confirmed)</div>\n'
                )
        else:
            body += '    <div class="line">No confirmed items logged yet.</div>\n'

        body += '''</section>

<section class="pending">
    <h2>⏳ Pending / Not Yet Confirmed</h2>
'''
        if pending:
            for item in pending:
                body += f'    <div class="line">{esc(item)}</div>\n'
        else:
            body += '    <div class="line">Nothing pending.</div>\n'

        body += '''</section>

<section>
    <h2> Recent Work Log</h2>
'''
        if recent_log:
            for log_entry in recent_log[-8:]:
                body += f'    <div class="line stamp">{esc(log_entry)}</div>\n'
        else:
            body += '    <div class="line">No work log entries yet.</div>\n'

        body += '''</section>

<section>
    <h2>⚠️ Issues / Error Reports</h2>
'''
        if issues:
            for issue in issues:
                body += f'    <div class="line todo">{esc(issue)}</div>\n'
        else:
            body += '    <div class="line">No blocking issues right now.</div>\n'

        if extra_info:
            body += f'''
</section>

<div class="line muted">{esc(extra_info)}</div>
'''
        else:
            body += '</section>\n'

        body += '''
</body>
</html>
'''

        path = self.status_file
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f'.{path.name}.tmp')
        tmp.write_text(body, encoding='utf-8', newline='\n')
        tmp.replace(path)
        return body

    @staticmethod
    def _render_debug_step_section(
        debug_step: Optional[Mapping[str, str]],
        esc: Any,
    ) -> str:
        if not debug_step:
            return ''
        program = str(debug_step.get('program', '')).strip()
        step = str(debug_step.get('step', '')).strip()
        if not program and not step:
            return ''
        status = str(debug_step.get('status', '')).strip()
        html_parts = [
            '<section class="pending">',
            '    <h2> Debugging step</h2>',
        ]
        if program:
            html_parts.append(
                f'    <div class="line active">Program: <strong>{esc(program)}</strong></div>',
            )
        if step:
            html_parts.append(f'    <div class="line">Step: {esc(step)}</div>')
        if status:
            html_parts.append(f'    <div class="line stamp">Status: {esc(status)}</div>')
        for key, label in (
            ('user_report', 'User report'),
            ('cause', 'Cause'),
            ('fix', 'Fix'),
            ('retest', 'Retest'),
            ('retest_inputs', 'Try'),
            ('agent_checks', 'Agent checks'),
            ('next', 'Next'),
        ):
            value = str(debug_step.get(key, '')).strip()
            if value:
                html_parts.append(f'    <div class="line">{esc(label)}: {esc(value)}</div>')
        html_parts.append('</section>')
        html_parts.append('')
        return '\n'.join(html_parts) + '\n'

    @staticmethod
    def _render_workload_section(
        workload_report: Optional[Mapping[str, Any]],
        esc: Any,
    ) -> str:
        if not workload_report:
            return (
                '<section class="workload-warn">\n'
                '    <h2> Agent Workload</h2>\n'
                '    <div class="line">Resource checker unavailable.</div>\n'
                '</section>\n\n'
            )

        level = str(workload_report.get('level', 'ok')).lower()
        section_class = {
            'ok': 'workload-ok',
            'warn': 'workload-warn',
            'critical': 'workload-crit',
        }.get(level, 'workload-warn')

        action = str(workload_report.get('agent_action', ''))
        if workload_report.get('stop_work'):
            action_class = 'workload-action workload-stop'
        elif workload_report.get('reduce_workload'):
            action_class = 'workload-action workload-reduce'
        else:
            action_class = 'workload-action workload-ok-text'

        rss = workload_report.get('rss_mb', 0)
        peak = workload_report.get('peak_rss_mb', 0)
        free_mb = workload_report.get('system_available_mb', 0)
        used_pct = workload_report.get('system_used_percent', 0)
        cpu = workload_report.get('cpu_percent')
        stamp = workload_report.get('stamp', '')
        message = str(workload_report.get('message', ''))
        measurement_ok = workload_report.get('measurement_ok', True)
        recommendations = workload_report.get('recommendations') or []

        cpu_text = '' if cpu is None else f' • CPU ~{float(cpu):.0f}%'
        meas_text = '' if measurement_ok else ' • RSS measurement failed'

        html_parts = [
            f'<section class="{section_class}">',
            '    <h2> Agent Workload</h2>',
            f'    <div class="{action_class}">{esc(action)}</div>',
            f'    <div class="line">Level: <strong>{esc(level.upper())}</strong>'
            f' • checked {esc(str(stamp))}</div>',
            f'    <div class="line">RSS {esc(f"{float(rss):.0f}")} MB'
            f' • peak {esc(f"{float(peak):.0f}")} MB'
            f' • system free {esc(f"{float(free_mb):.0f}")} MB'
            f' • load {esc(f"{float(used_pct):.0f}")}%{esc(cpu_text)}{esc(meas_text)}</div>',
            f'    <div class="line">{esc(message)}</div>',
        ]

        if recommendations:
            html_parts.append('    <h3>Recommendations</h3>')
            html_parts.append('    <ul>')
            for tip in recommendations:
                html_parts.append(f'        <li class="todo">{esc(str(tip))}</li>')
            html_parts.append('    </ul>')

        html_parts.append('</section>')
        html_parts.append('')
        return '\n'.join(html_parts) + '\n'

    @staticmethod
    def _render_user_approval_section(
        user_approval: Optional[Mapping[str, Any]],
        esc: Any,
        current_program: str,
    ) -> str:
        if not user_approval:
            return ''

        pending = user_approval.get('pending') or []
        agent_pending = user_approval.get('agent_pending') or []
        agent_failed = user_approval.get('agent_failed') or []
        agent_snippets = user_approval.get('agent_snippets') or []
        verify_commands = user_approval.get('verify_commands') or []
        approved = user_approval.get('approved') or []
        approved_more = int(user_approval.get('approved_more') or 0)
        pending_count = int(user_approval.get('pending_count') or len(pending))
        note = str(
            user_approval.get('note')
            or 'Approve whole programs only after running mini_basic.py (see run_program.py)',
        )
        focus = str(user_approval.get('current_program') or current_program)

        html_parts = [
            '<section class="approval">',
            '    <h2> User Final Approval (whole programs)</h2>',
            f'    <div class="line">Focus: <strong>{esc(focus)}</strong>'
            f' • {esc(str(pending_count))} program(s) ready for your OK'
            f' • {esc(str(len(agent_pending) + len(agent_failed)))} still agent-side</div>',
            f'    <div class="line muted">{esc(note)}</div>',
        ]

        if verify_commands:
            html_parts.append('    <h3>Run the program yourself</h3>')
            for entry in verify_commands:
                program = str(entry.get('program', ''))
                command = str(entry.get('command', ''))
                kind = str(entry.get('kind', ''))
                html_parts.append(
                    f'    <div class="verify-cmd"><strong>{esc(program)}</strong>'
                    f'{f"<br><span class=muted>{esc(kind)}</span>" if kind else ""}<br>'
                    f'cd mini_basic<br>{esc(command)}</div>',
                )
                for note in entry.get('try_notes') or []:
                    html_parts.append(f'    <div class="line muted">• {esc(str(note))}</div>')
                agent_cmd = str(entry.get('agent_command', ''))
                if agent_cmd:
                    html_parts.append(
                        f'    <div class="line muted">Agent snippet checks (not user verify): '
                        f'{esc(agent_cmd)}</div>',
                    )

        if pending:
            html_parts.append('    <h3>Ready for your approval</h3>')
            html_parts.append('    <ul>')
            for item in pending:
                html_parts.append(
                    f'        <li class="approval-pending">[ ] {esc(str(item))}</li>',
                )
            html_parts.append('    </ul>')
        else:
            html_parts.append(
                '    <div class="line muted">No whole program ready for your OK yet.</div>',
            )

        if agent_snippets:
            html_parts.append('    <h3>Snippet failures (agent diagnostics)</h3>')
            html_parts.append('    <ul>')
            for item in agent_snippets:
                html_parts.append(f'        <li class="todo">{esc(str(item))}</li>')
            html_parts.append('    </ul>')

        if agent_failed:
            html_parts.append('    <h3>Programs still failing agent checks</h3>')
            html_parts.append('    <ul>')
            for item in agent_failed:
                html_parts.append(f'        <li class="todo">{esc(str(item))}</li>')
            html_parts.append('    </ul>')

        if agent_pending:
            html_parts.append('    <h3>Not yet checked</h3>')
            html_parts.append('    <ul>')
            for item in agent_pending:
                html_parts.append(f'        <li class="muted">… {esc(str(item))}</li>')
            html_parts.append('    </ul>')

        if approved:
            html_parts.append('    <h3>Recently approved</h3>')
            for item in approved:
                html_parts.append(
                    f'    <div class="line approval-done">[x] {esc(str(item))}</div>',
                )
            if approved_more:
                html_parts.append(
                    f'    <div class="line">... ({approved_more} more approved)</div>',
                )

        html_parts.append('</section>')
        html_parts.append('')
        return '\n'.join(html_parts) + '\n'