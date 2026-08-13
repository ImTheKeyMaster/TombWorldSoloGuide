import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class V868AttackBeforeMovementTests(unittest.TestCase):
    def test_01_version_is_displayed_consistently(self):
        self.assertIn("const APP_VERSION = '8.6.64';", APP)
        self.assertIn("const APP_VERSION = '8.6.64';", WORKER)
        self.assertIn('V8.6.64', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.64'))

    def test_02_shoot_check_precedes_reposition_intent(self):
        question = section('function npoActionQuestion', 'const npoQuestionIcons')
        self.assertIn('const availability=attackAvailabilityForMovementIntent(activation,movementInquiry)', question)
        self.assertIn('if(availability===null||availability===true)', question)

    def test_03_shoot_check_precedes_dash_intent(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        self.assertIn("id:'dash-enable-shoot'", movement)
        self.assertIn("followUpActionId:'shoot'", movement)

    def test_04_direct_shoot_wording(self):
        self.assertIn('Does this NPO currently have a Player operative it can Shoot without moving?', APP)

    def test_05_direct_shoot_helper(self):
        self.assertIn('Select Yes if it can make a shooting attack from its current position. Do not move the NPO.', APP)

    def test_06_shoot_yes_selects_target_flow(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn("if(q.actionId==='shoot')state.lastActivation.currentContext.hasValidShootTarget=true", prompt)
        self.assertIn('resolveNpo(n,{...nextAnswers,action},nextHistory)', prompt)

    def test_07_shoot_yes_does_not_commit_movement(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        yes = prompt[prompt.index('}else if(answer){'):prompt.index('else{', prompt.index('}else if(answer){'))]
        self.assertNotIn('commitNpoAction', yes)

    def test_08_shoot_yes_suppresses_reposition(self):
        self.assertIn('if(directAvailability===true)return directNpoAttackQuestion(n,action,directAvailability)', APP)

    def test_09_shoot_yes_suppresses_dash(self):
        self.assertIn('autoSelect:availability===true', APP)

    def test_10_shoot_no_records_explicit_false(self):
        self.assertIn("if(q.actionId==='shoot')state.lastActivation.currentContext.hasValidShootTarget=false", APP)

    def test_11_shoot_no_allows_reposition(self):
        self.assertIn('Can this NPO Reposition up to ${distance} and finish where it can Shoot?', APP)

    def test_12_shoot_no_is_not_reasked(self):
        self.assertIn('if(availability===null||availability===true)', APP)
        self.assertNotIn('if(!availability)', section('function npoActionQuestion', 'const npoQuestionIcons'))

    def test_13_fight_check_precedes_charge(self):
        self.assertIn("const chargeIntent=id==='charge'&&fightAction", APP)
        self.assertIn("purpose:'enable-fight'", APP)

    def test_14_fight_check_precedes_fight_movement(self):
        self.assertIn("id:'reposition-enable-fight'", APP)
        self.assertIn("id:'dash-enable-fight'", APP)

    def test_15_direct_fight_wording_and_helper(self):
        self.assertIn('Is a valid Player operative currently within this NPO’s control range?', APP)
        self.assertIn('Select Yes if this NPO can Fight a Player operative from its current position. Do not move the NPO.', APP)

    def test_16_fight_yes_selects_fight(self):
        self.assertIn("if(q.actionId==='fight')state.lastActivation.currentContext.hasValidFightTarget=true", APP)

    def test_17_fight_yes_spends_no_movement_ap(self):
        self.assertIn("const NPO_CORE_ACTION_COSTS={'reposition':1,'dash':1,'charge':1,'shoot':1,'fight':1,'fall-back':2};", APP)
        direct = section('function directNpoAttackQuestion', 'function npoActionQuestion')
        self.assertIn('movementIntent:null', direct)
        self.assertNotIn('commitNpoAction', direct)

    def test_18_fight_no_permits_ranked_continuation(self):
        self.assertIn("if(q.actionId==='fight')state.lastActivation.currentContext.hasValidFightTarget=false", APP)
        self.assertIn('save();runNpoPrompt(n,0,nextAnswers,nextHistory)', APP)

    def test_19_no_ranged_weapon_no_shoot(self):
        self.assertIn("if(id==='shoot'&&!(definition.rangedWeapons||[]).length)return false", APP)

    def test_20_no_melee_weapon_no_fight(self):
        self.assertIn("if(id==='fight'&&!(definition.meleeWeapons||[]).length)return false", APP)

    def test_21_insufficient_ap_filters_attack(self):
        self.assertIn('if(cost===null||cost>remainingAp||completed.has(id))return false', APP)

    def test_22_support_priorities_are_preserved(self):
        ranking = section('function rankLegalNpoActions', 'function recommendedNpoActions')
        self.assertIn("'geomancer':['Canoptek Control','Molecular Breach','Geomantic Disturbance','Shoot'", ranking)
        self.assertIn("'canoptek-macrocyte-reanimator':['Nanoscarab Beam','Reposition','Dash','Shoot','Fight']", ranking)

    def test_23_necron_fall_back_priority_is_preserved(self):
        self.assertIn("actions:['Fall Back','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission','Fight']", APP)

    def test_24_reposition_uses_profile_move(self):
        self.assertIn('formatMovementDistance(npoRepositionDistance(n))', APP)

    def test_25_dash_remains_three_inches(self):
        self.assertIn('Can a 3-inch Dash move this NPO to a position where it can Shoot?', APP)

    def test_26_confirmed_reposition_keeps_shoot_follow_up(self):
        self.assertIn("followUpActionId:'shoot',guaranteesFollowUp:true", APP)
        self.assertIn('movementCommitted:true', APP)

    def test_27_confirmed_charge_keeps_fight_follow_up(self):
        self.assertIn("id:'charge-enable-fight'", APP)
        self.assertIn("actionId:'fight'", APP)

    def test_28_non_guaranteed_movement_resets_spatial_context(self):
        self.assertIn('if(changesPosition)activation.currentContext={inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null}', APP)

    def test_29_back_from_target_selection_restores_question(self):
        back = section('function backFromNpoAttackSelection', 'function renderNpoMovementConfirmation')
        self.assertIn('activation.pendingAction=null', back)
        self.assertIn('activation.currentContext={...previous.contextBefore}', back)
        self.assertIn('history.slice(0,-2)', back)

    def test_30_question_history_uses_full_direct_question(self):
        self.assertIn('question:q.title', section('function runNpoPrompt', 'function chooseNpoDecision'))
        self.assertIn('item.question||item.action', APP)

    def test_31_refresh_restores_direct_question(self):
        restore = section('function continueNpoActivation', 'function continueGuaranteedNpoFollowUp')
        self.assertIn('runNpoPrompt(n,0,{},activation.questionHistory||[])', restore)

    def test_32_update_restores_direct_question(self):
        self.assertIn('currentContext:{inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null,...', APP)

    def test_33_unknown_legacy_movement_is_normalized(self):
        normalize = section('function normalizeUnknownAttackMovement', 'function continueGuaranteedNpoFollowUp')
        self.assertIn("attackAvailabilityForMovementIntent(activation,activation.movementIntent)!==null", normalize)
        self.assertIn('activation.pendingAction=null', normalize)
        self.assertIn('console.warn(', normalize)

    def test_34_saved_false_keeps_movement(self):
        helper = section('function attackAvailabilityForMovementIntent', 'function directNpoAttackQuestion')
        self.assertIn('hasValidShootTarget', helper)
        self.assertIn('hasValidFightTarget', helper)
        self.assertIn('availability===null||availability===true', APP)

    def test_35_multi_target_resolution_remains(self):
        self.assertIn('attackSummaries', APP)
        self.assertIn('weaponRuleResolution.currentTargetId', APP)

    def test_36_attack_now_has_no_movement_record(self):
        self.assertIn("if(q.movementIntent){", APP)
        self.assertIn('movementIntent:null,autoSelect', APP)

    def test_37_save_version_is_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_38_release_notes_and_assets(self):
        self.assertIn('Version 8.6.8 - Check Attacks Before NPO Movement', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.64', INDEX)

    def test_39_movement_availability_keeps_null_false_and_true_distinct(self):
        helper = section('function attackAvailabilityForMovementIntent', 'function directNpoAttackQuestion')
        script = f"""
{helper}
const values=[null,false,true];
process.stdout.write(JSON.stringify(values.map(value=>attackAvailabilityForMovementIntent(
  {{currentContext:{{hasValidShootTarget:value,hasValidFightTarget:value}}}},
  {{followUpActionId:'shoot'}}
))));
"""
        result = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), [None, False, True])

    def test_40_illegal_follow_up_is_not_treated_as_attack_enabling_movement(self):
        question = section('function npoActionQuestion', 'const npoQuestionIcons')
        self.assertIn("if(movementInquiry?.followUpActionId&&!intendedAttack)", question)
        self.assertIn("purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false", question)


if __name__ == '__main__':
    unittest.main()
