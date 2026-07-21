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
        player = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        npo = self.source('function showNpoAttackWizard', 'function spinnerField')
        shared = self.source('function runAutomaticCombatRolls', 'function retainedDiceTotals')
        self.assertIn('runAutomaticCombatRolls', player)
        self.assertIn('runAutomaticCombatRolls', npo)
        self.assertEqual(shared.count('timer=setTimeout'), 2)
        self.assertLess(shared.index('ATTACK DICE'), shared.index('DEFENSE DICE'))

    def test_shooting_calculates_and_persists_one_read_only_result(self):
        preview = self.source('function previewPendingPlayerAttack', 'function displayPendingPlayerCombat')
        display = self.source('function displayPendingPlayerCombat', 'function npoBehavior')
        self.assertIn('resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile)', preview)
        self.assertIn("damage:attackType==='shoot'?resolution.damage", preview)
        self.assertIn("stage[`${attackType}CombatDraft`]=result", preview)
        self.assertIn("state.combatState={side:'player',stage:{...stage}}", preview)
        self.assertIn('save();', preview)
        self.assertIn('renderCombatResolution(result', display)

    def test_saved_shooting_result_is_restored_without_reroll(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        restore = wizard.split('if(draft){', 1)[1]
        self.assertIn('displayPendingPlayerCombat', restore)
        self.assertIn("else if(attackType==='shoot'&&singleTarget)startAutomaticPlayerShooting()", restore)
        self.assertLess(restore.index('displayPendingPlayerCombat'), restore.index('startAutomaticPlayerShooting'))

    def test_damage_and_incapacitation_are_applied_exactly_once(self):
        apply_damage = self.source('function applyPendingPlayerDamage', 'function completePlayerActivation')
        self.assertIn('if(!pending||pending.committed)continue', apply_damage)
        self.assertIn('pending.committed=true', apply_damage)
        self.assertIn('n.wounds=Math.max(0,pending.after)', apply_damage)
        self.assertIn('if(n.wounds===0)n.ready=false', apply_damage)

    def test_shooting_has_no_manual_outcome_requirement(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        shooting_markup = wizard.split("attackType==='shoot'", 1)[1]
        self.assertIn('automaticPlayerCombat', shooting_markup)
        self.assertNotIn('Record Combat Outcome', wizard)
        self.assertNotIn("spinnerField('retainedNormal'", wizard)
        self.assertNotIn("spinnerField('retainedCritical'", wizard)

if __name__ == '__main__':
    unittest.main()
