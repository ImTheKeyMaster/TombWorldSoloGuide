import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MissionEngineFoundationTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_runtime_conditions_operations_transactions_and_idempotency(self):
        self.run_node(
            r"""
const assert=require('assert');
const fs=require('fs');
require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/fixtures/future-mission.json'));
(async()=>{
  let clock=0;
  const engine=api.createMissionEngine({requestDiceRoll:async()=>({dice:[6],total:6})});
  const runtime=engine.initializeMissionRuntime(definition,{now:()=>`2026-01-01T00:00:0${clock++}Z`});
  assert.equal(runtime.schemaVersion,1);assert.equal(runtime.missionId,'TEST-01');
  assert.equal(engine.getObjectiveValue('sabotagePoints'),0);
  engine.adjustObjectiveValue('sabotagePoints',99);assert.equal(engine.getObjectiveValue('sabotagePoints'),6);
  assert.equal(runtime.objectives.sabotagePoints.completed,true);
  engine.setObjectiveValue('sabotagePoints',0);assert.equal(engine.getObjectiveValue('sabotagePoints'),6);
  assert.equal(api.evaluateCondition({all:[{path:'score',operator:'>',value:1},{not:{path:'done',operator:'truthy'}}]},{score:2,done:false}),true);
  assert.equal(api.evaluateCondition({any:[{path:'value',operator:'in',value:[2,3]},{path:'value',operator:'falsy'}]},{value:3}),true);
  assert.throws(()=>api.evaluateCondition({path:'x',operator:'contains',value:1},{x:1}),error=>error.code==='UNSUPPORTED_CONDITION_OPERATOR');
  assert.throws(()=>api.evaluateCondition({path:'constructor.value',operator:'truthy'},{}),error=>error.code==='UNSAFE_PATH');

  const actionEngine=api.createMissionEngine({requestDiceRoll:async()=>({dice:[4],total:4})});
  actionEngine.initializeMissionRuntime(definition);
  await actionEngine.executeMissionAction('sabotageGenerator',{turningPoint:1});
  assert.equal(actionEngine.getObjectiveValue('sabotagePoints'),4);
  assert.equal(actionEngine.getMissionRuntime().history.length,1);
  assert.equal(actionEngine.getMissionHudModel().value,4);
  assert.equal(actionEngine.getMissionDetailsModel().history.length,1);

  const rollbackDefinition=JSON.parse(JSON.stringify(definition));
  rollbackDefinition.actions=[{id:'rollback',label:'Rollback',operations:[
    {type:'addCounter',objectiveId:'sabotagePoints',value:2},
    {type:'showDialog',title:'Fail'}
  ]}];
  const rollbackEngine=api.createMissionEngine({showDialog:async()=>{throw new Error('dialog failed')}});
  const exposedRuntime=rollbackEngine.initializeMissionRuntime(rollbackDefinition);
  await assert.rejects(()=>rollbackEngine.executeMissionAction('rollback'),/dialog failed/);
  assert.strictEqual(rollbackEngine.getMissionRuntime(),exposedRuntime);
  assert.equal(rollbackEngine.getObjectiveValue('sabotagePoints'),0);
  assert.equal(exposedRuntime.objectives.sabotagePoints.value,0);
  assert.equal(rollbackEngine.getMissionRuntime().history.length,0);

  const onceDefinition=JSON.parse(JSON.stringify(definition));
  onceDefinition.hooks={onTurningPointEnded:[{id:'once',label:'Once',oncePer:'turningPoint',operations:[{type:'addCounter',objectiveId:'sabotagePoints',value:1}]}]};
  const onceEngine=api.createMissionEngine();onceEngine.initializeMissionRuntime(onceDefinition);
  await onceEngine.executeMissionHook('onTurningPointEnded',{turningPoint:2});
  const repeated=await onceEngine.executeMissionHook('onTurningPointEnded',{turningPoint:2});
  assert.equal(repeated[0].status,'already-executed');assert.equal(onceEngine.getObjectiveValue('sabotagePoints'),1);

  const unsupported=JSON.parse(JSON.stringify(definition));
  unsupported.actions[0].operations.push({type:'unknown'});
  assert.throws(()=>api.validateMissionDefinition(unsupported),error=>error.code==='UNSUPPORTED_OPERATION');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_registry_loader_validation_and_malformed_json(self):
        self.run_node(
            r"""
const assert=require('assert');const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const mission=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
(async()=>{
  const files={'Missions/manifest.json':{definitions:[{file:'04.json'}]},'Missions/04.json':mission};
  const response=value=>({ok:true,status:200,json:async()=>value});
  const loaded=await api.loadMissionDefinition('destroy-sarcophagus',{fetch:async path=>response(files[path])});
  assert.equal(loaded.id,'04');assert.equal(loaded.completion.endsBattle,false);
  await assert.rejects(()=>api.loadMissionDefinition('missing',{fetch:async path=>response(files[path])}),error=>error.code==='UNKNOWN_MISSION_ID');
  await assert.rejects(()=>api.loadMissionDefinition('04',{fetch:async path=>path.endsWith('manifest.json')?response(files[path]):({ok:true,status:200,json:async()=>{throw new SyntaxError('bad json')}})}),error=>error.code==='MALFORMED_JSON');
  await assert.rejects(()=>api.createMissionRegistry(['a','b'],async()=>mission),error=>error.code==='DUPLICATE_MISSION_ID');
  const missing={...mission};delete missing.name;assert.throws(()=>api.validateMissionDefinition(missing),error=>error.code==='INVALID_DEFINITION');
  const badHook={...mission,hooks:{onMadeUp:[]}};assert.throws(()=>api.validateMissionDefinition(badHook),error=>error.code==='UNKNOWN_HOOK');
  const duplicateObjective={...mission,objectives:[mission.objectives[0],mission.objectives[0]]};assert.throws(()=>api.validateMissionDefinition(duplicateObjective),error=>error.code==='DUPLICATE_OBJECTIVE_ID');
  const duplicateAction={...mission,actions:[mission.actions[0],mission.actions[0]]};assert.throws(()=>api.validateMissionDefinition(duplicateAction),error=>error.code==='DUPLICATE_ACTION_ID');
  const unsafe='<img src=x onerror=globalThis.compromised=true>';
  const safe=api.validateMissionDefinition({...mission,briefing:unsafe});assert.equal(safe.briefing,unsafe);assert.equal(globalThis.compromised,undefined);
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_json_contract_and_deferred_integration(self):
        manifest = json.loads((ROOT / "Missions/manifest.json").read_text())
        self.assertEqual(
            manifest["definitions"],
            [
                {"id": "01", "file": "definition-01-shifting-labyrinth.json"},
                {"id": "04", "file": "definition-04-destroy-sarcophagus.json"},
            ],
        )
        for relative in (
            "Missions/mission.schema.json",
            "Missions/definition-04-destroy-sarcophagus.json",
            "Missions/MissionTemplate.json",
            "Missions/fixtures/future-mission.json",
        ):
            json.loads((ROOT / relative).read_text())
        app = (ROOT / "app.js").read_text()
        self.assertIn("TombWorldMissionEngine", app)
        self.assertIn("missionRuntime", app)
        self.assertIn("Mission Details", app)
        self.assertIn("mission-hud", (ROOT / "styles.css").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertLess(index.index("mission-engine.js"), index.index("app.js"))


if __name__ == "__main__":
    unittest.main()
