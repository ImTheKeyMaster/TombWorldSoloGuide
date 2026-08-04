import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()
EVENT_EFFECTS = (ROOT / 'event-effects.js').read_text()


def function_source(name):
    start = APP.index(f'function {name}')
    parenthesis = APP.index('(', start)
    paren_depth = 0
    brace = None
    for index in range(parenthesis, len(APP)):
        if APP[index] == '(':
            paren_depth += 1
        elif APP[index] == ')':
            paren_depth -= 1
        elif APP[index] == '{' and paren_depth == 0:
            brace = index
            break
    if brace is None:
        raise AssertionError(f'Unable to locate body for {name}')
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(APP)):
        char = APP[index]
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return APP[start:index + 1]
    raise AssertionError(f'Unable to extract {name}')


def severe(dice, profile):
    script = '\n'.join([
        function_source('weaponHasRule'),
        function_source('applySevereToAttackDice'),
        f"process.stdout.write(JSON.stringify(applySevereToAttackDice({json.dumps(dice)},{json.dumps(profile)})));",
    ])
    result = subprocess.run(['node', '-e', script], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


class SevereWeaponRuleTests(unittest.TestCase):
    def test_version_850_is_consistent_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.34';", APP)
        self.assertIn("const APP_VERSION = '8.6.34';", WORKER)
        self.assertIn('V8.6.34', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.34'))
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.34', INDEX)
        self.assertNotIn('8.4.2', APP + INDEX + WORKER)
        self.assertIn('## v8.6.25', README)

    def test_rule_detection_uses_ids_then_rules_fallback(self):
        die = [{'value': 4, 'kind': 'hit', 'retained': True}]
        self.assertTrue(severe(die, {'ruleIds': ['SeVeRe']})['applied'])
        self.assertTrue(severe(die, {'rules': [' Severe ']})['applied'])
        helper = function_source('weaponHasRule')
        self.assertLess(helper.index('ruleIds'), helper.index('rules'))

    def test_one_normal_is_converted_without_mutating_value_or_count(self):
        dice = [{'value': 4, 'kind': 'hit', 'retained': True}]
        result = severe(dice, {'ruleIds': ['severe']})
        self.assertTrue(result['applied'])
        self.assertEqual(0, result['convertedIndex'])
        self.assertEqual(1, len(result['dice']))
        self.assertEqual(4, result['dice'][0]['value'])
        self.assertEqual('crit', result['dice'][0]['kind'])
        self.assertEqual('hit', result['dice'][0]['originalKind'])
        self.assertTrue(result['dice'][0]['severeConverted'])
        self.assertEqual('hit', dice[0]['kind'])

    def test_several_normals_convert_exactly_one_and_reapply_is_idempotent(self):
        dice = [{'value': value, 'kind': 'hit', 'retained': True} for value in (3, 4, 5)]
        first = severe(dice, {'rules': ['Severe']})
        second = severe(first['dice'], {'rules': ['Severe']})
        self.assertEqual(1, sum(d['kind'] == 'crit' for d in first['dice']))
        self.assertEqual(2, sum(d['kind'] == 'hit' for d in first['dice']))
        self.assertFalse(second['applied'])
        self.assertEqual(-1, second['convertedIndex'])
        self.assertEqual(first['dice'], second['dice'])

    def test_natural_or_lethal_critical_and_all_misses_do_not_convert(self):
        natural = severe([
            {'value': 6, 'kind': 'crit', 'retained': True},
            {'value': 4, 'kind': 'hit', 'retained': True},
        ], {'ruleIds': ['severe']})
        lethal = severe([
            {'value': 5, 'kind': 'crit', 'retained': True},
            {'value': 4, 'kind': 'hit', 'retained': True},
        ], {'rules': ['Severe', 'Lethal 5+']})
        misses = severe([{'value': 2, 'kind': 'miss', 'retained': False}], {'ruleIds': ['severe']})
        self.assertFalse(natural['applied'])
        self.assertFalse(lethal['applied'])
        self.assertFalse(misses['applied'])

    def test_shared_roll_prepares_accurate_before_severe_and_restores_defensively(self):
        roller = function_source('rolledAttackDiceForProfile')
        shared = function_source('runAutomaticCombatRolls')
        self.assertLess(roller.index('accurate'), roller.index('applySevereToAttackDice'))
        self.assertIn("automatic:'Accurate 1'", roller)
        self.assertIn('applySevereToAttackDice(retainSuccessfulDice(rolledAttackDice),profile).dice', shared)
        self.assertIn(': rolledAttackDiceForProfile(profile)', shared)
        self.assertNotIn('profile.accurate\n      ?', shared)

    def test_severe_is_resolved_before_cancellation_damage_and_persistence(self):
        shared = function_source('runAutomaticCombatRolls')
        player = function_source('previewPendingPlayerAttack')
        npo = function_source('showNpoAttackWizard')
        self.assertIn('onComplete(attackDice,defenseDice)', shared)
        self.assertIn('resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile)', player)
        self.assertIn('result.rolledAttackDice=diceDraft.attackDice.map', player)
        self.assertIn('stage[`${attackType}CombatDraft`]=resolvedResult', player)
        self.assertIn('resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile)', npo)
        self.assertIn('combatDraft:resolvedCombat', npo)
        self.assertIn('damage:resolution.damage', npo)

    def test_player_and_npo_shooting_and_melee_share_the_severe_path(self):
        player = function_source('showPlayerCombatResolution')
        npo = function_source('showNpoAttackWizard')
        self.assertIn("attackType==='shoot'?'Shooting':'Melee'", player)
        self.assertIn('runAutomaticCombatRolls({container:screen.dice,profile', player)
        self.assertIn("action?.includes('Fight')?'melee':'shoot'", npo)
        self.assertIn('runAutomaticCombatRolls({container:screen.dice,profile', npo)
        self.assertIn('canonicalAttackProfile(availableProfiles[profileIndex])', npo)
        self.assertIn('playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex})', player)

    def test_profiles_preserve_rules_ids_piercing_lethal_and_my_will_be_done(self):
        canonical = function_source('canonicalAttackProfile')
        player = function_source('playerWeaponProfile')
        self.assertIn('rules:[...(profile?.rules||[])]', canonical)
        self.assertIn('ruleIds:[...(profile?.ruleIds||[])]', canonical)
        self.assertIn('rules:[...(weapon?.rules||[])]', player)
        self.assertIn('ruleIds:[...(weapon?.ruleIds||[])]', player)
        self.assertIn('ap:Number(piercing?.[1]||0)', canonical)
        self.assertIn('critThreshold:Number(lethal?.[1]||6)', canonical)
        self.assertIn('profile.accurate=Math.max(1,Number(profile.accurate||0))', EVENT_EFFECTS)

    def test_manual_resolution_is_replaced_by_registered_rule_handlers(self):
        canonical = function_source('canonicalAttackProfile')
        self.assertNotIn('manualResolution', canonical)
        self.assertIn('WEAPON_RULE_HANDLERS', APP)
        self.assertNotIn('<strong>Manual tabletop resolution</strong>', APP)
        self.assertIn("rules:['Severe','Shock','Stun']", APP)
        self.assertIn("rules:['Piercing 1','Severe']", APP)

    def test_message_and_accessible_label_only_follow_a_conversion(self):
        message = function_source('severeAppliedHtml')
        die = function_source('dieHtml')
        render = function_source('renderCombatResolution')
        self.assertIn('dice.some(die=>die.severeConverted)', message)
        self.assertIn('Severe applied: one normal success became a critical success.', message)
        self.assertIn('Critical success, converted from a normal success by Severe. Rolled value ${d.value}.', die)
        self.assertIn('severeAppliedHtml(combat.attackDice,combat.severeApplied)', render)
        self.assertIn('role="status"', message)

    def test_saved_converted_die_restores_without_second_conversion_or_damage_commit(self):
        converted = severe([{'value': 4, 'kind': 'hit', 'retained': True}], {'ruleIds': ['severe']})['dice']
        restored = severe(json.loads(json.dumps(converted)), {'ruleIds': ['severe']})
        self.assertFalse(restored['applied'])
        self.assertTrue(restored['dice'][0]['severeConverted'])
        self.assertEqual(4, restored['dice'][0]['value'])
        npo = function_source('showNpoAttackWizard')
        player = function_source('previewPendingPlayerAttack')
        player_display = function_source('displayPendingPlayerCombat')
        self.assertIn('severeApplied:diceDraft.attackDice.some(die=>die.severeConverted)', player)
        self.assertIn('severeApplied:rolledAttackDice.some(die=>die.severeConverted)', npo)
        self.assertIn('if(sameCombat)displayCombat(saved,animateCombat)', npo)
        self.assertIn('if(resolutionCommitted', npo)
        self.assertIn('if(resolutionCommitted||stage[`${attackType}CombatDraft`]!==result)return', player_display)
        self.assertIn('resolutionCommitted=true', player_display)


if __name__ == '__main__':
    unittest.main()
