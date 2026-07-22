import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mission03Tests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_loading_search_completion_lifecycle_hud_details_and_restore(self):
        self.run_node(r"""
const assert=require('assert').strict;const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-03-recover-transponder.json'));
(async()=>{
  api.validateMissionDefinition(definition);
  const rolls=[{dice:[1],total:1},{dice:[3],total:3}];
  const engine=api.createMissionEngine({requestDiceRoll:async()=>rolls.shift()});
  const runtime=engine.initializeMissionRuntime(definition,{turningPoint:1,now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getObjectiveValue('transponderRecovered'),0);
  assert.deepEqual(engine.getMissionHudModel(),{missionId:'03',name:'Recover Transponder',label:'MISSION',objectiveId:'transponderRecovered',value:0,target:1,completed:false,visible:true});
  for(const hook of ['onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded']){
    assert.deepEqual(await engine.executeMissionHook(hook,{turningPoint:1,activationId:'one'}),[]);
  }
  const first=await engine.executeMissionAction('searchTransponder',{turningPoint:1,phase:'firefight',operativeId:'alpha'});
  assert.equal(first.results.searchRoll.total,1);assert.equal(engine.getObjectiveValue('transponderRecovered'),0);
  const second=await engine.executeMissionAction('searchTransponder',{turningPoint:2,phase:'firefight',operativeId:'alpha'});
  assert.equal(second.results.searchRoll.total,3);assert.equal(engine.getMissionDetailsModel().history.length,2);
  const completion=await engine.executeMissionAction('recordTransponderEscape',{turningPoint:2,phase:'firefight',operativeId:'alpha'});
  assert.deepEqual(completion.changes[0],{objectiveId:'transponderRecovered',before:0,after:1});
  assert.equal(runtime.objectives.transponderRecovered.completed,true);assert.equal(runtime.objectives.transponderRecovered.completedTurningPoint,2);
  assert.equal(engine.getMissionHudModel().completed,true);assert.equal(definition.completion.endsBattle,true);
  assert.deepEqual(runtime.history.at(-1).completedObjectiveIds,['transponderRecovered']);
  assert.equal((await engine.executeMissionAction('searchTransponder',{turningPoint:2})).status,'unavailable');
  const saved=JSON.parse(JSON.stringify(runtime));
  const refreshed=api.createMissionEngine();refreshed.restoreMissionRuntime(definition,saved,{turningPoint:2});
  assert.equal(refreshed.getObjectiveValue('transponderRecovered'),1);assert.equal(refreshed.getMissionHudModel().completed,true);
  assert.equal(refreshed.getMissionDetailsModel().history.length,3);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_registry_ui_persistence_offline_and_reference_regressions(self):
        manifest=json.loads((ROOT/'Missions/manifest.json').read_text())
        self.assertIn({'id':'03','file':'definition-03-recover-transponder.json'},manifest['definitions'])
        mission=json.loads((ROOT/'Missions/03-recover-transponder.json').read_text())
        self.assertEqual(len(mission['missionEngine']['sites']),3)
        app=(ROOT/'app.js').read_text();worker=(ROOT/'service-worker.js').read_text()
        self.assertIn("executeMissionAction('searchTransponder'",app)
        self.assertIn("executeMissionAction('recordTransponderEscape'",app)
        self.assertIn("if(missionEngine(selectedMission)?.type==='transponder')objectiveEngine.setObjectiveValue('transponderRecovered'",app)
        self.assertIn("'./Missions/definition-03-recover-transponder.json'",worker)
        self.assertIn('objectiveEngine.getMissionDetailsModel()',app)
        self.assertIn('missionHudHtml()',app)
        files=('definition-01-shifting-labyrinth.json','definition-02-demolition-protocol.json','definition-04-destroy-sarcophagus.json')
        for filename in files:
            self.assertTrue((ROOT/'Missions'/filename).exists())


if __name__ == '__main__':
    unittest.main()
