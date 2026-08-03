import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


class SetupDesktopBackgroundTests(unittest.TestCase):
    def test_version_and_release_notes(self):
        self.assertIn("const APP_VERSION = '8.6.29';", APP)
        self.assertIn("const APP_VERSION = '8.6.29';", WORKER)
        self.assertIn("V8.6.29", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.29"))
        self.assertIn("## v8.6.25", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.29", INDEX)

    def test_new_setup_selects_saves_then_renders(self):
        start = section("function startNewGameSetup(){", "function confirmNewGame")
        self.assertLess(start.index("state=initialState()"), start.index("ensureGameBackgroundSelection()"))
        self.assertLess(start.index("ensureGameBackgroundSelection()"), start.index("save()"))
        self.assertLess(start.index("save()"), start.index("updateGameBackground()"))
        self.assertLess(start.index("updateGameBackground()"), start.index("render()"))
        self.assertIn("state.screen='setup'", start)

    def test_new_setup_removes_the_previous_image_before_replacement(self):
        start = section("function startNewGameSetup(){", "function confirmNewGame")
        self.assertIn("classList.remove('desktop-game-background')", start)
        self.assertIn("gameBackground.style.backgroundImage='none'", start)
        self.assertIn("state=initialState()", start)
        self.assertIn("backgroundSelection:null", APP)

    def test_setup_and_game_share_the_desktop_renderer(self):
        renderer = section("function updateGameBackground(){", "if(desktopBackgroundMedia.addEventListener)")
        self.assertIn("['setup','game'].includes(state.screen)", renderer)
        self.assertIn("desktopBackgroundMedia.matches", renderer)
        self.assertIn("const image=new Image()", renderer)
        self.assertIn("!['setup','game'].includes(state.screen)", renderer)
        self.assertIn("classList.add('desktop-game-background')", renderer)

    def test_selection_helper_validates_and_repairs_once(self):
        helper = section("function ensureGameBackgroundSelection", "function updateGameBackground")
        self.assertIn("isValidLandscapeBackground(current)", helper)
        self.assertIn("selectRandomLandscapeBackground()", helper)
        self.assertIn("sourceState.backgroundSelection={landscape:selected}", helper)
        render = section("function render(){", "function guideInstructionsHtml")
        self.assertNotIn("ensureGameBackgroundSelection", render)

    def test_setup_navigation_and_edits_do_not_reroll(self):
        setup = section("function renderSetup(){", "function missionSetupChecks") + section("function bindSetup", "$('#beginGame')?.addEventListener")
        self.assertNotIn("selectRandomLandscapeBackground", setup)
        self.assertNotIn("ensureGameBackgroundSelection", setup)
        self.assertIn("state.setupStep=Math.max", setup)
        self.assertIn("state.missionId=missionId", setup)
        self.assertIn("selectPlayerTeam", setup)

    def test_game_start_preserves_valid_setup_selection(self):
        begin = section("$('#beginGame')?.addEventListener('click',async()=>", "function runStartingNpoGeneration")
        self.assertIn("ensureGameBackgroundSelection()", begin)
        self.assertNotIn("selectRandomLandscapeBackground", begin)
        self.assertNotIn("backgroundSelection=null", begin)

    def test_restore_repairs_setup_and_game_then_saves(self):
        startup = section("else Promise.all([loadMissionPack()", "function preventDoubleTapZoom")
        self.assertIn("['setup','game'].includes(state.screen)", startup)
        self.assertIn("ensureGameBackgroundSelection()", startup)
        self.assertIn("save()", startup)

    def test_import_and_regeneration_use_the_same_guard(self):
        imported = section("async function commitImported", "function showRegenerationNotice")
        self.assertIn("ensureGameBackgroundSelection()", imported)
        self.assertIn("report.requiresRegeneration?'setup':'game'", imported)
        self.assertIn("backgroundSelection:null", section("function resetActiveBattle", "function normalizeSave") if "function resetActiveBattle" in APP else PERSISTENCE.split("function resetActiveBattle", 1)[1].split("function normalizeSave", 1)[0])

    def test_battle_complete_keeps_selection(self):
        complete = section("function completeMission", "function checkGameEnd")
        self.assertNotIn("backgroundSelection", complete)
        self.assertNotIn("selectRandomLandscapeBackground", complete)

    def test_mobile_portrait_styling_and_detection_are_unchanged(self):
        self.assertIn("(hover: hover) and (pointer: fine) and (min-width: 769px)", APP)
        self.assertIn("radial-gradient(circle at 80% 0,#123326 0,transparent 32%),var(--bg)", STYLES)
        combined = APP + INDEX + STYLES + WORKER
        self.assertNotIn("Portrait-", combined)
        self.assertNotIn("orientationchange", APP)

    def test_save_schema_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
