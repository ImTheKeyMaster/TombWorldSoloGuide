import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RosterWoundControlTests(unittest.TestCase):
    def test_npo_restoration_respects_active_cap_before_changing_wounds(self):
        app = (ROOT / "app.js").read_text()
        match = re.search(r"function adjustWounds\(id,d\)\{(.*?)\n  \}", app, re.S)
        self.assertIsNotNone(match)
        source = match.group(1)
        cap_guard = "if(wasOut&&d>0&&activeNpos().length>=MAX_NPOS)"
        wound_mutation = "n.wounds=Math.max"
        self.assertIn(cap_guard, source)
        self.assertIn("showToast(`Only ${MAX_NPOS} active NPOs can be on the battlefield.`)", source)
        self.assertLess(source.index(cap_guard), source.index(wound_mutation))


if __name__ == "__main__":
    unittest.main()
