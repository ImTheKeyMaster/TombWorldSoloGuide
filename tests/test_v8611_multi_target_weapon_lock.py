import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class V8611MultiTargetWeaponLockTests(unittest.TestCase):
    def assert_app(self, *needles):
        for needle in needles:
            self.assertIn(needle, APP)

    def test_01_version(self):
        self.assertIn("const APP_VERSION = '8.6.24';", APP)
        self.assertIn("const APP_VERSION = '8.6.24';", WORKER)
        self.assertIn("V8.6.24", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.24"))

    def test_02_sequence_stores_stable_profile(self):
        self.assert_app("weaponId,weaponName,profileKey,profileName,weaponRules:[...weaponRules]", "lockedMultiTargetProfile")

    def test_03_all_targets_restore_the_lock(self):
        self.assert_app("locked?availableProfiles.findIndex", "const weapon=locked?.weapon||weapons[weaponIndex]")

    def test_04_secondary_does_not_select_again(self):
        self.assert_app("availableProfiles.length>1&&!locked", "sequence?.orderedTargetIds?.length>1")

    def test_05_each_target_gets_fresh_dice(self):
        self.assert_app("rolledAttackDiceForProfile(profile)", "rolledCombatDice(effectiveDefenseDiceCount")

    def test_06_sequence_completion_and_ap_are_deferred(self):
        self.assert_app("completed:nextIndex<0", "if(onDone)onDone(summary,completed.sequenceResults)")

    def test_07_rules_supported_for_both_sides(self):
        self.assert_app("weaponHasRule(baseProfile,'torrent')", "weaponHasRule(baseProfile,'blast')")
        self.assert_app("attackerSide:'npo'", "attackerSide:'player'")

    def test_08_persistence_and_legacy_normalization(self):
        self.assert_app("normalizeMultiTargetAttackSequence(raw.weaponRuleResolution", "legacyCombatProfile?.weaponId")
        self.assert_app("sequenceResults:Array.isArray(resolution.sequenceResults)")

    def test_09_visible_recovery_preserves_results(self):
        self.assert_app("Attack profile unavailable", "Completed target results were preserved.")
        self.assertNotIn("state.weaponRuleResolution=null", APP[APP.index("function showMultiTargetProfileRecovery"):APP.index("function weaponRuleTargetOption")])

    def test_10_idempotent_transactions(self):
        self.assert_app("committedTargetIds", "resolutionCommitted||stage", "if(rollStarted)return")

    def test_10a_npo_lock_does_not_use_current_loadout(self):
        locked = APP[APP.index("function lockedMultiTargetProfile"):APP.index("function showMultiTargetProfileRecovery")]
        self.assertIn("npoWeapon(definition,sequence.weaponId)", locked)
        self.assertIn("weaponProfiles(weapon).map(canonicalAttackProfile)", locked)
        self.assertNotIn("npoAttackProfiles(attacker", locked)

    def test_10b_sequence_keeps_weapon_and_profile_names_distinct(self):
        self.assert_app("weaponName:profile?.weaponName", "profileName:profile?.name")
        self.assert_app("weaponName:profile.weaponName", "profileName:profile.profileName")

    def test_11_single_target_selection_unchanged(self):
        self.assert_app("const weaponControl=weapons.length===1", "Select a weapon...")

    def test_12_save_version_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_13_release_notes(self):
        self.assertIn("Version 8.6.11 - Preserve Weapon Across Multi-Target Attacks", README)


if __name__ == "__main__":
    unittest.main()
