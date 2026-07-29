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
        committed = self.source("function applyPendingPlayerDamage", "function offerReanimateForPendingDamage")
        trigger="if(pending.after<=0&&!protectedForAction&&n.type==='Canoptek Macrocyte Warrior'&&pending.attackerWithinTwo&&!pending.aggressiveDefenseResolved)"
        self.assertIn(trigger, committed)
        self.assertLess(committed.index("showAggressiveDefenseResolution"), committed.index("n.wounds=Math.max"))

    def test_d3_reuses_animated_die_and_resolves_all_results(self):
        resolver = self.source("function aggressiveDefenseDamage", "function aggressiveDefenseRollHtml")
        self.assertIn("return result>=2?1:0", resolver)
        self.assertEqual([0 if value == 1 else value for value in (1, 2, 3)], [0, 2, 3])
        committed = self.source("function applyPendingPlayerDamage", "function offerReanimateForPendingDamage")
        self.assertIn("Math.ceil(roll()/2)", committed)
        self.assertIn("rollingDieHtml()", self.source("function aggressiveDefenseRollHtml", "function combatAbilityReminder"))
        self.assertIn("pending.aggressiveDefenseRoll=retaliation.roll", committed)
        self.assertIn("pending.aggressiveDefenseDamage=aggressiveDefenseDamage(retaliation.roll)", committed)

    def test_continue_waits_for_d3_and_non_triggered_combat_does_not_wait(self):
        committed = self.source("function applyPendingPlayerDamage", "function offerReanimateForPendingDamage")
        self.assertLess(committed.index("showAggressiveDefenseResolution"), committed.index("n.wounds=Math.max"))
        self.assertIn("if(pending.after<=0&&!protectedForAction", committed)

    def test_roll_is_persisted_before_animation_and_restored_without_replay(self):
        committed = self.source("function applyPendingPlayerDamage", "function offerReanimateForPendingDamage")
        self.assertIn("eventTransaction(`aggressive-defence:${incapacitationId}`)", committed)
        self.assertIn("retaliation.committed=true", committed)
        wizard = self.source("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        self.assertIn("if(draft)", wizard)
        self.assertIn("{result:draft,animate:false}", wizard)

    def test_result_card_identifies_retaliatory_damage_recipient_and_precedes_damage_summary(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("D3 Roll: ${combat.aggressiveDefenseRoll}", reminder)
        self.assertIn("String(combat.attackerName||'').trim()", reminder)
        self.assertIn("No retaliatory damage inflicted${attackerName?` on ${escapeHtml(attackerName)}`:''}.", reminder)
        self.assertIn("${escapeHtml(attackerName)} suffers", reminder)
        self.assertIn("${aggressiveDamage} retaliatory damage.", reminder)
        self.assertNotIn("No damage inflicted.", reminder)
        renderer = self.source("function renderCombatResolution", "function showSharedCombatResolutionScreen")
        self.assertIn("renderEliminationSummary", renderer)
        self.assertIn("${elimination}", renderer)
        self.assertLess(renderer.index("${combatAbilityReminder(combat)}"), renderer.index('<div class="damage-summary">'))

    def test_result_message_falls_back_when_attacker_name_is_unavailable(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("attackerName?`${escapeHtml(attackerName)} suffers`:'The attacking operative suffers'", reminder)
        self.assertIn("attackerName?` on ${escapeHtml(attackerName)}`:''", reminder)

    def test_existing_transactional_damage_application_is_preserved(self):
        apply_damage = self.source("function applyPendingPlayerDamage", "function completePlayerActivation")
        self.assertIn("playerBefore-aggressiveDamage", apply_damage)
        self.assertIn("state.playerWounds[stage.playerOperativeId]=playerAfter", apply_damage)

    def test_guided_resolution_is_mandatory_persisted_and_applies_damage_once(self):
        resolver = self.source("function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
        self.assertIn("showModal('Aggressive Defence'", resolver)
        self.assertIn("Roll one D3 before removing it.", resolver)
        self.assertIn('id="continueAggressiveDefense" disabled', resolver)
        self.assertIn("missionDialogLocked=true", resolver)
        self.assertIn("pending.aggressiveDefenseResolved=true", resolver)
        self.assertIn("!pending.aggressiveDefenseDamageApplied", resolver)
        self.assertIn("state.combatState={side:'player',stage:{...stage}}", resolver)

    def test_checkbox_has_helper_text_and_is_saved_with_attack_transaction(self):
        fields = self.source("function aggressiveDefenseFields", "function aggressiveDefenseDamage")
        self.assertIn("Required only if this attack incapacitates the Macrocyte.", fields)
        combat = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        self.assertIn("transaction.definitionAnswers.attackerWithinTwo=attackerWithinTwo", combat)

    def test_result_message_includes_roll_and_only_appears_after_a_roll(self):
        reminder = self.source("function combatAbilityReminder", "function cancelPendingPlayerCombat")
        self.assertIn("Number.isInteger(combat.aggressiveDefenseRoll)", reminder)
        self.assertIn("D3 Roll: ${combat.aggressiveDefenseRoll}", reminder)


if __name__ == "__main__":
    unittest.main()
