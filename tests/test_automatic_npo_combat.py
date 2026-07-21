#!/usr/bin/env python3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AutomaticNpoCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_attack_then_defense_rolls_are_automatic_and_animated(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("startAutomaticCombat();", wizard)
        self.assertIn("rolledCombatDice(profile.dice,profile.hit)", wizard)
        self.assertIn("rolledCombatDice(Math.max(0,3-profile.ap),Number(target.save)||3)", wizard)
        self.assertGreaterEqual(wizard.count("combatTimer=setTimeout"), 2)
        self.assertIn("rollingDieHtml()", wizard)
        self.assertIn("animated-roll", wizard)

    def test_successes_and_damage_are_calculated_without_editable_counters(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("retainSuccessfulDice", wizard)
        self.assertIn("resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile)", wizard)
        self.assertIn("damage:resolution.damage", wizard)
        self.assertNotIn("combatOutcomeFields()", wizard)
        self.assertNotIn("retainedNormal", wizard)
        self.assertNotIn("retainedCritical", wizard)
        self.assertNotIn("data-spin", wizard)

    def test_combat_summary_contains_dice_and_final_damage(self):
        summary = self.source("function renderCombatResolution", "function settleCombatDice")
        self.assertIn("ATTACK DICE", summary)
        self.assertIn("SAVE DICE", summary)
        self.assertIn("Total damage", summary)
        self.assertIn("combat.attackDice.map", summary)
        self.assertIn("combat.saveDice.map", summary)

    def test_combat_result_is_saved_and_restored(self):
        wizard = self.source("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("state.lastActivation={...state.lastActivation,combatDraft:combat}", wizard)
        self.assertIn("save();", wizard)
        self.assertIn("const sameCombat=saved&&saved.targetId===target.id&&saved.attackType===attackType", wizard)
        self.assertIn("const combat=saved", wizard)
        self.assertIn("renderCombatResolution(combat", wizard)

    def test_aggressive_defense_rolls_without_a_manual_button(self):
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        roll_ui = self.source("function aggressiveDefenseRollHtml", "function combatAbilityReminder")
        self.assertIn("Math.ceil(roll()/2)", preview)
        self.assertIn("diceAnimationTimer=setTimeout", preview)
        self.assertIn("aggressiveDefenseDamage(rolledValue)", preview)
        self.assertNotIn("rollAggressiveDefense", preview + roll_ui)
        self.assertNotIn("Roll D3", roll_ui)


if __name__ == "__main__":
    unittest.main()
