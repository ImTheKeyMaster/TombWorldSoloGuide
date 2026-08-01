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


class TransdimensionalRelocationTests(unittest.TestCase):
    def test_version_864_is_consistent_without_save_schema_change(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.15"))
        self.assertIn("Version 8.6.5 - Show Player Wounds in Target Selection", README)
        self.assertIn("const APP_VERSION = '8.6.15';", APP)
        self.assertIn("const APP_VERSION = '8.6.15';", WORKER)
        self.assertIn("V8.6.15", INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.15", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_definition_has_correct_effect_and_safe_redraw(self):
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        relocation = next(line for line in definitions.splitlines() if "'transdimensional-relocation':" in line)
        self.assertIn("Randomly select two Player operatives and swap their positions.", relocation)
        self.assertIn("redrawIfImpossible:true", relocation)
        self.assertNotIn("closest to an NPO", relocation)

    def test_selection_is_unbiased_without_replacement_and_preserves_roster(self):
        helper = source("function selectRandomDistinctPlayerOperatives", "function eligibleTransdimensionalRelocationOperativeIds")
        self.assertIn("[...new Set(operativeIds)]", helper)
        self.assertIn("roll(index+1)-1", helper)
        self.assertIn("[available[index],available[swapIndex]]=[available[swapIndex],available[index]]", helper)
        self.assertIn("available.slice(0,count)", helper)
        self.assertNotIn("playerName", helper)
        self.assertNotIn("splice", helper)

    def test_eligibility_includes_ready_and_expended_but_excludes_off_board_and_incapacitated(self):
        eligibility = source("function eligibleTransdimensionalRelocationOperativeIds", "function validTransdimensionalRelocationSelection")
        self.assertIn("inPlayLivingPlayerOperativeIds()", eligibility)
        living = source("function livingPlayerOperativeIds", "function setOperativeInPlay")
        self.assertIn("!casualties.has(id)", living)
        self.assertIn("filter(isPlayerOperativeInPlay)", living)
        self.assertNotIn("playerActivatedIds", eligibility)
        self.assertNotIn("playerReady", eligibility)

    def test_pair_is_validated_and_persisted_on_the_event_instance(self):
        preparation = source("function validTransdimensionalRelocationSelection", "function strategyEventCount")
        self.assertIn("selected.length===2", preparation)
        self.assertIn("new Set(selected).size===2", preparation)
        self.assertIn("selected.every(id=>eligibleIds.includes(id))", preparation)
        self.assertIn("if(validTransdimensionalRelocationSelection(event,eligibleIds))return true", preparation)
        self.assertIn("event.resolution={", preparation)
        self.assertIn("playerOperativeIds:selectRandomDistinctPlayerOperatives(eligibleIds,2)", preparation)
        self.assertIn("confirmed:false", preparation)
        self.assertIn("save();", preparation)

    def test_exactly_two_are_both_selected_and_insufficient_count_redraws(self):
        helper = source("function selectRandomDistinctPlayerOperatives", "function eligibleTransdimensionalRelocationOperativeIds")
        self.assertIn("available.slice(0,count)", helper)
        preparation = source("function prepareTransdimensionalRelocation", "function strategyEventCount")
        self.assertIn("if(eligibleIds.length<2)return false", preparation)
        begin = source("function beginCurrentEvent", "function completeCurrentEvent")
        self.assertIn("fewer than two Player operatives were on the battlefield", begin)
        self.assertIn("redrawCurrentEvent", begin)

    def test_pending_card_names_both_operatives_with_semantic_instructions(self):
        card = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("OPERATIVES TO SWAP", card)
        self.assertIn("<ol>", card)
        self.assertIn("names.map(name=>`<li>", card)
        self.assertIn("Set each operative up in the other operative’s previous position.", card)
        self.assertIn("Keep their wounds, order, Ready or Expended state, and all other statuses unchanged.", card)
        self.assertIn("aria-label=\"Transdimensional Relocation. Operatives to swap:", card)
        self.assertIn("Confirm Positions Swapped", card)
        self.assertNotIn("Confirm Tabletop Resolution", APP)

    def test_confirmation_is_guarded_idempotent_and_changes_no_operative_state(self):
        resolution = source("function resolveStrategyEvent", "function randomReinforcement")
        relocation = resolution.split("if(event.execution.type==='transdimensional-relocation')", 1)[1].split("}else if", 1)[0]
        self.assertIn("event.status!=='drawn'", relocation)
        self.assertIn("event.resolution?.confirmed", relocation)
        self.assertIn("validTransdimensionalRelocationSelection(event)", relocation)
        self.assertIn("prepareTransdimensionalRelocation(event)", relocation)
        self.assertIn("redrawCurrentEvent", relocation)
        self.assertIn("event.resolution.confirmed=true", relocation)
        self.assertIn("swapped positions.", relocation)
        for field in ("playerWounds", "playerActivatedIds", "playerOperativeStates", ".ready", ".order", ".apl"):
            self.assertNotIn(field, relocation)

    def test_accessible_focus_and_live_resolution_are_present(self):
        card = source("function strategyEventHtml", "function activationTracker")
        binding = source("function bindPlay", "function showPlayerActivation")
        resolution = source("function resolveStrategyEvent", "function randomReinforcement")
        self.assertIn('aria-live="polite"', card)
        self.assertIn('id="transdimensional-relocation-selection-heading" tabindex="-1"', card)
        self.assertIn("transdimensional-relocation-selection-heading", binding)
        self.assertIn("focusedRelocationInstanceId!==pendingRelocation.instanceId", binding)
        self.assertIn("else focusedRelocationInstanceId=null", binding)
        self.assertIn('id="resolved-transdimensional-relocation-heading" tabindex="-1"', card)
        self.assertIn("resolved-transdimensional-relocation-heading", resolution)
        self.assertIn("button.disabled=true", binding)

    def test_deck_weighting_and_other_effects_are_unchanged(self):
        deck = source("const eventDeck = [", "];\n\n  const missionStateFactories")
        self.assertEqual(deck.count("transdimensional-relocation"), 2)
        self.assertEqual(deck.count("awakened-warrior"), 4)
        self.assertEqual(deck.count("instanceId:"), 12)
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        for event_id in ("subjugation-glyphs", "restless", "living-metal-flux", "maze-reforms", "stirrings-of-horror"):
            if event_id != "restless":
                self.assertIn(event_id, definitions)


if __name__ == "__main__":
    unittest.main()
