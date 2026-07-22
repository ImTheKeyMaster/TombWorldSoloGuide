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
        event_stage = self.function_source("processEventStage", "eventRecord")
        self.assertIn("if(d.event){beginCurrentEvent();return;}", event_stage)
        current = self.function_source("beginCurrentEvent", "completeCurrentEvent")
        self.assertIn("d.eventPending=true", current)
        resolution = self.function_source("completeCurrentEvent", "redrawCurrentEvent")
        self.assertIn("d.eventPending=false", resolution)
        self.assertIn("beginCurrentEvent();", resolution)
        reinforcement = self.function_source("processReinforcementStage", "rollInitiative")
        self.assertIn("completed.includes('reinforcement')", reinforcement)

    def test_event_capacity_is_evaluated_before_reinforcements(self):
        event_gate = self.function_source("beginCurrentEvent", "completeCurrentEvent")
        self.assertIn("activeNpos().length>=MAX_NPOS", event_gate)
        self.assertIn("redrawCurrentEvent", event_gate)
        strategy_card = self.function_source("strategyCard", "strategyEventHtml")
        self.assertIn("Resolve the Tomb World event before generating reinforcements", strategy_card)
        self.assertIn("reinforcementPending||placementPending||missionPending?'disabled'", strategy_card)

    def test_mission_four_repair_is_a_ready_hook(self):
        source = self.function_source("applyMissionReadyHooks", "determineInitiative")
        self.assertIn("executeMissionLifecycleHook('onStrategyPhaseReadyStep'", source)
        self.assertIn("phase:'strategy-ready'", source)
        self.assertIn("turningPoint:state.turningPoint", self.app)
        self.assertIn("outcomes.filter(outcome=>outcome.status==='completed')", source)
        self.assertIn("progress changed from", self.app)

    def test_sarcophagus_controller_count_is_integer_and_roster_bounded(self):
        helper = self.function_source("normalizeSarcophagusControllers", "checkGameEnd")
        self.assertIn("Math.round(Number(value)||0)", helper)
        self.assertIn("Math.min(limit", helper)
        numeric_input = self.function_source("requestMissionNumber", "runMissionEvent")
        self.assertIn("Number.isInteger(value)", numeric_input)
        self.assertIn("inPlayLivingPlayerOperativeCount()", numeric_input)
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("livingImportedPlayers", normalize)
        self.assertIn("normalizeSarcophagusControllers(raw.missionReadyContext.sarcophagusControllers,livingImportedPlayers)", normalize)

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

    def test_resolved_initiative_routes_directly_to_firefight(self):
        bind_play = self.function_source("bindPlay", "startTurningPoint")
        self.assertIn("beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player')", bind_play)
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("merged.phase==='strategy'&&merged.strategyStage==='initiative'", normalize)
        self.assertIn("merged.nextSide=resolvedSide", normalize)
        self.assertNotIn("Begin Player Activation", self.app)
        self.assertNotIn("Begin with NPOs", self.app)
        self.assertNotIn("data-init", self.app)

    def test_firefight_activation_screens_omit_initiative_message(self):
        next_step = self.function_source("nextStepCard", "missionStrategyPending")
        player_activation, npo_activation = next_step.split("if(state.nextSide==='npo'", 1)
        self.assertNotIn("initiativeStatusHtml()", player_activation)
        self.assertNotIn("initiativeStatusHtml()", npo_activation)
        self.assertNotIn("has initiative", next_step)
        self.assertNotIn("have initiative", next_step)
        self.assertIn("Identify the next ready NPO using the Threat Principle.", npo_activation)
        self.assertNotIn("Apply the Threat Principle to select the next ready NPO.", npo_activation)
        self.assertIn('id="npoActivation">Activate NPO</button>', npo_activation)

    def test_legacy_null_rolls_migrate_as_automatic_initiative(self):
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("hasRolledInitiative?'rolled':'automatic'", normalize)
        self.assertIn("Threat was 0 when initiative was determined", normalize)

    def test_import_normalizes_threat_and_new_state(self):
        normalize = self.function_source("normalizeState", "npoDefinition")
        self.assertIn("boundedInteger(raw.threat,0,15)", normalize)
        self.assertIn("importedDormancy.has(npo.id)", normalize)
        self.assertIn("npo.battlefieldState==='reserve'", normalize)
        self.assertIn("merged.strategyPipeline", normalize)

    def test_versions_are_synchronized(self):
        expected = "6.3.0"
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / "service-worker.js").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"styles.css?v={expected}", index)
        self.assertIn(f"app.js?v={expected}", index)
        self.assertIn(f"V{expected}", index)
        self.assertTrue((ROOT / "README.md").read_text().startswith(f"# Tomb World Solo Guide v{expected}"))

if __name__ == "__main__":
    unittest.main()
