import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
SFX = (ROOT / "dice-sfx.js").read_text(encoding="utf-8")


class PreservedDiceRollBehaviorTests(unittest.TestCase):
    def test_preference_master_menu_and_new_game_behavior_remain(self):
        self.assertIn("tombWorldSoloGuide.diceRollEnabled", SFX)
        self.assertIn("localStorage.getItem(PREFERENCE_KEY) !== 'false'", SFX)
        self.assertIn("!masterEnabled || !preferenceEnabled", SFX)
        self.assertIn("if (!masterEnabled) stop();", SFX)
        self.assertIn('id="diceRollToggle"', APP)
        handler = APP[APP.index("$('#diceRollToggle').onclick") : APP.index("const gameVolume")]
        self.assertIn("TombWorldDiceSfx.setPreferenceEnabled", handler)
        new_game = APP[APP.index("function startNewGameSetup") : APP.index("function confirmNewGame")]
        self.assertIn("TombWorldDiceSfx.stop()", new_game)

    def test_visible_batches_keep_synchronous_750ms_triggers(self):
        self.assertIn("const DICE_ROLL_ANIMATION_MS = 750;", APP)
        self.assertEqual(5, APP.count("void TombWorldDiceSfx.play()"))
        self.assertNotIn("await TombWorldDiceSfx.play()", APP)
        self.assertIn("row?.classList.contains('animated-roll')&&dice.length", APP)
        automatic = APP[APP.index("function runAutomaticCombatRolls") : APP.index("function retainedDiceTotals")]
        self.assertRegex(automatic, re.compile(r"innerHTML=.*?void TombWorldDiceSfx\.play\(\)", re.S))

    def test_fallback_still_preserves_default_on_preference(self):
        start = APP.index("function createDiceSfxFallback")
        fallback = APP[start : APP.index("const TombWorldDiceSfx", start)]
        self.assertIn("localStorage.getItem(preferenceKey)!=='false'", fallback)
        self.assertIn("activateFromGesture:()=>Promise.resolve(false)", fallback)
        self.assertIn("play:()=>Promise.resolve(false)", fallback)


if __name__ == "__main__":
    unittest.main()
