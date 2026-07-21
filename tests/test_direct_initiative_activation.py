#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DirectInitiativeActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def function_source(self, name, next_name):
        return self.app.split(f"function {name}(", 1)[1].split(f"function {next_name}(", 1)[0]

    def test_turning_point_one_keeps_automatic_player_initiative_and_dormancy(self):
        initiative = self.function_source("rollInitiative", "beginFirefight")
        self.assertIn("state.turningPoint===1||state.threat===0", initiative)
        self.assertIn("suggestedInitiative='player'", initiative)
        ready = self.function_source("processReadyStep", "applyMissionReadyHooks")
        self.assertIn("npo.dormant=dormant", ready)
        self.assertIn("npo.ready=!dormant", ready)

    def test_strategy_completion_uses_resolved_side_without_reroll(self):
        binding = self.function_source("bindPlay", "startTurningPoint")
        direct_route = "beginFirefight(state.strategyData.suggestedInitiative)"
        self.assertIn(direct_route, binding)
        self.assertNotIn("rollInitiative()", binding)
        self.assertNotIn("rerollInitiative", self.app)

    def test_removed_confirmation_controls_do_not_render(self):
        for obsolete in (
            "The Player has automatic initiative",
            "Begin Player Activation",
            "Begin with NPOs",
            "data-init",
        ):
            self.assertNotIn(obsolete, self.app)

    def test_legacy_confirmation_save_restores_directly(self):
        rendering = self.function_source("renderPlay", "activeEventEffectsHtml")
        self.assertIn("state.phase==='strategy'&&state.strategyStage==='initiative'", rendering)
        self.assertIn("state.strategyData?.suggestedInitiative||state.initiative||'player'", rendering)
        begin = self.function_source("beginFirefight", "resolveStrategyEvent")
        self.assertIn("state.initiative=side", begin)
        self.assertIn("setNextActivation(side)", begin)

    def test_strategy_pipeline_still_precedes_activation(self):
        start = self.function_source("startTurningPoint", "completeStrategyStage")
        expected = [
            "processReadyStep();",
            "applyMissionReadyHooks();",
            "determineInitiative();",
            "processEventStage();",
            "processReinforcementStage();",
        ]
        self.assertEqual(expected, sorted(expected, key=start.index))
        binding = self.function_source("bindPlay", "startTurningPoint")
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled'", self.function_source("strategyCard", "actualReinforcementCount"))
        self.assertIn("beginFirefight(state.strategyData.suggestedInitiative)", binding)


if __name__ == "__main__":
    unittest.main()
