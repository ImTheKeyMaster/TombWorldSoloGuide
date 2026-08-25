"""Picker reopen safety assertions updated for the v9.1 locked activation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text()
STYLES=(ROOT/'styles.css').read_text()
PERSISTENCE=(ROOT/'persistence.js').read_text()

class PlayerActivationReopenSelectTests(unittest.TestCase):
    def test_closing_and_reopening_restores_locked_operative(self):
        show=APP.split('function showPlayerActivation()',1)[1].split('function playerActivationSummary',1)[0]
        self.assertIn('if(active){renderHumanPlayerActionPicker();return;}',show)
        shell=APP.split('function renderHumanActivationShell',1)[1].split('function renderHumanPlayerActionPicker',1)[0]
        self.assertIn('Close Guide',shell)

    def test_selection_is_one_explicit_commit(self):
        show=APP.split('function showPlayerActivation()',1)[1].split('function playerActivationSummary',1)[0]
        self.assertEqual(show.count("beginPlayerActivation($('#humanPlayerSelection').value)"),1)
        self.assertIn('confirmHumanPlayerSelection',show)

    def test_touch_and_focus_safety_remain(self):
        self.assertNotRegex(STYLES,r'#humanPlayerSelection[^}]*pointer-events\\s*:\\s*none')
        self.assertIn("window.matchMedia('(hover: none) and (pointer: coarse)').matches",APP)
        self.assertIn('focusInitialDialogControl',APP)

    def test_save_version_is_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;',PERSISTENCE)

if __name__=='__main__': unittest.main()
