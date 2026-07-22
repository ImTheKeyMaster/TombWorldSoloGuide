import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mission05Tests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_definition_actions_completion_correction_history_and_restore(self):
        self.run_node(r"""
const assert=require('assert').strict;const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-05-scout-sub-crypt.json'));
(async()=>{
  api.validateMissionDefinition(definition);
  const rolls=[{dice:[1],total:1},{dice:[3],total:3}];
  const engine=api.createMissionEngine({requestDiceRoll:async()=>rolls.shift()});
  const runtime=engine.initializeMissionRuntime(definition,{turningPoint:1,now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getObjectiveValue('scoutedRooms'),0);
  assert.deepEqual(engine.getMissionHudModel(),{missionId:'05',name:'Scout Sub-Crypt',label:'MISSION',objectiveId:'scoutedRooms',value:0,target:3,completed:false,visible:true});
  const low=await engine.executeMissionAction('awakenRoom',{turningPoint:1,phase:'firefight'});
  const high=await engine.executeMissionAction('awakenRoom',{turningPoint:2,phase:'firefight'});
  assert.equal(low.results.awakenRoll.total,1);assert.equal(high.results.awakenRoll.total,3);
  for(let index=0;index<3;index++)await engine.executeMissionAction('recordScout',{turningPoint:index+1,phase:'firefight'});
  assert.equal(engine.getObjectiveValue('scoutedRooms'),3);assert.equal(runtime.objectives.scoutedRooms.completed,true);
  assert.equal(runtime.objectives.scoutedRooms.completedTurningPoint,3);assert.equal(definition.completion.endsBattle,true);
  assert.equal(engine.getMissionHudModel().completed,true);assert.deepEqual(runtime.history.at(-1).completedObjectiveIds,['scoutedRooms']);
  assert.equal(engine.getMissionDetailsModel().history.length,5);
  await engine.executeMissionAction('correctScout',{turningPoint:3,phase:'firefight'});
  assert.equal(engine.getObjectiveValue('scoutedRooms'),2);assert.equal(engine.getMissionHudModel().completed,false);
  for(let index=0;index<4;index++)await engine.executeMissionAction('correctScout',{turningPoint:3});
  assert.equal(engine.getObjectiveValue('scoutedRooms'),0);
  for(let index=0;index<8;index++)await engine.executeMissionAction('recordScout',{turningPoint:4});
  assert.equal(engine.getObjectiveValue('scoutedRooms'),5);
  const saved=JSON.parse(JSON.stringify(runtime));saved.objectives.scoutedRooms.value='tampered';
  const restored=api.createMissionEngine();restored.restoreMissionRuntime(definition,saved,{turningPoint:4});
  assert.equal(restored.getObjectiveValue('scoutedRooms'),0);
  assert.equal(restored.getMissionDetailsModel().history.length,Math.min(saved.history.length,50));
  for(const hook of ['onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded'])
    assert.deepEqual(await engine.executeMissionHook(hook,{turningPoint:4,activationId:'one'}),[]);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_invalid_dice_result_is_atomic(self):
        self.run_node(r"""
const assert=require('assert').strict;const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine,definition=JSON.parse(fs.readFileSync('Missions/definition-05-scout-sub-crypt.json'));
(async()=>{const engine=api.createMissionEngine({requestDiceRoll:async()=>({dice:[4],total:4})});engine.initializeMissionRuntime(definition);
await assert.rejects(()=>engine.executeMissionAction('awakenRoom',{turningPoint:1}),error=>error.code==='INVALID_DICE_RESULT');
assert.equal(engine.getMissionRuntime().history.length,0);assert.equal(engine.getObjectiveValue('scoutedRooms'),0);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_registry_ui_offline_rules_and_version(self):
        manifest=json.loads((ROOT/'Missions/manifest.json').read_text())
        self.assertIn({'id':'05','file':'definition-05-scout-sub-crypt.json'},manifest['definitions'])
        mission=json.loads((ROOT/'Missions/05-scout-sub-crypt.json').read_text())
        self.assertEqual(mission['startingNpos']['formula'],'0')
        self.assertEqual(mission['missionEngine']['required'],3)
        self.assertEqual(len(mission['missionEngine']['rooms']),5)
        self.assertEqual(mission['missionEngine']['objectiveId'],'scoutedRooms')
        self.assertEqual(mission['missionEngine']['progressIdsField'],'scoutedRoomIds')
        self.assertEqual(mission['missionEngine']['actions'],{
            'awakenRoom':'awakenRoom','recordScout':'recordScout','correctScout':'correctScout'
        })
        app=(ROOT/'app.js').read_text();worker=(ROOT/'service-worker.js').read_text();index=(ROOT/'index.html').read_text()
        for action in ('awakenRoom','recordScout','correctScout'):
            self.assertIn(f"missionEngine().actions?.{action}",app)
        self.assertIn('data-scout-operative',app)
        self.assertIn("inPlayLivingPlayerOperativeIds().includes(operativeId)",app)
        self.assertIn('state.missionState.scoutedByRoom[button.dataset.scoutRoom]=operativeId',app)
        self.assertIn('delete state.missionState.scoutedByRoom[button.dataset.correctScoutRoom]',app)
        self.assertIn('normalized.scoutedByRoom=',app)
        self.assertLess(app.index('state.missionState=normalizeMissionState(state.missionState,selectedMission,state.tracker)'),app.index('objectiveDefinition=await TombWorldMissionEngine.loadMissionDefinition'))
        self.assertIn("Math.min(5,(outcome?.results?.awakenRoll?.total??rollD3())+threatGrade())",app)
        self.assertIn("setThreat(gradeFloor-state.threat,'Scout Room')",app)
        self.assertIn("stage.hatch&&state.missionId!=='scout-sub-crypt'",app)
        self.assertIn("'./Missions/definition-05-scout-sub-crypt.json'",worker)
        self.assertIn("const APP_VERSION = '6.4.0'",app)
        self.assertIn("const APP_VERSION = '6.4.0'",worker)
        self.assertIn('V6.4.0',index)


if __name__ == '__main__':
    unittest.main()
