import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
README = (ROOT / "README.md").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class RestlessTombMissionBriefingTests(unittest.TestCase):
    def test_accessible_option_appears_once_in_shared_mission_briefing(self):
        briefing = APP.split("return `<h3>Mission Briefing</h3>", 1)[1].split("function bindSetup", 1)[0]
        self.assertEqual(briefing.count('id="restlessTombEnabled"'), 1)
        self.assertIn('<label class="check-row restless-tomb-option">', briefing)
        self.assertIn('<input id="restlessTombEnabled" type="checkbox"', briefing)
        self.assertIn('<strong>Restless Tomb</strong>', briefing)
        self.assertIn('Beginning with Turning Point 2', briefing)
        self.assertIn('Turning Point 1 is unaffected', briefing)
        self.assertIn('standard event rules may require additional events', briefing)
        self.assertIn('optional house rule increases activity and difficulty', briefing)
        self.assertNotIn('disabled', briefing)

    def test_option_defaults_off_updates_immediately_and_survives_setup_navigation(self):
        self.assertIn('setupChecks:{}, restlessTombEnabled:false', APP)
        self.assertIn("merged.restlessTombEnabled=raw.restlessTombEnabled===true", APP)
        self.assertIn("$('#restlessTombEnabled')?.addEventListener('change',e=>{state.restlessTombEnabled=e.target.checked;save();render();});", APP)
        mission_change = re.search(r"\$\$\('\.mission-choice'\).*?;\}\);", APP).group(0)
        self.assertNotIn('restlessTombEnabled', mission_change)
        self.assertNotIn('restlessTombEnabled', APP.split('async function loadObjectiveMission', 1)[1].split('let playerManifest', 1)[0])

    def test_option_is_shared_by_all_missions_and_read_only_in_active_references(self):
        self.assertEqual(len(list((ROOT / 'Missions').glob('[0-9][0-9]-*.json'))), 6)
        count_logic = APP.split('function strategyEventCount', 1)[1].split('function threatLabel', 1)[0]
        self.assertNotRegex(count_logic, r"mission(?:Id|\(\)|\.number)")
        self.assertIn("<strong>Restless Tomb:</strong> ${state.restlessTombEnabled?'On':'Off'}", APP)
        self.assertIn("Restless Tomb: ${state.restlessTombEnabled?'On':'Off'}", APP)
        active_reference = APP.split('function renderMission()', 1)[1].split('function renderRoster', 1)[0]
        self.assertNotIn('type="checkbox"', active_reference)

    def test_mobile_option_reuses_touch_target_and_has_visible_keyboard_focus(self):
        styles = (ROOT / 'styles.css').read_text()
        self.assertIn('.check-row input{width:22px;height:22px', styles)
        self.assertIn('.restless-tomb-option input:focus-visible{outline:2px solid var(--green)', styles)


class RestlessTombEventCountTests(unittest.TestCase):
    def test_official_and_effective_event_counts(self):
        source = re.search(
            r"function normalStrategyEventCount\([\s\S]*?\n  \}\n  function strategyEventCount\([\s\S]*?\n  \}",
            APP,
        ).group(0)
        script = f"""
const assert=require('assert');
let state={{turningPoint:1,threat:0,restlessTombEnabled:false,strategyData:null}};
{source}
const count=(turningPoint,threat,grade,suggestedInitiative,enabled)=>{{
  state={{turningPoint,threat,restlessTombEnabled:enabled,strategyData:null}};
  return strategyEventCount({{grade,suggestedInitiative}});
}};
assert.equal(count(1,15,3,'npo',true),0);
assert.equal(count(2,0,0,'player',false),0);
assert.equal(count(2,1,1,'player',false),0);
assert.equal(count(2,6,2,'player',false),0);
assert.equal(count(2,0,0,'player',true),1);
assert.equal(count(2,1,1,'player',true),1);
assert.equal(count(2,6,2,'player',true),1);
assert.equal(count(2,11,3,'player',true),1);
assert.equal(count(2,11,3,'npo',true),2);
assert.equal(count(2,15,3,'player',true),2);
assert.equal(count(7,0,0,'player',true),1);
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_event_stage_uses_one_central_count_and_existing_deck_and_resolver(self):
        stage = APP.split('function processEventStage()', 1)[1].split('function eventRecord', 1)[0]
        self.assertIn('d.requiredEventCount=strategyEventCount(d)', stage)
        self.assertIn('for(let i=0;i<d.requiredEventCount;i++)', stage)
        self.assertIn('const event=drawEvent()', stage)
        self.assertNotIn('setThreat(', stage)
        self.assertNotIn('eventDefinitions', stage)
        self.assertIn("event.requiredBy=i>=d.normalEventCount?'restless-tomb':'standard'", stage)
        self.assertIn("const index=roll(state.eventState.available.length)-1", APP)
        self.assertIn('const definition=eventDefinitions[card.definitionId]', APP)

    def test_pending_slots_are_persisted_and_block_strategy_completion(self):
        self.assertIn('d.eventRequirementTurningPoint=state.turningPoint', APP)
        self.assertIn('d.eventSlotsDrawn=0', APP)
        self.assertIn('event.status=\'resolved\'', APP)
        self.assertIn("!d.eventPending", APP)
        self.assertIn("strategyRequiredRedrawPending()", APP)
        self.assertIn("if(state.phase!=='strategy'||state.strategyStage!=='summary'||!event||!state.strategyData.eventPending)return", APP)
        self.assertIn("replacement.requiredBy=event.requiredBy", APP)
        self.assertIn('events:Array.isArray(raw.strategyData.events)', APP)

    def test_history_records_turning_point_source_name_and_result_once(self):
        completion = APP.split('function completeCurrentEvent', 1)[1].split('function redrawCurrentEvent', 1)[0]
        self.assertEqual(completion.count('log('), 1)
        self.assertIn('Turning Point ${state.turningPoint}', completion)
        self.assertIn('${event.title}', completion)
        self.assertIn('Restless Tomb minimum', completion)
        self.assertIn('${result}', completion)


class RestlessTombPersistenceAndRegressionTests(unittest.TestCase):
    def test_persistence_round_trip_and_safe_legacy_normalization(self):
        script = """
const assert=require('assert');
const p=require('./persistence.js');
const base={saveVersion:p.currentSaveVersion(),roster:[],playerRoster:[]};
assert.equal(p.migrateSave({...base,restlessTombEnabled:true}).restlessTombEnabled,true);
assert.equal(p.migrateSave({...base,restlessTombEnabled:false}).restlessTombEnabled,false);
assert.equal(p.migrateSave(base).restlessTombEnabled,false);
for(const value of ['true',1,{},[],null]) assert.equal(p.migrateSave({...base,restlessTombEnabled:value}).restlessTombEnabled,false);
const saved=p.createPersistedSave({...base,restlessTombEnabled:true,strategyData:{eventRequirementTurningPoint:2,requiredEventCount:1,eventSlotsDrawn:1,events:[{instanceId:'card-1',status:'drawn'}]}});
assert.equal(saved.restlessTombEnabled,true);
assert.deepEqual(p.migrateSave(saved).strategyData,saved.strategyData);
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn('normalized.restlessTombEnabled=save.restlessTombEnabled===true', PERSISTENCE)

    def test_existing_threat_awakening_reinforcement_and_initiative_paths_are_unchanged(self):
        set_threat = APP.split('function setThreat', 1)[1].split('function escapeHtml', 1)[0]
        self.assertIn("if(before===0&&state.threat>0)", set_threat)
        self.assertIn("npo.dormant=false;npo.ready=true", set_threat)
        event_count = APP.split('function strategyEventCount', 1)[1].split('function threatLabel', 1)[0]
        self.assertNotIn('setThreat', event_count)
        self.assertEqual(APP.count('function processReinforcementStage()'), 1)
        self.assertEqual(APP.count('function rollInitiative()'), 1)
        self.assertEqual(APP.count('function processEventStage()'), 1)

    def test_mission_05_room_rules_remain_separate(self):
        mission_05 = (ROOT / 'tests/test_mission_05.py').read_text()
        self.assertIn('awakenRoom', mission_05)
        core_rule = APP.split('function strategyEventCount', 1)[1].split('function threatLabel', 1)[0]
        self.assertNotIn('awakenedRooms', core_rule)
        self.assertNotIn("type==='scout'", core_rule)

    def test_release_and_out_of_scope_constraints(self):
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.9'))
        self.assertIn('## v8.6.9', README)
        self.assertIn("const APP_VERSION = '8.6.9';", APP)
        self.assertIn("const APP_VERSION = '8.6.9';", WORKER)
        self.assertIn('V8.6.9', INDEX)
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'app.js'):
            self.assertIn(f'{asset}?v=8.6.9', INDEX)
        self.assertNotIn('portrait', APP.split('const eventDefinitions', 1)[1].split('const eventDeck', 1)[0].lower())
        self.assertNotIn('obelisk', APP.split('function strategyEventCount', 1)[1].split('function threatLabel', 1)[0].lower())


if __name__ == '__main__':
    unittest.main()
