import re
import unittest
from pathlib import Path


APP = (Path(__file__).parents[1] / "app.js").read_text()


class ReinforcementCheckboxInteractionTests(unittest.TestCase):
    def function_source(self, start, end):
        return APP.split(f"function {start}", 1)[1].split(f"function {end}", 1)[0]

    def test_placement_checkboxes_are_enabled_and_bound_after_render(self):
        placement_markup = re.search(
            r"const placements=.*?\.join\(''\);", APP, re.DOTALL
        ).group(0)
        self.assertNotIn("'disabled'", placement_markup)
        self.assertIn("data-reinforcement-placement", placement_markup)
        self.assertIn(
            "$$('[data-reinforcement-placement]').forEach(input=>input.addEventListener('change'",
            APP,
        )
        self.assertLess(APP.index("app.innerHTML=hud()"), APP.index("bindPlay();", APP.index("app.innerHTML=hud()")))

    def test_hatchway_change_does_not_replace_checkbox_before_click(self):
        hatchway = self.function_source(
            "recordReinforcementHatchway(id,hatchway)", "rollInitiative()"
        )
        self.assertIn("npo.reinforcement.hatchway=recordedHatchway", hatchway)
        self.assertIn("save();", hatchway)
        self.assertNotIn("render();", hatchway)

    def test_all_confirmed_placements_enable_strategy_confirmation(self):
        confirmation = self.function_source(
            "confirmReinforcementPlacement(id,confirmed)",
            "recordReinforcementHatchway(id,hatchway)",
        )
        self.assertIn("operativeIds.every", confirmation)
        self.assertIn("complete?'complete':'placement'", confirmation)
        strategy_card = self.function_source("strategyCard()", "strategyEventHtml(event)")
        self.assertIn("placementPending=state.reinforcementState.status==='placement'", strategy_card)
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled':''", strategy_card)


if __name__ == "__main__":
    unittest.main()
