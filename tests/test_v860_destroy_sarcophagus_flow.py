import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
DEFINITION = json.loads((ROOT / "Missions/definition-04-destroy-sarcophagus.json").read_text())


class DestroySarcophagusV860Tests(unittest.TestCase):
    def test_version_and_definition(self):
        self.assertIn("const APP_VERSION = '8.6.29';", APP)
        self.assertIn("const APP_VERSION = '8.6.29';", WORKER)
        self.assertIn("V8.6.29", INDEX)
        self.assertTrue(DEFINITION["completion"]["endsBattle"])
        self.assertEqual(DEFINITION["actions"][0]["oncePer"], "activation")
        self.assertEqual(DEFINITION["dialogs"]["objectiveComplete"]["message"], "The sarcophagus has been destroyed. The Player team is victorious.")

    def test_activation_only_guided_presentation(self):
        self.assertIn("Breach Sarcophagus (${breachCost} AP)", APP)
        self.assertIn("Is this operative within the sarcophagus’s control range?", APP)
        self.assertIn("Is this operative outside the control range of every NPO?", APP)
        self.assertIn("Not enough AP to Breach the sarcophagus.", APP)
        self.assertIn("Player operatives can perform Breach Sarcophagus during their activations", APP)
        self.assertNotIn("Breach Sarcophagus (2D6)", APP)
        destruction_renderer = APP.split("destruction:(engine,progress", 1)[1].split("scout:(engine,progress", 1)[0]
        self.assertNotIn("resolveMissionAction", destruction_renderer)

    def test_context_persistence_discount_and_idempotency_guards(self):
        for text in (
            "missionActionContext",
            "operativeId,activationId,apCost",
            "controlRangeConfirmed",
            "enemyControlRangeConfirmed",
            "context.committed=true",
            "button.disabled=true",
            "context.newTotal!=null",
            "stage.missionBreachCommitted",
            "Math.max(1,qualifyingBreachDiscount",
            "!rules.some(rule=>/^(?:Blast|Torrent)",
        ):
            self.assertIn(text, APP)

    def test_engine_rolls_once_per_activation_clamps_and_repairs_only_incomplete(self):
        script = r"""
const assert=require('assert').strict,fs=require('fs');require('./mission-engine.js');
const d=JSON.parse(fs.readFileSync('Missions/definition-04-destroy-sarcophagus.json'));
let calls=0;const e=TombWorldMissionEngine.createMissionEngine({requestDiceRoll:async()=>{calls++;return {dice:[6,6],total:12}},requestNumericInput:async()=>0});
e.initializeMissionRuntime(d);e.setObjectiveValue('destructionPoints',16);
(async()=>{const c={turningPoint:2,activationId:'2:4:player:bombard',operativeId:'bombard'};
 const first=await e.executeMissionAction('breachSarcophagus',c);assert.equal(first.changes[0].before,16);assert.equal(first.changes[0].after,20);assert.equal(calls,1);
 const repeat=await e.executeMissionAction('breachSarcophagus',c);assert.equal(repeat.status,'unavailable');assert.equal(calls,1);
 assert.equal((await e.executeMissionHook('onStrategyPhaseReadyStep',{turningPoint:3}))[0].status,'unavailable');assert.equal(e.getObjectiveValue('destructionPoints'),20);
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_other_mission_completion_definitions_unchanged(self):
        expected = {"01": False, "02": True, "03": True, "05": True}
        for mission_id, ends_battle in expected.items():
            path = next((ROOT / "Missions").glob(f"definition-{mission_id}-*.json"))
            self.assertEqual(json.loads(path.read_text())["completion"]["endsBattle"], ends_battle)


if __name__ == "__main__":
    unittest.main()
