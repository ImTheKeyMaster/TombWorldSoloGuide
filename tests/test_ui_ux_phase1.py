#!/usr/bin/env python3
from versioning import CURRENT_APP_VERSION
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UiUxPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_random_team_reuses_editable_roster_state(self):
        generator = self.source("function randomPlayerRoster()", "function save()")
        self.assertIn("playerRosterLimits()", generator)
        self.assertIn("requiredCount", generator)
        self.assertIn("mandatoryTroopers", generator)
        self.assertIn("maxGunners", generator)
        self.assertIn("maxGravis", generator)
        self.assertIn("applyPlayerRoster(selected)", generator)
        self.assertIn("id=\"randomPlayerTeam\"", self.app)
        manual_handler = self.source("$$('[data-select-player]')", "$('#playerDeployed')")
        self.assertIn("applyPlayerRoster(selected)", manual_handler)

    def test_every_team_can_fill_a_roster_with_its_constraints(self):
        for path in (ROOT / "Player_Operatives").glob("*.json"):
            data = json.loads(path.read_text())
            if "operatives" not in data:
                continue
            maximum = data.get("maxRoster", data.get("rosterSize", 5))
            self.assertGreaterEqual(len(data["operatives"]), maximum)
            rules = data.get("selectionRules", {})
            leader = rules.get("leader", {}).get("operativeId")
            if leader:
                self.assertIn(leader, {operative["id"] for operative in data["operatives"]})
            troopers = [operative for operative in data["operatives"] if operative.get("role") == "Trooper"]
            self.assertGreaterEqual(len(troopers), rules.get("mandatoryTroopers", 0))

    def test_check_all_updates_authoritative_deployment_state_once(self):
        handler = self.source("$('#checkAllDeployment')", "$$('[data-roster-category-toggle]')")
        self.assertIn("missionSetupChecks('deploy')", handler)
        self.assertIn("setStartingNposDeployed(true)", handler)
        self.assertIn("if(playerRosterValidation().valid)state.playerDeployed=true", handler)
        self.assertEqual(handler.count("save();render()"), 1)
        self.assertNotIn("dispatchEvent", handler)
        self.assertIn("id=\"checkAllDeployment\"", self.app)

    def test_activation_tracker_reuses_eliminated_state_for_players_and_npos(self):
        styles = (ROOT / "styles.css").read_text()
        tracker = self.source("function activationTracker()", "function showPlayerOperativeStatus")
        self.assertNotIn('tracker-elimination-icon', tracker)
        self.assertIn("border:2px solid var(--danger)", styles)
        self.assertIn("color:var(--danger)", styles)
        self.assertIn("container-type:inline-size", styles)
        self.assertNotIn(".tracker-operative.spent,\n.tracker-operative.eliminated", styles)
        self.assertIn("data-player-operative=", tracker)

    def test_application_ui_uses_solo_terminology(self):
        ui_files = [ROOT / "index.html", ROOT / "app.js", *(ROOT / "Missions").glob("*.json")]
        for path in ui_files:
            content = path.read_text()
            self.assertIsNone(re.search(r"\bPlayer [AB]\b", content), path)

    def test_release_versions_and_description_are_synchronized(self):
        version = f"{CURRENT_APP_VERSION}"
        self.assertIn(f"const APP_VERSION = '{version}'", self.app)
        self.assertIn(f"V{version}", (ROOT / "index.html").read_text())
        self.assertIn(f"const APP_VERSION = '{version}'", (ROOT / "service-worker.js").read_text())
        self.assertIn("Version 5.3.2 - Melee Workflow Cleanup", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
