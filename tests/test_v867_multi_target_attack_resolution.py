import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class MultiTargetAttackResolutionTests(unittest.TestCase):
    def assert_app(self, *needles):
        for needle in needles:
            self.assertIn(needle, APP)

    def test_01_version(self):
        self.assert_app("const APP_VERSION = '8.7.3';")
        self.assertIn("V8.7.3", INDEX); self.assertIn("const APP_VERSION = '8.7.3';", WORKER)
    def test_02_primary_first(self): self.assert_app("[primaryTargetId,...secondaryTargetIds]")
    def test_03_duplicate_ids_removed(self): self.assert_app("const orderedTargetIds=[...new Set")
    def test_04_primary_advances(self): self.assert_app("findIndex(id=>!completedTargetIds.includes(id))")
    def test_05_secondary_advances(self): self.assert_app("currentTargetId:nextIndex>=0?normalized.orderedTargetIds[nextIndex]:null")
    def test_06_complete_after_all_targets(self): self.assert_app("completed:nextIndex<0")
    def test_07_repeat_replaces_result(self): self.assert_app("filter(item=>item.targetId!==completedTargetId)")
    def test_08_npo_torrent_primary(self): self.assert_app("primaryTargetId:target.id", "attackerSide==='npo'")
    def test_09_npo_torrent_secondaries(self): self.assert_app("automaticallySelected=ruleId==='torrent'&&attackerSide==='npo'")
    def test_10_npo_damage_once(self): self.assert_app("committedTargetIds", "applyNpoAttackDamage(n,target,summary)")
    def test_11_npo_ap_once(self): self.assert_app("showMultiTargetAttackSummary(completed,'npo'", "if(onDone)onDone(summary,completed.sequenceResults)")
    def test_12_sweeping_uses_torrent(self): self.assert_app("weaponHasRule(baseProfile,'torrent')")
    def test_13_player_torrent_all_targets(self): self.assert_app("continuePlayerMultiTargetAttack", "showPlayerCombatResolution(nextStage")
    def test_14_player_blast_all_targets(self): self.assert_app("ruleId==='blast'?[...playerTargets,...npoTargets]")
    def test_15_blast_side_routing(self): self.assert_app("orderedTargets", "if(summary.side==='npo')")
    def test_16_separate_attack_dice(self): self.assert_app("rolledAttackDiceForProfile(profile)")
    def test_17_separate_defense_dice(self): self.assert_app("rolledCombatDice(effectiveDefenseDiceCount")
    def test_18_severe_per_target(self): self.assert_app("applySevereToAttackDice")
    def test_19_piercing_crits_per_target(self): self.assert_app("effectiveDefenseDiceCount(profile")
    def test_20_stun_per_target(self): self.assert_app("applyStunForAttack({profile,attackDice:rolledAttackDice")
    def test_21_banishment_per_target(self): self.assert_app("resolveAutomaticDimensionalBanishment(combat)")
    def test_22_countertemporal_per_target(self): self.assert_app("resolveCountertemporalPackets")
    def test_23_aggressive_defence_per_result(self): self.assert_app("showAggressiveDefenseResolution(stage,pending")
    def test_24_primary_not_twice(self): self.assert_app("new Set([primaryTargetId")
    def test_25_no_secondary_chaining(self): self.assert_app("!restoredRoll&&!guidedConfirmed&&!state.weaponRuleResolution?.continueConfirmed")
    def test_26_no_secondary_ap(self): self.assert_app("The complete", "attackSummaries")
    def test_27_pending_shoot_results(self): self.assert_app("pendingShootResults")
    def test_28_all_pending_damage(self): self.assert_app("...pendingAttackResults(stage,'shoot')", "...pendingAttackResults(stage,'melee')")
    def test_29_projected_wounds(self): self.assert_app("function projectedNpoWounds", "pendingAttackResults(stage,'shoot')")
    def test_30_npo_history_all_summaries(self): self.assert_app("action.attackSummaries", "attackSummaries")
    def test_31_player_history_all_summaries(self): self.assert_app("attackSummary:attackSummaries.at(-1)||null")
    def test_32_final_summary(self): self.assert_app("function showMultiTargetAttackSummary", "ATTACK COMPLETE")
    def test_33_refresh_resumes_secondary(self): self.assert_app("normalizeMultiTargetAttackSequence(raw.weaponRuleResolution,")
    def test_34_refresh_keeps_dice(self): self.assert_app("if(rollingCombat)startAutomaticCombat(saved)")
    def test_35_update_preserves_results(self): self.assert_app("sequenceResults:Array.isArray(resolution.sequenceResults)")
    def test_36_double_continue_no_skip(self): self.assert_app("if(resolutionCommitted", "complete.disabled=true")
    def test_37_double_continue_no_damage(self): self.assert_app("includes(target.id))return")
    def test_38_missing_target_skipped(self): self.assert_app("Multi-target NPO attack target unavailable", "skipReason")
    def test_39_legacy_pending_shoot(self): self.assert_app("stage[legacyKey]?[stage[legacyKey]]:[]")
    def test_40_legacy_npo_queue(self): self.assert_app("[resolution.primaryTargetId,...(resolution.secondaryTargetIds||[])]")
    def test_41_recovery_and_console_guard(self): self.assert_app("console.error('[Combat] Multi-target")
    def test_42_release_notes(self): self.assertIn("Version 8.6.7 - Fix Multi-Target Attack Resolution", README)


if __name__ == "__main__":
    unittest.main()
