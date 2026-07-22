#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION_FILES = sorted((ROOT / "Missions").glob("[0-9][0-9]-*.json"))


class RemediationPr8MissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()
        cls.missions = [json.loads(path.read_text()) for path in MISSION_FILES]
        cls.by_type = {mission["missionEngine"]["type"]: mission for mission in cls.missions}

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_all_six_missions_define_distinct_official_objectives(self):
        self.assertEqual(len(self.missions), 6)
        self.assertEqual(set(self.by_type), {"escape", "sabotage", "transponder", "destruction", "scout", "regroup"})
        self.assertEqual(self.by_type["sabotage"]["missionEngine"]["required"], 7)
        self.assertEqual(self.by_type["destruction"]["missionEngine"]["required"], 20)
        self.assertEqual(self.by_type["scout"]["missionEngine"]["required"], 3)

    def test_mission_one_waits_for_every_operative_and_requires_half_to_escape(self):
        evaluator = self.source("escape:(engine,progress)=>{", "sabotage:(engine,progress)")
        self.assertIn("departed.size<total", evaluator)
        self.assertIn("Math.ceil(total/2)", evaluator)
        self.assertNotIn("activeNpos", evaluator)
        self.assertNotIn("failedExitIds", self.app)
        self.assertNotIn("Other Exit", self.app)
        self.assertIn("missionStrategyPending", self.app)
        self.assertIn("reinforcementPending||placementPending||missionPending", self.app)

    def test_mission_two_tracks_individual_permanently_open_features(self):
        engine = self.by_type["sabotage"]["missionEngine"]
        self.assertEqual(len(engine["features"]), 11)
        self.assertEqual(len({item["id"] for item in engine["features"]}), 11)
        self.assertIn("completedFeatureIds", self.app)

    def test_mission_three_uses_official_search_threshold_and_carrier_escape(self):
        handler = self.source("$$('[data-search-site]')", "$('#transponderEscape')")
        self.assertIn("result>otherRemaining", handler)
        self.assertIn("progress.carrierId=carrier", handler)
        evaluator = self.source("transponder:(engine,progress)", "destruction:(engine,progress)")
        self.assertIn("progress.escaped?'victory'", evaluator)
        self.assertIn("const transponderFound=Object.values(progress.sites).includes('found')", self.app)
        self.assertIn("id=\"transponderCarrier\"", self.app)
        self.assertIn("!state.playerCasualtyIds.includes(progress.carrierId)", self.app)

    def test_mission_four_progresses_by_2d6_and_repairs_during_ready_step(self):
        self.assertIn("const amount=roll()+roll();state.missionState.destruction+=amount", self.app)
        hook = self.source("function applyMissionReadyHooks()", "function determineInitiativeStep()")
        self.assertIn("repairRoll-controllers", hook)
        self.assertIn("state.missionState.destruction-=repaired", hook)

    def test_mission_five_awakens_once_and_scouts_only_after_placement(self):
        renderer = self.source("scout:(engine,progress)=>{", "regroup:(engine,progress)=>{")
        self.assertIn("First Open / Entry", renderer)
        self.assertIn("awakening?.placementConfirmed", renderer)
        handler = self.source("$$('[data-awaken-room]')", "$$('[data-regroup-check]')")
        self.assertIn("Math.min(5,rollD3()+threatGrade())", handler)
        self.assertIn("order:'Conceal'", handler)
        self.assertIn("setThreat(gradeFloor-state.threat,'Scout Room')", handler)
        self.assertIn("ready:true,dormant:false", handler)
        self.assertIn("stage.hatch&&state.missionId!=='scout-sub-crypt'", self.app)

    def test_mission_six_victory_is_only_evaluated_at_end_of_turning_point(self):
        evaluator = self.source("regroup:(engine,progress,timing)=>{", "  };\n\n  function missionOutcome")
        self.assertIn("timing!=='end-turning-point'", evaluator)
        for predicate in ("inDropZone", "outsideNpoControl", "nearPlayer"):
            self.assertIn(predicate, evaluator)
        self.assertIn("checkGameEnd('end-turning-point')", self.app)
        self.assertIn("if(missionEngine()?.type==='regroup')state.missionState={operativeChecks:{},lastCheckedTurningPoint:state.turningPoint}", self.app)

    def test_defeat_is_player_elimination_not_npo_elimination(self):
        outcome = self.source("function missionOutcome(timing='immediate')", "function completeMission(outcome)")
        self.assertIn("livingPlayerOperativeCount()===0", outcome)
        game_end = self.source("function checkGameEnd(timing='immediate')", "function totalLivingOperatives()")
        self.assertNotIn("activeNpos().length===0", game_end)
        self.assertNotIn("turningPoint>=4", self.app)

    def test_state_persists_and_legacy_tracker_is_migrated(self):
        normalize = self.source("function normalizeMissionState", "  const initialState")
        for field in ("escapedIds", "completedFeatureIds", "sites", "destruction", "scoutedRoomIds", "operativeChecks"):
            self.assertIn(field, normalize)
        self.assertIn("normalizeMissionState(raw?.missionState,savedMission,raw?.tracker)", self.app)
        self.assertIn("localStorage.setItem(STORAGE_KEY,JSON.stringify(state))", self.app)

    def test_completed_outcome_is_preserved_for_review(self):
        complete = self.source("function completeMission(outcome)", "function checkGameEnd")
        self.assertIn("state.gameEnd=outcome", complete)
        self.assertIn("state.completed=true", complete)
        self.assertIn("Completed mission state is preserved for review", self.app)
        self.assertIn("Assets/Images/${victory?'victory':'defeat'}.png", self.app)

    def test_version_and_cache_identifiers_are_synchronized(self):
        expected = "5.7.7"
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"styles.css?v={expected}", index)
        self.assertIn(f"app.js?v={expected}", index)
        self.assertIn(f"V{expected}", index)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / "service-worker.js").read_text())
        self.assertIn(f"## v{expected}", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
