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


def run_distance_helpers(expressions):
    helpers = section('const missingNpoRepositionMoveWarnings', 'function npoMovementInquiry')
    script = f"""
const definitions={{Known:{{move:6}},Invalid:{{move:0}}}};
const npoDefinition=type=>definitions[type]||null;
const console={{warn:()=>{{}}}};
{helpers}
process.stdout.write(JSON.stringify([{','.join(expressions)}]));
"""
    result = subprocess.run(
        ['node', '-e', script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class V866NpoRepositionDistanceTests(unittest.TestCase):
    def test_version_and_release_notes(self):
        self.assertIn("const APP_VERSION = '8.6.51';", APP)
        self.assertIn("const APP_VERSION = '8.6.51';", WORKER)
        self.assertIn('V8.6.51', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.51'))
        self.assertIn('Version 8.6.6 - Show Reposition Distance in NPO Guidance', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.51', INDEX)

    def test_distance_uses_current_npo_move_then_definition(self):
        helper = section('function npoRepositionDistance', 'function formatMovementDistance')
        self.assertIn('Number(npo?.move)', helper)
        self.assertIn('Number(npoDefinition(npo?.type)?.move)', helper)
        self.assertIn('Number.isFinite(currentMove)&&currentMove>0', helper)
        self.assertIn('Number.isFinite(definitionMove)&&definitionMove>0', helper)
        self.assertIn('return null', helper)
        self.assertEqual(
            run_distance_helpers([
                "npoRepositionDistance({type:'Known',move:7})",
                "npoRepositionDistance({type:'Known'})",
                "npoRepositionDistance({type:'Known',move:0})",
                "npoRepositionDistance({type:'Known',move:'invalid'})",
            ]),
            [7, 6, 6, 6],
        )

    def test_distance_formatting_handles_plural_and_singular(self):
        helper = section('function formatMovementDistance', 'function npoMovementInquiry')
        self.assertIn("distance===1?'inch':'inches'", helper)
        self.assertIn("if(!Number.isFinite(distance))return ''", helper)
        self.assertEqual(
            run_distance_helpers([
                'formatMovementDistance(1)',
                'formatMovementDistance(5)',
                'formatMovementDistance(NaN)',
            ]),
            ['1 inch', '5 inches', ''],
        )

    def test_every_reposition_question_variant_uses_distance(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        for wording in (
            'Can this NPO Reposition up to ${distance} and finish where it can Shoot?',
            'Can this NPO Reposition up to ${distance} to improve its position for the next activation or the mission?',
            'Can this NPO Reposition up to ${distance} closer to its target?',
            'Can this NPO Reposition up to ${distance} to use a support action or help the mission?',
            'Can this NPO Reposition up to ${distance} to help complete or defend the mission?',
        ):
            self.assertIn(wording, movement)
        self.assertIn('Select Yes only if it can finish the Reposition with a Player operative it can Shoot.', movement)

    def test_profiles_produce_different_move_distances(self):
        self.assertIn("id:'canoptek-macrocyte-warrior',name:'Canoptek Macrocyte Warrior',type:'Canoptek Macrocyte Warrior',faction:'Canoptek Circle',physicalQuantity:3,move:7", APP)
        self.assertIn("id:'necron-warrior',name:'Necron Warrior',type:'Necron Warrior',faction:'Necron Host',physicalQuantity:10,move:5", APP)
        self.assertNotIn("const distance='7 inches'", APP)

    def test_invalid_distance_warns_once_and_uses_generic_questions(self):
        helper = section('const missingNpoRepositionMoveWarnings', 'function formatMovementDistance')
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        self.assertIn('missingNpoRepositionMoveWarnings.has(warningKey)', helper)
        self.assertIn('console.warn(', helper)
        self.assertIn("'Can this NPO Reposition to a position where it can Shoot?'", movement)
        self.assertIn("'Can this NPO Reposition to improve its position for the next activation or the mission?'", movement)
        for unsafe in ('up to undefined inches', 'up to NaN inches', 'up to 0 inches'):
            self.assertNotIn(unsafe, APP)
        self.assertEqual(
            run_distance_helpers([
                "npoRepositionDistance({type:'Invalid',move:0})",
                "npoRepositionDistance({type:'Missing',move:'invalid'})",
            ]),
            [None, None],
        )

    def test_confirmation_reuses_dynamic_distance_and_movement_intent(self):
        instruction = section('function npoMovementInstruction', 'function npoActionCost')
        self.assertIn("formatMovementDistance(npoRepositionDistance(n))", instruction)
        self.assertIn("movementIntent?.purpose==='enable-shoot'", instruction)
        self.assertIn('Move this NPO up to ${distance} and finish where it can Shoot.', instruction)
        self.assertIn("movementIntent?.purpose==='general-position'", instruction)
        self.assertIn('Move this NPO up to ${distance} to improve its cover, mission position, or setup for a later activation.', instruction)
        confirmation = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('escapeHtml(decision.reason)', confirmation)
        self.assertIn('Confirm ${escapeHtml(displayAction)} Complete', confirmation)

    def test_history_preserves_full_rendered_question(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        history = section('function renderCompletedNpoQuestions', 'function renderActiveNpoQuestion')
        self.assertIn('question:q.title', prompt)
        self.assertIn('item.question||item.action', history)

    def test_dash_and_canoptek_control_limits_are_unchanged(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        self.assertIn('Can a 3-inch Dash move this NPO to a position where it can Shoot?', movement)
        self.assertIn("const distance=name==='Dash'?'3 inches'", section('function npoMovementInstruction', 'function npoActionCost'))
        self.assertIn('freeAction:{ap:1,consumeTargetApl:false,startActivation:false,preserveActivatedState:true,obeyNormalRestrictions:true,maxMove:2,repositionWhollyWithin:2}', APP)

    def test_ap_intent_follow_up_and_save_version_are_unchanged(self):
        self.assertIn("const NPO_CORE_ACTION_COSTS={'reposition':1,'dash':1,'charge':1,'shoot':1,'fight':1,'fall-back':2};", APP)
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('state.lastActivation.movementIntent={...q.movementIntent', prompt)
        follow_up = section('function continueGuaranteedNpoFollowUp', 'function canCommitNpoAction')
        self.assertIn('movementCommitted!==true', follow_up)
        self.assertIn('resolveNpoAction(n,activation.pendingAction)', follow_up)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_restore_regenerates_pending_question_from_active_npo(self):
        restore = section('function continueNpoActivation', 'function continueGuaranteedNpoFollowUp')
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('runNpoPrompt(n,0,{},activation.questionHistory||[])', restore)
        self.assertIn('const q=npoActionQuestion(n,index)', prompt)


if __name__ == '__main__':
    unittest.main()
