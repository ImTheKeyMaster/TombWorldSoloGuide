import re
import unittest
from pathlib import Path

from tests.test_v800_npo_multi_action_activations import ActivationModel

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


def section(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class V831FallBackQuestionGuidanceTests(unittest.TestCase):
    def test_applicability_question_explicitly_prevents_movement(self):
        inquiry = section("'fall-back':{", '    shoot:{')
        self.assertIn("applicabilityQuestion:'Is this NPO within the control range of any Player operative?'", inquiry)
        self.assertIn(
            "applicabilityHelp:'Select Yes if this NPO is currently within a Player operative’s control range. Do not move the NPO yet.'",
            inquiry,
        )
        self.assertNotIn(
            'Select Yes if a Player operative is in its control range. Do not move the NPO yet.',
            inquiry,
        )

    def test_applicability_help_contains_no_movement_instruction(self):
        inquiry = section("'fall-back':{", '    shoot:{')
        applicability = re.search(r"applicabilityHelp:'([^']+)'", inquiry).group(1)
        self.assertNotIn('move up to', applicability.lower())
        self.assertNotIn('destination', applicability.lower())
        self.assertNotIn('base can fit', applicability.lower())

    def test_feasibility_help_uses_actual_move_value_dynamically(self):
        inquiry = section("'fall-back':{", '    shoot:{')
        self.assertIn('feasibilityHelp:n=>`Move it up to ${npoDefinition(n.type)?.move} inches.', inquiry)
        warrior = section("'Necron Warrior': {", "'Canoptek Tomb Crawler': {")
        self.assertRegex(warrior, r'move:5,apl:2')

    def test_question_stage_selects_separate_helper_text(self):
        question = section('function npoActionQuestion', 'const npoQuestionIcons')
        self.assertIn("applicability?inquiry?.applicabilityHelp:", question)
        self.assertIn("inquiry?.feasibilityHelp??inquiry?.help", question)

    def test_normal_apl_two_necron_warrior_completes_after_two_ap_fall_back(self):
        warrior = section("'Necron Warrior': {", "'Canoptek Tomb Crawler': {")
        apl = int(re.search(r'apl:(\d+)', warrior).group(1))
        activation = ActivationModel(apl)

        self.assertEqual(ActivationModel.COSTS['fall-back'], 2)
        self.assertIn("'fall-back':2", APP)
        self.assertTrue(activation.commit('fall-back'))
        self.assertEqual(activation.remaining, 0)

        continuation = section('function continueNpoActivation', 'function canCommitNpoAction')
        self.assertIn('if(activation.remainingAp<=0){completeNpoActivation();return;}', continuation)

    def test_fall_back_moves_only_after_feasibility_yes_and_confirmation(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn("}else if(answer){", prompt)
        self.assertIn('resolveNpo(n,{...nextAnswers,action},nextHistory)', prompt)
        movement = section('function resolveNpoAction', 'function initiativeSummary')
        self.assertIn("$('#confirmNpoMovement').onclick=()", movement)
        self.assertIn("commitNpoAction({actionId:pendingAction.id", movement)

    def test_version_831_is_consistent_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.7';", APP)
        self.assertIn("const APP_VERSION = '8.6.7';", WORKER)
        self.assertIn('V8.6.7', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.7'))
        self.assertIn('## v8.6.7', README)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.7', INDEX)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
