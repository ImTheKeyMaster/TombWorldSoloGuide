#!/usr/bin/env python3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class EventPlacementWordingTests(unittest.TestCase):
    def test_current_version_is_consistent_without_save_schema_change(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.63"))
        self.assertIn("## v8.6.25", README)
        self.assertIn("Version 8.6.5 - Show Player Wounds in Target Selection", README)
        self.assertIn("const APP_VERSION = '8.6.63';", APP)
        self.assertIn("const APP_VERSION = '8.6.63';", WORKER)
        self.assertIn("V8.6.63", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.63", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_awakened_warrior_instruction_is_specific(self):
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        awakened = next(line for line in definitions.splitlines() if "'awakened-warrior':" in line)
        self.assertIn("using the placement instructions on the event card", awakened)
        self.assertIn("If no eligible Necron Warrior can be placed", awakened)
        self.assertIn("one Ready Necron Warrior", awakened)
        self.assertNotIn("as described", awakened)

    def test_awakened_warrior_resolution_uses_dynamic_name_and_clear_wording(self):
        resolution = source("function resolveStrategyEvent", "function randomReinforcement")
        expected = "${npoName(n)} was set up Ready with a Conceal order using the event card’s placement instructions."
        self.assertIn(expected, resolution)
        self.assertNotIn("printed placement", resolution.lower())
        self.assertNotIn("placement confirmed", resolution.lower())

    def test_player_facing_runtime_text_has_no_banned_placement_phrases(self):
        for phrase in ("printed placement", "printed requirements", "printed instructions", "as printed", "placement confirmed"):
            self.assertNotIn(phrase, APP.lower())
        self.assertNotIn("printed placement confirmed", INDEX.lower())

    def test_awakened_warrior_confirmation_names_the_action(self):
        event_card = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("'awakened-warrior':'Confirm Necron Warrior Placement'", event_card)
        self.assertIn("aria-live=\"polite\"", event_card)

    def test_transdimensional_relocation_uses_corrected_random_swap_effect(self):
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        relocation = next(line for line in definitions.splitlines() if "'transdimensional-relocation':" in line)
        self.assertIn("Randomly select two Player operatives and swap their positions.", relocation)
        self.assertNotIn("closest to an NPO", relocation)
        self.assertNotIn("placement restrictions", relocation)

    def test_event_selection_allocation_and_impossible_redraw_logic_remain(self):
        deck = source("const eventDeck = [", "];\n\n  const missionStateFactories")
        self.assertEqual(deck.count("awakened-warrior"), 4)
        begin = source("function beginCurrentEvent", "function completeCurrentEvent")
        self.assertIn("activeNpos().length>=MAX_NPOS||!npoInventory()['Necron Warrior'].remaining", begin)
        self.assertIn("redrawCurrentEvent('No Necron Warrior could be set up.');return;", begin)
        resolution = source("function resolveStrategyEvent", "function randomReinforcement")
        self.assertIn("createNpo(type,`${type} E${state.turningPoint}`,{order:'Conceal'})", resolution)
        self.assertIn("n.ready=true;n.dormant=false", resolution)

    def test_pending_and_resolved_event_records_are_preserved_on_load(self):
        normalization = source("function normalizeState", "function npoDefinition")
        self.assertIn("...raw.strategyData", normalization)
        self.assertIn("events:Array.isArray(raw.strategyData.events)?raw.strategyData.events", normalization)
        self.assertIn("status:raw.strategyData.eventPending?'drawn':'resolved'", normalization)
        completion = source("function completeCurrentEvent", "function redrawCurrentEvent")
        self.assertIn("event.status='resolved';event.result=result", completion)
        self.assertIn("d.eventPending=false", completion)


if __name__ == "__main__":
    unittest.main()
