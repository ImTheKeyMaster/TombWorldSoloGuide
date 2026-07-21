#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationPr7CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()

    def source(self, name, next_name):
        return self.app.split(f'function {name}(', 1)[1].split(f'function {next_name}(', 1)[0]

    def test_obsolete_sequence_panels_are_removed(self):
        self.assertNotIn('SHOOTING SEQUENCE', self.app)
        self.assertNotIn('FIGHT SEQUENCE', self.app)
        self.assertNotIn('attackSequenceSteps', self.app)
        self.assertIn('function weaponRulesHtml', self.app)

    def test_canonical_npo_profiles_are_consumed_for_each_action(self):
        profiles = self.source('npoAttackProfiles', 'canonicalAttackProfile')
        self.assertIn("attackType==='shoot'", profiles)
        self.assertIn('definition.rangedWeapons', profiles)
        self.assertIn('definition.meleeWeapons', profiles)
        wizard = self.source('showNpoAttackWizard', 'applyNpoAttackDamage')
        self.assertIn('npoAttackProfiles(n,attackType)', wizard)
        self.assertIn("id=\"npoCombatProfile\"", wizard)
        self.assertEqual(self.app.count('const npoDefinitions = {'), 1)

    def test_weapon_rules_and_critical_successes_are_recorded(self):
        self.assertIn("rules:[...(profile?.rules||[])]", self.app)
        recorded = self.source('recordedCombat', 'applyDimensionalBanishment')
        self.assertIn('criticalSuccesses', recorded)
        self.assertIn('critRemaining:', recorded)
        self.assertIn('normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical', self.app)
        for rule in ('Piercing 1', 'Punishing', 'Torrent 1"', 'Brutal', 'Blast 2"'):
            self.assertIn(rule, self.app)

    def test_player_shooting_uses_shared_automatic_combat(self):
        resolution = self.source('showPlayerCombatResolution', 'previewPendingPlayerAttack')
        preview = self.source('previewPendingPlayerAttack', 'displayPendingPlayerCombat')
        self.assertIn('runAutomaticCombatRolls', resolution)
        self.assertIn('showSharedCombatResolutionScreen', resolution)
        shared_screen = self.source('showSharedCombatResolutionScreen', 'displaySharedCombatResult')
        self.assertIn('dedicated-combat-screen', shared_screen)
        self.assertIn('previewPendingPlayerAttack(stage,attackType', resolution)
        self.assertIn('resolution.damage', preview)
        self.assertNotIn('Record Combat Outcome', self.app)

    def test_pack_defined_combat_abilities_have_follow_up_handlers(self):
        handlers = self.app.split('const combatAbilityHandlers = {', 1)[1].split('\n  };', 1)[0]
        self.assertIn("'dimensional-banishment'", handlers)
        self.assertIn("'aggressive-defence-construct'", handlers)
        reminder = self.source('combatAbilityReminder', 'showPendingPlayerAttackWizard')
        self.assertIn('criticalSuccesses:combat.critRemaining', reminder)
        self.assertIn('remaining wounds', reminder)
        self.assertIn('aggressiveDefenseDamage', reminder)
        self.assertIn('applyDimensionalBanishment', self.app)
        self.assertIn("total>combat.after?0:combat.after", self.app)

    def test_damage_and_incapacitation_use_one_recorded_outcome(self):
        recorded = self.source('recordedCombat', 'combatOutcomeFields')
        self.assertIn('after:Math.max(0,before-appliedDamage)', recorded)
        player_damage = self.source('applyPendingPlayerDamage', 'completePlayerActivation')
        self.assertIn('n.wounds=Math.max(0,pending.after)', player_damage)
        self.assertIn('if(n.wounds===0)n.ready=false', player_damage)
        npo_damage = self.source('applyNpoAttackDamage', 'showNpoAttackWizard')
        self.assertIn('state.playerWounds[target.id]=summary.after', npo_damage)
        self.assertIn('casualties.add(target.id)', npo_damage)

    def test_combat_state_and_legacy_saves_normalize(self):
        initial = self.app.split('const initialState = () => ({', 1)[1].split('\n  });', 1)[0]
        self.assertIn('combatState:null', initial)
        normalize = self.source('normalizeState', 'npoDefinition')
        self.assertIn('isRecord(raw.combatState)', normalize)
        self.assertIn('raw.roster', normalize)
        self.assertIn("raw.combatState.side==='player'", normalize)
        self.assertIn('combatDraft', self.app)
        self.assertIn('state.combatState=null', self.app)
        self.assertIn('shootCombatDraft', self.app)

    def test_mission_end_logic_was_not_added_by_combat_release(self):
        self.assertIn('missionState:', self.app)
        self.assertNotIn('postGame', self.app)

    def test_versions_are_synchronized(self):
        expected = '5.5.1'
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        self.assertIn(f"styles.css?v={expected}", (ROOT / 'index.html').read_text())
        self.assertIn(f"app.js?v={expected}", (ROOT / 'index.html').read_text())
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / 'service-worker.js').read_text())
        self.assertIn(f'## v{expected}', (ROOT / 'README.md').read_text())


if __name__ == '__main__':
    unittest.main()
