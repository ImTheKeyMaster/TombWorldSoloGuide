import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


class TeamLoadingLayoutTests(unittest.TestCase):
    def test_01_loading_presentation_has_no_visible_content(self):
        helper = APP[APP.index("  function playerTeamLoadPresentation"):
                     APP.index("  function playerTeamLoadingAnnouncement")]
        self.assertNotIn("playerTeamLoadStatus==='loading'", helper)
        self.assertNotIn("Loading selected Kill Team operatives", helper)

    def test_02_loading_button_wording_remains(self):
        self.assertIn("loading?'Loading Team...':'Build Roster'", APP)

    def test_03_build_roster_is_disabled_while_loading(self):
        self.assertIn("canBuildPlayerRoster()?'':`disabled aria-disabled=", APP)
        self.assertIn("playerTeamLoadStatus==='loaded'", APP)

    def test_04_team_selection_exposes_busy_state(self):
        self.assertGreaterEqual(APP.count('aria-busy="${playerTeamLoadStatus===\'loading\'}"'), 2)

    def test_05_loading_announcement_is_visually_hidden(self):
        announcement = APP[APP.index("  function playerTeamLoadingAnnouncement"):
                           APP.index("  function buildPlayerRosterButton")]
        self.assertIn('class="visually-hidden"', announcement)
        self.assertIn('role="status" aria-live="polite"', announcement)

    def test_06_no_visible_loading_paragraph_between_grid_and_actions(self):
        for marker in ("teamSelectNext", "setupNext')"):
            area = APP[max(0, APP.index(marker) - 700):APP.index(marker) + 100]
            self.assertNotIn('<p class="muted" role="status"', area)

    def test_07_success_does_not_add_or_remove_visible_status_row(self):
        presentation = APP[APP.index("  function playerTeamLoadPresentation"):
                           APP.index("  function playerTeamLoadingAnnouncement")]
        self.assertEqual(presentation.count('<p'), 1)
        self.assertIn("playerTeamLoadStatus==='error'", presentation)

    def test_08_visible_load_error_remains(self):
        self.assertIn('<p class="muted" role="alert">Unable to load this Kill Team.', APP)

    def test_09_retry_team_load_remains_available(self):
        self.assertIn('>Retry Team Load</button>', APP)
        self.assertIn("loadPlayerTeamData(state.playerTeamId).catch", APP)

    def test_10_defensive_loading_screen_does_not_repeat_visible_label(self):
        render_setup = APP[APP.index("  function renderSetup"):
                           APP.index("  function missionSetupChecks")]
        self.assertNotIn('<p role="status" aria-live="polite">Loading selected Kill Team operatives', render_setup)
        self.assertNotIn("'Loading selected Kill Team operatives", render_setup)

    def test_11_defensive_screen_retains_stable_content(self):
        self.assertIn('<h2>Build Player Roster</h2>', APP)
        self.assertIn('Loading the selected Kill Team before displaying its operatives.', APP)
        self.assertIn('aria-busy="true"', APP)

    def test_12_stale_response_protection_is_unchanged(self):
        self.assertIn('let playerTeamLoadRequestId=0;', APP)
        self.assertGreaterEqual(
            APP.count('requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId'), 2
        )
        self.assertIn('loadedPlayerTeamId===state.playerTeamId', APP)

    def test_13_build_roster_cannot_advance_while_loading(self):
        self.assertIn("if(stepId==='team'&&!canBuildPlayerRoster())", APP)
        self.assertIn("if(!canBuildPlayerRoster()){showToast", APP)

    def test_14_only_matching_team_roster_can_display(self):
        self.assertIn("loadedPlayerTeamId===state.playerTeamId", APP)
        self.assertIn("if(!canBuildPlayerRoster())", APP[APP.index("  function renderSetup"):])

    def test_15_application_displays_version_762(self):
        self.assertIn("const APP_VERSION = '7.6.2';", APP)
        self.assertIn("const APP_VERSION = '7.6.2';", WORKER)
        self.assertIn("V7.6.2", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v7.6.2"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js",
                      "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=7.6.2", INDEX)


if __name__ == "__main__":
    unittest.main()
