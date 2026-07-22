import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MissionValidationHardeningTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_definition_references_duplicates_empty_lists_and_future_properties(self):
        self.run_node(
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
vm.runInThisContext(fs.readFileSync('mission-engine.js','utf8'));
const api=globalThis.TombWorldMissionEngine;
const original=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
const copy=()=>JSON.parse(JSON.stringify(original));
const fails=(mutate,code)=>{const value=copy();mutate(value);assert.throws(()=>api.validateMissionDefinition(value,'fixture.json'),error=>error.code===code&&error.details.path.startsWith('fixture.json'));};
fails(value=>{value.hooks.onBattleEnded=[{id:'duplicateEvent',operations:[]}];value.hooks.onTurningPointEnded=[{id:'duplicateEvent',operations:[]}]},'DUPLICATE_EVENT_ID');
fails(value=>value.completion.objectiveId='missing','INVALID_OBJECTIVE_REFERENCE');
fails(value=>value.completion.dialogId='missing','INVALID_DIALOG_REFERENCE');
fails(value=>value.actions[0].operations[1].valueFrom='results.missing.total','INVALID_EVENT_REFERENCE');
fails(value=>value.hooks.notAHook=[],'UNKNOWN_HOOK');
fails(value=>value.schemaVersion=2,'UNSUPPORTED_SCHEMA_VERSION');
fails(value=>value.dialogs=null,'INVALID_DEFINITION');
fails(value=>value.actions[0].oncePer='week','INVALID_DEFINITION');
const sharedId=copy();sharedId.hooks.onBattleEnded=[{id:sharedId.actions[0].id,operations:[]}];assert.equal(api.validateMissionDefinition(sharedId).id,'04');
const empty=copy();empty.objectives=[];empty.actions=[];empty.hooks={};empty.completion={endsBattle:false};empty.dialogs={};empty.futureMetadata={safe:true};
assert.equal(api.validateMissionDefinition(empty).futureMetadata.safe,true);
"""
        )

    def test_runtime_guards_restore_and_completion_are_idempotent(self):
        self.run_node(
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
vm.runInThisContext(fs.readFileSync('mission-engine.js','utf8'));
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
assert.throws(()=>api.createMissionEngine(null),error=>error.code==='INVALID_SERVICES');
(async()=>{const engine=api.createMissionEngine();
assert.throws(()=>engine.getMissionHudModel(),error=>error.code==='MISSION_NOT_INITIALIZED');
engine.restoreMissionRuntime(definition,{missionId:'04',objectives:{destructionPoints:{value:'invalid',completed:true}},history:null,eventExecutions:null},null);
assert.equal(engine.getObjectiveValue('destructionPoints'),0);
assert.equal(engine.getMissionRuntime().objectives.destructionPoints.completed,false);
assert.deepEqual(engine.evaluateObjectiveCompletion(null),{destructionPoints:false});
assert.deepEqual(await engine.executeMissionHook('onBattleEnded',null),[]);
engine.setObjectiveValue('destructionPoints',20,{turningPoint:2,now:()=> 'first'});
const first=engine.getMissionRuntime().objectives.destructionPoints;
engine.setObjectiveValue('destructionPoints',20,{turningPoint:3,now:()=> 'second'});
const repeated=engine.getMissionRuntime().objectives.destructionPoints;
assert.equal(repeated.completedAt,'first');assert.equal(repeated.completedTurningPoint,2);
assert.throws(()=>engine.adjustObjectiveValue('missing',1),error=>error.code==='UNKNOWN_OBJECTIVE');
assert.throws(()=>engine.adjustObjectiveValue('destructionPoints',NaN),error=>error.code==='INVALID_COUNTER_VALUE');
assert.throws(()=>engine.recordMissionHistory(null),error=>error.code==='INVALID_HISTORY_ENTRY');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_prior_individual_dice_results_validate_and_execute(self):
        self.run_node(
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
vm.runInThisContext(fs.readFileSync('mission-engine.js','utf8'));
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
definition.actions[0].operations[1].valueFrom='results.breachRoll.dice.0';
assert.equal(api.validateMissionDefinition(definition).id,'04');
const invalid=JSON.parse(JSON.stringify(definition));
invalid.actions[0].operations[1].valueFrom='results.breachRoll.dice.2';
assert.throws(()=>api.validateMissionDefinition(invalid),error=>error.code==='INVALID_EVENT_REFERENCE');
(async()=>{
  const engine=api.createMissionEngine({requestDiceRoll:async()=>({dice:[4,2],total:6})});
  engine.initializeMissionRuntime(definition);
  await engine.executeMissionAction('breachSarcophagus');
  assert.equal(engine.getObjectiveValue('destructionPoints'),4);
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_loader_reports_malformed_json_and_duplicate_missions(self):
        self.run_node(
            r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
vm.runInThisContext(fs.readFileSync('mission-engine.js','utf8'));
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
(async()=>{
  await assert.rejects(()=>api.createMissionRegistry(['a.json','b.json'],async()=>definition),error=>error.code==='DUPLICATE_MISSION_ID');
  const fetch=async path=>({ok:true,json:async()=>{if(path.endsWith('manifest.json'))return {definitions:[{file:'bad.json'}]};throw new SyntaxError('bad json');}});
  await assert.rejects(()=>api.loadMissionDefinition('04',{fetch}),error=>error.code==='MALFORMED_JSON');
  await assert.rejects(()=>api.loadMissionDefinition('',{fetch}),error=>error.code==='INVALID_DEFINITION');
  await assert.rejects(()=>api.loadMissionDefinition('04',null),error=>error.code==='INVALID_OPTIONS');
  await assert.rejects(()=>api.createMissionRegistry([],null),error=>error.code==='INVALID_REGISTRY');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_accessibility_and_listener_regression_guards(self):
        app = (ROOT / "app.js").read_text()
        styles = (ROOT / "styles.css").read_text()
        index = (ROOT / "index.html").read_text()
        self.assertIn('aria-label="Mission details,', app)
        self.assertIn("modal.addEventListener('cancel'", app)
        self.assertIn("if(event.key!='Tab')", app.replace("!==", "!="))
        self.assertIn("returnFocus?.isConnected", app)
        self.assertIn('aria-live="polite"', app)
        self.assertEqual(app.count("modal.addEventListener('keydown'"), 1)
        self.assertIn("min-height:44px", styles)
        self.assertIn('aria-modal="true"', index)


if __name__ == "__main__":
    unittest.main()
