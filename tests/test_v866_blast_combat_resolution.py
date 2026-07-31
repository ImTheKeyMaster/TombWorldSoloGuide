import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class BlastCombatResolutionTests(unittest.TestCase):
    def source(self, start, end):
        return APP[APP.index(start):APP.index(end, APP.index(start))]

    def test_locked_multi_profile_starts_a_fresh_roll_for_each_target(self):
        wizard = self.source("function showNpoAttackWizard", "function renderRoster")
        self.assertIn("else if(locked&&!resumeGuided)startAutomaticCombat();", wizard)
        self.assertIn("state.lastActivation={...state.lastActivation,combatDraft:null};", wizard)
        self.assertIn("state.npoAttackTargetId=state.weaponRuleResolution.currentTargetId", wizard)

    def test_each_npo_blast_target_is_damaged_before_sequence_advances(self):
        wizard = self.source("function showNpoAttackWizard", "function renderRoster")
        damage = wizard.index("applyNpoAttackDamage(n,target,summary);")
        advance = wizard.index("advanceMultiTargetAttackSequence(queue,target.id,summary)")
        self.assertLess(damage, advance)

    def test_invalid_targets_are_skipped_before_rendering_combat(self):
        wizard = self.source("function showNpoAttackWizard", "function renderRoster")
        self.assertIn("if(!target&&state.weaponRuleResolution?.currentTargetId)", wizard)
        self.assertIn("skipReason:'Target is no longer on the battlefield.'", wizard)

    def test_cancel_clears_blast_sequence_and_dice_draft(self):
        wizard = self.source("function showNpoAttackWizard", "function renderRoster")
        self.assertIn("state.lastActivation={...state.lastActivation,combatDraft:null};", wizard)
        self.assertIn("if(sequence){state.weaponRuleResolution=null;state.npoAttackTargetId=null;}", wizard)

    def test_player_cancel_discards_pending_blast_results(self):
        combat = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        self.assertIn("stage[listKey]=[];", combat)
        self.assertIn("stage[legacyKey]=null;", combat)
        self.assertIn("state.weaponRuleResolution=null;", combat)

    def test_missing_locked_profile_returns_without_stale_sequence(self):
        player = self.source("function showPlayerCombatResolution", "function previewPendingPlayerAttack")
        npo = self.source("function showNpoAttackWizard", "function renderRoster")
        self.assertIn("showMultiTargetProfileRecovery('player',()=>{state.weaponRuleResolution=null;", player)
        self.assertIn("showMultiTargetProfileRecovery('npo',()=>{state.weaponRuleResolution=null;state.npoAttackTargetId=null;", npo)

    def test_single_target_path_remains_automatic(self):
        wizard = self.source("function showNpoAttackWizard", "function renderRoster")
        self.assertIn("else if(availableProfiles.length===1&&!resumeGuided)startAutomaticCombat();", wizard)


if __name__ == "__main__":
    unittest.main()
