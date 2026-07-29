#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class ActivationTrackerV712Tests(unittest.TestCase):
    def source(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def run_tracker_helpers(self, roster, npo_activated=0):
        helpers = "function trackerNpos()" + self.source("function trackerNpos()", "function livingPlayerOperativeCount")
        script = f"""
const state={{roster:{json.dumps(roster)},npoActivated:{npo_activated}}};
{helpers}
console.log(JSON.stringify({{rows:trackerNpos().map(npo=>({{id:npo.id,...npoTrackerStatus(npo)}}))}}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["rows"]

    @staticmethod
    def roster(threat):
        dormant = threat == 0
        return [
            {"id": "Warrior 10", "wounds": 7, "battlefieldState": "deployed", "dormant": dormant, "ready": not dormant},
            {"id": "Warrior 2", "wounds": 7, "battlefieldState": "deployed", "dormant": dormant, "ready": not dormant},
            {"id": "Reserve", "wounds": 7, "battlefieldState": "reserve", "dormant": False, "ready": False},
        ]

    def test_threat_zero_scope_and_status_are_common_to_all_six_missions(self):
        for mission in ("01", "02", "03", "04", "05", "06"):
            with self.subTest(mission=mission):
                rows = self.run_tracker_helpers(self.roster(0))
                self.assertEqual([row["id"] for row in rows], ["Warrior 10", "Warrior 2"])
                self.assertTrue(all(row["status"] == "DORMANT" for row in rows))
                self.assertNotIn("ACTIVATED", [row["status"] for row in rows])
        helper = self.source("function trackerNpos()", "function livingPlayerOperativeCount")
        self.assertNotIn("missionId", helper)

    def test_reserve_cannot_fall_through_to_activated(self):
        reserve = self.roster(0)[2]
        rows = self.run_tracker_helpers([reserve])
        self.assertEqual(rows, [])
        resolver = self.source("function npoTrackerStatus(npo)", "function livingPlayerOperativeCount")
        self.assertLess(resolver.index("battlefieldState==='reserve'"), resolver.index("status:'ACTIVATED'"))

    def test_dormant_ready_activated_and_eliminated_precedence(self):
        roster = [
            {"id": "Dormant", "wounds": 5, "battlefieldState": "deployed", "dormant": True, "ready": False},
            {"id": "Ready", "wounds": 5, "battlefieldState": "deployed", "dormant": False, "ready": True},
            {"id": "Activated", "wounds": 5, "battlefieldState": "deployed", "dormant": False, "ready": False},
            {"id": "Eliminated", "wounds": 0, "battlefieldState": "out-of-action", "dormant": False, "ready": False},
        ]
        rows = self.run_tracker_helpers(roster, npo_activated=1)
        self.assertEqual([(r["status"], r["className"]) for r in rows], [
            ("DORMANT", "dormant"), ("READY", "ready"),
            ("ACTIVATED", "activated"), ("ELIMINATED", "eliminated")])

    def test_threat_above_zero_and_one_completed_activation(self):
        roster = self.roster(1)
        self.assertEqual([r["status"] for r in self.run_tracker_helpers(roster)], ["READY", "READY"])
        roster[0]["ready"] = False
        self.assertEqual([r["status"] for r in self.run_tracker_helpers(roster, npo_activated=1)], ["ACTIVATED", "READY"])

    def test_player_activation_does_not_classify_an_npo_as_activated(self):
        roster = self.roster(1)
        roster[0]["ready"] = False
        self.assertEqual([r["status"] for r in self.run_tracker_helpers(roster)], ["READY", "READY"])
        resolver = self.source("function npoTrackerStatus(npo)", "function livingPlayerOperativeCount")
        self.assertIn("state.npoActivated>0", resolver)
        self.assertNotIn("state.activationNumber>0", resolver)

    def test_tracker_uses_filtered_sorted_copy_and_leaves_gameplay_selection_order(self):
        tracker = self.source("function activationTracker()", "function showPlayerOperativeStatus")
        self.assertIn("sortedNposForDisplay(trackerNpos()).map", tracker)
        self.assertNotIn("state.roster.sort", APP)
        selection = self.source("function showNpoSelection()", "function remainingPlayerOperatives")
        self.assertIn("const candidates=readyNpos()", selection)
        self.assertNotIn("candidates=sortedNposForDisplay", selection)

    def test_reinforcement_is_reserved_until_confirmation_then_uses_threat_state(self):
        generation = self.source("function processReinforcementStage()", "function reinforcementTriggered")
        self.assertIn("battlefieldState='reserve'", generation)
        self.assertIn("deployed:false", generation)
        confirmation = self.source("function confirmReinforcementPlacement", "function rollInitiative")
        self.assertIn("battlefieldState=npo.deployed?'deployed':'reserve'", confirmation)
        self.assertIn("npo.dormant=npo.deployed&&state.threat===0", confirmation)
        self.assertIn("npo.ready=npo.deployed&&!npo.dormant", confirmation)

    def test_scuttling_creates_a_new_deployed_ready_instance(self):
        scuttling = self.source("function createCeaselessScuttlingWarrior", "function aggressiveDefenceDamage")
        self.assertIn("createNpo(definition.type,definition.name,{weaponId,ready:true,dormant:false})", scuttling)
        self.assertIn("state.roster.push(warrior)", scuttling)
        create = self.source("function createNpo", "function rollNpo")
        self.assertIn("id:physicalInstance.id", create)

    def test_save_normalization_preserves_canonical_tracker_states(self):
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("importedDormancy.has(npo.id)?importedDormancy.get(npo.id)", normalize)
        self.assertIn("npo.battlefieldState==='reserve'", normalize)
        self.assertIn("npo.dormant=false", normalize)
        self.assertIn("merged.reinforcementState.status==='placement'", normalize)
        npo = self.source("function normalizeNpo(npo)", "function mission()")
        self.assertIn("['reserve','deployed','out-of-action']", npo)

    def test_distinct_accessible_dormant_style_and_elimination_treatment(self):
        self.assertIn(".tracker-operative.dormant{", CSS)
        self.assertIn(".tracker-operative.reserve{", CSS)
        self.assertIn(".tracker-operative.eliminated{", CSS)
        tracker = self.source("function activationTracker()", "function showPlayerOperativeStatus")
        self.assertIn("<strong>${trackerStatus.status}</strong>", tracker)
        self.assertIn("tracker-elimination-icon", tracker)

    def test_player_tracker_and_activation_count_are_unchanged(self):
        tracker = self.source("function activationTracker()", "function showPlayerOperativeStatus")
        self.assertIn("const playerRows=(state.playerRoster||[]).map", tracker)
        self.assertIn("${state.activationNumber} activations completed", tracker)
        self.assertNotIn("npoRows.length", tracker)

    def test_current_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.0.0';", APP)
        self.assertIn("const APP_VERSION = '8.0.0';", WORKER)
        self.assertIn("V8.0.0", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "app.js"):
            self.assertIn(f"{asset}?v=8.0.0", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.0.0"))


if __name__ == "__main__":
    unittest.main()
