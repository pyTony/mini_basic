"""Tests for utils.agent_resource."""
from __future__ import annotations

import unittest

from utils.agent_resource import (
    ResourceSample,
    agent_workload_ok,
    build_workload_report,
    evaluate_resources,
    format_resource_line,
    record_allocation_failure,
    sample_resources,
    should_reduce_workload,
    workload_report_dict,
)


class AgentResourceTests(unittest.TestCase):
    def test_sample_resources_returns_real_rss_on_windows(self):
        sample = sample_resources()
        self.assertTrue(sample.measurement_ok, 'RSS measurement must not silently return 0')
        self.assertGreater(sample.rss_mb, 0.5)
        self.assertGreaterEqual(sample.peak_rss_mb, sample.rss_mb - 0.1)
        self.assertRegex(sample.stamp, r'^\d{4}-\d{2}-\d{2} ')

    def test_evaluate_resources_ok_by_default(self):
        sample = ResourceSample(
            rss_mb=50.0,
            peak_rss_mb=50.0,
            system_available_mb=4096.0,
            system_used_percent=40.0,
            cpu_percent=10.0,
            stamp='2026-06-23 12:00:00',
            measurement_ok=True,
        )
        verdict = evaluate_resources(sample)
        self.assertEqual(verdict.level, 'ok')
        self.assertFalse(verdict.reduce_workload)
        self.assertFalse(verdict.stop_work)

    def test_evaluate_resources_critical_on_high_rss(self):
        sample = ResourceSample(
            rss_mb=300.0,
            peak_rss_mb=300.0,
            system_available_mb=4096.0,
            system_used_percent=40.0,
            cpu_percent=10.0,
            stamp='2026-06-23 12:00:00',
            measurement_ok=True,
        )
        verdict = evaluate_resources(sample)
        self.assertEqual(verdict.level, 'critical')
        self.assertTrue(verdict.stop_work)
        self.assertTrue(verdict.recommendations)

    def test_format_resource_line_includes_agent_action(self):
        sample = ResourceSample(
            rss_mb=300.0,
            peak_rss_mb=300.0,
            system_available_mb=4096.0,
            system_used_percent=40.0,
            cpu_percent=None,
            stamp='2026-06-23 12:00:00',
            measurement_ok=True,
        )
        verdict = evaluate_resources(sample)
        line = format_resource_line(verdict)
        self.assertIn('STOP heavy work', line)

    def test_workload_report_dict_has_status_fields(self):
        sample = ResourceSample(
            rss_mb=100.0,
            peak_rss_mb=120.0,
            system_available_mb=2048.0,
            system_used_percent=50.0,
            cpu_percent=12.0,
            stamp='2026-06-23 12:00:00',
            measurement_ok=True,
        )
        report = build_workload_report(
            evaluate_resources(sample, include_crash_marker=False),
            write_check=False,
        )
        payload = workload_report_dict(report)
        self.assertEqual(payload['level'], 'ok')
        self.assertIn('agent_action', payload)
        self.assertIn('rss_mb', payload)
        self.assertIn('recommendations', payload)

    def test_record_crash_forces_stop(self):
        verdict = record_allocation_failure(
            'memory allocation of 296812544 bytes failed',
            bytes_requested=296_812_544,
        )
        self.assertEqual(verdict.level, 'critical')
        self.assertTrue(verdict.stop_work)
        reduce, reason = should_reduce_workload()
        self.assertTrue(reduce)
        self.assertIn('STOP', reason)
        ok_heavy, msg = agent_workload_ok()
        self.assertFalse(ok_heavy)
        self.assertIn('STOP', msg)


if __name__ == '__main__':
    unittest.main()