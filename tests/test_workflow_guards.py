"""Regression tests for workflow data-integrity gating.

These assertions intentionally match the current update.yml contract:
- post-sync validator step id: validate_data
- the five pre-existing continue-on-error directives remain unchanged
- failed validation prevents downstream engines (when sync succeeded),
  prediction, and the save step through GitHub Actions' default success() gate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "update.yml"


class WorkflowGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_post_sync_validator_uses_current_step_id_and_command(self):
        workflow = self.workflow
        self.assertIn("id: validate_data", workflow)
        self.assertIn("if: steps.sync.outcome == 'success'", workflow)
        self.assertIn("run: python3 -m unittest tests.test_data_integrity -v", workflow)
        self.assertNotIn("steps.integrity", workflow, "stale step id must not return")

    def test_validation_gates_downstream_engines_and_prediction(self):
        workflow = self.workflow
        self.assertIn(
            "if: steps.sync.outcome != 'success' || steps.validate_data.outcome == 'success'",
            workflow,
        )
        self.assertIn(
            "if: steps.sync.outcome == 'success' && steps.validate_data.outcome == 'success'",
            workflow,
        )
        self.assertIn("steps.validate_data.outcome == 'failure'", workflow)

    def test_save_step_keeps_default_success_gate(self):
        lines = self.workflow.splitlines()
        save_index = next(
            i for i, line in enumerate(lines)
            if line.strip() == "- name: Lưu thay đổi"
        )
        # An explicit always()/failure() condition here could save invalid output.
        following = lines[save_index + 1 : save_index + 4]
        self.assertFalse(any("if:" in line for line in following))
        validator_index = next(
            i for i, line in enumerate(lines)
            if line.strip() == "id: validate_data"
        )
        self.assertLess(validator_index, save_index)

    def test_five_existing_continue_on_error_directives_are_preserved(self):
        # The current workflow has five: sync, optional AI, analytics, evaluation,
        # and prediction. Do not add one to the validator or alter this contract.
        self.assertEqual(self.workflow.count("continue-on-error: true"), 5)


if __name__ == "__main__":
    unittest.main()
