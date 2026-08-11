import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class V810StreamlinedNpoActionFlowTests(unittest.TestCase):
    def test_explicit_transition_modes_have_safe_default(self):
        self.assertIn("AUTO_CONTINUE:'auto-continue'", APP)
        self.assertIn("ACKNOWLEDGE:'acknowledge'", APP)
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        self.assertIn('transitionMode=NPO_ACTION_TRANSITIONS.ACKNOWLEDGE', commit)
        self.assertIn('transitionMode===NPO_ACTION_TRANSITIONS.ACKNOWLEDGE', commit)

    def test_routine_movement_keeps_physical_confirmation(self):
        movement = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn("Confirm ${escapeHtml(displayAction)} Complete", movement)
        for action in ('reposition', 'dash', 'charge', 'fall-back'):
            self.assertIn(action, section('const ROUTINE_NPO_MOVEMENT_ACTIONS', 'let lastTouchEnd'))

    def test_routine_movement_explicitly_auto_continues(self):
        movement = section('function resolveNpoAction', 'function initiativeSummary')
        handler = movement[movement.index("$('#confirmNpoMovement').onclick"):]
        self.assertIn('button.disabled=true', handler)
        self.assertIn('NPO_ACTION_TRANSITIONS.AUTO_CONTINUE', handler)
        self.assertIn('NPO_ACTION_TRANSITIONS.COMPLETE_ACTIVATION', handler)
        self.assertNotIn('renderNpoActionResult(', handler.split('};', 1)[0])

    def test_auto_commit_saves_without_pending_result_then_schedules(self):
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        auto = commit[commit.index('activation.awaitingActionResult=null;'):]
        self.assertLess(auto.index('save();'), auto.index('scheduleNpoActionTransition('))
        self.assertIn('requestAnimationFrame', section('function scheduleNpoActionTransition', 'function commitNpoAction'))
        self.assertIn('current.activationId!==activation.activationId', APP)

    def test_movement_context_and_questions_are_reset(self):
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        self.assertIn('activation.declinedActionIds=[]', commit)
        self.assertIn('activation.questionHistory=[]', commit)
        self.assertIn('inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null', commit)

    def test_zero_ap_completes_without_generic_result(self):
        scheduler = section('function scheduleNpoActionTransition', 'function commitNpoAction')
        self.assertIn('current.remainingAp<=0', scheduler)
        self.assertIn('completeNpoActivation();return;', scheduler)
        continuation = section('function continueNpoActivation', 'function canCommitNpoAction')
        self.assertIn('if(activation.remainingAp<=0){completeNpoActivation();return;}', continuation)

    def test_attacks_auto_continue_after_acknowledged_combat(self):
        callback = section('function openNpoCombat', 'function renderNpoDecisionResult')
        self.assertIn('attackSummary:summary,attackSummaries,transitionMode:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE', callback)

    def test_special_actions_keep_acknowledgment_by_default(self):
        special = section('function finishNpoSpecialAction', 'function resolveNpo')
        self.assertNotIn('transitionMode:', special)
        for action in ('canoptek-control', 'molecular-breach', 'geomantic-disturbance', 'overcharge', 'cranial-overload', 'nanoscarab-beam'):
            self.assertIn(action, APP)

    def test_compact_progress_is_chronological_and_nonblocking(self):
        progress = section('function renderNpoActionProgress', 'function titleCaseRuleId')
        self.assertIn('activation?.resolvedActions||[]', progress)
        self.assertIn("actions.map(action=>escapeHtml(conciseNpoActionName(action))).join(', ')", progress)
        self.assertIn('AP left (${names} complete)', progress)
        self.assertIn('activation.remainingAp<=0', progress)
        self.assertNotIn('button', progress)
        self.assertIn('${renderNpoActionProgress()}', APP)

    def test_accessible_announcement_and_focus(self):
        self.assertIn('role="status" aria-live="polite"', APP)
        self.assertIn('Continuing activation.', APP)
        self.assertNotIn("$('#activeNpoQuestionHeading')?.focus", APP)
        self.assertIn('focusInitialDialogControl(modal)', APP)

    def test_v801_routine_results_recover_without_recommit(self):
        continuation = section('function continueNpoActivation', 'function canCommitNpoAction')
        self.assertIn('ROUTINE_NPO_MOVEMENT_ACTIONS.has(activation.awaitingActionResult.id)', continuation)
        self.assertIn('activation.awaitingActionResult=null', continuation)
        self.assertIn('save();', continuation)
        self.assertNotIn('commitNpoAction(', continuation)

    def test_meaningful_saved_results_remain_reviewable(self):
        continuation = section('function continueNpoActivation', 'function canCommitNpoAction')
        self.assertIn('if(activation.awaitingActionResult){renderNpoActionResult', continuation)

    def test_idempotency_guards_remain(self):
        guard = section('function canCommitNpoAction', 'function scheduleNpoActionTransition')
        self.assertIn('pending?.id===actionId', guard)
        self.assertIn('pending.decisionPass===activation.decisionPass', guard)
        self.assertIn('completedActionIds', guard)

    def test_current_version_830_everywhere(self):
        self.assertIn("const APP_VERSION = '8.6.51';", APP)
        self.assertIn("const APP_VERSION = '8.6.51';", WORKER)
        self.assertIn('V8.6.51', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.51'))
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.51', INDEX)


if __name__ == '__main__':
    unittest.main()
