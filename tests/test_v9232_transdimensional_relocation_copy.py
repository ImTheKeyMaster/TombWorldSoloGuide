#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "Player_Operatives/manifest.json").read_text(encoding="utf-8"))


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class TransdimensionalRelocationCopyTests(unittest.TestCase):
    def test_selection_still_uses_exactly_two_eligible_player_operatives(self):
        eligibility = source(
            "function eligibleTransdimensionalRelocationOperativeIds", 
            "function validTransdimensionalRelocationSelection",
        )
        preparation = source(
            "function prepareTransdimensionalRelocation", "function npoProfileSchemaValid"
        )
        self.assertIn("return inPlayLivingPlayerOperativeIds()", eligibility)
        self.assertIn("playerOperativeIds:selectRandomDistinctPlayerOperatives(eligibleIds,2)", preparation)
        self.assertNotIn("state.roster", eligibility + preparation)

    def test_selection_is_prepared_and_saved_before_pending_ui(self):
        preparation = source(
            "function prepareTransdimensionalRelocation", "function npoProfileSchemaValid"
        )
        begin = source("async function beginCurrentEvent", "function narrateAcceptedEvent")
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertLess(preparation.index("event.resolution={"), preparation.index("save();"))
        self.assertLess(begin.index("prepareTransdimensionalRelocation(event)"), begin.index("d.eventPending=true"))
        self.assertIn("if(isRelocation&&event.status==='drawn')prepareTransdimensionalRelocation(event)", renderer)

    def test_pending_effect_uses_authoritative_data_driven_team_name(self):
        helper = source("function selectedPlayerTeamName", "function playerSideLabel")
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("playerTeamData?.teamName||playerTeamEntry()?.name||fallback", helper)
        self.assertIn("`Two ${selectedPlayerTeamName('Player')} operatives were randomly selected to swap positions.`", renderer)
        self.assertIn("presentSideTerminology(displayDescription)", renderer)
        for team_name in ("Scout Squad", "Deathwatch", "Spectre Squad", "Kasrkin", "Tempestus Aquilons"):
            self.assertIn(team_name, {team["name"] for team in MANIFEST["teams"]})
            self.assertNotIn(f"Two {team_name} operatives", renderer)

    def test_old_rule_copy_is_not_used_for_completed_selection_presentation(self):
        definitions = source("const eventDefinitions = {", "const eventDeck = [")
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("Randomly select two Player operatives and swap their positions.", definitions)
        self.assertNotIn("Randomly select two Player operatives and swap their positions.", renderer)
        self.assertIn("displayDescription", renderer)

    def test_operatives_and_physical_instructions_remain_visible(self):
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("OPERATIVES TO SWAP", renderer)
        self.assertIn("names.map(name=>`<li>", renderer)
        self.assertIn("Remove both operatives from the killzone.", renderer)
        self.assertIn("Set each operative up in the other operative’s previous position.", renderer)
        self.assertIn("Keep their wounds, order, Ready or Expended state, and all other statuses unchanged.", renderer)
        self.assertIn("Confirm Positions Swapped", renderer)

    def test_confirmation_and_resolution_behavior_are_unchanged(self):
        resolution = source("async function resolveStrategyEvent", "function randomReinforcement")
        relocation = resolution.split("if(event.execution.type==='transdimensional-relocation')", 1)[1].split("}else if", 1)[0]
        self.assertIn("event.status!=='drawn'||event.resolution?.confirmed", relocation)
        self.assertIn("validTransdimensionalRelocationSelection(event)", relocation)
        self.assertIn("event.resolution.confirmed=true", relocation)
        self.assertIn("swapped positions.", relocation)
        self.assertIn("await completeCurrentEvent(result)", resolution)

    def test_reload_and_rerender_reuse_the_persisted_pair(self):
        preparation = source(
            "function prepareTransdimensionalRelocation", "function npoProfileSchemaValid"
        )
        self.assertIn("if(validTransdimensionalRelocationSelection(event,eligibleIds))return true", preparation)
        self.assertIn("playerOperativeIds", preparation)
        self.assertIn("Object.entries(state)", PERSISTENCE)
        self.assertNotIn("'strategyData'", PERSISTENCE.split("NON_PERSISTED_FIELDS", 1)[1].split(");", 1)[0])

    def test_missing_team_metadata_has_safe_player_fallback(self):
        helper = source("function selectedPlayerTeamName", "function playerSideLabel")
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertIn("fallback='Kill Team'", helper)
        self.assertIn("selectedPlayerTeamName('Player')", renderer)

    def test_solo_and_pvp_do_not_change_relocation_targeting(self):
        relocation = source(
            "function eligibleTransdimensionalRelocationOperativeIds", 
            "function npoProfileSchemaValid",
        )
        self.assertNotIn("isPvpMode", relocation)
        self.assertNotIn("activeNpos", relocation)
        self.assertNotIn("npo", relocation.lower())

    def test_long_team_copy_uses_existing_wrapping_card_style(self):
        renderer = source("function strategyEventHtml", "function activationTracker")
        self.assertIn('class="tomb-world-event-description"', renderer)
        self.assertIn(".strategy-event .tomb-world-event-description{margin:0", STYLES)
        description_rule = STYLES.split(".strategy-event .tomb-world-event-description{", 1)[1].split("}", 1)[0]
        self.assertNotIn("white-space:nowrap", description_rule)

    def test_release_versions_and_save_contract(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn("const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertEqual(INDEX.count(f"?v={CURRENT_APP_VERSION}"), 10)
        self.assertTrue(README.startswith(
            f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
        ))
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", APP)


if __name__ == "__main__":
    unittest.main()
