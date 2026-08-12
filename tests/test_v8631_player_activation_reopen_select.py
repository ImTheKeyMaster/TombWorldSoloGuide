import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
STYLES = (ROOT / "styles.css").read_text()


class PlayerActivationReopenSelectTests(unittest.TestCase):
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
        cls.focus = re.search(
            r"let modalFocusGeneration=0;.*?\n  modal\.addEventListener\('cancel'",
            APP,
            re.S,
        ).group()
        cls.close_helper = re.search(
            r"function closeTouchSelectAfterCommit\(select,onComplete\)\{.*?\n  \}",
            APP,
            re.S,
        ).group()

    def test_01_application_displays_version_8631(self):
        self.assertIn("const APP_VERSION = '8.6.59';", APP)
        self.assertIn("const APP_VERSION = '8.6.59';", WORKER)
        self.assertIn("V8.6.59", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.59"))

    def test_02_selector_never_uses_pointer_events_none(self):
        self.assertNotRegex(self.activation, r"pointerEvents\s*=\s*['\"]none")
        self.assertNotRegex(self.activation, r"pointer-events\s*:\s*none")
        self.assertNotIn("operativeSelect?.style", self.activation)

    def test_03_no_animation_frame_disables_selector(self):
        frames = re.findall(r"requestAnimationFrame\(.*?\);", self.activation, re.S)
        self.assertFalse(any("pointer" in frame for frame in frames))

    def test_04_selector_is_outside_inactive_action_fieldset(self):
        select_end = self.activation.index('</select>')
        fieldset_start = self.activation.index('<fieldset id="playerActivationControls"')
        self.assertLess(select_end, fieldset_start)
        self.assertIn("class=\"${selectedId?'':'inactive'}\"", self.activation)

    def test_05_cancel_does_not_complete_activation(self):
        self.assertIn("$('#cancelPlayerActivation').onclick=()=>{closeModal();render();};", self.activation)
        cancel = self.activation.split("$('#cancelPlayerActivation').onclick=", 1)[1].split("$('#confirmPlayer').onclick=", 1)[0]
        self.assertNotRegex(cancel, r"complete|confirm|resolvePendingPlayerAttacks")

    def test_06_cancel_does_not_decrement_player_ready(self):
        cancel = self.activation.split("$('#cancelPlayerActivation').onclick=", 1)[1].split("$('#confirmPlayer').onclick=", 1)[0]
        self.assertNotIn("playerReady", cancel)

    def test_07_cancel_does_not_increment_activation_count(self):
        cancel = self.activation.split("$('#cancelPlayerActivation').onclick=", 1)[1].split("$('#confirmPlayer').onclick=", 1)[0]
        self.assertNotRegex(cancel, r"activationCount|completedActivations|activationNumber")

    def test_08_reopen_builds_a_fresh_enabled_selector(self):
        self.assertIn('<select id="playerOperativeSelect">', self.activation)
        opening_tag = self.activation.split('<select id="playerOperativeSelect"', 1)[1].split('>', 1)[0]
        self.assertNotIn('disabled', opening_tag)
        self.assertIn("modalBody.innerHTML=", self.focus)

    def test_09_reopen_has_placeholder_without_pending_activation(self):
        self.assertIn('<option value="">Select a Player operative...</option>', self.activation)
        self.assertIn("const stagedId=String(stage.playerOperativeId||'')", self.activation)

    def test_10_selector_remains_touch_interactive_after_reopen(self):
        self.assertNotIn("operativeSelect.style.pointerEvents", self.activation)
        self.assertNotRegex(STYLES, r"#playerOperativeSelect[^}]*pointer-events\s*:\s*none")

    def test_11_coarse_pointer_focus_does_not_target_select(self):
        self.assertIn("focusContainerOnTouch&&coarsePointer?dialog", self.focus)
        self.assertIn("data-touch-dialog-focus-container", self.activation)

    def test_12_coarse_pointer_focus_uses_safe_dialog_container(self):
        self.assertIn("window.matchMedia('(hover: none) and (pointer: coarse)').matches", self.focus)
        self.assertIn("modal.setAttribute('tabindex','-1')", self.focus)
        self.assertRegex(STYLES, r"\.modal:focus\{\s*outline:none;")

    def test_13_desktop_keyboard_focus_can_reach_selector(self):
        self.assertIn("select:not([disabled])", self.focus)
        self.assertIn("select:not([disabled])", self.focus.split("modal.addEventListener('keydown'", 1)[-1] if "modal.addEventListener('keydown'" in self.focus else APP)
        self.assertNotRegex(STYLES, r"select:focus(?:-visible)?\s*\{\s*outline\s*:\s*none")

    def test_14_selection_commits_exactly_once(self):
        self.assertEqual(self.handler.count("selectOperative(stage,operativeId)"), 1)
        self.assertEqual(self.handler.count("showPlayerActivation(selectedStage)"), 1)
        self.assertEqual(self.activation.count("operativeSelect?.addEventListener('change'"), 1)

    def test_15_selected_operative_enables_legal_actions(self):
        self.assertIn("class=\"${selectedId?'':'inactive'}\"", self.activation)
        self.assertIn("updatePlayerActionAvailability();", self.activation)
        self.assertIn("box.disabled=", self.activation)

    def test_16_touch_picker_closing_behavior_remains(self):
        self.assertIn("if(document.activeElement===select)select.blur();", self.close_helper)
        self.assertLess(self.close_helper.index("select.blur()"), self.close_helper.rindex("onComplete()"))
        self.assertIn("closeTouchSelectAfterCommit(select,()=>showPlayerActivation(selectedStage))", self.handler)
        self.assertIn("focusGeneration!==modalFocusGeneration||!modal.open", self.close_helper)

    def test_17_close_clears_modal_focus_suppression_state(self):
        close = self.focus.split("function closeModal(){", 1)[1]
        for state in ("_skipFocusRestoreId", "_focusKey", "_onClose", "_returnFocus"):
            self.assertIn(f"modal.{state}=null", close)
        self.assertIn("document.getElementById(returnFocusId)", close)

    def test_18_stale_focus_frames_are_generation_guarded(self):
        self.assertIn("const focusGeneration=++modalFocusGeneration;", self.focus)
        self.assertGreaterEqual(self.focus.count("focusGeneration!==modalFocusGeneration"), 3)

    def test_19_rapid_cancel_activate_cannot_disable_selector(self):
        self.assertIn("const focusGeneration=++modalFocusGeneration;", self.focus.split("function closeModal(){", 1)[1])
        self.assertNotIn("style.pointerEvents", self.activation)
        self.assertNotIn("setTimeout", self.activation.split("const operativeSelect", 1)[1].split("const actionIds", 1)[0])

    def test_20_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_21_release_notes_are_present(self):
        self.assertIn("## v8.6.31", README)
        self.assertIn("Version 8.6.31 - Fix Player Operative Selector After Cancel", README)
        self.assertIn("## v8.6.30", README)


if __name__ == "__main__":
    unittest.main()
