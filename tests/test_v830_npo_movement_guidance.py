import re
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


class V830NpoMovementGuidanceTests(unittest.TestCase):
    def test_action_questions_do_not_show_printed_objective(self):
        inquiries = section('const NPO_ACTION_INQUIRIES=', 'function npoActionCost')
        self.assertNotIn('printed objective', inquiries.lower())
        self.assertNotIn('printed behavior', section('function renderCompletedNpoQuestions', 'function continueNpoActivation').lower())

    def test_dash_question_and_help_describe_a_useful_destination(self):
        self.assertIn("question:'Can a 3-inch Dash put this NPO in a better position?'", APP)
        self.assertIn("help:'Select Yes if the Dash moves it toward a clear shot or a better mission position.'", APP)

    def test_movement_guidance_is_tailored_without_changing_action_definitions(self):
        guidance = section('function npoMovementInstruction', 'function npoActionCost')
        self.assertIn('toward the selected Player operative, using cover when possible', guidance)
        self.assertIn('to get a clear shot', guidance)
        self.assertIn('toward the mission objective or a position that helps defend it', guidance)
        self.assertIn("'Dash towards the closest player operative, to cover if possible'", APP)
        self.assertIn("'Dash to gain a valid unobscured target or better win the mission'", APP)

    def test_compact_progress_uses_only_concise_action_names(self):
        progress = section('function renderNpoActionProgress', 'function runNpoPrompt')
        self.assertIn('conciseNpoActionName(action)', progress)
        concise = section('function conciseNpoActionName', 'function legalNpoActions')
        self.assertIn("action.id==='fall-back'?'Fall Back'", concise)
        self.assertIn("action.id[0].toUpperCase()+action.id.slice(1)", concise)
        self.assertIn('return action.name', concise)
        self.assertNotIn('action.name)).join', progress)

    def test_history_and_journal_retain_detailed_action_text(self):
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        self.assertIn('name:actionName', commit)
        self.assertIn('result,\n      ...(allAttackSummaries.length?', commit)
        self.assertIn("const journalAction=['reposition','dash'].includes(actionId)?npoMovementInstruction(n,actionName):actionName", commit)
        self.assertIn('log(`${npoName(n)} completed ${journalAction}. ${activation.remainingAp} AP remaining.`)', commit)
        self.assertIn('activation.resolvedActions=[...(activation.resolvedActions||[]),record]', commit)

    def test_action_prompts_and_result_summaries_do_not_repeat_long_internal_names(self):
        movement = section('function renderNpoMovementConfirmation', 'function resolveNpoAction')
        self.assertIn('const displayAction=conciseNpoActionName(pendingAction)', movement)
        self.assertIn('Confirm ${escapeHtml(displayAction)} Complete', movement)
        result = section('function renderNpoActionResult', 'function renderNpoActivationEnd')
        self.assertIn('conciseNpoActionName(record)', result)
        self.assertIn('map(action=>escapeHtml(conciseNpoActionName(action)))', result)

    def test_priorities_ap_costs_and_action_results_are_unchanged(self):
        self.assertIn("const NPO_CORE_ACTION_COSTS={'reposition':1,'dash':1,'charge':1,'shoot':1,'fight':1,'fall-back':2}", APP)
        self.assertIn("'geomancer':['Canoptek Control','Molecular Breach','Geomantic Disturbance','Shoot','Fight','Reposition','Dash']", APP)
        self.assertIn('activation.remainingAp=Math.max(0,before-apCost)', APP)
        self.assertIn('const record={sequence:activation.actionSequence,id:actionId,name:actionName,apCost,apBefore:before,apRemaining:activation.remainingAp,result', APP)
        self.assertIn('scheduleNpoActionTransition(activation,n.id,transitionMode)', APP)

    def test_version_830_is_consistent_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.53';", APP)
        self.assertIn("const APP_VERSION = '8.6.53';", WORKER)
        self.assertIn('V8.6.53', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.53'))
        self.assertIn('## v8.6.25', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.53', INDEX)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
