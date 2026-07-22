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
        direct_route = "beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player')"
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

    def test_firefight_activation_cards_do_not_repeat_initiative(self):
        card = self.function_source("nextStepCard", "missionStrategyPending")
        self.assertNotIn("initiativeStatusHtml", card)
        self.assertNotIn("has initiative", card)
        self.assertNotIn("have initiative", card)
        self.assertIn("<h2>Player Activation</h2>", card)
        self.assertIn(">NPO Activation</h2>", card)
        self.assertIn("activationProgressLabel()", card)

    def test_legacy_confirmation_save_restores_directly(self):
        normalization = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("merged.phase==='strategy'&&merged.strategyStage==='initiative'", normalization)
        self.assertIn("merged.strategyData?.suggestedInitiative==='npo'?'npo':'player'", normalization)
        self.assertIn("merged.phase='firefight'", normalization)
        self.assertIn("merged.strategyStage=null", normalization)
        self.assertIn("merged.nextSide=resolvedSide", normalization)
        rendering = self.function_source("renderPlay", "activeEventEffectsHtml")
        self.assertNotIn("beginFirefight", rendering)

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
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled'", self.function_source("strategyCard", "strategyEventHtml"))
        self.assertIn("beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player')", binding)


if __name__ == "__main__":
    unittest.main()
