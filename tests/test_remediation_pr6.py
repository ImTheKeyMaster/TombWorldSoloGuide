#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationPr6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def function_source(self, name, next_name):
        return self.app.split(f"function {name}(", 1)[1].split(f"function {next_name}(", 1)[0]

    def test_reinforcement_runs_only_from_strategy_pipeline_after_events(self):
        start = self.function_source("startTurningPoint", "completeStrategyStage")
        self.assertLess(start.index("processEventStage();"), start.index("processReinforcementStage();"))
        self.assertIn("if(!state.strategyData.eventPending)processReinforcementStage();", start)
        self.assertEqual(self.app.count("processReinforcementStage();"), 2)
        trigger = self.function_source("reinforcementTriggered", "confirmReinforcementPlacement")
        self.assertIn("state.strategyPipeline?.current==='reinforcement'", trigger)
        self.assertIn("state.turningPoint>1", trigger)
        self.assertIn("Number(data.grade)>0", trigger)

    def test_generation_reuses_canonical_table_and_preserves_variant_and_order(self):
        reinforcement = self.function_source("processReinforcementStage", "reinforcementTriggered")
        self.assertIn("randomReinforcement()", reinforcement)
        self.assertIn("weaponId:rr.weaponId", reinforcement)
        self.assertIn("deployed:true", reinforcement)
        self.assertIn("function randomReinforcement(){return rollNpo();}", self.app)
        create = self.function_source("createNpo", "rollNpo")
        self.assertIn("weaponId,order:'Conceal'", create)

    def test_official_quantity_and_ten_npo_limit(self):
        source = self.function_source("processReinforcementStage", "reinforcementTriggered")
        self.assertLess(source.index("d.grade=threatGrade()"), source.index("requested=d.grade"))
        self.assertIn("requested=d.grade", source)
        self.assertIn("MAX_NPOS-activeNpos().length", source)
        self.assertIn("actual=Math.min(requested,slots)", source)
        self.assertIn("blocked=requested-actual", source)
        self.assertIn("Battlefield NPO limit reached.", self.app)

    def test_placement_is_manual_and_blocks_progress_until_confirmed(self):
        card = self.function_source("strategyCard", "strategyEventHtml")
        self.assertIn("Randomly determine an open hatchway", card)
        self.assertIn("printed placement requirements", card)
        self.assertIn("placementPending||missionPending?'disabled'", card)
        placement = self.function_source("confirmReinforcementPlacement", "recordReinforcementHatchway")
        self.assertIn("Boolean(confirmed&&npo.reinforcement.hatchway)", placement)
        self.assertIn("npo.deployed=true", placement)
        self.assertIn("placementConfirmed", placement)
        self.assertNotIn("coordinates", placement)
        hatchway = self.function_source("recordReinforcementHatchway", "rollInitiative")
        self.assertIn("recordedHatchway=hatchway.trim()", hatchway)
        self.assertIn("npo.reinforcement.placementConfirmed=false", hatchway)
        self.assertIn("npo.deployed=true", hatchway)
        self.assertIn("state.reinforcementState.status='placement'", hatchway)
        self.assertIn("save();", hatchway)
        self.assertNotIn("save();render();", hatchway)
        self.assertIn("setTimeout(render,0);", hatchway)

    def test_reinforcement_state_and_metadata_are_normalized(self):
        initial = self.app.split("const initialState = () => ({", 1)[1].split("\n  });", 1)[0]
        self.assertIn("reinforcementState:{turningPoint:0,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0}", initial)
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("isRecord(raw.reinforcementState)", normalize)
        self.assertIn("normalizeIdList(importedReinforcements.operativeIds", normalize)
        npo = self.function_source("normalizeNpo", "mission")
        self.assertIn("placementConfirmed:Boolean", npo)


if __name__ == "__main__":
    unittest.main()
