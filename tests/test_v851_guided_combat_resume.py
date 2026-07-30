import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


class GuidedCombatResumeTests(unittest.TestCase):
    def test_01_torrent_and_blast_share_fresh_resume_path(self):
        self.assertIn("function resumeCombatAfterWeaponRuleCheck", APP)
        self.assertIn("render:()=>showNpoAttackWizard", APP)
        self.assertIn("render:()=>showPlayerCombatResolution", APP)
        self.assertIn("requestAnimationFrame", APP)
        self.assertIn("finally{\n        weaponRuleResumePending=false", APP)
        self.assertIn("Guided weapon-rule combat screen render failed.", APP)

    def test_02_required_mount_is_checked_before_roll(self):
        check = "if(!combatResults||!completeButton||!screen?.dice?.isConnected)"
        self.assertIn(check, APP)
        self.assertNotIn("$('#combatResults').replaceChildren()", APP)
        self.assertLess(APP.index("const combatResults=$('#combatResults')", APP.index("const startAutomaticCombat=")), APP.index("combatResults.replaceChildren()", APP.index("const startAutomaticCombat=")))

    def test_03_fresh_dice_mount_is_passed_to_each_roll(self):
        self.assertIn("onMounted:mounted=>mounted.startAutomaticCombat(null,true)", APP)
        self.assertIn("onMounted:mounted=>mounted.startRoll()", APP)
        self.assertIn("return {...screen,startAutomaticCombat}", APP)
        self.assertIn("return {...screen,startRoll}", APP)
        self.assertIn("else if(availableProfiles.length===1&&!resumeGuided)startAutomaticCombat()", APP)

    def test_04_guided_answers_and_secondary_targets_are_persisted(self):
        self.assertIn("secondaryTargetIds", APP)
        self.assertIn("tabletopCheckConfirmed:confirmation.checked", APP)
        self.assertIn("seekLightAnswer", APP)
        self.assertIn("input.checked=sameStep", APP)
        self.assertIn(".filter(id=>id!==primaryTargetId)", APP)

    def test_05_sequences_are_separate_and_completed_targets_are_idempotent(self):
        self.assertIn("function advanceWeaponRuleResolution", APP)
        self.assertIn("new Set([...(resolution.completedTargetIds||[]),completedTargetId])", APP)
        self.assertIn("targets.find(id=>!completed.includes(id))", APP)
        self.assertIn("state.weaponRuleResolution.currentTargetId", APP)

    def test_06_continue_is_guarded_against_repeated_clicks(self):
        self.assertIn("let weaponRuleResumePending=false", APP)
        self.assertIn("event.currentTarget.disabled=true", APP)
        self.assertIn("continueConfirmed:true", APP)
        self.assertIn("if(rollStarted)return", APP)
        self.assertIn("if(resolutionCommitted", APP)

    def test_07_damage_waits_for_continue_and_is_committed_once(self):
        self.assertIn("Damage is applied exactly once when you Continue.", APP)
        self.assertIn("if(resolutionCommitted", APP)
        self.assertIn("if(stage[`${attackType}CombatDraft`]===result)onResolved(result)", APP)

    def test_08_visible_recovery_replaces_uncaught_missing_dom_failure(self):
        self.assertIn("function showCombatResumeRecovery", APP)
        self.assertIn("Combat could not resume", APP)
        self.assertIn("No dice or damage were committed.", APP)
        self.assertIn("Return to Combat", APP)
        self.assertIn("console.error('[Combat]", APP)

    def test_09_close_back_and_refresh_state_are_supported(self):
        self.assertIn('data-close>Close Guide', APP)
        self.assertIn('id="secondaryTargetsBack">Back', APP)
        self.assertIn("merged.weaponRuleResolution", APP)
        self.assertIn("completedTargetIds:normalizeIdList", APP)
        self.assertIn("rolling:true", APP)

    def test_10_seek_light_can_chain_into_secondary_target_guidance(self):
        self.assertIn("onContinue:selectSecondaryTargets", APP)
        self.assertIn("weaponHasRule(baseProfile,'seek-light')", APP)
        self.assertIn("weaponHasRule(profile,'seek-light')", APP)
        self.assertIn("weaponHasRule(baseProfile,'blast')", APP)
        self.assertIn("weaponHasRule(profile,'torrent')", APP)
        self.assertIn("const weaponIndex=Number(weaponSelect.value)", APP)
        self.assertIn("const moreThanEight=Boolean($('#darkOfTombDistance')?.checked)", APP)

    def test_11_version_851_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.5.1';", APP)
        self.assertIn("const APP_VERSION = '8.5.1';", WORKER)
        self.assertIn("V8.5.1", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.5.1"))
        self.assertIn("## v8.5.1", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.5.1", INDEX)


if __name__ == "__main__":
    unittest.main()
