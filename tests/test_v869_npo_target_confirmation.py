import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class V869NpoTargetConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.confirm = section("function confirmNpoAttackTarget", "function renderNpoDecisionResult")
        self.render = section("function renderNpoDecisionResult", "async function completeNpoActivation")

    def test_01_version_8610_is_displayed(self):
        self.assertIn("const APP_VERSION = '8.6.31';", APP)
        self.assertIn("const APP_VERSION = '8.6.31';", WORKER)
        self.assertIn("V8.6.31", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.31"))

    def test_02_direct_shoot_yes_opens_selection(self): self.assertIn("resolveNpo(n,{...nextAnswers,action},nextHistory)", APP)
    def test_03_direct_shoot_confirmation_advances(self): self.assertIn("openNpoCombat(n,decision,[],state.lastActivation.answers||{})", self.confirm)
    def test_04_direct_fight_yes_opens_selection(self): self.assertIn("if(q.actionId==='fight')state.lastActivation.currentContext.hasValidFightTarget=true", APP)
    def test_05_direct_fight_confirmation_advances(self): self.assertIn("['shoot','fight'].includes(pendingAction.id)", self.confirm)
    def test_06_handler_reads_selector_value(self): self.assertIn("targetControl.value", self.confirm)
    def test_07_no_change_event_required(self): self.assertIn("confirmNpoAttackTarget(n,decision)", self.render)
    def test_08_stores_stable_id(self): self.assertIn("state.npoAttackTargetId=selectedTargetId", self.confirm)
    def test_09_does_not_store_wound_label(self): self.assertNotIn("playerTargetLabel(selectedTargetId)", self.confirm)
    def test_10_sets_target_confirmed(self): self.assertIn("targetConfirmed:true", self.confirm)
    def test_11_preserves_pending_shoot(self): self.assertIn("state.lastActivation={...activation", self.confirm)
    def test_12_preserves_pending_fight(self): self.assertNotIn("pendingAction:", self.confirm)
    def test_13_confirmation_spends_no_ap(self): self.assertNotIn("remainingAp", self.confirm)
    def test_14_confirmation_rolls_no_dice(self): self.assertNotIn("rolledCombatDice", self.confirm)
    def test_15_multiple_targets_have_selector(self): self.assertIn('<select id="npoPriorityTarget"', self.render)
    def test_16_single_target_uses_stable_state_id(self): self.assertIn("eligibleTargetIds.length===1)state.npoAttackTargetId=eligibleTargetIds[0]", self.render)
    def test_17_readonly_target_includes_wounds(self): self.assertIn("const targetName=state.npoAttackTargetId?playerTargetLabel", self.render)
    def test_18_invalid_target_has_visible_recovery(self): self.assertIn("That Player operative is no longer an eligible target. Select another target.", self.confirm)
    def test_19_missing_action_has_visible_recovery(self):
        recovery = section("function showNpoTargetRecovery", "function confirmNpoAttackTarget")
        self.assertIn("Target could not be confirmed", recovery)
        self.assertIn("No AP, dice, or damage were committed.", recovery)
    def test_20_back_direct_shoot_returns_to_question(self): self.assertIn("runNpoPrompt(n,0,previous.answers", APP)
    def test_21_back_direct_fight_clears_target(self): self.assertIn("state.npoAttackTargetId=null;state.npoAttackSummary=null", section("function backFromNpoAttackSelection", "function renderNpoMovementConfirmation"))
    def test_22_refresh_rebinds_confirm(self): self.assertIn("confirmTargetButton.onclick=", self.render)
    def test_23_update_restores_confirmed_state(self): self.assertIn("Boolean(activation.targetConfirmed)", APP)
    def test_24_repeated_taps_are_guarded(self):
        self.assertIn("if(confirmTargetButton.disabled)return", self.render)
        self.assertIn("confirmTargetButton.disabled=true", self.render)
    def test_25_shoot_after_reposition_preserved(self): self.assertIn("followUpActionId:'shoot',guaranteesFollowUp:true", APP)
    def test_26_shoot_after_dash_preserved(self): self.assertIn("id:'dash-enable-shoot'", APP)
    def test_27_fight_after_charge_preserved(self): self.assertIn("id:'charge-enable-fight'", APP)
    def test_28_blast_primary_preserved(self): self.assertIn("weaponHasRule(baseProfile,'blast')?'blast'", APP)
    def test_29_torrent_primary_preserved(self): self.assertIn("weaponHasRule(baseProfile,'torrent')?'torrent'", APP)
    def test_30_sweeping_primary_preserved(self): self.assertIn("ruleId==='torrent'&&attackerSide==='npo'", APP)
    def test_31_secondary_sequences_preserved(self): self.assertIn("advanceMultiTargetAttackSequence(queue,target.id,summary)", APP)
    def test_32_console_reference_error_fixed(self): self.assertIn("targetSide==='npo'?npoName(target):playerName(target.id)", APP)
    def test_33_save_version_unchanged(self): self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
    def test_34_release_notes_and_placeholder(self):
        self.assertIn("Version 8.6.9 - Fix NPO Target Confirmation", README)
        self.assertIn('<option value="" ${state.npoAttackTargetId?\'\':\'selected\'}>', self.render)


if __name__ == "__main__":
    unittest.main()
