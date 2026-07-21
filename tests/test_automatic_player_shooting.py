#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AutomaticPlayerShootingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_player_and_npo_use_same_sequential_animation_path(self):
        player = self.source('function showPlayerCombatResolution', 'function previewPendingPlayerAttack')
        npo = self.source('function showNpoAttackWizard', 'function spinnerField')
        shared = self.source('function runAutomaticCombatRolls', 'function retainedDiceTotals')
        self.assertIn('runAutomaticCombatRolls', player)
        self.assertIn('runAutomaticCombatRolls', npo)
        self.assertEqual(shared.count('timer=setTimeout'), 1)
        self.assertIn('timer=settleCombatDice', shared)
        self.assertLess(shared.index('ATTACK DICE'), shared.index('DEFENSE DICE'))

    def test_shooting_calculates_and_persists_one_read_only_result(self):
        preview = self.source('function previewPendingPlayerAttack', 'function displayPendingPlayerCombat')
        display = self.source('function displayPendingPlayerCombat', 'function npoBehavior')
        self.assertIn('resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile)', preview)
        self.assertIn("stage[`${attackType}CombatDraft`]=result", preview)
        self.assertIn("state.combatState={side:'player',stage:{...stage}}", preview)
        self.assertIn('displaySharedCombatResult(result', display)
        shared_display = self.source('function displaySharedCombatResult', 'function settleCombatDice')
        self.assertIn('renderCombatResolution(combat', shared_display)

    def test_saved_shooting_result_is_restored_without_reroll(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function showPlayerCombatResolution')
        self.assertIn('{result:draft,animate:false}', wizard)
        resolution = self.source('function showPlayerCombatResolution', 'function previewPendingPlayerAttack')
        self.assertLess(resolution.index('if(result){'), resolution.index('runAutomaticCombatRolls'))
        self.assertIn('displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false)', resolution)

    def test_damage_and_incapacitation_are_applied_exactly_once(self):
        apply_damage = self.source('function applyPendingPlayerDamage', 'function completePlayerActivation')
        self.assertIn('if(!pending||pending.committed)continue', apply_damage)
        self.assertIn('pending.committed=true', apply_damage)
        self.assertIn('n.wounds=Math.max(0,pending.after)', apply_damage)
        self.assertIn('if(n.wounds===0)n.ready=false', apply_damage)

    def test_continue_enables_only_after_visible_result_settles(self):
        display = self.source('function displaySharedCombatResult', 'function settleCombatDice')
        self.assertIn('let visualComplete=!animate', display)
        self.assertIn('button.disabled=!visualComplete', display)
        self.assertIn('if(visualComplete&&onContinue)', display)
        shared = self.source('function runAutomaticCombatRolls', 'function retainedDiceTotals')
        preview = self.source('function previewPendingPlayerAttack', 'function displayPendingPlayerCombat')
        self.assertLess(shared.index('timer=settleCombatDice'), shared.index('onComplete(attackDice,defenseDice)'))
        self.assertIn('displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false)', preview)

if __name__ == '__main__':
    unittest.main()
