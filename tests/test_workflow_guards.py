"""Regression tests for workflow data-integrity gating."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowGuardTests(unittest.TestCase):
    def test_integrity_failure_blocks_engines_and_save(self):
        workflow = (ROOT / ".github/workflows/update.yml").read_text(encoding="utf-8")
        self.assertIn("if: steps.integrity.outcome != 'failure'", workflow)
        self.assertIn("steps.sync.outcome == 'success' && steps.integrity.outcome == 'success'", workflow)
        self.assertIn("steps.integrity.outcome == 'failure'", workflow)

    def test_original_continue_on_error_steps_are_preserved(self):
        workflow = (ROOT / ".github/workflows/update.yml").read_text(encoding="utf-8")
        # Preserve the original five and add one for the validator's failure-reporting step.
        self.assertEqual(workflow.count("continue-on-error: true"), 6)
        self.assertIn("name: Kiểm tra toàn vẹn dữ liệu sau đồng bộ", workflow)


if __name__ == "__main__":
    unittest.main()
