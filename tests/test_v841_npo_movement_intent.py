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


class V841NpoMovementIntentTests(unittest.TestCase):
    def test_reposition_intents_are_distinct_and_stable(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        self.assertIn("id:'reposition-enable-shoot'", movement)
        self.assertIn("purpose:'enable-shoot'", movement)
        self.assertIn("followUpActionId:'shoot'", movement)
        self.assertIn('Can this NPO Reposition up to ${distance} and finish where it can Shoot?', movement)
        self.assertIn('Can this NPO Reposition up to ${distance} to improve its position for the next activation or the mission?', movement)

    def test_declining_one_movement_intent_does_not_decline_action(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('declinedMovementIntentIds', prompt)
        self.assertIn('const nextIntent=npoMovementInquiry', prompt)
        self.assertIn('if(!nextIntent||state.lastActivation.declinedMovementIntentIds.includes(nextIntent.id))', prompt)

    def test_guaranteed_follow_up_bypasses_second_question(self):
        follow_up = section('function continueGuaranteedNpoFollowUp', 'function canCommitNpoAction')
        self.assertIn('movementCommitted!==true', follow_up)
        self.assertIn('activation.currentContext.hasValidShootTarget=true', follow_up)
        self.assertIn('activation.currentContext.hasValidFightTarget=true', follow_up)
        self.assertIn('resolveNpoAction(n,activation.pendingAction)', follow_up)
        self.assertNotIn('runNpoPrompt(n,0,{},activation.questionHistory||[]);return true', follow_up)

    def test_dash_intents_and_final_ap_are_explicit(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        self.assertIn("id:'dash-enable-shoot'", movement)
        self.assertIn('Can a 3-inch Dash move this NPO to a position where it can Shoot?', movement)
        self.assertIn('Can a 3-inch Dash improve this NPO’s position?', movement)
        self.assertIn('Can this NPO use its last AP to Dash to a better position?', movement)
        self.assertIn('The activation will end after the Dash.', movement)
        confirmation = section('function resolveNpoAction', 'function initiativeSummary')
        self.assertIn("const finalApDash=pendingAction.id==='dash'", confirmation)
        self.assertIn('NPO_ACTION_TRANSITIONS.COMPLETE_ACTIVATION', confirmation)

    def test_charge_promises_fight_only_with_ap_remaining(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn("q.actionId==='charge'&&state.lastActivation.remainingAp>=2", prompt)
        self.assertIn("id:'charge-enable-fight'", prompt)
        question = section('function npoActionQuestion', 'const npoQuestionIcons')
        self.assertIn("id==='charge'&&activation.remainingAp===1", question)
        self.assertIn('it will not Fight afterward', question)

    def test_persistence_normalizes_additive_state_without_save_bump(self):
        normalization = section('if(isRecord(merged.lastActivation)', 'state.npoAttackTargetId=null')
        for field in ('movementIntent', 'declinedMovementIntentIds', 'pendingFollowUpAction'):
            self.assertIn(field, normalization)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_movement_and_follow_up_commit_guards(self):
        commit = section('function canCommitNpoAction', 'function renderNpoActionResult')
        self.assertIn('completedActionIds', commit)
        self.assertIn('activation.remainingAp=Math.max(0,before-apCost)', commit)
        self.assertIn('movementCommitted:true', commit)
        combat = section('function showNpoAttackWizard', 'function spinnerField')
        self.assertIn('resolutionCommitted', combat)
        self.assertIn('canCommitNpoAction(pending.id,pending.apCost)', combat)

    def test_version_and_release_notes(self):
        self.assertIn("const APP_VERSION = '8.7.1';", APP)
        self.assertIn("const APP_VERSION = '8.7.1';", WORKER)
        self.assertIn('V8.7.1', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.7.1'))
        self.assertIn('## v8.6.25', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.7.1', INDEX)


if __name__ == '__main__':
    unittest.main()
