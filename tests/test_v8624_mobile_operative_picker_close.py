import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class MobileOperativePickerCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activation = re.search(
            r"function showPlayerActivation\(stage=\{\}\).*?\n  function readPlayerActivationStage",
            APP,
            re.S,
        ).group()
        cls.handler = re.search(
            r"operativeSelect\?\.addEventListener\('change',event=>\{.*?\n    \}\);",
            cls.activation,
            re.S,
        ).group()
        cls.close_helper = re.search(
            r"function closeTouchSelectAfterCommit\(select,onComplete\)\{.*?\n  \}", APP, re.S
        ).group()

    def test_01_application_displays_version_8624(self):
        self.assertIn("const APP_VERSION = '8.6.42';", APP)
        self.assertIn("const APP_VERSION = '8.6.42';", WORKER)
        self.assertIn("V8.6.42", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.42"))

    def test_02_player_selection_has_one_canonical_change_handler(self):
        self.assertEqual(self.activation.count("operativeSelect?.addEventListener('change'"), 1)
        self.assertNotIn("operativeSelect?.addEventListener('input'", self.activation)

    def test_03_valid_selection_commits_once(self):
        self.assertEqual(self.handler.count("selectOperative(stage,operativeId)"), 1)
        self.assertEqual(self.handler.count("showPlayerActivation(selectedStage)"), 1)

    def test_04_selection_does_not_rerun_initial_focus(self):
        self.assertNotIn("focusInitialDialogControl", self.handler)
        self.assertIn("modal._skipFocusRestoreId=select.id", self.handler)

    def test_05_selector_is_not_refocused_after_rerender(self):
        self.assertIn("const shouldRestoreFocus=modal._skipFocusRestoreId!==activeControlId;", APP)
        self.assertIn("else if(shouldRestoreFocus)restoreDialogControlFocus", APP)
        self.assertNotRegex(self.handler, r"\.focus\(")

    def test_06_coarse_pointer_releases_focus_after_commit(self):
        self.assertIn("window.matchMedia('(hover: none) and (pointer: coarse)').matches", self.close_helper)
        self.assertIn("if(document.activeElement===select)select.blur();", self.close_helper)
        self.assertIn("closeTouchSelectAfterCommit(select,()=>showPlayerActivation(selectedStage))", self.handler)
        self.assertLess(self.close_helper.index("select.blur()"), self.close_helper.rindex("onComplete()"))

    def test_07_value_is_captured_before_blur(self):
        self.assertLess(self.handler.index("const operativeId=select.value"), self.handler.index("closeTouchSelectAfterCommit(select"))

    def test_08_keyboard_selection_is_not_unconditionally_blurred(self):
        self.assertIn("if(!coarsePointer){onComplete();return;}", self.close_helper)
        self.assertLess(self.close_helper.index("if(!coarsePointer)"), self.close_helper.index("select.blur()"))

    def test_09_selected_operative_remains_displayed(self):
        self.assertIn("selectedId===id?'selected':''", self.activation)
        self.assertIn("playerOperativeId:id||''", self.activation)

    def test_10_ap_is_preserved_during_selection(self):
        self.assertIn("baseApl,apl:id?effectiveApl(id,baseApl):baseApl", self.activation)
        self.assertNotRegex(self.handler, r"playerActionCost|apl\s*[-+]=|spend")

    def test_11_available_actions_update_for_selected_operative(self):
        self.assertIn("const moveDistance=Number(selectedOperative?.move||6)", self.activation)
        self.assertIn("updatePlayerActionAvailability", self.activation)

    def test_12_placeholder_does_not_commit(self):
        self.assertIn("if(!operativeId)return;", self.handler)

    def test_13_no_duplicate_input_and_change_commits(self):
        self.assertNotRegex(self.activation, r"operativeSelect.*addEventListener\('input'")
        self.assertEqual(self.handler.count("selectOperative(stage,operativeId)"), 1)

    def test_14_refresh_preserves_selected_operative(self):
        self.assertIn("state.combatState?.side==='player'", self.activation)
        self.assertIn("stage={...state.combatState.stage}", self.activation)

    def test_15_update_preserves_selected_operative(self):
        self.assertIn("const stagedId=String(stage.playerOperativeId||'')", self.activation)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_16_npo_selection_remains_functional(self):
        self.assertIn("$('#officialNpoSelection').onchange", APP)
        self.assertIn("$('#npoPriorityTarget')?.addEventListener('change'", APP)

    def test_17_real_controls_keep_visible_keyboard_focus(self):
        self.assertIn(".btn:focus-visible", STYLES)
        self.assertNotRegex(STYLES, r"select:focus(?:-visible)?\s*\{\s*outline\s*:\s*none")

    def test_18_save_version_remains_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_19_release_notes_are_present(self):
        self.assertIn("## v8.6.25", README)
        self.assertIn("Version 8.6.24 - Close Player Operative Picker After Selection", README)


if __name__ == "__main__":
    unittest.main()
