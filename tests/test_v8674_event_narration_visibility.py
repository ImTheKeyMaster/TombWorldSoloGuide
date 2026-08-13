import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


class EventNarrationVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.render_play = source("function renderPlay", "function activeEventEffectsHtml")
        self.visibility = source("function narrateVisibleStrategyEvents", "function beginCurrentEvent")
        self.begin = source("function beginCurrentEvent", "function completeCurrentEvent")
        self.complete = source("function completeCurrentEvent", "function redrawCurrentEvent")

    def test_turning_point_processing_does_not_request_event_narration(self):
        startup = source("function finishTurningPointStart", "function completeStrategyStage")
        self.assertIn("processEventStage();", startup)
        self.assertNotIn("TombWorldNarration", startup)
        self.assertNotIn("narrateAcceptedEvent", self.begin)
        self.assertNotIn("TombWorldNarration", self.complete)

    def test_rendered_events_view_is_the_only_app_level_trigger(self):
        self.assertLess(self.render_play.index("app.innerHTML="), self.render_play.index("narrateVisibleStrategyEvents();"))
        self.assertLess(self.render_play.index("bindPlay();"), self.render_play.index("narrateVisibleStrategyEvents();"))
        self.assertIn("state.phase!=='strategy'", self.visibility)
        self.assertIn("state.strategyStage!=='summary'", self.visibility)
        self.assertIn("strategyViewStep(d)!=='events'", self.visibility)
        self.assertIn("!$('#strategy-step-heading')", self.visibility)

    def test_all_accepted_events_are_requested_once_in_gameplay_order(self):
        self.assertIn("events.slice(0,acceptedCount)", self.visibility)
        self.assertIn("(d.eventIndex||0)+(d.eventPending?1:0)", self.visibility)
        self.assertIn(".forEach(narrateAcceptedEvent)", self.visibility)
        narration = (ROOT / "narration.js").read_text(encoding="utf-8")
        play_event = narration[narration.index("function playEvent"):narration.index("function playOutcome")]
        self.assertIn("automaticPlayback.has(duplicateKey)", play_event)
        self.assertIn("eventQueue.push", play_event)

    def test_redrawn_events_are_never_requested(self):
        self.assertIn("filter(event=>event.status!=='redrawn')", self.visibility)
        redraw = source("function redrawCurrentEvent", "function processReinforcementStage")
        self.assertIn("event.status='redrawn'", redraw)
        self.assertNotIn("narrateAcceptedEvent", redraw)

    def test_rerender_and_back_forward_rely_on_instance_deduplication(self):
        self.assertEqual(self.render_play.count("narrateVisibleStrategyEvents();"), 1)
        self.assertIn("event.instanceId", source("function narrateAcceptedEvent", "function narrateVisibleStrategyEvents"))
        navigation = source("function showStrategyViewStep", "function strategyActionsStepHtml")
        self.assertIn("save();render();", navigation)

    def test_other_narration_paths_and_controls_remain_independent(self):
        narration = (ROOT / "narration.js").read_text(encoding="utf-8")
        for behavior in ("playDeadlyEncounter", "playMissionIntro", "playOutcome", "replayLast", "pauseNarration", "resumeNarration", "stop"):
            self.assertIn(f"function {behavior}", narration)
        self.assertIn("TombWorldNarration.stop();", APP)


if __name__ == "__main__":
    unittest.main()
