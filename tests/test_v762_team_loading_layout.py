from versioning import CURRENT_APP_VERSION
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
        setup_shell = APP[APP.index("    const details=setupStepDefinitions[stepId];"):
                          APP.index("    bindSetup(stepId);")]
        self.assertIn("stepId==='team'", setup_shell)

    def test_05_loading_announcement_is_visually_hidden(self):
        announcement = APP[APP.index("  function playerTeamLoadingAnnouncement"):
                           APP.index("  function buildPlayerRosterButton")]
        self.assertIn('class="visually-hidden"', announcement)
        self.assertIn('role="status" aria-live="polite"', announcement)

    def test_06_no_visible_loading_paragraph_between_grid_and_actions(self):
        standalone = APP[APP.index("  function renderTeamSelection"):
                         APP.index("  const setupStepDefinitions")]
        setup_content = APP.index("  function setupContent(stepId)")
        team_start = APP.index("    if(stepId==='team'){", setup_content)
        setup_team = APP[team_start:APP.index("    if(stepId==='playerRoster'){", team_start)]
        for area in (standalone, setup_team):
            grid_end = area.index('${playerTeamLoadPresentation()}')
            actions = area.index('<div class="wizard-actions">', grid_end)
            self.assertNotIn('role="status"', area[grid_end:actions])

    def test_07_team_grid_contains_only_team_cards(self):
        setup_content = APP.index("  function setupContent(stepId)")
        team_start = APP.index("    if(stepId==='team'){", setup_content)
        setup_team = APP[team_start:APP.index("    if(stepId==='playerRoster'){", team_start)]
        grid = setup_team[setup_team.index('<div class="team-select-grid">'):
                          setup_team.index('${playerTeamLoadPresentation()}')]
        self.assertNotIn('visually-hidden', grid)

    def test_08_success_does_not_add_or_remove_visible_status_row(self):
        presentation = APP[APP.index("  function playerTeamLoadPresentation"):
                           APP.index("  function playerTeamLoadingAnnouncement")]
        self.assertEqual(presentation.count('<p'), 1)
        self.assertIn("playerTeamLoadStatus==='error'", presentation)

    def test_09_visible_load_error_remains(self):
        self.assertIn('<p class="muted" role="alert">Unable to load this Kill Team.', APP)

    def test_10_retry_team_load_remains_available(self):
        self.assertIn('>Retry Team Load</button>', APP)
        self.assertIn("loadPlayerTeamData(state.playerTeamId).catch", APP)

    def test_11_defensive_loading_screen_does_not_repeat_visible_label(self):
        render_setup = APP[APP.index("  function renderSetup"):
                           APP.index("  function missionSetupChecks")]
        self.assertNotIn('<p role="status" aria-live="polite">Loading selected Kill Team operatives', render_setup)
        self.assertNotIn("'Loading selected Kill Team operatives", render_setup)

    def test_12_defensive_screen_retains_stable_content(self):
        self.assertIn('<h2>Build Player Roster</h2>', APP)
        self.assertIn('Loading the selected Kill Team before displaying its operatives.', APP)
        self.assertIn('aria-busy="true"', APP)

    def test_13_stale_response_protection_is_unchanged(self):
        self.assertIn('let playerTeamLoadRequestId=0;', APP)
        self.assertGreaterEqual(
            APP.count('requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId'), 2
        )
        self.assertIn('loadedPlayerTeamId===state.playerTeamId', APP)

    def test_14_build_roster_cannot_advance_while_loading(self):
        self.assertIn("if(stepId==='team'&&!canBuildPlayerRoster())", APP)
        self.assertIn("if(!canBuildPlayerRoster()){showToast", APP)

    def test_15_only_matching_team_roster_can_display(self):
        self.assertIn("loadedPlayerTeamId===state.playerTeamId", APP)
        self.assertIn("if(!canBuildPlayerRoster())", APP[APP.index("  function renderSetup"):])

    def test_16_application_displays_version_763(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f"V{CURRENT_APP_VERSION}", INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js",
                      "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)


if __name__ == "__main__":
    unittest.main()
