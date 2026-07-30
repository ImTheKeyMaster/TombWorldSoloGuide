import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
STYLES = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
README = (ROOT / 'README.md').read_text()
STRATEGY = APP.split('function strategyProgressHtml', 1)[1].split('function strategyEventHtml', 1)[0]
EVENT_HTML = APP.split('function strategyEventHtml', 1)[1].split('function activationTracker', 1)[0]


class StrategyPhaseResultsTests(unittest.TestCase):
    def test_screen_sections_follow_required_document_order(self):
        self.assertIn('Resolve Strategy Phase Actions', STRATEGY)
        self.assertIn('Resolve Tomb World Events', STRATEGY)
        self.assertIn('Deploy Reinforcements and Review', STRATEGY)
        self.assertIn("missionStrategyPromptHtml()}${factionGuidanceHtml('gambits')}${scuttlingCard}", STRATEGY)
        self.assertNotIn('Restless Tomb:</strong> Resolve one Tomb World event.', APP)

    def test_empty_actions_and_events_have_guided_messages(self):
        self.assertIn('No additional guided Strategy Phase actions are required.', STRATEGY)
        self.assertIn('No Tomb World event is required during this Strategy Phase.', STRATEGY)

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
        battlefield = STRATEGY.split('const battlefield=', 1)[1]
        self.assertIn('${state.threat}', battlefield)
        self.assertIn('${threatGrade()}', battlefield)
        self.assertIn('${readyNpos().length}', battlefield)
        self.assertIn("state.reinforcementState.status!=='placement'", STRATEGY)
        self.assertNotIn('eventPresentation.resolved?', STRATEGY)

    def test_accessible_responsive_presentation(self):
        self.assertIn('aria-label="Strategy Phase, step ${number} of 3: ${label}"', STRATEGY)
        self.assertIn('id="strategy-step-heading" tabindex="-1"', STRATEGY)
        self.assertIn('aria-labelledby="battlefield-state-heading"', STRATEGY)
        self.assertIn('aria-label="${summary.accessible}"', STRATEGY)
        self.assertIn('@media(max-width:420px)', STYLES)
        self.assertNotIn('position:absolute', STYLES.split('.strategy-actions-section', 1)[1].split('\n', 1)[0])

    def test_release_version_and_notes_are_consistent(self):
        self.assertIn("const APP_VERSION = '8.4.0';", APP)
        self.assertIn('V8.4.0', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.4.0'))
        self.assertIn('Version 7.4.0 - Reorganize Strategy Phase Results', README)
        self.assertNotIn('portrait', EVENT_HTML.lower())
        self.assertNotIn('obelisk', EVENT_HTML.lower())


if __name__ == '__main__':
    unittest.main()
