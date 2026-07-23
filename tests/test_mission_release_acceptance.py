import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MissionReleaseAcceptanceTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_complete_mission_04_runtime_flow_survives_restore(self):
        self.run_node(
            r"""
const assert=require('assert').strict;
const fs=require('fs');
require('./mission-engine.js');
const api=globalThis.TombWorldMissionEngine;
const definition=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
(async()=>{
  const rolls=[{dice:[4,5],total:9},{dice:[5],total:5},{dice:[6,6],total:12}];
  let inputRequests=0;
  const engine=api.createMissionEngine({
    requestDiceRoll:async()=>rolls.shift(),
    requestNumericInput:async()=>{inputRequests++;return 2;}
  });
  const runtime=engine.initializeMissionRuntime(definition,{now:()=> '2026-07-22T00:00:00Z'});
  assert.equal(engine.getMissionHudModel().value,0);
  await engine.executeMissionAction('breachSarcophagus',{turningPoint:1,phase:'firefight'});
  assert.equal(engine.getMissionHudModel().value,9);
  assert.equal(engine.getMissionDetailsModel().history.length,1);
  await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:2,phase:'strategy'});
  assert.equal(inputRequests,1);
  assert.equal(engine.getObjectiveValue('destructionPoints'),6);
  assert.equal((await engine.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:2}))[0].status,'already-executed');
  assert.equal(inputRequests,1);
  await engine.executeMissionAction('breachSarcophagus',{turningPoint:2,phase:'firefight'});
  assert.equal(engine.getObjectiveValue('destructionPoints'),18);
  engine.adjustObjectiveValue('destructionPoints',7,{turningPoint:3});
  assert.equal(engine.getObjectiveValue('destructionPoints'),20);
  assert.equal(runtime.objectives.destructionPoints.completed,true);
  assert.equal(definition.completion.endsBattle,false);
  const historyLength=runtime.history.length;
  engine.adjustObjectiveValue('destructionPoints',-20,{turningPoint:3});
  assert.equal(engine.getObjectiveValue('destructionPoints'),20);
  assert.equal(runtime.history.length,historyLength);
  const restored=api.createMissionEngine();
  restored.restoreMissionRuntime(definition,JSON.parse(JSON.stringify(runtime)));
  assert.equal(restored.getMissionHudModel().completed,true);
  assert.equal(restored.getMissionDetailsModel().objectives[0].value,20);
  assert.equal((await restored.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:2}))[0].status,'unavailable');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        )

    def test_release_assets_versions_and_mission_scope_are_consistent(self):
        app = (ROOT / "app.js").read_text()
        index = (ROOT / "index.html").read_text()
        worker = (ROOT / "service-worker.js").read_text()
        manifest = json.loads((ROOT / "Missions/manifest.json").read_text())

        self.assertIn("const APP_VERSION = '6.4.1'", app)
        self.assertIn("const APP_VERSION = '6.4.1'", worker)
        self.assertIn("V6.4.1", index)
        for asset in ("app.js", "mission-engine.js", "persistence.js", "styles.css"):
            self.assertIn(f"{asset}?v=6.4.1", index)
        for asset in (
            "Missions/manifest.json",
            "Missions/mission.schema.json",
            "Missions/definition-01-shifting-labyrinth.json",
            "Missions/definition-02-demolition-protocol.json",
            "Missions/definition-03-recover-transponder.json",
            "Missions/definition-04-destroy-sarcophagus.json",
            "Missions/definition-05-scout-sub-crypt.json",
        ):
            self.assertIn(f"'./{asset}'", worker)
        self.assertEqual(
            manifest["definitions"],
            [
                {"id": "01", "file": "definition-01-shifting-labyrinth.json"},
                {"id": "02", "file": "definition-02-demolition-protocol.json"},
                {"id": "03", "file": "definition-03-recover-transponder.json"},
                {"id": "04", "file": "definition-04-destroy-sarcophagus.json"},
                {"id": "05", "file": "definition-05-scout-sub-crypt.json"},
            ],
        )
        self.assertEqual(
            len(re.findall(r"definition-[^'\"]+\.json", worker)), 5
        )


if __name__ == "__main__":
    unittest.main()
