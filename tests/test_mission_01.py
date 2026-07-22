import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mission01Tests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_loading_initialization_progress_completion_save_and_models(self):
        self.run_node(r"""
const assert=require('assert');const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-01-shifting-labyrinth.json'));
(async()=>{
  const rolls=[{dice:[1],total:1},{dice:[3],total:3}];
  const engine=api.createMissionEngine({requestDiceRoll:async()=>rolls.shift()});
  const context={turningPoint:1,phase:'firefight',gameplay:{playerOperativeCount:5,turningPoint:1,escapedOperativeCount:0}};
  const runtime=engine.initializeMissionRuntime(definition,context);
  assert.equal(runtime.objectives.escapedOperatives.target,3);
  assert.deepEqual(engine.getMissionHudModel(),{missionId:'01',name:'Shifting Labyrinth',label:'MISSION',objectiveId:'escapedOperatives',value:0,target:3,completed:false,visible:true});
  await engine.executeMissionHook('onMissionInitialized',context);
  await engine.executeMissionAction('recordEscape',context);
  await engine.executeMissionAction('recordEscape',{...context,turningPoint:2});
  assert.equal(engine.getMissionDetailsModel().objectives[0].value,2);
  assert.equal(engine.getMissionDetailsModel().history.length,2);
  const calibration=await engine.executeMissionAction('auspexCalibration',{...context,turningPoint:2,phase:'strategy',gameplay:{...context.gameplay,turningPoint:2}});
  assert.equal(calibration.results.directionRoll.total,1);assert.equal(calibration.results.distanceRoll.total,3);
  const completed=await engine.executeMissionAction('recordEscape',{...context,turningPoint:2});
  assert.equal(completed.changes[0].after,3);assert.equal(engine.getMissionHudModel().completed,true);
  assert.deepEqual(engine.getMissionRuntime().history.at(-1).completedObjectiveIds,['escapedOperatives']);
  const afterCompletion=await engine.executeMissionAction('recordEscape',{...context,turningPoint:2});
  assert.equal(afterCompletion.changes[0].after,4);assert.deepEqual(engine.getMissionRuntime().history.at(-1).completedObjectiveIds,[]);
  assert.equal(definition.completion.endsBattle,false);
  await engine.executeMissionAction('correctEscape',{...context,turningPoint:2});
  assert.equal(engine.getMissionHudModel().completed,true);
  await engine.executeMissionAction('correctEscape',{...context,turningPoint:2});
  assert.equal(engine.getMissionHudModel().completed,false);
  await engine.executeMissionAction('recordEscape',{...context,turningPoint:2});
  const saved=JSON.parse(JSON.stringify(runtime));
  saved.objectives.escapedOperatives.target=99;
  const restored=api.createMissionEngine();restored.restoreMissionRuntime(definition,saved,context);
  assert.equal(restored.getMissionHudModel().target,3);assert.equal(restored.getMissionHudModel().value,3);
  assert.ok(restored.getMissionDetailsModel().history.length>=6);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_dynamic_target_edges_expression_safety_and_d3_validation(self):
        self.run_node(r"""
const assert=require('assert');const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-01-shifting-labyrinth.json'));
const copy=()=>JSON.parse(JSON.stringify(definition));
const target=count=>api.createMissionEngine().initializeMissionRuntime(copy(),{gameplay:{playerOperativeCount:count}}).objectives.escapedOperatives.target;
assert.equal(target(1),1);assert.equal(target(2),1);assert.equal(target(4),2);assert.equal(target(5),3);assert.equal(target(0),1);
assert.throws(()=>target('five'),error=>error.code==='INVALID_EXPRESSION_VALUE');
for(const path of ['window.location','document.body','localStorage.secret','gameplay.__proto__','gameplay.notApproved']){
  const invalid=copy();invalid.objectives[0].targetExpression={path};
  assert.throws(()=>api.validateMissionDefinition(invalid),error=>['INVALID_EXPRESSION_PATH','INVALID_EXPRESSION'].includes(error.code));
}
for(const expression of [
  {operation:'unknown',arguments:[1]},
  {operation:'divide',arguments:[1]},
  {operation:'ceil',arguments:[1,2]},
  {operation:'divide',arguments:[1,0]}
]){
  const invalid=copy();invalid.objectives[0].targetExpression=expression;
  assert.throws(()=>api.createMissionEngine().initializeMissionRuntime(invalid,{gameplay:{playerOperativeCount:4}}));
}
(async()=>{
  const invalidDice=api.createMissionEngine({requestDiceRoll:async()=>({dice:[4],total:4})});
  invalidDice.initializeMissionRuntime(copy(),{gameplay:{playerOperativeCount:4}});
  await assert.rejects(()=>invalidDice.executeMissionAction('auspexCalibration',{gameplay:{playerOperativeCount:4,turningPoint:2,escapedOperativeCount:0}}),error=>error.code==='INVALID_DICE_RESULT');
  assert.equal(invalidDice.getMissionRuntime().history.length,0);
  const floor=api.createMissionEngine();floor.initializeMissionRuntime(copy(),{gameplay:{playerOperativeCount:4}});
  await floor.executeMissionAction('correctEscape');assert.equal(floor.getObjectiveValue('escapedOperatives'),0);
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_registry_offline_assets_and_app_lifecycle_integration(self):
        manifest=json.loads((ROOT/'Missions/manifest.json').read_text())
        self.assertEqual(manifest['definitions'][:2], [
            {'id':'01','file':'definition-01-shifting-labyrinth.json'},
            {'id':'04','file':'definition-04-destroy-sarcophagus.json'},
        ])
        app=(ROOT/'app.js').read_text(); worker=(ROOT/'service-worker.js').read_text()
        self.assertIn("executeMissionAction(wasEscaped?'correctEscape':'recordEscape'", app)
        self.assertIn("executeMissionAction('auspexCalibration'", app)
        self.assertIn('playerOperativeCount:Array.isArray(state.playerRoster)?state.playerRoster.length:0', app)
        self.assertEqual(app.count('objectiveEngine?.refreshMissionContext(missionLifecycleContext())'), 3)
        self.assertIn('Array.from({length:operation.dice.count},()=>roll(operation.dice.sides))', app)
        self.assertIn("new TombWorldMissionEngine.MissionEngineError('DICE_CANCELLED'", app)
        self.assertIn("'./Missions/definition-01-shifting-labyrinth.json'", worker)
        for hook in ('onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded'):
            self.assertIn(hook, app)


if __name__ == '__main__':
    unittest.main()
