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


class NonFocusableTitleTests(unittest.TestCase):
    def test_01_version_is_8622(self):
        self.assertIn("const APP_VERSION = '8.7.3';", APP)
        self.assertIn("const APP_VERSION = '8.7.3';", WORKER)
        self.assertIn("V8.7.3", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.7.3"))

    def test_02_select_npo_uses_shared_semantic_title(self):
        self.assertIn("showModal('Select NPO to Activate'", APP)
        self.assertIn('<h2 id="modalTitle">', APP)

    def test_03_shared_title_has_no_tabindex_zero(self):
        self.assertNotIn('<h2 id="modalTitle" tabindex="0"', APP)

    def test_04_shared_title_has_no_tabindex_minus_one(self):
        self.assertNotIn('<h2 id="modalTitle" tabindex="-1"', APP)

    def test_05_titles_are_not_programmatically_focused(self):
        for title_id in ('modalTitle', 'strategy-step-heading', 'activeNpoQuestion',
                         'activeNpoQuestionHeading', 'activeNpoMovementHeading'):
            self.assertNotRegex(APP, rf"(?:#|getElementById\()['\"]?{title_id}.*?\.focus\(")

    def test_06_dialog_is_named_by_title(self):
        self.assertIn("modal.setAttribute('aria-labelledby','modalTitle')", APP)
        self.assertIn('aria-modal="true"', INDEX)

    def test_07_npo_selection_is_preferred_initial_focus(self):
        self.assertIn('<select id="officialNpoSelection" data-dialog-focus>', APP)
        self.assertIn("const preferred=$$('[data-dialog-focus]:not([disabled])',dialog)", APP)

    def test_08_tab_query_excludes_titles(self):
        trap = re.search(r"modal\.addEventListener\('keydown'.*?\n  \}\);", APP, re.S).group()
        self.assertNotRegex(trap, r'h[1-6]')

    def test_09_shift_tab_uses_interactive_control_list(self):
        self.assertIn('event.shiftKey&&document.activeElement===first', APP)

    def test_10_titles_have_no_activation_handlers(self):
        self.assertNotRegex(APP, r"\$\(['\"]#modalTitle['\"].*?(?:onclick|addEventListener)")

    def test_11_same_dialog_rerender_does_not_refocus(self):
        self.assertIn("const shouldFocus=!modal.open||modal._focusKey!==nextFocusKey;", APP)
        self.assertIn("else if(shouldRestoreFocus)restoreDialogControlFocus(modal,activeControlId);", APP)

    def test_12_new_guide_step_has_focus_identity(self):
        self.assertIn("function showModal(title,content,onClose,focusKey=null)", APP)
        self.assertIn("'breach-control-range'", APP)
        self.assertIn("'breach-enemy-range'", APP)
        self.assertIn("'player-activation'", APP)

    def test_13_refresh_restoration_never_focuses_title(self):
        self.assertNotRegex(APP, r"(?:restore|startup|refresh).*?modalTitle.*?focus", re.S)

    def test_14_update_restoration_never_focuses_title(self):
        self.assertNotRegex(APP, r"(?:update|reload).*?modalTitle.*?focus", re.S)

    def test_15_help_heading_is_not_focusable(self):
        self.assertRegex(APP, r'function renderHelp\(\).*?<h2>Instructions & quick reference</h2>')

    def test_16_about_heading_uses_non_focusable_shared_title(self):
        self.assertIn("showModal('About'", APP)

    def test_17_game_menu_heading_uses_non_focusable_shared_title(self):
        self.assertIn("showModal('Game Menu'", APP)

    def test_18_threat_escalation_heading_is_not_focusable(self):
        heading = re.search(r'<h2 id="grade-milestone-heading"[^>]*>', APP).group()
        self.assertNotIn('tabindex', heading)

    def test_19_battle_complete_heading_is_not_focusable(self):
        self.assertIn('<h2>Battle Complete</h2>', APP)

    def test_20_real_buttons_keep_focus_indicator(self):
        self.assertIn('.btn:focus-visible', STYLES)
        self.assertNotIn('*:focus{outline:none}', STYLES.replace(' ', ''))

    def test_21_selects_keep_focus_indicators(self):
        self.assertNotRegex(STYLES, r'(?:select|\*):focus(?:-visible)?\s*\{\s*outline\s*:\s*none')

    def test_22_text_inputs_keep_focus_indicators(self):
        self.assertNotRegex(STYLES, r'(?:input|\*):focus(?:-visible)?\s*\{\s*outline\s*:\s*none')

    def test_23_accordion_buttons_remain_keyboard_accessible(self):
        self.assertIn('class="roster-category-heading"', APP)
        self.assertIn('.roster-category-heading{', STYLES)

    def test_24_titles_remain_assistive_technology_labels(self):
        self.assertIn('<h2 id="modalTitle">', APP)
        self.assertIn("modal.setAttribute('aria-labelledby','modalTitle')", APP)

    def test_25_save_version_is_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_26_collapsed_controls_are_not_focus_targets(self):
        self.assertIn("element.closest('details:not([open])')", APP)
        self.assertIn("':scope > summary'", APP)

    def test_27_no_heading_is_given_focusability(self):
        self.assertNotRegex(APP + INDEX, r'<h[1-6][^>]*(?:tabindex|autofocus)')


if __name__ == '__main__':
    unittest.main()
