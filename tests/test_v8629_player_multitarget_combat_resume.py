import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
DEATHWATCH = (ROOT / "Player_Operatives" / "DeathWatch.json").read_text()


def function_source(name):
    start = APP.index(f"  function {name}")
    end = APP.find("\n  function ", start + 1)
    return APP[start:end if end >= 0 else None]


class V8629PlayerMultiTargetCombatResumeTests(unittest.TestCase):
    def test_01_active_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.7.4';", APP)
        self.assertIn("const APP_VERSION = '8.7.4';", WORKER)
        self.assertIn("V8.7.4", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.7.4"))

    def test_02_canonical_identity_is_deterministic_and_nonempty(self):
        source = function_source("canonicalPlayerWeaponIdentity")
        self.assertIn("operativeId", source)
        self.assertIn("attackType", source)
        self.assertIn("stableIndex", source)
        self.assertIn("weapon?.name", source)
        self.assertNotIn("random", source.lower())
        self.assertNotIn("date", source.lower())
        self.assertIn("profileId:explicitProfileId||`${weaponId}:default`", source)

    def test_03_explicit_weapon_and_profile_ids_are_preserved(self):
        source = function_source("canonicalPlayerWeaponIdentity")
        self.assertIn("normalizeStableId(weapon?.id)", source)
        self.assertIn("normalizeStableId(weapon?.profileKey)||normalizeStableId(weapon?.profileId)", source)
        self.assertIn("explicitWeaponId||fallbackWeaponId", source)

    def test_04_duplicate_names_are_disambiguated_by_position(self):
        source = function_source("canonicalPlayerWeaponIdentity")
        self.assertIn(":${stableIndex}:", source)

    def test_05_profile_and_restore_share_canonical_identity(self):
        profile = function_source("playerWeaponProfile")
        locked = function_source("lockedMultiTargetProfile")
        self.assertIn("canonicalPlayerWeaponIdentity", profile)
        self.assertIn("playerWeaponProfile(weapon,{operativeId,attackType:sequence.attackType,weaponIndex})", locked)

    def test_06_new_player_sequence_rejects_empty_identity(self):
        source = function_source("createWeaponRuleResolution")
        self.assertIn("attackerSide==='player'&&(!weaponId||!profileKey)", source)
        self.assertIn("return null", source)
        self.assertNotIn("weaponName===", source)

    def test_07_deathwatch_hellstorm_uses_runtime_fallback(self):
        self.assertIn('"id": "breacher"', DEATHWATCH)
        self.assertIn('"name": "Hellstorm bolt rifle"', DEATHWATCH)
        self.assertIn('"Torrent 1\\\""', DEATHWATCH)
        self.assertIn("player:${stablePlayerIdentityPart(operativeId,'operative')}", APP)

    def test_08_torrent_and_blast_mount_locked_combat(self):
        wizard = function_source("showPendingPlayerAttackWizard")
        combat = function_source("showPlayerCombatResolution")
        self.assertIn("weaponHasRule(profile,'blast')", wizard)
        self.assertIn("weaponHasRule(profile,'torrent')", wizard)
        self.assertIn("resumeCombatAfterWeaponRuleCheck", wizard)
        self.assertIn("lockedMultiTargetProfile", combat)
        self.assertIn("locked?.profile", combat)

    def test_09_resume_guard_and_rapid_continue_protection_remain(self):
        resume = function_source("resumeCombatAfterWeaponRuleCheck")
        secondary = function_source("showSecondaryTargetCheck")
        combat = function_source("showPlayerCombatResolution")
        self.assertIn("requestAnimationFrame", resume)
        self.assertIn("combatResults", resume)
        self.assertIn("showCombatResumeRecovery", resume)
        self.assertIn("event.currentTarget.disabled=true", secondary)
        self.assertIn("if(rollStarted)return", combat)

    def test_10_sequence_progress_and_commit_state_are_persisted(self):
        normalize = function_source("normalizeMultiTargetAttackSequence")
        advance = function_source("advanceMultiTargetAttackSequence")
        self.assertIn("completedTargetIds", normalize)
        self.assertIn("committedTargetIds", normalize)
        self.assertIn("sequenceResults", normalize)
        self.assertIn("findIndex(id=>!completedTargetIds.includes(id))", advance)

    def test_11_legacy_identity_recovers_only_an_unambiguous_match(self):
        source = function_source("normalizeLegacyPlayerMultiTargetIdentity")
        self.assertIn("matches.length!==1", source)
        self.assertIn("weaponName", source)
        self.assertIn("profileName", source)
        self.assertIn("state.weaponRuleResolution=normalized", source)
        self.assertNotIn("secondaryTargetIds=[]", source)

    def test_12_ambiguous_legacy_state_returns_to_selection_without_combat(self):
        recovery = function_source("showLegacyPlayerWeaponRecovery")
        combat = function_source("showPlayerCombatResolution")
        self.assertIn("Weapon selection must be confirmed", recovery)
        self.assertIn("No dice or damage were committed", recovery)
        self.assertIn("legacyIdentity.status==='ambiguous'", combat)
        self.assertIn("state.weaponRuleResolution=null", combat)
        self.assertIn("preferredTargetId", combat)
        self.assertLess(combat.index("legacyIdentity.status==='ambiguous'"), combat.index("runAutomaticCombatRolls"))

    def test_13_primary_and_secondary_targets_are_distinct_and_sequential(self):
        create = function_source("createWeaponRuleResolution")
        advance = function_source("advanceMultiTargetAttackSequence")
        self.assertIn("new Set([primaryTargetId,...secondaryTargetIds]", create)
        self.assertIn("currentSequenceIndex:0", create)
        self.assertIn("currentTargetId:orderedTargetIds[0]", create)
        self.assertIn("currentTargetId:nextIndex>=0", advance)

    def test_14_player_ap_and_single_target_paths_are_unchanged(self):
        wizard = function_source("showPendingPlayerAttackWizard")
        self.assertIn("const weaponControl=weapons.length===1", wizard)
        self.assertIn("if(!ruleId){proceed();return;}", wizard)
        self.assertNotIn("apl", function_source("canonicalPlayerWeaponIdentity").lower())

    def test_15_npo_lock_path_is_unchanged(self):
        locked = function_source("lockedMultiTargetProfile")
        npo = locked[:locked.index("const operativeId=")]
        self.assertIn("npoWeapon(definition,sequence.weaponId)", npo)
        self.assertIn("weaponProfiles(weapon).map(canonicalAttackProfile)", npo)

    def test_16_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_17_release_notes_are_present(self):
        self.assertIn("Version 8.6.29 - Fix Player Multi-Target Combat Resume", README)
        self.assertIn("safe recovery for older pending combat state", README)


if __name__ == "__main__":
    unittest.main()
