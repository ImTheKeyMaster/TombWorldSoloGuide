#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class Stage3CombatDiceProviderTests(unittest.TestCase):
    def section(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_attack_and_defense_use_sequential_provider_requests(self):
        attack = self.section("async function requestAttackDiceForProfile", "async function requestDefenseDice")
        defense = self.section("async function requestDefenseDice", "function retainSuccessfulDice")
        combat = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("await requestDiceResults", attack)
        self.assertIn("title:'ATTACK ROLL'", attack)
        self.assertIn("await requestDiceResults", defense)
        self.assertIn("title:'DEFENSE ROLL'", defense)
        self.assertLess(combat.index("await requestAttackDiceForProfile"), combat.index("effectiveDefenseDiceCount"))
        self.assertLess(combat.index("effectiveDefenseDiceCount"), combat.index("await requestDefenseDice"))

    def test_accurate_reduces_only_physical_pool_and_classification_is_shared(self):
        attack = self.section("async function requestAttackDiceForProfile", "async function requestDefenseDice")
        self.assertIn("const rolledCount=total-accurate", attack)
        self.assertIn("count:rolledCount", attack)
        self.assertIn("classifyCombatDice(values,profile.hit,profile.critThreshold)", attack)
        self.assertIn("applySevereToAttackDice", attack)

    def test_piercing_is_applied_before_defense_request(self):
        combat = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("const defenseCount=effectiveDefenseDiceCount(profile,attackDice,3)", combat)
        self.assertIn("requestDefenseDice(defenseCount", combat)
        self.assertLess(combat.index("effectiveDefenseDiceCount"), combat.index("requestDefenseDice(defenseCount"))

    def test_manual_combat_skips_fake_animation_and_sound(self):
        combat = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("const animate=!isPvpMode()", combat)
        self.assertIn("if(animate&&attackDice.length)void TombWorldDiceSfx.play()", combat)
        self.assertIn("const animateDefense=!isPvpMode()", combat)

    def test_combat_triggered_special_rolls_use_logical_provider_dice(self):
        expected = [
            ("DIMENSIONAL BANISHMENT", "count:2,sides:6"),
            ("HOT TEST", "count:1,sides:6"),
            ("COUNTERTEMPORAL SHIFTING", "count:qualifyingIndexes.length,sides:6"),
            ("REANIMATION PROTOCOLS", "count:1,sides:6"),
            ("AGGRESSIVE DEFENCE", "count:1,sides:3"),
        ]
        for title, request in expected:
            with self.subTest(title=title):
                nearby = APP[max(0, APP.index(title)-500):APP.index(title)+500]
                self.assertIn("requestDiceResults", nearby)
                self.assertIn(request, nearby)

    def test_committed_combat_is_reused_and_deferred_systems_remain_automatic(self):
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("if(sameCombat)void displayCombat(saved,animateCombat)", npo)
        initiative = self.section("function rollInitiative", "function beginFirefight")
        self.assertIn("const p=roll(),n=roll()", initiative)
        self.assertNotIn("requestDiceResults", initiative)
        generation = self.section("function rollNpo", "function availableGenerationResult")
        self.assertIn("roll(6)", generation)
        self.assertNotIn("requestDiceResults", generation)
        mission = self.section("function animateMissionDice", "function rollingDieHtml")
        self.assertNotIn("requestDiceResults", mission)

    def test_provider_failures_do_not_fallback_to_random_combat_dice(self):
        combat = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        failure = combat.split("catch(error)", 1)[1]
        self.assertIn("No combat result was committed", failure)
        self.assertNotIn("roll(", failure)
        self.assertNotIn("rollDice(", failure)


if __name__ == "__main__":
    unittest.main()
