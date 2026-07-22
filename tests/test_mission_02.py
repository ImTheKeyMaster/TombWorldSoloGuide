import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Mission02Tests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_loading_initialization_progress_completion_lifecycle_and_restore(self):
        self.run_node(r"""
const assert=require('assert').strict;const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-02-demolition-protocol.json'));
(async()=>{
  api.validateMissionDefinition(definition);
  const engine=api.createMissionEngine();
  const runtime=engine.initializeMissionRuntime(definition,{turningPoint:1,now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getObjectiveValue('sabotagedFeatures'),0);
  assert.deepEqual(engine.getMissionHudModel(),{missionId:'02',name:'Demolition Protocol',label:'MISSION',objectiveId:'sabotagedFeatures',value:0,target:7,completed:false,visible:true});
  for(const hook of ['onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded']){
    assert.deepEqual(await engine.executeMissionHook(hook,{turningPoint:1,activationId:'one'}),[]);
  }
  for(let index=0;index<6;index++)await engine.executeMissionAction('recordBreach',{turningPoint:index<3?1:2,phase:'firefight'});
  assert.equal(engine.getObjectiveValue('sabotagedFeatures'),6);
  assert.equal(engine.getMissionHudModel().completed,false);
  assert.equal(engine.getMissionDetailsModel().history.length,6);
  const completion=await engine.executeMissionAction('recordBreach',{turningPoint:2,phase:'firefight'});
  assert.deepEqual(completion.changes[0],{objectiveId:'sabotagedFeatures',before:6,after:7});
  assert.equal(runtime.objectives.sabotagedFeatures.completed,true);
  assert.equal(runtime.objectives.sabotagedFeatures.completedTurningPoint,2);
  assert.equal(engine.getMissionHudModel().completed,true);
  assert.deepEqual(runtime.history.at(-1).completedObjectiveIds,['sabotagedFeatures']);
  assert.equal(definition.completion.endsBattle,true);
  const completedSave=JSON.parse(JSON.stringify(runtime));
  const refreshed=api.createMissionEngine();refreshed.restoreMissionRuntime(definition,completedSave,{turningPoint:2});
  assert.equal(refreshed.getObjectiveValue('sabotagedFeatures'),7);
  assert.equal(refreshed.getMissionHudModel().completed,true);
  assert.equal(refreshed.getMissionDetailsModel().history.length,7);
  await engine.executeMissionAction('correctBreach',{turningPoint:2,phase:'firefight'});
  assert.equal(engine.getObjectiveValue('sabotagedFeatures'),6);
  assert.equal(engine.getMissionHudModel().completed,false);
  assert.equal(engine.getMissionDetailsModel().history.length,8);
  const saved=JSON.parse(JSON.stringify(runtime));
  const restored=api.createMissionEngine();restored.restoreMissionRuntime(definition,saved,{turningPoint:2});
  assert.equal(restored.getObjectiveValue('sabotagedFeatures'),6);
  assert.equal(restored.getMissionHudModel().completed,false);
  assert.equal(restored.getMissionDetailsModel().history.length,8);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_registry_features_ui_save_refresh_and_reference_mission_regressions(self):
        manifest = json.loads((ROOT / "Missions/manifest.json").read_text())
        self.assertIn({"id": "02", "file": "definition-02-demolition-protocol.json"}, manifest["definitions"])
        mission = json.loads((ROOT / "Missions/02-demolition-protocol.json").read_text())
        self.assertEqual(len(mission["missionEngine"]["features"]), 11)
        self.assertEqual(mission["missionEngine"]["required"], 7)
        self.assertEqual(len({feature["id"] for feature in mission["missionEngine"]["features"]}), 11)
        app = (ROOT / "app.js").read_text()
        worker = (ROOT / "service-worker.js").read_text()
        self.assertIn("executeMissionAction(actionId,missionLifecycleContext())", app)
        self.assertIn("setObjectiveValue('sabotagedFeatures',state.missionState?.completedFeatureIds?.length||0", app)
        self.assertIn("'./Missions/definition-02-demolition-protocol.json'", worker)
        self.assertIn("state.missionRuntime=objectiveEngine.getMissionRuntime()", app)
        self.assertIn("objectiveEngine.getMissionDetailsModel()", app)
        self.assertIn("missionHudHtml()", app)


if __name__ == "__main__":
    unittest.main()
