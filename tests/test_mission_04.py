import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Mission04Tests(unittest.TestCase):
    def test_json_driven_breach_repair_completion_and_persistence(self):
        script = r"""
const assert=require('assert');const fs=require('fs');require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
(async()=>{
  const rolls=[{dice:[2,3],total:5},{dice:[5],total:5},{dice:[2],total:2},{dice:[6,6],total:12},{dice:[6,6],total:12}];
  const inputs=[2,4];let victory=false;
  const engine=api.createMissionEngine({requestDiceRoll:async()=>rolls.shift(),requestNumericInput:async()=>inputs.shift()});
  const runtime=engine.initializeMissionRuntime(definition,{now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getObjectiveValue('destructionPoints'),0);
  assert.equal((await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:1}))[0].status,'unavailable');
  const breach=await engine.executeMissionAction('breachSarcophagus',{turningPoint:1});
  assert.equal(engine.getObjectiveValue('destructionPoints'),5);assert.deepEqual(breach.changes[0],{objectiveId:'destructionPoints',before:0,after:5});
  const repair=await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:2});
  assert.equal(engine.getObjectiveValue('destructionPoints'),2);assert.deepEqual(repair[0].changes[0],{objectiveId:'destructionPoints',before:5,after:2});
  assert.equal((await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:2}))[0].status,'already-executed');
  const noRepair=await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:3});
  assert.equal(engine.getObjectiveValue('destructionPoints'),2);assert.equal(noRepair[0].changes[0].before,noRepair[0].changes[0].after);
  await engine.executeMissionAction('breachSarcophagus',{turningPoint:3});
  const completion=await engine.executeMissionAction('breachSarcophagus',{turningPoint:3});
  assert.equal(engine.getObjectiveValue('destructionPoints'),20);assert.equal(completion.changes[0].after,20);
  assert.equal(runtime.objectives.destructionPoints.completed,true);assert.equal(runtime.objectives.destructionPoints.completedTurningPoint,3);assert.equal(definition.completion.endsBattle,false);assert.equal(victory,false);
  assert.equal(engine.evaluateMissionConditions(definition.actions[0].availability),false);
  assert.equal((await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:4}))[0].status,'unavailable');
  assert.equal(engine.getObjectiveValue('destructionPoints'),20);
  assert.ok(runtime.history.every(entry=>Array.isArray(entry.changes)));assert.deepEqual(runtime.history.at(-1).completedObjectiveIds,['destructionPoints']);
  const restored=api.createMissionEngine();restored.restoreMissionRuntime(definition,JSON.parse(JSON.stringify(runtime)));
  assert.equal(restored.getObjectiveValue('destructionPoints'),20);assert.equal(restored.getMissionRuntime().objectives.destructionPoints.completed,true);
  assert.ok(restored.getMissionRuntime().eventExecutions['nanoscarabRepair:turningPoint:2']);

  const floorEngine=api.createMissionEngine({requestDiceRoll:async()=>({dice:[6],total:6}),requestNumericInput:async()=>0});
  floorEngine.initializeMissionRuntime(definition);floorEngine.setObjectiveValue('destructionPoints',2);
  await floorEngine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:1});assert.equal(floorEngine.getObjectiveValue('destructionPoints'),0);
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_work_packages_04_and_05_are_present_and_06_through_08_are_deferred(self):
        app=(ROOT/'app.js').read_text()
        styles=(ROOT/'styles.css').read_text()
        self.assertIn('Mission Details', app)
        self.assertIn('mission-hud', styles)
        self.assertIn('onPlayerActivationStarted', app)
        self.assertNotIn('MISSION AUTOMATION UNAVAILABLE', app)


if __name__ == '__main__':
    unittest.main()
