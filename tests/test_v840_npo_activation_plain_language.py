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


class V840NpoActivationPlainLanguageTests(unittest.TestCase):
    def test_version_and_save_compatibility(self):
        self.assertIn("const APP_VERSION = '8.6.32';", APP)
        self.assertIn("const APP_VERSION = '8.6.32';", WORKER)
        self.assertIn('V8.6.32', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.32'))
        self.assertIn('## v8.6.25', README)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.32', INDEX)

    def test_profile_and_progress_plain_language(self):
        prompt = section('function renderNpoActivationHeader', 'function renderNpoGuideFooter')
        self.assertIn('Wounds: ${n.wounds}/${n.maxWounds}', prompt)
        self.assertIn("effective===definition.apl?'':` (${effective} AP this activation)`", prompt)
        self.assertNotIn(' · effective ', prompt)
        self.assertIn('Order: ${escapeHtml(n.order)}', prompt)
        self.assertIn("AP this activation (${escapeHtml(titleCaseRuleId(item.ruleId))})", prompt)
        self.assertIn('Next movement uses Molecular Breach', prompt)
        progress = section('function renderNpoActionProgress', 'function titleCaseRuleId')
        self.assertIn('AP left (${names} complete)', progress)
        self.assertIn('activation.remainingAp<=0', progress)
        self.assertIn('role="status" aria-live="polite"', progress)

    def test_history_hides_engine_labels(self):
        history = section('function renderCompletedNpoQuestions', 'function renderActiveNpoQuestion')
        for label in ('APPLICABILITY', 'FEASIBILITY', 'SELECTED ACTION'):
            self.assertNotIn(label, history)
        self.assertIn("item.type==='selected'?'Selected'", history)

    def test_core_questions_are_physical_and_specific(self):
        inquiries = section('const NPO_ACTION_INQUIRIES=', 'function npoMovementFocus')
        expected = (
            'Is this NPO within the control range of any Player operative?',
            'Can it move away and finish outside every Player operative’s control range?',
            'Does this NPO currently have a Player operative it can Shoot without moving?',
            'Is a valid Player operative currently within this NPO’s control range?',
            'Can this NPO reach a Player operative with a Charge?',
        )
        for wording in expected:
            self.assertIn(wording, inquiries)
        for banned in ('living Player operative', 'legally', 'printed objective', 'printed behavior'):
            self.assertNotIn(banned, inquiries)

    def test_special_actions_have_specific_tabletop_questions(self):
        inquiries = section('const NPO_ACTION_INQUIRIES=', 'function npoMovementFocus')
        expected = (
            'Can the Geomancer see a terrain point within 8 inches?',
            'Can the Geomancer see a friendly Canoptek within 6 inches?',
            'Can the Geomancer see a friendly Canoptek Circle NPO within 6 inches?',
            'Can the Accelerator see another friendly Canoptek within 3 inches?',
            'Can the Accelerator see a Player operative within 3 inches?',
            'Can the Reanimator see a wounded Canoptek Circle NPO within 6 inches?',
        )
        for wording in expected:
            self.assertIn(wording, inquiries)

    def test_reposition_and_dash_are_behavior_specific(self):
        movement = section('function npoMovementInquiry', 'function npoMovementInstruction')
        for wording in (
            'Can this NPO Reposition up to ${distance} and finish where it can Shoot?',
            'Can this NPO Reposition up to ${distance} closer to its target?',
            'Can this NPO Reposition up to ${distance} to use a support action or help the mission?',
            'Can this NPO Reposition up to ${distance} to help complete or defend the mission?',
            'Can a 3-inch Dash put this NPO in a better position?',
            'Can a 3-inch Dash move this NPO closer to its target?',
            'Can a 3-inch Dash help this NPO use a support action?',
        ):
            self.assertIn(wording, movement)

    def test_fallback_next_action_and_end_wording(self):
        question = section('function npoActionQuestion', 'const npoQuestionIcons')
        self.assertIn('Can this NPO use ${action} now?', question)
        self.assertIn('Check the action’s target, distance, and placement.', question)
        result = section('function renderNpoDecisionResult', 'async function completeNpoActivation')
        self.assertIn('NEXT ACTION', result)
        self.assertNotIn('ACTIVATION PLAN', result)
        self.assertIn('No useful actions remain.', APP)
        self.assertIn('Close Guide', APP)

    def test_target_priorities_are_semantic_and_ranking_is_unchanged(self):
        decision = section('function chooseNpoDecision', 'function continueNpoActivation')
        fight = "['Most likely to be taken out','Most important to the mission','A Ready operative']"
        shoot = "['Most likely to be taken out','Most important to the mission','Clearest shot','Not in cover','Closest','A Ready operative']"
        self.assertIn(fight, decision)
        self.assertIn(shoot, decision)
        result = section('function renderNpoDecisionResult', 'async function completeNpoActivation')
        self.assertIn('<ol>${decision.target.map', result)
        self.assertIn('Randomize only if still tied.', result)
        self.assertIn('Select Target', result)
        self.assertIn('Select the first operative that matches the priority above.', result)

    def test_combat_and_special_action_labels(self):
        self.assertIn('<strong>Weapon guidance</strong>', APP)
        self.assertIn('Choose Weapon Profile', APP)
        self.assertIn('Choose a profile...', APP)
        self.assertIn('Is this NPO in the same room as the sarcophagus?', APP)
        combat = section('function showNpoAttackWizard', 'function spinnerField')
        self.assertNotIn('C1 sarcophagus', combat)
        special = section('function resolveNpoSpecialAction', 'function finishNpoSpecialAction')
        for wording in ('Player operative', 'Friendly NPO', 'Use Canoptek Control', 'Apply Molecular Breach', 'Use Overcharge', 'Use Cranial Overload', 'Roll Healing', 'Roll Damage'):
            self.assertIn(wording, special)
        self.assertNotIn('>Resolve</button>', special)

    def test_special_action_steps_use_semantic_markup(self):
        descriptions = section('function npoSpecialActionDescription', 'function resolveNpoSpecialAction')
        self.assertIn("if(action.id==='geomantic-disturbance')return `<ol><li>", descriptions)
        self.assertIn('</li></ol><p>Cannot be used while the Geomancer', descriptions)
        for action in ('canoptek-control', 'molecular-breach', 'overcharge', 'cranial-overload', 'nanoscarab-beam'):
            self.assertIn(action, descriptions)

    def test_question_and_profile_accessibility_associations(self):
        active = section('function renderActiveNpoQuestion', 'function renderNpoActionProgress')
        self.assertIn('aria-labelledby="activeNpoQuestion"', active)
        self.assertIn('aria-describedby="activeNpoQuestionHelp"', active)
        header = section('function renderNpoActivationHeader', 'function renderNpoGuideFooter')
        self.assertIn('role="status" aria-live="polite" aria-label="Activation profile"', header)

    def test_gameplay_constants_and_priority_order_are_unchanged(self):
        self.assertIn("const NPO_CORE_ACTION_COSTS={'reposition':1,'dash':1,'charge':1,'shoot':1,'fight':1,'fall-back':2}", APP)
        self.assertIn("'geomancer':['Canoptek Control','Molecular Breach','Geomantic Disturbance','Shoot','Fight','Reposition','Dash']", APP)
        self.assertIn("'canoptek-tomb-crawler':context.inEnemyControlRange?['Fight','Shoot','Charge','Reposition','Dash']:['Shoot','Charge','Fight','Reposition','Dash']", APP)
        legality = section('function legalNpoActions', 'function rankLegalNpoActions')
        self.assertIn("if(['shoot','fight','charge'].includes(id)&&!inPlayLivingPlayerOperativeIds().length)return false", legality)
        self.assertIn("if((id==='shoot'&&completed.has('fight'))||(id==='fight'&&completed.has('shoot')))return false", legality)


if __name__ == '__main__':
    unittest.main()
