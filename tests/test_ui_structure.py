"""Static regression checks for the mobile-first 2.0 navigation structure."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UIStructureTests(unittest.TestCase):
    def test_six_primary_tabs_and_separate_lab(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        tabs = re.findall(r'<button class="tab" data-t="([^"]+)', html)
        self.assertEqual(tabs, ["check", "pred", "lab", "stats", "hist", "tools"])
        self.assertIn('id="t-lab"', html)
        self.assertNotIn('id="predictionLab"', html)
        pred_start, lab_start = html.index('id="t-pred"'), html.index('id="t-lab"')
        self.assertLess(pred_start, lab_start)
        self.assertNotIn('id="t-lab"', html[pred_start:lab_start])

    def test_tools_are_grouped_and_density_preference_is_local(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for tool in ("cage", "cageh", "tally"):
            self.assertIn(f'id="tool-{tool}"', html)
        self.assertIn('store("uiDensity", density)', html)
        self.assertIn('store("uiDensity") || "compact"', html)
        self.assertIn('id="predOfficial"', html)
        # init() gắn sự kiện vào #t-cage / #t-cageh / #t-tally; thiếu id nào là JS dừng giữa chừng.
        for el in ("t-cage", "t-cageh", "t-tally", "t-tools"):
            self.assertIn(f'id="{el}"', html)
        tools_start = html.index('id="t-tools"')
        for el in ("tool-cage", "tool-cageh", "tool-tally"):
            self.assertGreater(html.index(f'id="{el}"'), tools_start)


if __name__ == "__main__":
    unittest.main()
