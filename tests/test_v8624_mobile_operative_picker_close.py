"""The v8.6.24 touch regression adapted to the v9.1 separated operative picker."""
from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class MobileOperativePickerCloseTests(unittest.TestCase):
    def test_selection_is_separate_and_commits_once(self):
        section = APP.split("function showPlayerActivation()", 1)[1].split("function playerActivationSummary", 1)[0]
        self.assertEqual(section.count("beginPlayerActivation($('#humanPlayerSelection').value)"), 1)
        self.assertIn("Choose a Ready operative", section)
        self.assertNotIn("data-human-action", section)

    def test_activation_picker_locks_selected_operative(self):
        picker = APP.split("function renderHumanPlayerActionPicker", 1)[1].split("function playerSequentialStage", 1)[0]
        self.assertIn("activation.operativeId", picker)
        self.assertNotIn("humanPlayerSelection", picker)

    def test_touch_select_exemption_and_focus_contract_remain(self):
        helper = APP.split("function closeTouchSelectAfterCommit", 1)[1].split("let modalFocusSequence", 1)[0]
        self.assertIn("(hover: none) and (pointer: coarse)", helper)
        self.assertIn("select.blur()", helper)
        self.assertIn(".btn:focus-visible", STYLES)
        self.assertNotRegex(STYLES, r"select:focus(?:-visible)?\\s*\\{\\s*outline\\s*:\\s*none")

    def test_mobile_shell_wraps_and_keeps_touch_targets(self):
        self.assertIn("@media(max-width:430px)", STYLES)
        self.assertIn("min-height:56px", STYLES)
        self.assertIn("overflow-wrap:anywhere", STYLES)

    def test_release_and_save_schema(self):
        self.assertRegex(CURRENT_APP_VERSION, r"^9[.]1[.]0$")
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
