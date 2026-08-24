#!/usr/bin/env python3
import unittest
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class Stage5FullPvpCombatTests(unittest.TestCase):
    def section(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_player_combat_requires_human_target_profile_and_legality(self):
        wizard = self.section("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        self.assertIn('id="combatTarget"', wizard)
        self.assertIn('id="playerWeaponSelect"', wizard)
        self.assertIn('id="playerTabletopTargetConfirmed"', wizard)
        self.assertIn("valid target for this shooting attack, including visibility, range", wizard)
        self.assertIn("within control range and is a valid target for this Fight action", wizard)
        self.assertIn("!target||!weapon||!tabletopConfirmed", wizard)
        self.assertIn("if(isPvpMode()&&!$('#playerTabletopTargetConfirmed')?.checked)return", wizard)
        self.assertIn("resetTabletopConfirmation", wizard)
        self.assertIn("if(!isPvpMode()&&singleTarget", wizard)

    def test_player_target_controls_use_necron_terminology_in_pvp(self):
        wizard = self.section("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        recovery = self.section("function showMultiTargetProfileRecovery", "function weaponRuleTargetOption")
        self.assertIn("const targetSideLabel=isPvpMode()?'Necron':'NPO'", wizard)
        self.assertIn("Target ${targetSideLabel}", wizard)
        self.assertIn("Select a target ${targetSideLabel}", wizard)
        self.assertIn("isPvpMode()?'Necron':'NPO'", recovery)

    def test_both_sides_use_specific_operative_dice_labels(self):
        player = self.section("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("attackerLabel:playerName(stage.playerOperativeId),defenderLabel:targetName", player)
        self.assertIn("requestDimensionalBanishment(result,playerName(stage.playerOperativeId))", APP)
        self.assertIn("attackerLabel:npoName(n),defenderLabel:targetName", npo)

    def test_attack_results_persist_before_the_defense_handoff(self):
        shared = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        player = self.section("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertLess(shared.index("isPvpMode()&&!rolledAttackDice&&onAttackComplete"), shared.index("effectiveDefenseDiceCount"))
        self.assertIn("rolling:true,attackType,targetId,targetName,weaponIndex,profile,attackDice", player)
        self.assertIn("rolling:true,attackType,targetId:target.id,targetName:targetName,profile,attackDice", npo)
        self.assertIn("if(committedAttackDice)screen.cancelButton.disabled=true", player)
        self.assertIn("if(rollingCombat)screen.cancelButton.disabled=true", npo)

    def test_committed_attack_resumes_without_another_attack_request(self):
        wizard = self.section("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        combat = self.section("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
        self.assertIn("draft.rolling", wizard)
        self.assertIn("committedAttackDice:draft.attackDice", wizard)
        self.assertIn("rolledAttackDice:committedAttackDice", combat)
        self.assertIn("rolledAttackDice", self.section("function runAutomaticCombatRolls", "function retainedDiceTotals"))

    def test_committed_defense_resumes_without_another_defense_request(self):
        wizard = self.section("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
        combat = self.section("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
        shared = self.section("function runAutomaticCombatRolls", "function retainedDiceTotals")
        self.assertIn("committedDefenseDice:draft.saveDice", wizard)
        self.assertIn("rolledDefenseDice:committedDefenseDice", combat)
        self.assertIn("saveDice:defenseDice.map", combat)
        self.assertLess(combat.index("saveDice:defenseDice.map"), combat.index("previewPendingPlayerAttack"))
        self.assertIn("rolledDefenseDice||await requestDefenseDice", shared)

    def test_pvp_necron_profile_change_invalidates_confirmation(self):
        wizard = self.section("function showNpoAttackWizard", "function spinnerField")
        profile_change = wizard.split("$('#npoCombatProfile')?.addEventListener", 1)[1]
        self.assertIn("tabletopTargetConfirmed:false", profile_change)
        self.assertIn("confirmation.checked=false", profile_change)
        self.assertIn("screen.continueButton.disabled=true", profile_change)

    def test_ai_guidance_and_torrent_auto_selection_are_solo_only(self):
        guidance = self.section("function npoCombatGuidanceHtml", "function recordedCombat")
        secondary = self.section("function showSecondaryTargetCheck", "function weaponRuleSequenceProgress")
        self.assertIn("if(isPvpMode())return ''", guidance)
        self.assertIn("!isPvpMode()&&ruleId==='torrent'&&attackerSide==='npo'", secondary)

    def test_shared_rules_and_transaction_guards_remain_in_use(self):
        resolver = self.section("function resolveRetainedCombat", "function aggressiveDefenseFields")
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        player_result = self.section("function displayPendingPlayerCombat", "function npoBehavior")
        for rule in ("criticalCancellations", "criticalVsNormal", "normalCancellations"):
            self.assertIn(rule, resolver)
        self.assertIn("if(resolutionCommitted", npo)
        self.assertIn("includes(target.id))return", npo)
        self.assertIn("if(resolutionCommitted||stage[`${attackType}CombatDraft`]!==result)return", player_result)

    def test_pvp_terminology_is_used_for_guided_necron_choices(self):
        shock = self.section("function showGuidedShockStep", "function weaponRuleHandler")
        npo = self.section("function showNpoAttackWizard", "function spinnerField")
        self.assertIn("the attacking Necron", shock)
        self.assertIn("isPvpMode()?'Necron':'NPO'", npo)

    def test_version_and_deferred_dice_work_are_unchanged(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        initiative = self.section("function rollInitiative", "function beginFirefight")
        self.assertNotIn("requestDiceResults", initiative)


if __name__ == "__main__":
    unittest.main()
