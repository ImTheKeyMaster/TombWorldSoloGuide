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


class V8610DirectTargetToCombatTests(unittest.TestCase):
    def setUp(self):
        self.confirm = section("function confirmNpoAttackTarget", "function openNpoCombat")
        self.entry = section("function openNpoCombat", "function renderNpoDecisionResult")
        self.render = section("function renderNpoDecisionResult", "async function completeNpoActivation")

    def test_01_version_displays_8610(self):
        self.assertIn("const APP_VERSION = '8.6.23';", APP)
        self.assertIn("const APP_VERSION = '8.6.23';", WORKER)
        self.assertIn("V8.6.23", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.23"))

    def test_02_confirm_target_immediately_opens_combat(self):
        self.assertIn("openNpoCombat(n,decision,[]", self.confirm)
        self.assertIn("showNpoAttackWizard(n,resolvedDice", self.entry)

    def test_03_confirm_does_not_render_readonly_intermediate_screen(self):
        self.assertNotIn("false,false,true,true", self.confirm)
        self.assertIn("if(attackRequired&&targetConfirmed&&!attackResolved)", self.render)

    def test_04_one_target_resolves_without_confirm_button(self):
        self.assertIn("eligibleTargetIds.length===1?`<button", self.render)
        self.assertIn('id="resolveNpoTarget">Resolve Combat', self.render)
        self.assertIn("eligibleTargetIds.length>1?`<button", self.render)

    def test_05_multiple_targets_still_require_selection(self):
        self.assertIn('<select id="npoPriorityTarget"', self.render)
        self.assertIn('id="confirmNpoTarget"', self.render)
        self.assertIn("targetControl.value", self.confirm)

    def test_06_selected_stable_operative_id_is_saved(self):
        self.assertIn("state.npoAttackTargetId=selectedTargetId", self.confirm)
        self.assertIn("save();", self.confirm)
        self.assertNotIn("playerTargetLabel(selectedTargetId)", self.confirm)

    def test_07_confirmation_spends_no_ap_and_rolls_no_dice(self):
        self.assertNotIn("remainingAp", self.confirm)
        self.assertNotIn("commitNpoAction", self.confirm)
        self.assertNotIn("rolledCombatDice", self.confirm)

    def test_08_shoot_and_fight_use_the_same_confirmation(self):
        self.assertIn("['shoot','fight'].includes(pendingAction.id)", self.confirm)

    def test_09_movement_follow_up_attacks_are_preserved(self):
        self.assertIn("followUpActionId:'shoot',guaranteesFollowUp:true", APP)
        self.assertIn("id:'dash-enable-shoot'", APP)
        self.assertIn("id:'charge-enable-fight'", APP)

    def test_10_multi_target_weapon_guidance_is_preserved(self):
        self.assertIn("weaponHasRule(baseProfile,'blast')?'blast'", APP)
        self.assertIn("weaponHasRule(baseProfile,'torrent')?'torrent'", APP)
        self.assertIn("ruleId==='torrent'&&attackerSide==='npo'", APP)

    def test_11_back_returns_to_unconfirmed_target_selection(self):
        self.assertIn("renderNpoDecisionResult(n,decision,resolvedDice,answers,false,false,true,false)", self.entry)
        self.assertNotIn("commitNpoAction", self.entry.split("},()=>{", 1)[1])

    def test_12_refresh_and_update_restore_the_correct_step(self):
        self.assertIn("Boolean(activation.targetConfirmed)", APP)
        self.assertIn("openNpoCombat(n,decision,dice,answers)", self.render)

    def test_13_rapid_double_taps_open_combat_once(self):
        self.assertIn("if(confirmTargetButton.disabled)return", self.render)
        self.assertIn("confirmTargetButton.disabled=true", self.render)
        self.assertIn("if(resolveTargetButton.disabled)return", self.render)
        self.assertIn("resolveTargetButton.disabled=true", self.render)

    def test_14_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_15_release_notes_are_present(self):
        self.assertIn("## v8.6.23", README)
        self.assertIn("Version 8.6.10 - Remove Redundant Target Confirmation Screen", README)


if __name__ == "__main__":
    unittest.main()
