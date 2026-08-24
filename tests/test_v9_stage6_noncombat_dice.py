#!/usr/bin/env python3
import unittest
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class Stage6NoncombatDiceTests(unittest.TestCase):
    def section(self, start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_initiative_is_sequential_provider_dice_with_automatic_exceptions(self):
        flow = self.section("async function rollInitiative", "function beginFirefight")
        self.assertIn("state.turningPoint===1||state.threat===0", flow)
        self.assertEqual(flow.count("await requestDiceResults"), 2)
        self.assertLess(flow.index("rollerLabel:playerLabel"), flow.index("rollerLabel:'Necrons'"))
        self.assertIn("suggestedInitiative=n>p?'npo':'player'", flow)
        self.assertNotIn("roll()", flow)

    def test_strategy_pipeline_awaits_initiative_and_event_dice(self):
        flow = self.section("async function finishTurningPointStart", "function completeStrategyStage")
        self.assertIn("await determineInitiative()", flow)
        self.assertIn("await processEventStage()", flow)
        self.assertLess(flow.index("await determineInitiative()"), flow.index("await processEventStage()"))
        self.assertLess(flow.index("await processEventStage()"), flow.index("processReinforcementStage()"))
        self.assertIn("if(Array.isArray(state.strategyData.events))await beginCurrentEvent()", flow)

    def test_interrupted_strategy_dice_have_a_safe_idempotent_retry(self):
        normalization = self.section("function normalizeState", "function npoDefinition")
        card = self.section("function strategyCard", "function strategyEventHtml")
        bindings = self.section("function bindPlay", "async function startTurningPoint")
        self.assertIn("merged.strategyData?.initiativeMode!=='pending'", normalization)
        self.assertIn("id=\"retryStrategyDice\"", card)
        self.assertIn("$('#retryStrategyDice')?.addEventListener('click',finishTurningPointStart)", bindings)

    def test_mission_adapter_uses_provider_but_preserves_solo_animation_and_audio(self):
        flow = self.section("async function animateMissionDice", "function requestMissionNumber")
        self.assertIn("suppliedDice||await requestDiceResults", flow)
        self.assertIn("if(isPvpMode())return result", flow)
        self.assertIn("animated-roll", flow)
        self.assertIn("TombWorldDiceSfx.play()", flow)
        self.assertIn("return new Promise", flow)

    def test_mission_fallbacks_are_provider_aware(self):
        helper = self.section("async function missionDiceTotal", "diceEntryUndo.addEventListener")
        self.assertIn("await requestDiceResults", helper)
        for legacy in ("searchRoll?.total??rollD3", "awakenRoll?.total??rollD3", "directionRoll?.total||rollD3"):
            self.assertNotIn(legacy, APP)
        self.assertIn("missionDiceTotal(outcome,'searchRoll'", APP)
        self.assertIn("missionDiceTotal(outcome,'awakenRoll'", APP)
        self.assertIn("missionDiceTotal(outcome,'directionRoll'", APP)
        self.assertIn("missionDiceTotal(outcome,'distanceRoll'", APP)

    def test_breach_sarcophagus_waits_for_exact_two_d6_before_commit(self):
        flow = self.section("async function performBreachSarcophagus", "function confirmMissionAction")
        request = "context.dice=await requestDiceResults({count:2,sides:6"
        self.assertIn(request, flow)
        self.assertLess(flow.index(request), flow.index("context.committed=true"))
        self.assertNotIn("context.dice=[roll(),roll()]", flow)

    def test_event_dice_are_manual_but_selection_remains_automatic(self):
        flow = self.section("async function beginCurrentEvent", "async function completeCurrentEvent")
        self.assertIn("const selectedIndex=roll(remaining.length)-1", flow)
        self.assertIn("title:'SUBJUGATION GLYPHS'", flow)
        self.assertIn("title:'LIVING METAL FLUX'", flow)
        self.assertIn("title:'THE MAZE REFORMS'", flow)
        self.assertIn("sortedNposForDisplay(activeNpos().filter", flow)
        self.assertIn("transaction.rolls=[die]", flow)
        self.assertGreaterEqual(flow.count("save();"), 3)
        self.assertNotIn("const die=roll()", flow)
        self.assertNotIn("openHatchwayLimit=rollD3()", flow)

    def test_administrative_event_selection_remains_automatic(self):
        draw = self.section("function drawEvent", "function drawReplacementEvent")
        replacement = self.section("function drawReplacementEvent", "function currentEvent")
        relocation = self.section("function selectRandomDistinctPlayerOperatives", "function eligibleTransdimensionalRelocationOperativeIds")
        self.assertIn("roll(state.eventState.available.length)", draw)
        self.assertIn("roll(validPool.length)", replacement)
        self.assertIn("roll(index+1)", relocation)
        self.assertNotIn("requestDiceResults", draw + replacement + relocation)

    def test_threat_checks_are_sequential_checkpointed_and_precede_completion(self):
        flow = self.section("async function completePlayerActivation", "function renderNpoActionResult")
        self.assertIn("id:'operateHatch'", flow)
        self.assertIn("id:'breach'", flow)
        self.assertIn("state.missionId!=='scout-sub-crypt'", flow)
        self.assertIn("for(const check of missingThreatChecks)", flow)
        self.assertIn("stage.threatRolls[check.id]=die", flow)
        self.assertIn("if(stage.threatDiceResolving)return false", flow)
        self.assertLess(flow.index("await requestDiceResults"), flow.index("state.playerActivatedIds.push"))
        self.assertIn("inc++;\n      const r=stage.threatRolls.breach", flow)

    def test_nanoscarab_beam_acquires_three_d3_before_mutation_and_ap_commit(self):
        flow = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        self.assertIn("count:3,sides:3,title:'NANOSCARAB BEAM'", flow)
        self.assertIn("result=useNanoscarabBeam(target,dice)", flow)
        self.assertLess(flow.index("await requestDiceResults({count:3"), flow.index("useNanoscarabBeam(target,dice)"))
        self.assertNotIn("useNanoscarabBeam(target);", flow)

    def test_geomantic_disturbance_collects_ordered_two_d6_before_damage(self):
        flow = self.section("function resolveNpoSpecialAction", "function finishNpoSpecialAction")
        self.assertIn("for(const target of targets)", flow)
        self.assertIn("count:2,sides:6,title:'GEOMANTIC DISTURBANCE'", flow)
        self.assertIn("committedRolls[targets.indexOf(operative)]", flow)
        self.assertLess(flow.index("dice=await requestDiceResults"), flow.index("results.forEach"))
        self.assertIn("pendingAction.diceResults=savedRolls", flow)
        helper = self.section("function resolveGeomanticDisturbance", "function markerControlApl")
        self.assertIn("damage:Math.max(0,total-operative.wounds)", helper)

    def test_generation_and_reinforcement_randomness_remain_automatic(self):
        starting = self.section("function startingNpoRoll", "function selectStartingNpos")
        generation = self.section("function rollNpo", "function availableGenerationResult")
        reinforcement = self.section("function processReinforcementStage", "function reinforcementTriggered")
        self.assertIn("rollD3()", starting)
        self.assertIn("roll(6)", generation)
        self.assertIn("randomReinforcement()", reinforcement)
        self.assertNotIn("requestDiceResults", starting + generation + reinforcement)

    def test_version_and_stage7_boundary_are_unchanged(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        initial = self.section("const initialState", "const loadedSave")
        self.assertNotIn("pendingDice", initial)
        self.assertNotIn("diceEntry", initial)


if __name__ == "__main__":
    unittest.main()
