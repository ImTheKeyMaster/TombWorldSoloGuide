"""The v8.6.24 touch regression adapted to the separated v9.1 picker."""
from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
INDEX=(ROOT/'index.html').read_text()
STYLES=(ROOT/'styles.css').read_text()
WORKER=(ROOT/'service-worker.js').read_text()
README=(ROOT/'README.md').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()


def section(start,end): return APP.split(start,1)[1].split(end,1)[0]


class MobileOperativePickerCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection=section('function showPlayerActivation()','function playerActivationSummary')
        cls.begin=section('function beginPlayerActivation','function playerHumanActionCatalog')
        cls.picker=section('function renderHumanPlayerActionPicker','function playerSequentialStage')
        cls.shell=section('function renderHumanActivationShell','function renderHumanPlayerActionPicker')
        cls.touch=section('function closeTouchSelectAfterCommit','let modalFocusSequence')

    def test_01_release_surfaces_are_current(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';",APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';",WORKER)
        self.assertIn(f'V{CURRENT_APP_VERSION}',INDEX)
        self.assertTrue(README.startswith(f'# Tomb World Battle Guide v{CURRENT_APP_VERSION}'))

    def test_02_selection_is_separate_from_actions(self):
        self.assertIn('Choose a Ready operative',self.selection)
        self.assertNotIn('data-human-action',self.selection)

    def test_03_selection_has_one_commit_handler(self):
        self.assertEqual(self.selection.count("beginPlayerActivation($('#humanPlayerSelection').value)"),1)

    def test_04_placeholder_cannot_continue(self):
        self.assertIn('id="confirmHumanPlayerSelection" disabled',self.selection)
        self.assertIn("disabled=!$('#humanPlayerSelection').value",self.selection)

    def test_05_selection_uses_one_change_handler(self):
        self.assertEqual(self.selection.count("$('#humanPlayerSelection').onchange"),1)
        self.assertNotIn("addEventListener('input'",self.selection)

    def test_06_begin_validates_ready_operative(self):
        self.assertIn('remainingPlayerOperatives().includes(operativeId)',self.begin)

    def test_07_begin_persists_before_rendering_picker(self):
        self.assertLess(self.begin.index('save()'),self.begin.index('renderHumanPlayerActionPicker()'))

    def test_08_selected_operative_is_locked(self):
        self.assertIn('activation.operativeId',self.picker)
        self.assertNotIn('humanPlayerSelection',self.picker)

    def test_09_closing_guide_does_not_cancel_activation(self):
        self.assertIn('Close Guide',self.shell)
        self.assertNotIn('cancelCurrentHumanPlayerAction',self.shell)

    def test_10_reopen_uses_existing_activation(self):
        self.assertIn('if(active){renderHumanPlayerActionPicker();return;}',self.selection)

    def test_11_numeric_ap_remains_visible(self):
        self.assertIn('${remainingAp} / ${startingAp} AP remaining',self.shell)

    def test_12_long_labels_can_wrap(self):
        self.assertIn('overflow-wrap:anywhere',STYLES)
        self.assertIn('white-space:normal',STYLES)

    def test_13_touch_targets_remain_large(self):
        self.assertIn('min-height:56px',STYLES)

    def test_14_narrow_layout_uses_one_action_column(self):
        self.assertIn('@media(max-width:520px)',STYLES)
        self.assertIn('grid-template-columns:1fr',STYLES)

    def test_15_320_width_action_content_stacks(self):
        self.assertIn('@media(max-width:340px)',STYLES)
        self.assertIn('flex-direction:column',STYLES)

    def test_16_coarse_pointer_helper_still_releases_select_focus(self):
        self.assertIn("(hover: none) and (pointer: coarse)",self.touch)
        self.assertIn('select.blur()',self.touch)

    def test_17_keyboard_focus_is_not_suppressed(self):
        self.assertIn('.btn:focus-visible',STYLES)
        self.assertNotRegex(STYLES,r'select:focus(?:-visible)?\s*\{\s*outline\s*:\s*none')

    def test_18_accessible_action_name_contains_cost_and_status(self):
        self.assertIn('`${action.name}, ${action.cost} AP, ${status}${detail}, ${remainingAp} AP remaining`',self.shell)
        self.assertIn('aria-description',self.shell)

    def test_19_save_version_remains_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;',PERSISTENCE)


if __name__=='__main__': unittest.main()
