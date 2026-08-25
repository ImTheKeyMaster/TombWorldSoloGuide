import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
DICE_SFX = (ROOT / "dice-sfx.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MANIFEST = (ROOT / "manifest.webmanifest").read_text(encoding="utf-8")


class Stage9ProductNamespaceTests(unittest.TestCase):
    def test_application_uses_only_new_state_namespace(self):
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", APP)
        self.assertNotIn("tombWorldSoloGuide.v1", APP)
        save_and_load = APP[APP.index("function save()") : APP.index("function recoverInvalidMission")]
        self.assertIn("localStorage.setItem(STORAGE_KEY", save_and_load)
        self.assertIn("localStorage.getItem(STORAGE_KEY)", save_and_load)
        self.assertNotIn("tombWorldSoloGuide", save_and_load)

    def test_all_active_preferences_use_new_namespace(self):
        expected_app_keys = (
            "tombWorldBattleGuide.diceRollEnabled",
            "tombWorldBattleGuide.showOperativeStatus",
            "tombWorldBattleGuide.ambientEnabled",
            "tombWorldBattleGuide.gameVolume",
        )
        for key in expected_app_keys:
            self.assertIn(key, APP)
        self.assertIn("tombWorldBattleGuide.diceRollEnabled", DICE_SFX)
        self.assertIn("tombWorldBattleGuide.narrationEnabled", NARRATION)
        self.assertIn("tombWorldBattleGuide.gameAudioEnabled", NARRATION)
        for source in (APP, DICE_SFX, NARRATION):
            self.assertNotIn("tombWorldSoloGuide", source)

    def test_legacy_state_is_ignored_without_migration_or_cleanup(self):
        load = APP[APP.index("function load()") : APP.index("function recoverInvalidMission")]
        self.assertEqual(load.count("localStorage.getItem("), 1)
        self.assertNotIn("localStorage.clear", APP)
        self.assertNotIn("tombWorldSoloGuide", APP)

    def test_new_game_resets_current_v9_battle_state(self):
        new_game = APP[APP.index("function startNewGameSetup") : APP.index("function confirmNewGame")]
        self.assertIn("localStorage.removeItem(STORAGE_KEY)", new_game)
        self.assertIn("state=initialState()", new_game)
        self.assertIn("state.screen='setup'", new_game)
        initial_state = APP[APP.index("const initialState") : APP.index("const loadedSave")]
        for default in ("gameMode:null", "missionId:null", "pendingDice:null"):
            self.assertIn(default, initial_state)

    def test_stage7_resume_remains_on_shared_new_save_path(self):
        persistence = APP[APP.index("function pendingDiceMatches") : APP.index("async function missionDiceTotal")]
        self.assertIn("state.pendingDice", persistence)
        self.assertIn("save()", persistence)
        self.assertIn("if(pending.status==='committed')return pending.values.slice()", persistence)
        self.assertIn("state.pendingDice=null;save();return true", persistence)
        self.assertIn("if(state.pendingDice)await resumePendingDiceWorkflow()", APP)

    def test_current_product_branding_covers_both_modes(self):
        self.assertIn("Tomb World Battle Guide", INDEX)
        self.assertIn("UNOFFICIAL TOMB WORLD PLAY AID", INDEX)
        self.assertRegex(INDEX, r'<meta name="description" content="[^"]*solo and two-player[^"]*">')
        self.assertIn('"name": "Tomb World Battle Guide"', MANIFEST)
        self.assertIn("title: 'Tomb World Battle Guide'", APP)
        self.assertNotIn("Tomb World Solo Guide", APP)


if __name__ == "__main__":
    unittest.main()
