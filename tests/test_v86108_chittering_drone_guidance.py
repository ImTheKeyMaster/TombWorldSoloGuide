from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class ChitteringDroneGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.definition = next(
            line for line in APP.split("const eventDefinitions = {", 1)[1].split("const eventDeck = [", 1)[0].splitlines()
            if line.strip().startswith("'chittering-drone':")
        )
        self.presentation = source("function strategyEventHtml", "function activationTracker")
        self.begin = source("function beginCurrentEvent", "function completeCurrentEvent")
        self.resolve = source("function resolveStrategyEvent", "function randomReinforcement")

    def test_official_effect_text_and_event_engine_branches_are_preserved(self):
        self.assertIn("If a Canoptek Scarab Swarm has lost any wounds, it regains all lost wounds.", self.definition)
        self.assertIn("redrawIfImpossible:true", self.definition)
        self.assertIn("wounded.length===1", self.begin)
        self.assertIn("event.eligibleNpoIds=wounded.map", self.begin)
        self.assertIn("No Scarab Swarm could be set up.", self.begin)
        self.assertIn("order:'Conceal'", self.resolve)
        self.assertIn("n.ready=true;n.dormant=false", self.resolve)

    def test_single_wounded_scarab_is_automatic_without_confirmation(self):
        single = self.begin.split("if(wounded.length===1)", 1)[1].split("if(wounded.length>1)", 1)[0]
        self.assertIn("wounded[0].wounds=wounded[0].maxWounds", single)
        self.assertIn("The Guide automatically restored", single)
        self.assertIn("(${before} → ${wounded[0].maxWounds})", single)
        self.assertIn("completeCurrentEvent", single)
        self.assertNotIn("eventPending=true", single)

    def test_multiple_wounded_scarabs_have_automatic_guidance_and_precise_action(self):
        self.assertIn("Multiple wounded Canoptek Scarab Swarms are eligible. Choose one below.", self.presentation)
        self.assertIn("The Guide will automatically restore the selected swarm to full wounds.", self.presentation)
        self.assertIn("Restore Selected Scarab Swarm", self.presentation)
        self.assertIn("event.eligibleNpoIds.map", self.presentation)
        self.assertIn("item.wounds<item.maxWounds", self.resolve)
        self.assertIn("n.wounds=n.maxWounds", self.resolve)
        self.assertIn("The Guide automatically restored", self.resolve)

    def test_placement_branch_explains_roster_check_and_keeps_confirmation(self):
        self.assertIn("No wounded Canoptek Scarab Swarms are currently on the battlefield.", self.presentation)
        self.assertIn("Set up one Ready Canoptek Scarab Swarm with a Conceal order", self.presentation)
        self.assertIn("'chittering-drone':'Confirm Scarab Placement'", self.presentation)
        self.assertIn("${scarabGuide}<div class=\"event-controls\">${scarabChoices}", self.presentation)

    def test_guidance_reuses_accessible_mobile_safe_event_styles(self):
        self.assertIn('<h4>GUIDE ACTION</h4><p>', self.presentation)
        self.assertIn(".event-guide-action p", STYLES)
        self.assertIn("overflow-wrap:anywhere", STYLES.split(".event-guide-action p", 1)[1].split("}", 1)[0])
        self.assertIn(".event-controls .btn{width:100%}", STYLES)

    def test_release_versions_match_without_save_schema_change(self):
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f"V{CURRENT_APP_VERSION}", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
