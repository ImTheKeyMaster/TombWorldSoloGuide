#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StartingNpoGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_two_d3_roll_is_stored_once_with_official_calculation(self):
        roll = self.source("function startingNpoRoll()", "function generateRoster")
        self.assertIn("[rollD3(),rollD3()]", roll)
        self.assertIn("dice[0]+dice[1]+3", roll)
        self.assertIn("calculation", roll)
        ensure = self.source("function ensureStartingNpoGeneration()", "function render()")
        self.assertIn("if(state.startingNpoGeneration)return false", ensure)
        self.assertIn("save()", ensure)

    def test_shared_dice_animation_settles_and_transitions_automatically(self):
        presentation = self.source("if(stepId==='npoRoster'){", "if(stepId==='deploy')")
        self.assertIn("rollingDieHtml()", presentation)
        self.assertIn("animated-roll", presentation)
        self.assertIn("startingNpoResult", presentation)
        flow = self.source("function runStartingNpoGeneration()", "function renderGame()")
        self.assertIn("settleAnimatedDice", flow)
        self.assertIn("dice:generation.dice.map(value=>({value,kind:'hit'}))", flow)
        self.assertIn("setTimeout(advance,1400)", flow)
        self.assertIn("state.setupStep=Math.min", flow)

    def test_deployment_is_capped_without_changing_mission_roll(self):
        roll = self.source("function startingNpoRoll()", "function generateRoster")
        self.assertIn("deploymentCount:Math.min(missionRoll,MAX_NPOS)", roll)
        roster = self.source("function generateRoster(generation)", "function ensureStartingNpoGeneration")
        self.assertIn("count=generation.deploymentCount", roster)
        presentation = self.source("if(stepId==='npoRoster'){", "if(stepId==='deploy')")
        self.assertIn("generation.missionRoll>generation.availableNpos", presentation)
        self.assertIn("Only ${generation.availableNpos} NPOs are available.", presentation)
        self.assertIn("Deploy all ${generation.deploymentCount} available NPOs.", presentation)
        self.assertNotIn("error", presentation.lower())

    def test_persistence_prevents_reroll_and_duplicate_navigation(self):
        initial = self.source("const initialState", "let state")
        self.assertIn("startingNpoGeneration:null", initial)
        normalized = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("raw?.startingNpoGeneration", normalized)
        flow = self.source("function runStartingNpoGeneration()", "function renderGame()")
        self.assertIn("generation.navigationComplete", flow)
        self.assertIn("generation.animationShown=true", flow)
        self.assertIn("if(generation.animationShown)", flow)
        self.assertLess(flow.index("generation.navigationComplete=true"), flow.index("state.setupStep=Math.min"))

    def test_legacy_setup_save_uses_existing_roster_without_rerolling(self):
        restored = self.source("function restoredStartingNpoGeneration()", "function generateRoster")
        self.assertIn("missionRoll=state.roster.length", restored)
        self.assertIn("animationShown:true", restored)
        ensure = self.source("function ensureStartingNpoGeneration()", "function render()")
        self.assertIn("if(state.roster.length)", ensure)
        self.assertIn("restoredStartingNpoGeneration()", ensure)
        self.assertLess(ensure.index("if(state.roster.length)"), ensure.index("startingNpoRoll()"))

    def test_generation_tables_and_reinforcements_are_unchanged(self):
        self.assertRegex(self.app, r"function rollNpo\(\)\{")
        self.assertRegex(self.app, r"function randomReinforcement\(\)\{return rollNpo\(\);\}")
        self.assertEqual(self.app.count("function rollNpo()"), 1)


if __name__ == "__main__":
    unittest.main()
