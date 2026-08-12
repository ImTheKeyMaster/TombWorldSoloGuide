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


class GradeGameplayDescriptionTests(unittest.TestCase):
    def test_01_version_and_save_version(self):
        self.assertIn("const APP_VERSION = '8.6.58';", APP)
        self.assertIn("const APP_VERSION = '8.6.58';", WORKER)
        self.assertIn("V8.6.58", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.58"))
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_02_every_grade_uses_one_canonical_configuration(self):
        config = function_source("gradeConfig", "threatGrade")
        helper = function_source("gradeGameplayDescription", "threatLabel")
        engine = function_source("processReinforcementStage", "reinforcementTriggered")
        for row in (
            "{grade:0,name:'Dormant',minThreat:0,maxThreat:0,reinforcements:0}",
            "{grade:1,name:'Stirring',minThreat:1,maxThreat:5,reinforcements:1}",
            "{grade:2,name:'Awakened',minThreat:6,maxThreat:10,reinforcements:2}",
            "{grade:3,name:'Overrun',minThreat:11,maxThreat:15,reinforcements:3}",
        ):
            self.assertIn(row, APP)
        self.assertIn("GRADE_CONFIG.find", config)
        self.assertIn("const config=gradeConfig(grade)", helper)
        self.assertIn("gradeConfig(d.grade).reinforcements", engine)

    def test_03_thresholds_and_event_mechanics_are_unchanged(self):
        event_rule = function_source("normalStrategyEventCount", "strategyEventCount")
        self.assertIn("turningPoint<=1||grade!==3", event_rule)
        self.assertIn("suggestedInitiative==='npo'||threat===15?2:1", event_rule)
        self.assertRegex(APP, r"grade:0,name:'Dormant',minThreat:0,maxThreat:0")
        self.assertRegex(APP, r"grade:1,name:'Stirring',minThreat:1,maxThreat:5")
        self.assertRegex(APP, r"grade:2,name:'Awakened',minThreat:6,maxThreat:10")
        self.assertRegex(APP, r"grade:3,name:'Overrun',minThreat:11,maxThreat:15")

    def test_04_structured_description_has_threat_range_and_effects(self):
        helper = function_source("gradeGameplayDescription", "threatLabel")
        self.assertIn("threatRange:", helper)
        self.assertIn("effects:[reinforcementEffect,eventEffect,awakeningEffect].filter(Boolean)", helper)
        self.assertNotIn("<li>", helper)

    def test_05_reinforcement_and_initial_grade_wording_matches_engine(self):
        helper = function_source("gradeGameplayDescription", "threatLabel")
        self.assertIn("config.reinforcements", helper)
        self.assertIn("No NPO reinforcements will be added through the normal Grade rules.", helper)
        self.assertIn("Deployed NPOs will remain Dormant unless another rule makes them Ready.", helper)
        self.assertIn("Deployed NPOs will enter play Ready instead of Dormant.", helper)

    def test_06_event_description_uses_normal_and_effective_helpers(self):
        helper = function_source("gradeGameplayDescription", "threatLabel")
        self.assertIn("normalStrategyEventCount", helper)
        self.assertIn("strategyEventCount", helper)
        self.assertIn("effectiveEvents>normalEvents", helper)
        self.assertIn("elevatedEvents>standardEvents", helper)
        self.assertIn("Threat reaches ${config.maxThreat}", helper)
        self.assertNotIn("Threat reaches 15", helper)
        self.assertIn("because Restless Tomb is enabled", helper)
        self.assertIn("Math.max(normalCount,1)", function_source("strategyEventCount", "gradeGameplayDescription"))

    def test_07_restless_tomb_does_not_claim_an_extra_grade_three_event(self):
        helper = function_source("gradeGameplayDescription", "threatLabel")
        restless_branch = helper.split("effectiveEvents>normalEvents", 1)[1].split("else if(config.grade===3)", 1)[0]
        self.assertNotIn("+ 1", restless_branch)
        self.assertNotIn("additional", restless_branch)

    def test_08_popup_is_semantic_safe_and_complete(self):
        render = function_source("renderPlay", "activeEventEffectsHtml")
        self.assertIn("GAMEPLAY CHANGES", render)
        self.assertIn('role="dialog"', render)
        self.assertIn("<h2 id=\"grade-milestone-heading\"", render)
        self.assertIn("<h3 id=\"grade-gameplay-heading\"", render)
        self.assertIn("<ul>", render)
        self.assertIn("gradeDescription.effects.map", render)
        self.assertIn("escapeHtml(effect.text)", render)
        self.assertIn("escapeHtml(gradeDescription.threatRange)", render)
        self.assertIn("dismissGradeMilestone')?.focus", render)

    def test_09_persisted_milestone_is_derived_without_retriggering_rules(self):
        render = function_source("renderPlay", "activeEventEffectsHtml")
        self.assertIn("state.gradeMilestone", render)
        self.assertIn("gradeGameplayDescription", render)
        for mutation in ("setThreat(", "processReinforcementStage(", "processEventStage(", "log(", "save()"):
            self.assertNotIn(mutation, render)

    def test_10_no_vague_placeholder_replaces_gameplay_effects(self):
        helper = function_source("gradeGameplayDescription", "threatLabel")
        for vague in ("grows stronger", "activity increases", "danger escalates", "Advanced Grade rules"):
            self.assertNotIn(vague, helper)

    def test_11_release_assets_and_notes(self):
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f'{asset}?v=8.6.58', INDEX)
        self.assertIn("## v8.6.25", README)
        self.assertIn("**Version 8.6.14 - Explain Grade Gameplay Changes**", README)

    def test_12_next_grade_threshold_uses_canonical_configuration(self):
        helper = function_source("nextGradeThreat", "threatToNext")
        self.assertIn("GRADE_CONFIG[threatGrade()+1]?.minThreat", helper)
        self.assertIn("nextGradeThreat()", function_source("threatToNext", "log"))
        self.assertIn("Next Grade at Threat Level ${nextGradeThreat()}", APP)
        self.assertNotIn("[1,6,11]", APP)


if __name__ == "__main__":
    unittest.main()
