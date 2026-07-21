#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class UnifiedPlayerCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()
        cls.css = (ROOT / 'styles.css').read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_shooting_and_melee_share_dedicated_resolution_screen(self):
        wizard = self.source('function showPendingPlayerAttackWizard', 'function showPlayerCombatResolution')
        resolution = self.source('function showPlayerCombatResolution', 'function previewPendingPlayerAttack')
        self.assertIn('showPlayerCombatResolution(stage,attackType', wizard)
        self.assertIn('dedicated-combat-screen', resolution)
        self.assertIn("attackType==='shoot'?'Shooting':'Melee'", resolution)
        self.assertEqual(self.app.count('function showPlayerCombatResolution'), 1)

    def test_resolution_opens_at_top_and_starts_attack_then_defense(self):
        resolution = self.source('function showPlayerCombatResolution', 'function previewPendingPlayerAttack')
        shared = self.source('function runAutomaticCombatRolls', 'function retainedDiceTotals')
        self.assertIn("window.scrollTo({top:0,left:0,behavior:'auto'})", resolution)
        self.assertIn('modal.scrollTop=0', resolution)
        self.assertIn('runAutomaticCombatRolls', resolution)
        self.assertLess(shared.index('ATTACK DICE'), shared.index('DEFENSE DICE'))

    def test_animated_and_restored_continue_timing(self):
        display = self.source('function displayPendingPlayerCombat', 'function npoBehavior')
        self.assertIn('let visualComplete=!animate', display)
        self.assertIn('if(animate)settleCombatDice', display)
        self.assertIn('button.disabled=false', display)
        wizard = self.source('function showPendingPlayerAttackWizard', 'function showPlayerCombatResolution')
        self.assertIn('{result:draft,animate:false}', wizard)

    def test_removed_ui_and_summary(self):
        for text in ('SHOOTING SEQUENCE','FIGHT SEQUENCE','Skip Melee','Confirm Player Activation'):
            self.assertNotIn(text, self.app)
        resolver = self.source('function resolvePendingPlayerAttacks', 'function applyPendingPlayerDamage')
        self.assertIn('applyPendingPlayerDamage(stage)', resolver)
        self.assertNotIn('showPlayerActivationConfirmation', self.app)

    def test_footer_and_transactional_damage(self):
        resolution = self.source('function showPlayerCombatResolution', 'function previewPendingPlayerAttack')
        self.assertIn('id="cancelPendingAttack">Cancel</button>', resolution)
        self.assertIn('id="continuePendingAttack" disabled>Continue</button>', resolution)
        apply_damage = self.source('function applyPendingPlayerDamage', 'function completePlayerActivation')
        self.assertIn('if(!pending||pending.committed)continue', apply_damage)
        self.assertIn('pending.committed=true', apply_damage)

    def test_responsive_layout_has_no_fixed_content_height(self):
        self.assertIn('.dedicated-combat-screen', self.css)
        self.assertIn('@media(max-width:600px)', self.css)
        self.assertNotIn('.dedicated-combat-screen{height:', self.css)

if __name__ == '__main__':
    unittest.main()
