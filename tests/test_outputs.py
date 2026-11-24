"""Schema checks for the generated Analytics and Evaluation payloads."""
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GeneratedOutputTests(unittest.TestCase):
    def test_analytics_v2_schema_for_all_games(self):
        with open(os.path.join(ROOT, "analytics.json"), encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["engine_version"], 2)
        self.assertEqual(set(payload["games"]), {"655", "645", "535"})
        for game, data in payload["games"].items():
            self.assertIn("cooccurrence_baseline", data)
            self.assertIn("expected_uniform", data["pairs"][0])
        self.assertEqual(set(payload["games"]["535"]["by_hour"]), {"13", "21"})

    def test_evaluation_v2_includes_five_ticket_comparison(self):
        with open(os.path.join(ROOT, "evaluation.json"), encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["engine_version"], 2)
        self.assertEqual(set(payload["games"]), {"655", "645", "535"})
        for data in payload["games"].values():
            self.assertEqual(data["production_portfolio"]["ticket_count"], 5)
            self.assertEqual(data["production_portfolio"]["draws_with_overlap_violation"], 0)
            self.assertTrue(data["five_ticket_random_control"]["same_pairwise_overlap_cap_as_production"])
            self.assertIn("any_ticket_ge2_rate_diff_vs_random", data["portfolio_comparison"])


if __name__ == "__main__":
    unittest.main()
