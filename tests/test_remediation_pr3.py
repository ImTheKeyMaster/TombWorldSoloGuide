#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RemediationPr3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def function_source(self, name, next_name):
        return self.app.split(f"function {name}(", 1)[1].split(f"function {next_name}(", 1)[0]

    def test_strategy_pipeline_order(self):
        source = self.function_source("startTurningPoint", "completeStrategyStage")
        calls = ["processReadyStep();", "applyMissionReadyHooks();", "determineInitiative();", "processEventStage();", "processReinforcementStage();"]
        self.assertEqual(sorted(calls, key=source.index), calls)
        self.assertIn("strategyPipeline={current:'ready',completed:[]}", source)

    def test_interactive_event_blocks_reinforcements_until_resolved(self):
        start = self.function_source("startTurningPoint", "completeStrategyStage")
        self.assertIn("if(!state.strategyData.eventPending)processReinforcementStage();", start)
        event_stage = self.function_source("processEventStage", "eventNeedsResolution")
        self.assertIn("d.eventPending=eventNeedsResolution(d.event)", event_stage)
        self.assertIn("if(d.eventPending)return", event_stage)
        resolution = self.function_source("resolveStrategyNpoEvent", "randomReinforcement")
        self.assertLess(resolution.index("d.eventPending=false"), resolution.index("processReinforcementStage();"))
        reinforcement = self.function_source("processReinforcementStage", "rollInitiative")
        self.assertIn("completed.includes('reinforcement')", reinforcement)

    def test_event_capacity_is_evaluated_before_reinforcements(self):
        event_gate = self.function_source("eventNeedsResolution", "processReinforcementStage")
        self.assertIn("activeNpos().length<MAX_NPOS||hasWoundedTarget", event_gate)
        strategy_card = self.function_source("strategyCard", "actualReinforcementCount")
        self.assertIn("Resolve the Tomb World event before generating reinforcements", strategy_card)
        self.assertIn("reinforcementPending?'disabled'", strategy_card)

    def test_mission_four_repair_is_a_ready_hook(self):
        source = self.function_source("applyMissionReadyHooks", "determineInitiative")
        self.assertIn("state.missionId==='destroy-sarcophagus'", source)
        self.assertIn("repairRoll-controllers", source)
        self.assertIn("state.tracker-=repaired", source)
        self.assertIn("id:'nanoscarab-repair'", source)
        self.assertIn("during the Ready step", source)

    def test_dormant_npos_cannot_ready_at_threat_zero(self):
        ready = self.function_source("processReadyStep", "applyMissionReadyHooks")
        self.assertIn("npo.dormant=dormant", ready)
        self.assertIn("npo.ready=!dormant", ready)
        transition = self.function_source("setThreat", "escapeHtml")
        self.assertIn("before===0&&state.threat>0", transition)
        self.assertIn("npo.dormant=false;npo.ready=true", transition)
        self.assertIn("npo.dormant=true;npo.ready=false", transition)
        self.assertIn("!n.dormant)n.ready=!n.ready", self.app)

    def test_initiative_automatic_cases_precede_event(self):
        initiative = self.function_source("rollInitiative", "beginFirefight")
        self.assertIn("state.turningPoint===1||state.threat===0", initiative)
        self.assertIn("suggestedInitiative='player'", initiative)
        self.assertIn("initiativeMode='automatic'", initiative)
        self.assertIn("initiativeMode='rolled'", initiative)
        pipeline = self.function_source("startTurningPoint", "completeStrategyStage")
        self.assertLess(pipeline.index("determineInitiative();"), pipeline.index("processEventStage();"))

    def test_initiative_screen_uses_persisted_result_mode(self):
        strategy_card = self.function_source("strategyCard", "actualReinforcementCount")
        self.assertIn("d.initiativeMode==='automatic'", strategy_card)
        bind_play = self.function_source("bindPlay", "startTurningPoint")
        self.assertIn("initiativeRolling=state.strategyData.initiativeMode==='rolled'", bind_play)
        animation = self.function_source("animateInitiativeResult", "activationTracker")
        self.assertIn("state.strategyData?.initiativeMode==='automatic'", animation)
        self.assertNotIn("state.threat===0", animation)

    def test_legacy_null_rolls_migrate_as_automatic_initiative(self):
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("hasRolledInitiative?'rolled':'automatic'", normalize)
        self.assertIn("Threat was 0 when initiative was determined", normalize)

    def test_import_normalizes_threat_and_new_state(self):
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("Number(raw?.threat)", normalize)
        self.assertIn("Math.max(0,Math.min(15,Math.round(importedThreat)))", normalize)
        self.assertIn("npo.dormant=merged.threat===0", normalize)
        self.assertIn("merged.strategyPipeline", normalize)

    def test_versions_are_synchronized(self):
        expected = "4.2.0"
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / "service-worker.js").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"styles.css?v={expected}", index)
        self.assertIn(f"app.js?v={expected}", index)
        self.assertIn(f"V{expected}", index)
        self.assertTrue((ROOT / "README.md").read_text().startswith(f"# Tomb World Solo Guide v{expected}"))

if __name__ == "__main__":
    unittest.main()
