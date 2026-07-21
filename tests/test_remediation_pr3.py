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
        pipeline = self.function_source("startTurningPoint", "completeStrategyStage")
        self.assertLess(pipeline.index("determineInitiative();"), pipeline.index("processEventStage();"))

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
