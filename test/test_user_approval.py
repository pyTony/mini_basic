"""Tests for user approval gating."""
from __future__ import annotations

import unittest

from utils.user_approval import (
    agent_verify_command_for,
    build_approval_checklist,
    load_user_approval_labels,
    user_run_command_for,
)


class UserApprovalTests(unittest.TestCase):
    def test_user_approval_is_whole_programs(self):
        pending, _ = load_user_approval_labels()
        for label in pending:
            self.assertFalse(':' in label, f'section label not allowed: {label!r}')
            self.assertTrue(
                label.endswith('.txt') or label == 'corpus runnable audit',
                label,
            )

    def test_only_agent_ok_programs_in_user_pending(self):
        checklist = build_approval_checklist('animal.txt')
        pending = checklist['pending']
        for item in pending:
            self.assertNotIn('::', item)
            self.assertNotIn('startup', item.lower())
        agent_failed = checklist['agent_failed']
        for item in agent_failed:
            self.assertIn('::', item)

    def test_user_run_command_for_animal(self):
        self.assertIn(
            'mini_basic.py',
            user_run_command_for('animal.txt'),
        )
        self.assertIn('games/animal.txt', user_run_command_for('animal.txt'))

    def test_agent_verify_command_for_animal(self):
        self.assertEqual(
            agent_verify_command_for('animal.txt'),
            'python verify_program.py animal.txt',
        )

    def test_checklist_shows_user_run_not_agent_verify(self):
        checklist = build_approval_checklist('animal.txt')
        cmds = checklist.get('verify_commands') or []
        animal = next((c for c in cmds if c.get('program') == 'animal.txt'), None)
        self.assertIsNotNone(animal)
        self.assertIn('mini_basic.py', animal['command'])
        self.assertIn('verify_program.py', animal.get('agent_command', ''))


if __name__ == '__main__':
    unittest.main()