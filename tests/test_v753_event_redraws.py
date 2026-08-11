import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class EventRedrawTests(unittest.TestCase):
    def setUp(self):
        self.button = source("const impossibleControl=", "return `<div class=\"summary-box strategy-event")
        self.binding = source("$('#redrawStrategyEvent')", "$('#continueStrategy')")
        self.helper = source("function drawReplacementEvent", "function currentEvent")
        self.redraw = source("function redrawCurrentEvent", "function processReinforcementStage")
        self.begin = source("function beginCurrentEvent", "function completeCurrentEvent")

    def test_maze_reforms_has_idle_accessible_redraw_button(self):
        self.assertIn("No Valid Changes · Draw Again", self.button)
        self.assertIn('type="button"', self.button)
        self.assertIn('aria-label="No valid terrain changes are possible;', self.button)
        self.assertNotIn(" disabled", self.button)

    def test_button_locks_immediately_and_reenables_after_failure(self):
        self.assertLess(self.binding.index("button.disabled=true"), self.binding.index("redrawCurrentEvent("))
        self.assertIn("if(button.disabled)return", self.binding)
        self.assertIn("if(!redrawCurrentEvent", self.binding)
        self.assertIn("button.disabled=false", self.binding)
        self.assertIn("eventRedrawsInProgress.has(transactionId)", self.redraw)

    def test_atomic_commit_marks_original_and_inserts_one_replacement(self):
        draw_call = "const replacement=drawReplacementEvent(event,eventIndex+1)"
        self.assertIn(draw_call, self.redraw)
        self.assertLess(self.redraw.index(draw_call), self.redraw.index("event.status='redrawn'"))
        self.assertEqual(self.redraw.count(draw_call), 1)
        self.assertIn("state.strategyData.events.splice(insertAt,0,replacement)", self.helper)
        self.assertIn("replacement.requiredBy=event.requiredBy", self.redraw)
        self.assertIn("data.eventIndex=eventIndex+1", self.redraw)
        self.assertIn("data.event=replacement", self.redraw)
        self.assertIn("data.eventPending=true", self.redraw)

    def test_replacement_uses_normal_record_identity_and_physical_weighting(self):
        self.assertIn("const replacement=eventRecord(card)", self.helper)
        self.assertIn("card.instanceId===instanceId", self.helper)
        self.assertNotIn("title", self.helper)
        deck = source("const eventDeck = [", "];\n\n  const missionStateFactories")
        self.assertEqual(deck.count("awakened-warrior"), 4)
        self.assertIn("awakened-warrior-1", deck)
        self.assertIn("awakened-warrior-2", deck)

    def test_safe_recycling_excludes_the_redrawn_physical_card(self):
        self.assertIn("instanceId!==originalEvent.instanceId", self.helper)
        self.assertIn("[...new Set([...available,...used])]", self.helper)
        self.assertIn("state.eventState.used=[instanceId]", self.helper)
        self.assertLess(self.helper.index("if(!validPool.length)return null"), self.helper.index("state.eventState.available="))

    def test_complete_failure_is_retryable_and_does_not_advance(self):
        failure = self.redraw.split("if(!replacement){", 1)[1].split("event.status='redrawn'", 1)[0]
        self.assertIn("status:'failed',committed:false", failure)
        self.assertIn("the redraw remains available", failure)
        self.assertIn("The event deck has no valid replacement card available", failure)
        self.assertIn("data.event=event", failure)
        self.assertIn("data.eventPending=true", failure)
        self.assertIn("return false", failure)
        self.assertNotIn("eventIndex=", failure)
        self.assertNotIn("eventPending=false", failure)
        self.assertNotIn("completeStrategyStage", failure)

    def test_automatic_redraw_failure_keeps_reinforcements_blocked(self):
        failure = self.redraw.split("if(!replacement){", 1)[1].split("event.status='redrawn'", 1)[0]
        turning_point = source("function finishTurningPointStart", "function completeStrategyStage")
        self.assertIn("data.eventPending=true", failure)
        self.assertIn("if(!state.strategyData.eventPending)processReinforcementStage()", turning_point)

    def test_committed_transaction_is_stable_and_persistent(self):
        for field in ("transactionId", "type:'event-redraw'", "turningPoint", "originalEventInstanceId",
                      "originalDefinitionId", "replacementInstanceId", "reason", "status:'committed'", "committed:true"):
            self.assertIn(field, self.redraw)
        self.assertIn("existing.committed", self.redraw)
        self.assertIn("existing.replacementInstanceId", self.redraw)
        self.assertLess(self.redraw.index("save();", self.redraw.index("event.status='redrawn'")),
                        self.redraw.index("render();"))
        self.assertEqual(self.redraw.count("Another event card was drawn."), 1)

    def test_replacement_runs_normal_flow_and_blocks_strategy(self):
        self.assertIn("beginCurrentEvent();", self.redraw)
        strategy = source("function strategyProgressHtml", "function strategyEventHtml")
        self.assertIn("!d.eventPending", strategy)
        self.assertIn("strategyRequiredRedrawPending()", strategy)

    def test_all_impossible_events_share_centralized_redraw(self):
        self.assertIn("if(state.threat===15){redrawCurrentEvent('Threat was already 15.');return;}", self.begin)
        self.assertIn("redrawCurrentEvent('No Scarab Swarm could be set up.');return;", self.begin)
        self.assertIn("redrawCurrentEvent('No Necron Warrior could be set up.');return;", self.begin)
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        for definition_id in ("maze-reforms", "stirrings-of-horror", "chittering-drone", "awakened-warrior"):
            definition = next(line for line in definitions.splitlines() if line.strip().startswith(f"'{definition_id}':"))
            self.assertIn("redrawIfImpossible:true", definition)

    def test_summary_counts_redrawn_as_drawn_not_resolved(self):
        presentation = source("function strategyEventPresentation", "function strategyEventRequirementLabel")
        self.assertIn("cardsDrawn:currentEvents.length", presentation)
        self.assertIn("event.status==='resolved'", presentation)
        summary = source("function strategyEventSummary", "function strategyCard")
        self.assertIn("${required} required • ${cardsDrawn}", summary)
        self.assertIn("• ${resolved} resolved", summary)
        self.assertEqual("1 required • 2 cards drawn • 1 resolved",
                         f"{1} required • {2} cards drawn • {1} resolved")

    def test_restless_tomb_slot_is_preserved_until_replacement_resolution(self):
        self.assertIn("replacement.requiredBy=event.requiredBy", self.redraw)
        completion = source("function completeCurrentEvent", "function redrawCurrentEvent")
        self.assertIn("event.requiredBy==='restless-tomb'", completion)
        self.assertIn("event.status='resolved'", completion)
        self.assertNotIn("requiredEventCount", self.redraw)

    def test_existing_persistent_effects_and_aggressive_defence_remain_present(self):
        for definition_id in ("dark-of-the-tomb", "my-will-be-done", "countertemporal-shifting", "reanimation-protocols"):
            self.assertIn(f"'{definition_id}':", APP)
        self.assertIn("showModal('Aggressive Defence'", APP)
        self.assertIn("retaliation.committed=true", APP)

    def test_version_753_is_consistent_without_save_schema_change(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.52"))
        self.assertIn("## v8.6.25", README)
        self.assertIn("const APP_VERSION = '8.6.52';", APP)
        self.assertIn("const APP_VERSION = '8.6.52';", WORKER)
        self.assertIn("V8.6.52", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.52", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
