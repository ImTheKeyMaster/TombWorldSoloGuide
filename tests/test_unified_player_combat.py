#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UnifiedPlayerCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_shooting_and_melee_share_automatic_layout_and_sequence(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        self.assertIn('<div id="automaticPlayerCombat"', wizard)
        self.assertNotIn("attackType==='shoot'?'<div id=", wizard)
        self.assertIn('startAutomaticPlayerCombat()', wizard)
        self.assertNotIn('playerCombatDiceFields()', wizard)
        self.assertNotIn("spinnerField('resolvedDamage'", wizard)

    def test_both_combat_types_use_automatic_retention_and_damage(self):
        preview = self.source('function previewPendingPlayerAttack', 'function displayPendingPlayerCombat')
        self.assertIn('resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile)', preview)
        self.assertIn('damage:resolution.damage', preview)
        self.assertIn('result.attackDice=result.rolledAttackDice', preview)
        self.assertIn('result.saveDice=result.rolledDefenseDice', preview)
        self.assertIn('result.recordedOutcome=false', preview)
        self.assertNotIn("if(attackType==='shoot')", preview)

    def test_animated_continue_waits_for_visual_settlement(self):
        settle = self.source('function settleCombatDice', 'function projectedNpoWounds')
        display = self.source('function displayPendingPlayerCombat', 'function npoBehavior')
        self.assertIn("classList.replace('animated-roll','settled')", settle)
        self.assertLess(settle.index("classList.replace('animated-roll','settled')"), settle.index('onSettled()'))
        self.assertIn('let visualComplete=!animate', display)
        self.assertIn('button.disabled=!visualComplete||', display)
        self.assertIn('if(!visualComplete||', display)
        self.assertLess(display.index('settleCombatDice(result,()=>'), display.index('button.disabled=false'))

    def test_restored_results_enable_continue_without_settle_delay(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        restore = wizard.split('if(draft){', 1)[1]
        display = self.source('function displayPendingPlayerCombat', 'function npoBehavior')
        self.assertIn('displayPendingPlayerCombat(stage,attackType,draft,onResolved,onCancel,false)', restore)
        self.assertIn('let visualComplete=!animate', display)
        self.assertIn('if(animate)settleCombatDice', display)

    def test_skipping_melee_cancels_the_shared_animation_timer(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function previewPendingPlayerAttack')
        self.assertIn("if($('#skipPendingMelee'))$('#skipPendingMelee').onclick=()=>{stopDiceAnimation();stopAutomaticRolls();onSkip();}", wizard)

    def test_damage_remains_transactional_and_single_application(self):
        apply_damage = self.source('function applyPendingPlayerDamage', 'function completePlayerActivation')
        self.assertIn('if(!pending||pending.committed)continue', apply_damage)
        self.assertIn('pending.committed=true', apply_damage)


if __name__ == '__main__':
    unittest.main()
