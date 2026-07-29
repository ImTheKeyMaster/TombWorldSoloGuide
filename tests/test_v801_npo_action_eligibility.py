import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
V800 = (ROOT / 'tests/test_v800_npo_multi_action_activations.py').read_text()


def section(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


class V801NpoActionEligibilityTests(unittest.TestCase):
    def test_01_necron_fall_back_remains_first(self):
        warrior = re.search(r"'Necron Warrior': \{.*?behavior:\{.*?actions:\[(.*?)\]", APP, re.S).group(1)
        actions = re.findall(r"'([^']+)'", warrior)
        self.assertEqual(actions[:5], ['Fall Back', 'Shoot', 'Reposition to gain a valid unobscured target or better win the mission', 'Dash to gain a valid unobscured target or better win the mission', 'Fight'])

    def test_02_generic_fall_back_question_removed(self):
        self.assertNotIn('Can this NPO Fall Back?', APP)
        self.assertNotIn('title:`Can this NPO ${action}?`', APP)

    def test_03_fall_back_asks_control_range_first(self):
        self.assertIn("applicabilityQuestion:'Is this NPO within control range of a Player operative?'", APP)
        self.assertIn("applicability=id==='fall-back'", APP)

    def test_04_no_control_range_skips_without_spending_ap(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('currentContext.inEnemyControlRange=answer', prompt)
        self.assertIn("declinedActionIds=[...(state.lastActivation.declinedActionIds||[]),q.actionId]", prompt)
        self.assertNotIn('remainingAp=', prompt)

    def test_05_yes_control_range_proceeds_to_placement(self):
        self.assertNotIn('Can this NPO be placed legally after performing Fall Back?', APP)
        self.assertIn("feasibilityQuestion:'Can this NPO Fall Back and finish outside the control range of all Player operatives?'", APP)
        for guidance in ('It can move up to ${npoDefinition(n.type)?.move} inches', 'base can fit', 'outside every Player operative’s control range'):
            self.assertIn(guidance, APP)
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('if(answer){save();runNpoPrompt(n,0,nextAnswers,nextHistory);}', prompt)
        self.assertIn("nextHistory.push({action,type:'selected'", prompt)
        self.assertIn('resolveNpo(n,{...nextAnswers,action},nextHistory)', prompt)

    def test_05b_fall_back_instruction_is_explicit(self):
        self.assertIn("selectedInstruction:'Fall Back using the shortest available route and finish outside the control range of every Player operative.'", APP)

    def test_06_fall_back_costs_two_ap(self):
        self.assertIn("'fall-back':2", APP)

    def test_07_fall_back_not_offered_below_two_ap(self):
        legal = section('function legalNpoActions', 'function rankLegalNpoActions')
        self.assertIn('cost>remainingAp', legal)

    def test_07b_app_known_attack_requirements_are_filtered(self):
        legal = section('function legalNpoActions', 'function rankLegalNpoActions')
        self.assertIn("['shoot','fight','charge'].includes(id)&&!inPlayLivingPlayerOperativeIds().length", legal)
        self.assertIn("id==='shoot'&&!(definition.rangedWeapons||[]).length", legal)
        self.assertIn("id==='fight'&&!(definition.meleeWeapons||[]).length", legal)

    def test_08_legal_fall_back_precedes_shoot(self):
        warrior = APP[APP.index("'Necron Warrior': {"):APP.index("'Geomancer': {")]
        self.assertLess(warrior.index("'Fall Back'"), warrior.index("'Shoot'"))
        self.assertIn("action==='Fall Back'", section('function chooseNpoDecision', 'function continueNpoActivation'))

    def test_09_inapplicable_fall_back_continues_to_shoot(self):
        prompt = section('function runNpoPrompt', 'function chooseNpoDecision')
        self.assertIn('declinedActionIds=[...(state.lastActivation.declinedActionIds||[]),npoActionId(action)]', prompt)
        self.assertIn('save();runNpoPrompt(n,0,nextAnswers,nextHistory)', prompt)
        self.assertIn('Fall Back was not applicable.', APP)

    def test_09b_fall_back_question_and_help_are_screen_reader_available(self):
        rendered = section('function renderActiveNpoQuestion', 'function renderNpoActionProgress')
        self.assertIn('aria-live="polite" aria-atomic="true"', rendered)
        self.assertIn('<h3>${escapeHtml(q.title)}</h3><p>${escapeHtml(q.help)}</p>', rendered)
        self.assertIn('data-answer="no"', rendered)
        self.assertIn('data-answer="yes"', rendered)

    def test_10_shoot_wording_is_objective(self):
        self.assertIn('Does this NPO have a valid Player operative it can legally Shoot?', APP)
        for fact in ('visibility', 'obscuring', 'cover', 'weapon range', 'order restrictions', 'enemy control range', 'valid living target', 'active rule restrictions'):
            self.assertIn(fact, APP)

    def test_11_fight_wording_is_objective(self):
        self.assertIn('Is a valid Player operative within this NPO’s control range?', APP)

    def test_12_charge_wording_is_objective(self):
        self.assertIn('Can this NPO legally Charge and finish within control range of a valid Player operative?', APP)

    def test_13_reposition_requires_printed_purpose(self):
        self.assertIn('Can this NPO Reposition to gain an unobscured valid target or better accomplish the mission?', APP)

    def test_14_dash_requires_printed_purpose(self):
        self.assertIn('Can this NPO Dash to a more useful position?', APP)

    def test_15_movement_clears_spatial_context(self):
        commit = section('function commitNpoAction', 'function renderNpoActionResult')
        self.assertIn('if(changesPosition)activation.currentContext={inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null}', commit)

    def test_16_spatial_questions_repeat_after_movement(self):
        self.assertIn("applicability=id==='fall-back'&&activation.currentContext?.inEnemyControlRange===null", APP)
        self.assertIn('activation.decisionPass++', APP)

    def test_17_player_does_not_choose_priority(self):
        for phrase in ('The player chose not to Fall Back.', 'The NPO preferred to Shoot.'):
            self.assertNotIn(phrase, APP)

    def test_18_all_core_actions_have_inquiries(self):
        inquiry = section('const NPO_ACTION_INQUIRIES=', 'function npoActionCost')
        for action in ("'fall-back'", 'shoot:', 'fight:', 'charge:', 'reposition:', 'dash:'):
            self.assertIn(action, inquiry)
        self.assertIn('Are all requirements for ${action} currently satisfied?', APP)

    def test_19_supported_behavior_lists_unchanged(self):
        for npo in ('Necron Warrior', 'Canoptek Scarab Swarm', 'Canoptek Tomb Crawler', 'Canoptek Macrocyte Warrior', 'Canoptek Macrocyte Accelerator', 'Canoptek Macrocyte Reanimator', 'Geomancer'):
            self.assertIn(f"'{npo}': {{", APP)
        scarab = APP[APP.index("'Canoptek Scarab Swarm': {"):APP.index("'Necron Warrior': {")]
        self.assertNotIn("'Fall Back'", scarab)

    def test_20_v800_multi_action_continuation_remains(self):
        self.assertIn('if(activation.remainingAp<=0)', APP)
        self.assertIn("canContinue=!endsActivation&&activation.remainingAp>0", APP)
        self.assertIn('test_24_three_ap_supports_three_actions', V800)


if __name__ == '__main__':
    unittest.main()
