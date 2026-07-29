import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
STYLES = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
README = (ROOT / 'README.md').read_text()
STRATEGY = APP.split('function strategyCard()', 1)[1].split('function strategyEventHtml', 1)[0]
EVENT_HTML = APP.split('function strategyEventHtml', 1)[1].split('function activationTracker', 1)[0]


class StrategyPhaseResultsTests(unittest.TestCase):
    def test_screen_sections_follow_required_document_order(self):
        rendered = STRATEGY.rsplit('return `<section class="next-card"', 1)[1]
        order = [
            'Complete the Strategy Phase', 'strategy-intro', 'Strategy Phase Checklist',
            '${actionsSection}', '${eventsSection}', '${reinforcementResults}',
            '${battlefieldState}', 'id="continueStrategy"'
        ]
        positions = [rendered.index(value) for value in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("missionStrategyPromptHtml()}${factionGuidanceHtml('gambits')}${scuttlingCard}", STRATEGY)
        self.assertNotIn('Restless Tomb:</strong> Resolve one Tomb World event.', APP)

    def test_empty_actions_and_events_sections_are_omitted(self):
        self.assertIn("actionsHtml?`<section class=\"strategy-actions-section\"", STRATEGY)
        self.assertIn('showEvents=eventPresentation.required||eventPresentation.cardsDrawn||unmatchedActiveEvents', STRATEGY)
        self.assertIn('showEvents?`<section class="strategy-events-section"', STRATEGY)

    def test_requirement_and_summary_use_persisted_current_turn_state_without_mutation(self):
        helpers = re.search(
            r"function strategyEventPresentation[\s\S]*?\n  }\n\n  function strategyEventRequirementLabel[\s\S]*?\n  }",
            APP,
        ).group(0)
        script = f"""
const assert=require('assert');
let state={{turningPoint:2,strategyData:null}};
{helpers}
const events=[
  {{status:'redrawn',requiredBy:'restless-tomb'}},
  {{status:'resolved',requiredBy:'restless-tomb'}}
];
const data={{eventRequirementTurningPoint:2,requiredEventCount:1,normalEventCount:0,events}};
const before=JSON.stringify(data);
const result=strategyEventPresentation(data);
assert.deepEqual(result,{{required:1,cardsDrawn:2,resolved:1,events}});
assert.equal(strategyEventRequirementLabel(data,result),'1 event required by Restless Tomb.');
assert.equal(JSON.stringify(data),before);
data.normalEventCount=1;
assert.equal(strategyEventRequirementLabel(data,result),'1 event required by the standard Tomb World rules.');
data.normalEventCount=0;
events[1].requiredBy='standard';
assert.equal(strategyEventRequirementLabel(data,result),'1 event required by the standard Tomb World rules.');
events[1].requiredBy='restless-tomb';
data.requiredEventCount=2;
data.normalEventCount=2;
result.required=2;
assert.equal(strategyEventRequirementLabel(data,result),'2 events required by the standard Tomb World rules.');
state.turningPoint=3;
assert.deepEqual(strategyEventPresentation(data),{{required:0,cardsDrawn:0,resolved:0,events:[]}});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertNotIn('Deadly', helpers)
        for mutation in ('drawEvent(', 'setThreat(', 'save(', 'log('):
            self.assertNotIn(mutation, helpers)

    def test_canonical_status_has_visible_text_and_history_is_chronological(self):
        self.assertIn("statusLabels={drawn:'PENDING',resolved:activeEffect?'RESOLVED • ACTIVE':'RESOLVED',redrawn:'REDRAWN'}", EVENT_HTML)
        self.assertIn('data-event-status="${escapeHtml(event.status)}"', EVENT_HTML)
        self.assertIn("event.status!=='drawn'||index===d.eventIndex", STRATEGY)
        self.assertIn('displayedEvents.map(event=>strategyEventHtml(event,activeEffects))', STRATEGY)
        self.assertNotIn("event.status==='redrawn'?'Redraw required':'Resolved'", EVENT_HTML)

    def test_battlefield_values_remain_canonical_and_completion_logic_is_unchanged(self):
        battlefield = STRATEGY.split('const battlefieldState=', 1)[1]
        self.assertIn('${state.threat}', battlefield)
        self.assertIn('${threatGrade()}', battlefield)
        self.assertIn('${readyNpos().length}', battlefield)
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled':''", STRATEGY)
        self.assertNotIn('eventPresentation.resolved?', STRATEGY)

    def test_accessible_responsive_presentation(self):
        self.assertIn('aria-labelledby="strategy-actions-heading"', STRATEGY)
        self.assertIn('aria-labelledby="strategy-events-heading"', STRATEGY)
        self.assertIn('aria-labelledby="battlefield-state-heading"', STRATEGY)
        self.assertIn('aria-label="${eventSummary.accessible}"', STRATEGY)
        self.assertIn('@media(max-width:420px)', STYLES)
        self.assertNotIn('position:absolute', STYLES.split('.strategy-actions-section', 1)[1].split('\n', 1)[0])

    def test_release_version_and_notes_are_consistent(self):
        self.assertIn("const APP_VERSION = '7.5.3';", APP)
        self.assertIn('V7.5.3', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v7.5.3'))
        self.assertIn('Version 7.4.0 - Reorganize Strategy Phase Results', README)
        self.assertNotIn('portrait', EVENT_HTML.lower())
        self.assertNotIn('obelisk', EVENT_HTML.lower())


if __name__ == '__main__':
    unittest.main()
