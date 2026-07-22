import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STRATEGY_CARD = re.search(
    r"function strategyCard\(\)\{(?P<body>.*?)\n  \}\n\n  function actualReinforcementCount",
    APP,
    re.S,
).group("body")


class StrategyPhaseUiTests(unittest.TestCase):
    def test_obsolete_strategy_copy_is_removed(self):
        self.assertNotIn("STEP 1 OF 2", APP)
        self.assertNotIn(
            "When all Strategy Phase actions are complete, continue to initiative.",
            APP,
        )
        self.assertIn('<span class="phase">STRATEGY PHASE</span>', STRATEGY_CARD)

    def test_reinforcement_results_only_render_when_present(self):
        self.assertNotIn("No reinforcements arrive.", APP)
        self.assertIn(
            "rolls?`<h3>Reinforcements generated</h3><div class=\"reinforcement-grid\">${rolls}</div>",
            STRATEGY_CARD,
        )
        self.assertRegex(STRATEGY_CARD, r"rolls\?`<h3>Reinforcements generated.*?`\s*:\s*''")

    def test_tomb_world_event_placeholder_is_removed(self):
        self.assertNotIn("No Tomb World event is required.", APP)
        self.assertIn(
            "d.event?.status==='drawn'?strategyEventHtml(d.event):''",
            STRATEGY_CARD,
        )
        self.assertIn("strategyEventHtml", APP)


if __name__ == "__main__":
    unittest.main()
