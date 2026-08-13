from versioning import CURRENT_APP_VERSION
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


class WoundedOperativeStatusTests(unittest.TestCase):
    def setUp(self):
        self.row = APP[APP.index('function operativeStatusRow'):APP.index('function renderOperativeStatusPanel')]

    def test_wounded_class_uses_authoritative_current_and_maximum_values(self):
        self.assertIn("const wounded=!eliminated&&current>0&&current<maximum", self.row)
        self.assertIn("${wounded?' wounded':''}", self.row)
        self.assertNotRegex(self.row, r'percentage|percent|maximum\s*\*|maximum\s*/')

    def test_full_wound_operatives_do_not_match_wounded_condition(self):
        for current, maximum in ((7, 7), (9, 9), (15, 15)):
            self.assertFalse(not (current <= 0) and current > 0 and current < maximum)

    def test_living_wounded_operatives_match_wounded_condition(self):
        for current, maximum in ((6, 7), (8, 9), (13, 15), (1, 9)):
            self.assertTrue(not (current <= 0) and current > 0 and current < maximum)
        rule = re.search(r'\.operative-status-row\.wounded\{([^}]+)\}', CSS).group(1)
        self.assertIn('border:2px solid #f5ff5b', rule)

    def test_eliminated_rows_remain_red_and_cannot_be_wounded(self):
        self.assertIn("const eliminated=status==='ELIMINATED'", self.row)
        self.assertIn('const wounded=!eliminated', self.row)
        for current, maximum in ((0, 7), (0, 9)):
            self.assertFalse(not (current <= 0) and current > 0 and current < maximum)
        eliminated_rule = re.search(r'\.operative-status-row\.eliminated\{\n  ([^}]+)\n\}', CSS).group(1)
        self.assertIn('border:2px solid var(--danger)', eliminated_rule)
        self.assertGreater(CSS.index('.operative-status-row.eliminated{\n  border:2px'), CSS.index('.operative-status-row.wounded{'))

    def test_active_wounded_keeps_non_border_active_treatment_and_status(self):
        self.assertIn("const active=!eliminated&&status==='ACTIVE'", self.row)
        self.assertIn("${active?' active':''}${wounded?' wounded':''}", self.row)
        self.assertIn('${status}</span>', self.row)
        self.assertIn('.operative-status-row.active{border-color:var(--green);background:rgba(53,202,120,.13)}', CSS)
        self.assertLess(CSS.index('.operative-status-row.active{'), CSS.index('.operative-status-row.wounded{'))

    def test_wound_text_and_panel_scope_remain_unchanged(self):
        wounds_rule = re.search(r'\.operative-status-wounds\{([^}]+)\}', CSS).group(1)
        self.assertIn('color:var(--text)', wounds_rule)
        self.assertNotIn('#f5ff5b', wounds_rule)
        self.assertIn('@media (min-width:900px)', CSS[:CSS.index('.operative-status-row.wounded{')])
        self.assertNotRegex(self.row, r'<(?:button|input|select)')

    def test_release_updates_app_but_not_save_version(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
