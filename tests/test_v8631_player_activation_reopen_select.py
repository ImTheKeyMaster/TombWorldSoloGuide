"""Picker reopen safety coverage adapted to the v9.1 locked activation."""
from pathlib import Path
import unittest

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
INDEX=(ROOT/'index.html').read_text()
STYLES=(ROOT/'styles.css').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()
README=(ROOT/'README.md').read_text()


def section(start,end): return APP.split(start,1)[1].split(end,1)[0]


class PlayerActivationReopenSelectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection=section('function showPlayerActivation()','function playerActivationSummary')
        cls.active=section('function activePlayerActivation','function beginPlayerActivation')
        cls.begin=section('function beginPlayerActivation','function playerHumanActionCatalog')
        cls.picker=section('function renderHumanPlayerActionPicker','function playerSequentialStage')
        cls.shell=section('function renderHumanActivationShell','function renderHumanPlayerActionPicker')

    def test_01_application_displays_current_version(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';",APP)
        self.assertIn(f'V{CURRENT_APP_VERSION}',INDEX)

    def test_02_selector_never_disables_pointer_events(self):
        self.assertNotRegex(STYLES,r'#humanPlayerSelection[^}]*pointer-events\s*:\s*none')

    def test_03_no_animation_frame_disables_selector(self):
        self.assertNotIn('requestAnimationFrame',self.selection)

    def test_04_selection_is_outside_action_shell(self):
        self.assertNotIn('data-human-action',self.selection)
        self.assertNotIn('humanPlayerSelection',self.picker)

    def test_05_close_does_not_complete_activation(self):
        self.assertIn('Close Guide',self.shell)
        self.assertNotIn('completeHumanPlayerActivation',self.shell)

    def test_06_close_does_not_decrement_player_ready(self):
        self.assertNotIn('playerReady=',self.shell)

    def test_07_close_does_not_increment_activation_count(self):
        self.assertNotIn('activationNumber++',self.shell)

    def test_08_reopen_uses_locked_picker(self):
        self.assertIn('if(active){renderHumanPlayerActionPicker();return;}',self.selection)

    def test_09_fresh_selection_has_placeholder(self):
        self.assertIn('<option value="">Select a Ready operative</option>',self.selection)

    def test_10_selector_remains_touch_interactive(self):
        self.assertNotIn('disabled>',self.selection.split('id="humanPlayerSelection"',1)[1].split('</select>',1)[0])

    def test_11_touch_focus_uses_dialog_focus_marker(self):
        self.assertIn('data-dialog-focus',self.selection)

    def test_12_shell_close_is_a_real_button(self):
        self.assertIn('<button class="btn ghost" data-close>Close Guide</button>',self.shell)

    def test_13_desktop_keyboard_can_reach_selector(self):
        self.assertIn('<select id="humanPlayerSelection"',self.selection)
        self.assertNotIn('tabindex="-1"',self.selection)

    def test_14_selection_commits_exactly_once(self):
        self.assertEqual(self.selection.count("beginPlayerActivation($('#humanPlayerSelection').value)"),1)

    def test_15_selected_operative_gets_effective_ap(self):
        self.assertIn('apl=effectiveApl(operativeId,baseApl)',self.begin)

    def test_16_touch_exemption_remains(self):
        self.assertIn("window.matchMedia('(hover: none) and (pointer: coarse)').matches",APP)

    def test_17_close_uses_shared_modal_behavior(self):
        self.assertIn("$$('[data-human-action]',modalBody)",self.shell)
        self.assertIn('data-close',self.shell)

    def test_18_stale_active_activation_is_guarded(self):
        self.assertIn("state.lastActivation?.side==='player'",self.active)
        self.assertIn('!state.lastActivation.committed',self.active)

    def test_19_rapid_reopen_does_not_create_second_activation(self):
        self.assertLess(self.selection.index('if(active)'),self.selection.index('const candidates='))

    def test_20_save_version_is_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;',PERSISTENCE)

    def test_21_release_notes_are_present(self):
        self.assertIn(f'## v{CURRENT_APP_VERSION}',README)
        self.assertIn('Universal Human Activations',README)


if __name__=='__main__': unittest.main()
