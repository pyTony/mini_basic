"""Monitor process and system memory for agent / heartbeat safety checks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RESOURCE_CHECK_PATH = _PROJECT_ROOT / 'RESOURCE_CHECK.txt'
_AGENT_ALERT_PATH = _PROJECT_ROOT / 'AGENT_RESOURCE_ALERT.txt'
_PEAK_STATE_PATH = _PROJECT_ROOT / '.resource_peak.json'
_CRASH_STATE_PATH = _PROJECT_ROOT / '.resource_crash.json'

# Stay below the ~283 MB Rust/Python allocation failure the user hit.
WARN_PROCESS_RSS_MB = 220
CRIT_PROCESS_RSS_MB = 280
WARN_SYSTEM_AVAILABLE_MB = 768
CRIT_SYSTEM_AVAILABLE_MB = 384
WARN_SYSTEM_USED_PERCENT = 85.0
CRIT_SYSTEM_USED_PERCENT = 92.0

ResourceLevel = Literal['ok', 'warn', 'critical']


@dataclass(frozen=True)
class ResourceSample:
    rss_mb: float
    peak_rss_mb: float
    system_available_mb: float
    system_used_percent: float
    cpu_percent: Optional[float]
    stamp: str
    measurement_ok: bool


@dataclass(frozen=True)
class ResourceVerdict:
    level: ResourceLevel
    message: str
    sample: ResourceSample
    recommendations: tuple[str, ...]
    reduce_workload: bool
    stop_work: bool


@dataclass(frozen=True)
class WorkloadReport:
    """Structured workload snapshot for status.html and agents."""
    level: ResourceLevel
    agent_action: str
    message: str
    rss_mb: float
    peak_rss_mb: float
    system_available_mb: float
    system_used_percent: float
    cpu_percent: Optional[float]
    reduce_workload: bool
    stop_work: bool
    measurement_ok: bool
    recommendations: tuple[str, ...]
    stamp: str


def project_root() -> Path:
    return _PROJECT_ROOT


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def _read_peak_rss_mb() -> float:
    return float(_read_json(_PEAK_STATE_PATH).get('peak_rss_mb', 0.0))


def _write_peak_rss_mb(rss_mb: float) -> float:
    peak = max(_read_peak_rss_mb(), rss_mb)
    _write_json(
        _PEAK_STATE_PATH,
        {
            'peak_rss_mb': round(peak, 2),
            'updated': time.strftime('%Y-%m-%d %H:%M:%S'),
        },
    )
    return peak


def _recent_crash_recorded() -> tuple[bool, str]:
    data = _read_json(_CRASH_STATE_PATH)
    stamp = str(data.get('stamp', ''))
    message = str(data.get('message', ''))
    if not stamp:
        return False, ''
    try:
        recorded = time.mktime(time.strptime(stamp, '%Y-%m-%d %H:%M:%S'))
    except ValueError:
        return False, ''
    # Treat crash marker as active for 30 minutes.
    if time.time() - recorded > 30 * 60:
        return False, ''
    return True, message or 'recent allocation failure recorded'


def clear_crash_marker() -> None:
    """Remove crash alert after system has recovered."""
    for path in (_CRASH_STATE_PATH, _AGENT_ALERT_PATH):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def record_allocation_failure(
    message: str = 'memory allocation failed',
    *,
    bytes_requested: Optional[int] = None,
) -> ResourceVerdict:
    """Call after OOM / allocation crash to force critical alerts for agents."""
    detail = message.strip() or 'memory allocation failed'
    if bytes_requested is not None and bytes_requested > 0:
        detail = f'{detail} ({bytes_requested} bytes)'
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    _write_json(
        _CRASH_STATE_PATH,
        {
            'stamp': stamp,
            'message': detail,
            'pid': os.getpid(),
        },
    )
    sample = sample_resources()
    if bytes_requested is not None and bytes_requested > 0:
        implied_mb = bytes_requested / (1024 * 1024)
        sample = ResourceSample(
            rss_mb=max(sample.rss_mb, implied_mb),
            peak_rss_mb=max(sample.peak_rss_mb, implied_mb),
            system_available_mb=sample.system_available_mb,
            system_used_percent=sample.system_used_percent,
            cpu_percent=sample.cpu_percent,
            stamp=sample.stamp,
            measurement_ok=sample.measurement_ok,
        )
        _write_peak_rss_mb(sample.rss_mb)
    verdict = evaluate_resources(sample)
    write_resource_check(verdict=verdict)
    write_agent_alert(verdict=verdict, crash_note=detail)
    return verdict


def _process_rss_bytes_windows() -> int:
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('PageFaultCount', wintypes.DWORD),
            ('PeakWorkingSetSize', ctypes.c_size_t),
            ('WorkingSetSize', ctypes.c_size_t),
            ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
            ('QuotaPagedPoolUsage', ctypes.c_size_t),
            ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
            ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
            ('PagefileUsage', ctypes.c_size_t),
            ('PeakPagefileUsage', ctypes.c_size_t),
        ]

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    process = ctypes.windll.kernel32.GetCurrentProcess()

    for dll_name in ('psapi', 'Psapi.dll'):
        try:
            psapi = ctypes.WinDLL(dll_name)
        except OSError:
            continue
        get_info = psapi.GetProcessMemoryInfo
        get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        get_info.restype = wintypes.BOOL
        if get_info(process, ctypes.byref(counters), counters.cb):
            return int(counters.WorkingSetSize)

    try:
        result = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-Command',
                f'(Get-Process -Id {os.getpid()}).WorkingSet64',
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip().isdigit():
            return int(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return 0


def _process_rss_bytes() -> tuple[int, bool]:
    if sys.platform == 'win32':
        rss = _process_rss_bytes_windows()
        return rss, rss > 0

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = int(usage.ru_maxrss)
        if sys.platform == 'darwin':
            return rss, rss > 0
        return rss * 1024, rss > 0
    except Exception:
        return 0, False


def _system_memory() -> tuple[float, float]:
    """Return (available_mb, used_percent)."""
    if sys.platform == 'win32':
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return 0.0, 0.0
        available_mb = status.ullAvailPhys / (1024 * 1024)
        used_percent = float(status.dwMemoryLoad)
        return available_mb, used_percent

    try:
        with open('/proc/meminfo', encoding='utf-8') as handle:
            info = {}
            for line in handle:
                key, value = line.split(':', 1)
                info[key.strip()] = int(value.split()[0])
        available_kb = info.get('MemAvailable', info.get('MemFree', 0))
        total_kb = info.get('MemTotal', 0)
        available_mb = available_kb / 1024
        used_percent = 0.0
        if total_kb > 0:
            used_percent = max(0.0, min(100.0, 100.0 * (1 - available_kb / total_kb)))
        return available_mb, used_percent
    except OSError:
        return 0.0, 0.0


def _cpu_percent() -> Optional[float]:
    if sys.platform == 'win32':
        import ctypes

        class FILETIME(ctypes.Structure):
            _fields_ = [
                ('dwLowDateTime', ctypes.c_uint),
                ('dwHighDateTime', ctypes.c_uint),
            ]

        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            return None

        def _to_int(ft: FILETIME) -> int:
            return (ft.dwHighDateTime << 32) + ft.dwLowDateTime

        total = _to_int(kernel) + _to_int(user)
        if total <= 0:
            return None
        busy = total - _to_int(idle)
        return max(0.0, min(100.0, 100.0 * busy / total))

    try:
        load1, _, _ = os.getloadavg()
        cpu_count = os.cpu_count() or 1
        return max(0.0, min(100.0, 100.0 * load1 / cpu_count))
    except (AttributeError, OSError):
        return None


def sample_resources() -> ResourceSample:
    rss_bytes, measurement_ok = _process_rss_bytes()
    rss_mb = rss_bytes / (1024 * 1024)
    peak_rss_mb = _write_peak_rss_mb(rss_mb)
    available_mb, used_percent = _system_memory()
    cpu = _cpu_percent()
    return ResourceSample(
        rss_mb=round(rss_mb, 1),
        peak_rss_mb=round(peak_rss_mb, 1),
        system_available_mb=round(available_mb, 0),
        system_used_percent=round(used_percent, 1),
        cpu_percent=None if cpu is None else round(cpu, 1),
        stamp=time.strftime('%Y-%m-%d %H:%M:%S'),
        measurement_ok=measurement_ok,
    )


def evaluate_resources(
    sample: Optional[ResourceSample] = None,
    *,
    warn_rss_mb: float = WARN_PROCESS_RSS_MB,
    crit_rss_mb: float = CRIT_PROCESS_RSS_MB,
    warn_available_mb: float = WARN_SYSTEM_AVAILABLE_MB,
    crit_available_mb: float = CRIT_SYSTEM_AVAILABLE_MB,
    include_crash_marker: Optional[bool] = None,
) -> ResourceVerdict:
    live = sample is None
    if sample is None:
        sample = sample_resources()
    if include_crash_marker is None:
        include_crash_marker = live

    reasons: list[str] = []
    tips: list[str] = []
    level: ResourceLevel = 'ok'
    stop_work = False
    reduce_workload = False

    crash_active, crash_message = (
        _recent_crash_recorded() if include_crash_marker else (False, '')
    )
    if crash_active:
        level = 'critical'
        stop_work = True
        reduce_workload = True
        reasons.append(f'recent crash: {crash_message}')
        tips.extend([
            'STOP heavy agent work for 30 minutes after allocation failure',
            'single-program probes only; display="none"',
            'no parallel subagents or full corpus audits',
        ])

    if not sample.measurement_ok:
        if level == 'ok':
            level = 'warn'
        reduce_workload = True
        reasons.append('RSS measurement failed — assume memory pressure')
        tips.append('run lightweight checks only until verify_resources.py reports real RSS')

    if sample.rss_mb >= crit_rss_mb:
        level = 'critical'
        stop_work = True
        reduce_workload = True
        reasons.append(f'process RSS {sample.rss_mb:.0f} MB >= {crit_rss_mb:.0f} MB')
        tips.extend([
            'use display="none" for probes and audits',
            'run one program at a time; gc.collect() after each interpreter',
            'avoid full corpus audits with pygame',
        ])
    elif sample.rss_mb >= warn_rss_mb:
        if level == 'ok':
            level = 'warn'
        reduce_workload = True
        reasons.append(f'process RSS {sample.rss_mb:.0f} MB >= {warn_rss_mb:.0f} MB')
        tips.append('prefer lightweight tests until RSS drops')

    if sample.peak_rss_mb >= crit_rss_mb:
        if level == 'ok':
            level = 'warn'
        reduce_workload = True
        reasons.append(f'peak RSS {sample.peak_rss_mb:.0f} MB >= {crit_rss_mb:.0f} MB')

    if sample.system_available_mb and sample.system_available_mb <= crit_available_mb:
        level = 'critical'
        stop_work = True
        reduce_workload = True
        reasons.append(
            f'system free RAM {sample.system_available_mb:.0f} MB <= {crit_available_mb:.0f} MB',
        )
        tips.append('pause heavy agent work until system memory recovers')
    elif sample.system_available_mb and sample.system_available_mb <= warn_available_mb:
        if level == 'ok':
            level = 'warn'
        reduce_workload = True
        reasons.append(
            f'system free RAM {sample.system_available_mb:.0f} MB <= {warn_available_mb:.0f} MB',
        )

    if sample.system_used_percent >= CRIT_SYSTEM_USED_PERCENT:
        level = 'critical'
        stop_work = True
        reduce_workload = True
        reasons.append(
            f'system memory load {sample.system_used_percent:.0f}% >= {CRIT_SYSTEM_USED_PERCENT:.0f}%',
        )
        tips.append('defer non-essential agent tasks until memory load drops')
    elif sample.system_used_percent >= WARN_SYSTEM_USED_PERCENT:
        if level == 'ok':
            level = 'warn'
        reduce_workload = True
        reasons.append(
            f'system memory load {sample.system_used_percent:.0f}% >= {WARN_SYSTEM_USED_PERCENT:.0f}%',
        )

    if reasons:
        message = '; '.join(reasons)
    else:
        message = (
            f'RSS {sample.rss_mb:.0f} MB, peak {sample.peak_rss_mb:.0f} MB, '
            f'system free {sample.system_available_mb:.0f} MB'
        )

    return ResourceVerdict(
        level=level,
        message=message,
        sample=sample,
        recommendations=tuple(dict.fromkeys(tips)),
        reduce_workload=reduce_workload,
        stop_work=stop_work,
    )


def format_resource_line(verdict: ResourceVerdict) -> str:
    sample = verdict.sample
    cpu = '' if sample.cpu_percent is None else f', CPU ~{sample.cpu_percent:.0f}%'
    prefix = verdict.level.upper()
    action = ''
    if verdict.stop_work:
        action = ' [AGENT: STOP heavy work]'
    elif verdict.reduce_workload:
        action = ' [AGENT: reduce workload]'
    return (
        f'{prefix}: {verdict.message} '
        f'(peak {sample.peak_rss_mb:.0f} MB{cpu}){action}'
    )


def write_resource_check(
    path: str | Path | None = None,
    *,
    verdict: Optional[ResourceVerdict] = None,
) -> ResourceVerdict:
    if verdict is None:
        verdict = evaluate_resources()
    target = Path(path) if path is not None else _RESOURCE_CHECK_PATH
    lines = [
        f'# Resource check {verdict.sample.stamp}',
        f'level {verdict.level}',
        f'reduce_workload {str(verdict.reduce_workload).lower()}',
        f'stop_work {str(verdict.stop_work).lower()}',
        format_resource_line(verdict),
        f'rss_mb {verdict.sample.rss_mb}',
        f'peak_rss_mb {verdict.sample.peak_rss_mb}',
        f'system_available_mb {verdict.sample.system_available_mb}',
        f'system_used_percent {verdict.sample.system_used_percent}',
        f'measurement_ok {str(verdict.sample.measurement_ok).lower()}',
    ]
    if verdict.recommendations:
        lines.append('recommendations:')
        lines.extend(f'- {tip}' for tip in verdict.recommendations)
    text = '\n'.join(lines) + '\n'
    tmp = target.with_suffix('.tmp')
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, target)
    write_agent_alert(verdict=verdict)
    return verdict


def write_agent_alert(
    *,
    verdict: Optional[ResourceVerdict] = None,
    crash_note: str = '',
) -> None:
    if verdict is None:
        verdict = evaluate_resources()
    if verdict.level == 'ok' and not crash_note:
        if _AGENT_ALERT_PATH.is_file():
            try:
                _AGENT_ALERT_PATH.unlink()
            except OSError:
                pass
        return

    agent_action = _agent_action_text(verdict)

    lines = [
        f'# Agent resource alert {verdict.sample.stamp}',
        f'level {verdict.level}',
        f'agent_action {agent_action}',
        f'reduce_workload {str(verdict.reduce_workload).lower()}',
        f'stop_work {str(verdict.stop_work).lower()}',
        format_resource_line(verdict),
    ]
    if crash_note:
        lines.append(f'crash_note {crash_note}')
    if verdict.recommendations:
        lines.append('recommendations:')
        lines.extend(f'- {tip}' for tip in verdict.recommendations)
    lines.extend([
        'policy:',
        '- read AGENT_RESOURCE_ALERT.txt before starting heavy agent tasks',
        '- python verify_resources.py (exit 2 = stop, exit 1 = reduce)',
        '- python verify_resources.py --record-crash after allocation failures',
    ])
    text = '\n'.join(lines) + '\n'
    tmp = _AGENT_ALERT_PATH.with_suffix('.tmp')
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, _AGENT_ALERT_PATH)


def should_reduce_workload() -> tuple[bool, str]:
    """Agents call before heavy work. (reduce, reason)."""
    verdict = evaluate_resources()
    write_resource_check(verdict=verdict)
    if verdict.stop_work:
        return True, f'STOP: {verdict.message}'
    if verdict.reduce_workload:
        return True, f'REDUCE: {verdict.message}'
    return False, 'ok'


def agent_workload_ok() -> tuple[bool, str]:
    """Return (ok_to_proceed_heavy, message). Heavy = audits, parallel agents, pygame."""
    reduce, reason = should_reduce_workload()
    if reduce and reason.startswith('STOP'):
        return False, reason
    if reduce:
        return True, reason
    return True, 'ok'


def _agent_action_text(verdict: ResourceVerdict) -> str:
    if verdict.stop_work:
        return 'STOP heavy work — lightweight status/heartbeat only'
    if verdict.reduce_workload:
        return 'REDUCE workload — one small step, display=none, no parallel audits'
    return 'CONTINUE — normal single-program work'


def build_workload_report(
    verdict: Optional[ResourceVerdict] = None,
    *,
    write_check: bool = True,
) -> WorkloadReport:
    if verdict is None:
        verdict = evaluate_resources()
    if write_check:
        write_resource_check(verdict=verdict)
    sample = verdict.sample
    return WorkloadReport(
        level=verdict.level,
        agent_action=_agent_action_text(verdict),
        message=verdict.message,
        rss_mb=sample.rss_mb,
        peak_rss_mb=sample.peak_rss_mb,
        system_available_mb=sample.system_available_mb,
        system_used_percent=sample.system_used_percent,
        cpu_percent=sample.cpu_percent,
        reduce_workload=verdict.reduce_workload,
        stop_work=verdict.stop_work,
        measurement_ok=sample.measurement_ok,
        recommendations=verdict.recommendations,
        stamp=sample.stamp,
    )


def workload_report_dict(report: WorkloadReport) -> dict[str, object]:
    return {
        'level': report.level,
        'agent_action': report.agent_action,
        'message': report.message,
        'rss_mb': report.rss_mb,
        'peak_rss_mb': report.peak_rss_mb,
        'system_available_mb': report.system_available_mb,
        'system_used_percent': report.system_used_percent,
        'cpu_percent': report.cpu_percent,
        'reduce_workload': report.reduce_workload,
        'stop_work': report.stop_work,
        'measurement_ok': report.measurement_ok,
        'recommendations': list(report.recommendations),
        'stamp': report.stamp,
    }


def run_resource_verifier(*, write_file: bool = True) -> int:
    verdict = evaluate_resources()
    if write_file:
        write_resource_check(verdict=verdict)
    print(format_resource_line(verdict))
    if verdict.recommendations:
        for tip in verdict.recommendations:
            print(f'  - {tip}')
    if verdict.stop_work:
        print('AGENT ACTION: STOP heavy work')
    elif verdict.reduce_workload:
        print('AGENT ACTION: reduce workload')
    return 0 if verdict.level == 'ok' else (2 if verdict.level == 'critical' else 1)


def verdict_for_status() -> tuple[str, Optional[str], WorkloadReport]:
    """Short status snippet, optional issue line, and workload report for status.html."""
    report = build_workload_report()
    snippet = (
        f'resources {report.level}: RSS {report.rss_mb:.0f} MB '
        f'(peak {report.peak_rss_mb:.0f})'
    )
    if report.stop_work:
        snippet += ' STOP heavy work'
    elif report.reduce_workload:
        snippet += ' reduce workload'
    issue = None
    if report.level == 'critical':
        issue = f'Resource pressure — agent STOP heavy work: {report.message}'
    elif report.level == 'warn':
        issue = f'Resource watch — agent reduce workload: {report.message}'
    return snippet, issue, report


def snapshot_dict(verdict: ResourceVerdict) -> dict[str, object]:
    payload = asdict(verdict.sample)
    payload['level'] = verdict.level
    payload['message'] = verdict.message
    payload['reduce_workload'] = verdict.reduce_workload
    payload['stop_work'] = verdict.stop_work
    return payload