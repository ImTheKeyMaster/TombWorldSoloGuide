import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperativeInPlayTests(unittest.TestCase):
    def test_generic_state_queries_and_stale_activation_guards(self):
        app = (ROOT / "app.js").read_text()
        self.assertIn("function isPlayerOperativeInPlay(id)", app)
        self.assertIn("function inPlayPlayerOperativeIds()", app)
        self.assertIn("return inPlayPlayerOperativeIds().filter(id=>!used.has(id)&&!casualties.has(id));", app)
        self.assertIn("if(!remainingPlayerOperatives().includes(operativeId))", app)
        self.assertIn("function inPlayLivingPlayerOperativeIds()", app)
        self.assertIn("return inPlayLivingPlayerOperativeIds();", app)
        self.assertIn("inPlayLivingPlayerOperativeCount()", app)
        self.assertIn("playerOperativeCount:Array.isArray(state.playerRoster)?state.playerRoster.length:0", app)
        self.assertNotIn("state.missionId==='01'", app)
        self.assertNotIn("state.missionId===\"01\"", app)
        self.assertIn("Legacy escape progress needs confirmation.", app)

    def test_mission_01_uses_generic_definition_operation(self):
        definition = json.loads((ROOT / "Missions/definition-01-shifting-labyrinth.json").read_text())
        record, correct = definition["actions"][:2]
        self.assertEqual(record["operations"][0], {
            "type": "setOperativeInPlay", "side": "player",
            "operativeIdFrom": "operativeId", "inPlay": False, "reason": "escaped"
        })
        self.assertEqual(correct["operations"][0]["type"], "setOperativeInPlay")
        self.assertTrue(correct["operations"][0]["inPlay"])
        self.assertFalse(definition["completion"]["endsBattle"])

    def test_generic_engine_contains_no_mission_01_branch(self):
        engine = (ROOT / "mission-engine.js").read_text()
        self.assertIn("case 'setOperativeInPlay'", engine)
        self.assertNotIn("Mission 01", engine)
        self.assertNotIn("missionId==='01'", engine)
        self.assertNotIn("missionId===\"01\"", engine)


if __name__ == "__main__":
    unittest.main()
