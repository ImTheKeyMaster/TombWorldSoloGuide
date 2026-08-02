import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
INDEX=(ROOT/'index.html').read_text()
WORKER=(ROOT/'service-worker.js').read_text()
README=(ROOT/'README.md').read_text()

class GuidedWeaponRuleTests(unittest.TestCase):
    def test_01_version_850(self):
        self.assertIn("const APP_VERSION = '8.6.20';",APP); self.assertIn("const APP_VERSION = '8.6.20';",WORKER); self.assertIn('V8.6.20',INDEX)
    def test_02_no_manual_heading(self): self.assertNotIn('<strong>Manual tabletop resolution</strong>',APP)
    def test_03_no_generic_core_instruction(self): self.assertNotIn('using the Core rules and confirm any required tabletop',APP)
    def test_04_to_07_piercing_crits(self):
        self.assertIn('function effectiveDefenseDiceCount',APP); self.assertIn("weaponRuleValue(profile,'piercing-crits')",APP); self.assertIn("die.retained&&die.kind==='crit'",APP); self.assertIn('Math.max(0,Number(baseDice||0)-reduction)',APP)
        self.assertLess(APP.index('applySevereToAttackDice(retainedDice,profile)'),APP.index('function effectiveDefenseDiceCount'))
    def test_08_to_11_stun(self):
        self.assertIn('function applyStunForAttack',APP); self.assertIn("amount:-1,expires:'end-of-target-next-activation'",APP); self.assertIn('modifiers.some(modifier=>modifier.id===id)',APP); self.assertIn('sourceAttackId',APP)
    def test_12_13_seek_light(self):
        self.assertIn('Is the target visible and using Light terrain for cover?',APP); self.assertIn('It does not remove a cover save.',APP); self.assertIn("if(target?.order!=='Conceal')",APP); self.assertIn('seekLightAnswer',APP)
    def test_14_to_16_blast(self):
        self.assertIn('including friendly operatives',APP); self.assertIn("ruleId==='blast'?[...playerTargets,...npoTargets]",APP); self.assertIn("secondaryTargetIds:orderedTargetIds.slice(1)",APP)
    def test_17_to_21_torrent_and_secondary_attacks(self):
        self.assertIn("ruleId==='torrent'&&attackerSide==='npo'",APP); self.assertIn('completedTargetIds',APP); self.assertIn('currentSequenceIndex',APP); self.assertIn('totalSequences',APP)
    def test_22_to_24_shock(self):
        self.assertIn('function resolveShockCriticalStrike',APP); self.assertLess(APP.index("die.retained&&die.kind==='hit'",APP.index('function resolveShockCriticalStrike')),APP.index("die.retained&&die.kind==='crit'",APP.index('function resolveShockCriticalStrike'))); self.assertNotIn('Shock applied: the defender rolls',APP)
    def test_25_to_28_persistence_and_idempotence(self):
        self.assertIn('merged.weaponRuleResolution',APP); self.assertIn('createWeaponRuleResolution({activationId:',APP); self.assertIn('advanceMultiTargetAttackSequence',APP); self.assertIn('new Set([...(normalized.completedTargetIds||[])',APP)
    def test_29_30_back_and_close(self):
        self.assertIn('id="secondaryTargetsBack">Back',APP); self.assertIn('data-close>Close Guide',APP); self.assertIn('save();onContinue(state.weaponRuleResolution)',APP)
    def test_31_registered_modes(self):
        for rule in ('severe','piercing-crits','stun','seek-light','blast','torrent','shock','piercing','lethal','accurate'): self.assertIn(f"{rule}:{{mode:" if '-' not in rule else f"'{rule}':{{mode:",APP)
    def test_32_release_notes_and_accessibility(self):
        self.assertIn('## v8.6.20',README); self.assertIn('aria-live="polite"',APP); self.assertIn('data-weapon-rule-target',APP); self.assertIn('role="status"',APP)

if __name__=='__main__': unittest.main()
