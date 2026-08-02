import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def function_source(name, next_name):
    return APP.split(f"function {name}", 1)[1].split(f"function {next_name}", 1)[0]


class GradeDescriptionClarityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = function_source("gradeGameplayDescription", "threatLabel")
        cls.renderer = function_source("renderPlay", "activeEventEffectsHtml")

    def test_01_application_displays_version_8616(self):
        self.assertIn("const APP_VERSION = '8.6.23';", APP)
        self.assertIn("const APP_VERSION = '8.6.23';", WORKER)
        self.assertIn("V8.6.23", INDEX)

    def test_02_effects_are_structured_explanations(self):
        for field in ("id:", "subject:", "automation:", "text:"):
            self.assertIn(field, self.helper)
        self.assertIn("effect.text", self.renderer)

    def test_03_newly_active_effects_use_future_tense(self):
        for phrase in ("will prompt you", "will be added", "will be resolved", "will remain", "will enter play"):
            self.assertIn(phrase, self.helper)

    def test_04_reinforcement_ownership_is_explicit(self):
        self.assertIn("NPO reinforcement${config.reinforcements===1?'':'s'}", self.helper)
        self.assertIn("subject:'NPO reinforcements'", self.helper)

    def test_05_no_standalone_reinforcement_card_wording(self):
        self.assertNotIn("Deploy ${config.reinforcements} reinforcement", self.helper)
        self.assertNotIn("No normal reinforcements", self.helper)
        self.assertIn("NPO reinforcement${config.reinforcements===1?'':'s'}", self.helper)
        self.assertIn("No NPO reinforcements will be added", self.helper)

    def test_06_automatic_effects_are_not_commands(self):
        self.assertNotRegex(self.helper, r"(?:'|`)(?:Deploy|Resolve) ")
        self.assertIn("automation:'automatic'", self.helper)

    def test_07_guided_effects_explain_the_prompt(self):
        self.assertGreaterEqual(self.helper.count("The Guide will prompt you"), 3)
        self.assertIn("automation:config.reinforcements?'guided':'informational'", self.helper)

    def test_08_ready_and_dormant_are_future_oriented(self):
        self.assertIn("will remain Dormant", self.helper)
        self.assertIn("will enter play Ready instead of Dormant", self.helper)

    def test_09_singular_reinforcement_grammar(self):
        self.assertIn("config.reinforcements===1?'':'s'", self.helper)
        self.assertIn("{grade:1,name:'Stirring',minThreat:1,maxThreat:5,reinforcements:1}", APP)

    def test_10_plural_reinforcement_grammar(self):
        self.assertIn("{grade:2,name:'Awakened',minThreat:6,maxThreat:10,reinforcements:2}", APP)
        self.assertIn("{grade:3,name:'Overrun',minThreat:11,maxThreat:15,reinforcements:3}", APP)

    def test_11_event_timing_uses_gameplay_engine(self):
        self.assertIn("normalStrategyEventCount", self.helper)
        self.assertIn("strategyEventCount", self.helper)
        self.assertIn("during each Strategy Phase after Turning Point 1", self.helper)

    def test_12_reinforcement_timing_matches_engine(self):
        engine = function_source("reinforcementTriggered", "confirmReinforcementPlacement")
        self.assertIn("state.turningPoint>1", engine)
        self.assertIn("after Turning Point 1", self.helper)

    def test_13_restless_tomb_uses_effective_event_count(self):
        self.assertIn("effectiveEvents=strategyEventCount", self.helper)
        self.assertIn("effectiveEvents>normalEvents", self.helper)
        self.assertIn("because Restless Tomb is enabled", self.helper)

    def test_14_restless_tomb_does_not_claim_an_extra_event(self):
        self.assertIn("Math.max(normalCount,1)", function_source("strategyEventCount", "gradeGameplayDescription"))
        self.assertNotIn("additional Tomb World event", self.helper)

    def test_15_all_grades_share_consistent_terminology(self):
        configured = re.findall(r"\{grade:\d,name:'[^']+',minThreat:\d+,maxThreat:\d+,reinforcements:\d+\}", APP)
        self.assertEqual(len(configured), 4)
        for term in ("NPO", "Tomb World event", "Strategy Phase", "Turning Point", "Ready", "Dormant"):
            self.assertIn(term, self.helper)

    def test_16_grade_zero_describes_effective_state(self):
        self.assertIn("No NPO reinforcements will be added through the normal Grade rules.", self.helper)
        self.assertIn("No Tomb World events will be resolved through the normal Grade rules.", self.helper)
        self.assertIn("unless another rule makes them Ready", self.helper)

    def test_17_no_vague_thematic_wording(self):
        for phrase in ("More enemies", "threat becomes more dangerous", "unit", "troop", "spawn", "mob"):
            self.assertNotIn(phrase, self.helper)

    def test_18_mechanics_and_thresholds_are_unchanged(self):
        expected = (
            "{grade:0,name:'Dormant',minThreat:0,maxThreat:0,reinforcements:0}",
            "{grade:1,name:'Stirring',minThreat:1,maxThreat:5,reinforcements:1}",
            "{grade:2,name:'Awakened',minThreat:6,maxThreat:10,reinforcements:2}",
            "{grade:3,name:'Overrun',minThreat:11,maxThreat:15,reinforcements:3}",
        )
        for row in expected:
            self.assertIn(row, APP)

    def test_19_refresh_derives_persisted_card_wording(self):
        self.assertIn("state.gradeMilestone?gradeGameplayDescription", self.renderer)
        self.assertIn("state.gradeMilestone.threat", self.renderer)
        self.assertIn("suggestedInitiative:state.strategyData?.suggestedInitiative", self.renderer)
        self.assertIn("restlessTombEnabled:state.restlessTombEnabled", self.renderer)

    def test_20_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_21_release_assets_and_notes_are_current(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.23"))
        self.assertIn("**Version 8.6.16 - Clarify Grade Gameplay Changes**", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.23", INDEX)


if __name__ == "__main__":
    unittest.main()
