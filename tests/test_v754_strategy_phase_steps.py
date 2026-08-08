import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()
STYLES = (ROOT / 'styles.css').read_text()


def function_body(name):
    match = re.search(rf"  function {name}\([^\n]*", APP)
    if not match:
        return ''
    start = match.start()
    next_function = APP.find('\n  function ', match.end())
    return APP[start:next_function if next_function >= 0 else len(APP)]


class StrategyPhaseStepTests(unittest.TestCase):
    def test_01_new_phase_starts_on_actions(self):
        self.assertIn("viewStep:'actions'", APP)

    def test_02_actions_has_requested_checklist(self):
        body = function_body('strategyActionsStepHtml')
        for wording in ('Generate Command Points as required.', 'Play any Strategic Ploys.',
                        'Resolve abilities and mission rules.', 'Review optional Strategic Gambits.'):
            self.assertIn(wording, body)

    def test_03_actions_excludes_events_and_reinforcements(self):
        body = function_body('strategyActionsStepHtml')
        self.assertNotIn('strategyEventHtml(', body)
        self.assertNotIn('data-reinforcement-placement', body)

    def test_04_mandatory_mission_blocks_actions(self):
        self.assertIn('return !missionStrategyPending()', function_body('canLeaveStrategyActions'))

    def test_05_optional_gambits_do_not_block_actions(self):
        body = function_body('canLeaveStrategyActions')
        self.assertNotIn('ceaseless', body.lower())
        self.assertNotIn('gambit', body.lower())

    def test_06_continue_moves_to_events(self):
        self.assertIn("showStrategyViewStep('events','actions')", function_body('bindPlay'))

    def test_07_events_shows_requirement_summary_and_cards(self):
        body = function_body('strategyEventsStepHtml')
        for helper in ('strategyEventRequirementLabel', 'strategyEventSummary', 'strategyEventHtml'):
            self.assertIn(helper, body)

    def test_08_events_excludes_review_content(self):
        body = function_body('strategyEventsStepHtml')
        self.assertNotIn('data-reinforcement-placement', body)
        self.assertNotIn('Current Battlefield State', body)

    def test_09_pending_event_blocks_events(self):
        self.assertIn('!d.eventPending', function_body('canLeaveStrategyEvents'))

    def test_10_event_resolution_preserves_view(self):
        self.assertNotIn('viewStep', function_body('completeCurrentEvent'))

    def test_11_redraw_preserves_view(self):
        self.assertNotIn('viewStep', function_body('redrawCurrentEvent'))

    def test_12_replacement_preserves_view(self):
        self.assertNotIn('viewStep', function_body('drawReplacementEvent'))

    def test_13_resolved_event_allows_review(self):
        body = function_body('canLeaveStrategyEvents')
        self.assertIn("(d.events||[])[d.eventIndex||0]?.status!=='drawn'", body)

    def test_14_no_event_message(self):
        self.assertIn('No Tomb World event is required during this Strategy Phase.', function_body('strategyEventsStepHtml'))

    def test_15_review_has_reinforcements_and_statistics(self):
        body = function_body('strategyReviewStepHtml')
        self.assertIn('REINFORCEMENTS', body)
        self.assertIn('Current Battlefield State', body)

    def test_16_review_excludes_checklist_and_full_event_cards(self):
        body = function_body('strategyReviewStepHtml')
        self.assertNotIn('Strategy Phase Checklist', body)
        self.assertNotIn('strategyEventHtml(', body)

    def test_17_18_placement_blocks_until_confirmed(self):
        self.assertIn("state.reinforcementState.status!=='placement'", function_body('canCompleteStrategyPhase'))
        self.assertIn("status=complete?'complete':'placement'", function_body('confirmReinforcementPlacement').replace(' ', ''))

    def test_19_20_back_navigation(self):
        body = function_body('bindPlay')
        self.assertIn("showStrategyViewStep('events','review')", body)
        self.assertIn("showStrategyViewStep('actions','events')", body)

    def test_21_navigation_does_not_process_gameplay(self):
        body = function_body('showStrategyViewStep')
        for forbidden in ('startTurningPoint(', 'determineInitiative(', 'processEventStage(', 'processReinforcementStage('):
            self.assertNotIn(forbidden, body)

    def test_22_view_step_is_saved_by_normal_state_save(self):
        body = function_body('showStrategyViewStep')
        self.assertIn('d.viewStep=step', body)
        self.assertIn('save();render()', body)

    def test_23_24_25_legacy_view_normalization(self):
        normalization = APP[APP.index("viewStep:['actions'"):APP.index('};', APP.index("viewStep:['actions'"))]
        self.assertIn("? 'events'", normalization)
        self.assertIn("status==='placement'", normalization)
        self.assertIn("? 'review'", normalization)
        self.assertIn(": 'actions'", normalization)

    def test_26_complete_enters_firefight_once(self):
        self.assertIn("state.phase==='strategy'&&state.strategyStage==='summary'", function_body('canCompleteStrategyPhase'))
        binding = function_body('bindPlay')
        line = next(line for line in binding.splitlines() if "$('#continueStrategy')" in line)
        self.assertEqual(line.count('beginFirefight('), 1)

    def test_27_restless_tomb_unchanged(self):
        self.assertIn("i>=d.normalEventCount?'restless-tomb':'standard'", function_body('processEventStage'))

    def test_28_atomic_redraw_unchanged(self):
        body = function_body('redrawCurrentEvent')
        self.assertIn('eventRedrawsInProgress', body)
        self.assertIn("status:'committed',committed:true", body)

    def test_29_aggressive_defence_unchanged(self):
        self.assertIn('Aggressive Defence', APP)

    def test_30_event_automation_unchanged(self):
        self.assertIn('EventEffects.activeRecords', APP)
        self.assertIn('eventState.transactions', APP)

    def test_31_lowest_number_allocator_unchanged(self):
        self.assertIn('lowestAvailableNpoInstances', APP)

    def test_32_version_754_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.49';", APP)
        self.assertIn("const APP_VERSION = '8.6.49';", WORKER)
        self.assertIn('V8.6.49', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.49'))
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.49', INDEX)

    def test_33_accessible_progress_focus_and_mobile_layout(self):
        self.assertIn('aria-label="Strategy Phase, step ${number} of 3: ${label}"', function_body('strategyProgressHtml'))
        self.assertIn('id="strategy-step-heading"', APP)
        self.assertNotIn('id="strategy-step-heading" tabindex', APP)
        self.assertIn('focusInitialDialogControl(app)', function_body('showStrategyViewStep'))
        self.assertIn('.strategy-navigation{display:grid;grid-template-columns:1fr', STYLES)
        self.assertIn('.strategy-navigation.two-actions{grid-template-columns:minmax(0,1fr) minmax(0,1fr)', STYLES)
        self.assertIn('env(safe-area-inset-bottom)', STYLES)


if __name__ == '__main__':
    unittest.main()
