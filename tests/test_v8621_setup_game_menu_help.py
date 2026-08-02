import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
CSS = (ROOT / "styles.css").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
MENU = APP[APP.index("function isNewGameSetupActive()") : APP.index("function showAbout()")]
OPEN_HELP = APP[APP.index("function openHelpFromGameMenu()") : APP.index("function showGameMenu()")]
HELP = APP[APP.index("function renderHelp()") : APP.index("function boardSvg(")]
SETUP = APP[APP.index("function renderSetup()") : APP.index("function runStartingNpoGeneration()")]


class SetupGameMenuHelpV8621Tests(unittest.TestCase):
    def test_01_application_displays_version_8621(self):
        self.assertIn("const APP_VERSION = '8.6.24';", APP)
        self.assertIn("V8.6.24", INDEX)
        self.assertIn("const APP_VERSION = '8.6.24';", WORKER)

    def test_02_game_menu_contains_accessible_help_button_during_setup(self):
        self.assertIn('id="menuHelp" type="button">Help</button>', MENU)
        self.assertIn("isNewGameSetupActive()", MENU)

    def test_03_help_is_available_on_mission_selection(self):
        self.assertIn("if(stepId==='mission')", SETUP)
        self.assertNotIn("setupStep", APP[APP.index("function canOpenHelp()") : APP.index("function openHelpFromGameMenu()")])

    def test_04_help_is_available_on_player_team_selection(self):
        self.assertIn("if(stepId==='team')", SETUP)
        self.assertIn("canOpenHelp()", MENU)

    def test_05_help_is_available_on_roster_selection(self):
        self.assertIn("if(stepId==='playerRoster')", SETUP)
        self.assertIn("canOpenHelp()", MENU)

    def test_06_help_is_available_during_npo_setup(self):
        self.assertIn("startingNpoGeneration", SETUP)
        self.assertIn("canOpenHelp()", MENU)

    def test_07_help_is_available_during_deployment_setup(self):
        self.assertIn("if(stepId==='deploy')", SETUP)
        self.assertIn("canOpenHelp()", MENU)

    def test_08_help_opens_existing_shared_help_screen(self):
        self.assertIn("$('#menuHelp').onclick=openHelpFromGameMenu", MENU)
        self.assertIn("renderHelp();", OPEN_HELP)

    def test_09_no_duplicate_help_implementation_is_introduced(self):
        self.assertEqual(APP.count("function renderHelp()"), 1)
        self.assertNotIn("help-list", OPEN_HELP)

    def test_10_opening_help_preserves_current_setup_step(self):
        self.assertNotRegex(OPEN_HELP, r"state\.setupStep\s*=")
        self.assertNotIn("renderSetup()", OPEN_HELP)

    def test_11_opening_help_preserves_mission_selection(self):
        self.assertNotRegex(OPEN_HELP, r"state\.mission(?:Id|State)\s*=")

    def test_12_opening_help_preserves_player_roster_selections(self):
        self.assertNotRegex(OPEN_HELP, r"state\.player(?:TeamId|Roster)\s*=")

    def test_13_opening_help_preserves_npo_setup_state(self):
        self.assertNotRegex(OPEN_HELP, r"state\.(?:roster|startingNpoGeneration|setupChecks)\s*=")

    def test_14_opening_help_preserves_selected_desktop_background(self):
        self.assertNotRegex(OPEN_HELP, r"backgroundSelection|ensureGameBackgroundSelection|updateGameBackground")

    def test_15_closing_help_returns_to_game_menu(self):
        self.assertIn('id="returnToGameMenu">Return to Game Menu</button>', OPEN_HELP)
        self.assertRegex(OPEN_HELP, r"returnToGameMenu[\s\S]+showGameMenu\(\)")

    def test_16_focus_returns_to_help_button(self):
        self.assertIn("$('#menuHelp')?.focus({preventScroll:true})", OPEN_HELP)
        self.assertIn(".btn:focus-visible", CSS)

    def test_17_return_to_guided_play_returns_to_same_setup_step(self):
        handler = re.search(r"\$\$\('\[data-game-view\]'[\s\S]+?\n    \}\);", MENU).group(0)
        self.assertIn("if(inGame)", handler)
        self.assertNotIn("setupStep", handler)
        self.assertIn("render();", handler)

    def test_18_help_remains_available_during_active_guided_play_and_battle_complete(self):
        self.assertIn("isGuidedPlayActive()", MENU)
        self.assertIn("isBattleComplete()", MENU)
        self.assertIn("state.gameEnd||state.finalResolution?.pending", MENU)

    def test_19_about_remains_available_and_unchanged(self):
        self.assertIn('id="menuAbout" type="button">About</button>', MENU)
        self.assertIn("$('#menuAbout').onclick=showAbout", MENU)

    def test_20_export_and_import_remain_unchanged(self):
        self.assertIn("$('#menuExportSave').onclick=exportSave", MENU)
        self.assertIn("$('#menuImportSave').onclick=()=>importInput.click()", MENU)

    def test_21_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_22_release_references_and_notes_are_consistent(self):
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.24"))
        self.assertIn("## v8.6.24", README)
        for asset in ("styles.css", "app.js", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js"):
            self.assertIn(f"{asset}?v=8.6.24", INDEX)
        self.assertNotIn("8.6.20", APP + INDEX + WORKER)

    def test_23_help_open_and_close_do_not_save_or_mutate_state(self):
        self.assertNotRegex(OPEN_HELP, r"\bstate\.|\bsave\(|localStorage")

    def test_24_help_uses_existing_non_heading_focus_behavior(self):
        self.assertNotRegex(OPEN_HELP, r"(?:h1|h2|h3|modalTitle).*focus")
        self.assertIn("<details><summary>", HELP)


if __name__ == "__main__":
    unittest.main()
