#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AggressiveDefenseD3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_ui_uses_american_english_and_has_no_manual_d3_field(self):
        ui = "\n".join((ROOT / name).read_text() for name in ("index.html", "app.js"))
        for phrase in ("Aggressive Defence Construct", "defender’s defence dice", "Defence Dice"):
            self.assertNotIn(phrase, ui)
        self.assertNotIn("Aggressive Defense Construct D3 result", ui)
        self.assertNotIn("aggressiveDefenceRoll", self.app)

    def test_roll_is_only_offered_when_the_ability_applies(self):
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        self.assertIn("if(retaliationApplies)", preview)
        self.assertIn("aggressiveDefenseRollHtml()", preview)
        self.assertIn("targetIncapacitated:result.after<=0", preview)
        self.assertIn("attackerWithinTwo:Boolean($('#attackerWithinTwo')?.checked)", preview)

    def test_d3_reuses_animated_die_and_resolves_all_results(self):
        resolver = self.source("function aggressiveDefenseDamage", "function aggressiveDefenseRollHtml")
        self.assertIn("return result>=2?result:0", resolver)
        self.assertEqual([0 if value == 1 else value for value in (1, 2, 3)], [0, 2, 3])
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        self.assertIn("Math.ceil(roll()/2)", preview)
        self.assertIn("rollingDieHtml()", preview)
        self.assertIn("dieHtml({value:rolledValue,kind:'hit'})", preview)
        self.assertIn("showToast(message)", preview)
        self.assertIn("aggressiveDefenseRoll=rolledValue", preview)
        self.assertIn("aggressiveDefenseDamage=aggressiveDefenseDamage(rolledValue)", preview)
        self.assertIn("diceAnimationTimer=setTimeout", preview)

    def test_existing_transactional_damage_application_is_preserved(self):
        apply_damage = self.source("function applyPendingPlayerDamage", "function completePlayerActivation")
        self.assertIn("playerBefore-aggressiveDamage", apply_damage)
        self.assertIn("state.playerWounds[stage.playerOperativeId]=playerAfter", apply_damage)

    def test_result_message_includes_roll_and_only_appears_after_a_roll(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("Number.isInteger(combat.aggressiveDefenseRoll)", reminder)
        self.assertIn("D3 result ${combat.aggressiveDefenseRoll}", reminder)


if __name__ == "__main__":
    unittest.main()
