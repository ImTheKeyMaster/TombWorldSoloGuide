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
        self.assertIn("aggressiveDefenseAnimating:true", preview)
        self.assertIn("n.type==='Canoptek Macrocyte'", preview)
        self.assertIn("targetIncapacitated:result.after<=0", preview)
        self.assertIn("attackerWithinTwo:Boolean(diceDraft.attackerWithinTwo)", preview)

    def test_d3_reuses_animated_die_and_resolves_all_results(self):
        resolver = self.source("function aggressiveDefenseDamage", "function aggressiveDefenseRollHtml")
        self.assertIn("return result>=2?result:0", resolver)
        self.assertEqual([0 if value == 1 else value for value in (1, 2, 3)], [0, 2, 3])
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        self.assertIn("Math.ceil(roll()/2)", preview)
        self.assertIn("rollingDieHtml()", self.source("function aggressiveDefenseRollHtml", "function combatAbilityReminder"))
        self.assertIn("settleAnimatedDice", preview)
        self.assertIn("aggressiveDefenseRoll=rolledValue", preview)
        self.assertIn("aggressiveDefenseDamage=aggressiveDefenseDamage(rolledValue)", preview)

    def test_continue_waits_for_d3_and_non_triggered_combat_does_not_wait(self):
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        self.assertIn("aggressiveDefenseAnimating:true", preview)
        self.assertIn("onResolved,onCancel,false,true", preview)
        self.assertIn("displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false)", preview)
        self.assertIn("if(aggressiveDefenseDie?.isConnected)", preview)
        self.assertRegex(preview, r"if\(retaliationApplies\)\{[\s\S]+?return;\s*\}\s*result\.aggressiveDefenseDamage=0")

    def test_roll_is_persisted_before_animation_and_restored_without_replay(self):
        preview = self.source("function previewPendingPlayerAttack", "function displayPendingPlayerCombat")
        persisted = preview.index("save();")
        animated = preview.index("settleAnimatedDice")
        self.assertLess(persisted, animated)
        wizard = self.source("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        self.assertIn("if(draft)", wizard)
        self.assertIn("{result:draft,animate:false}", wizard)

    def test_result_card_is_concise_and_precedes_damage_summary(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("D3 Roll: ${combat.aggressiveDefenseRoll}", reminder)
        self.assertIn("No damage inflicted.", reminder)
        self.assertIn("The attacking operative suffers ${aggressiveDamage} damage.", reminder)
        renderer = self.source("function renderCombatResolution", "function showSharedCombatResolutionScreen")
        self.assertLess(renderer.index("${combatAbilityReminder(combat)}"), renderer.index('<div class="damage-summary">'))

    def test_existing_transactional_damage_application_is_preserved(self):
        apply_damage = self.source("function applyPendingPlayerDamage", "function completePlayerActivation")
        self.assertIn("playerBefore-aggressiveDamage", apply_damage)
        self.assertIn("state.playerWounds[stage.playerOperativeId]=playerAfter", apply_damage)

    def test_result_message_includes_roll_and_only_appears_after_a_roll(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("Number.isInteger(combat.aggressiveDefenseRoll)", reminder)
        self.assertIn("D3 Roll: ${combat.aggressiveDefenseRoll}", reminder)


if __name__ == "__main__":
    unittest.main()
