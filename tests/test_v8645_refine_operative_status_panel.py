import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


class RefinedOperativeStatusPanelTests(unittest.TestCase):
    def test_living_wounds_have_one_unclassified_presentation(self):
        wounds = APP[APP.index('function statusWoundsHtml'):APP.index('function operativeStatusRow')]
        self.assertIn('class="operative-status-wounds"', wounds)
        self.assertNotRegex(wounds, r'wounded|severe|maximum\s*/\s*2|current\s*<\s*maximum')
        self.assertIn('${current} / ${maximum}', wounds)
        self.assertNotIn('operative-status-current', CSS)

    def test_whole_wound_value_is_prominent_and_stable(self):
        rule = re.search(r'\.operative-status-wounds\{([^}]+)\}', CSS).group(1)
        self.assertIn('font-size:clamp(1rem,1.35vw,1.22rem)', rule)
        self.assertIn('font-weight:950', rule)
        self.assertIn('font-variant-numeric:tabular-nums', rule)
        self.assertIn('white-space:nowrap', rule)
        self.assertIn('text-align:right', rule)

    def test_living_rows_are_compact_bordered_boxes(self):
        rule = re.search(r'\.operative-status-row\{([^}]+)\}', CSS).group(1)
        self.assertIn('grid-template-columns:minmax(0,1fr) auto', rule)
        self.assertIn('border:1px solid var(--line)', rule)
        self.assertIn('border-radius:8px', rule)
        self.assertIn('background:rgba(7,20,15,.82)', rule)

    def test_eliminated_rows_reuse_red_treatment_and_accessible_text(self):
        shared = CSS[CSS.index('.tracker-operative.eliminated,'):CSS.index('.tracker-operative.eliminated{')]
        self.assertIn('.operative-status-row.eliminated', shared)
        self.assertIn('border:2px solid var(--danger)', shared)
        row = APP[APP.index('function operativeStatusRow'):APP.index('function renderOperativeStatusPanel')]
        self.assertIn('operative-status-elimination-icon ${side}', row)
        self.assertIn('aria-hidden="true"', row)
        self.assertIn("status==='ELIMINATED'", row)
        self.assertIn('eliminated', row)
        self.assertIn('eliminated-necron-skull.png', CSS)

    def test_eliminated_precedes_active_and_living_active_is_emphasized(self):
        row = APP[APP.index('function operativeStatusRow'):APP.index('function renderOperativeStatusPanel')]
        self.assertIn("const active=!eliminated&&status==='ACTIVE'", row)
        self.assertIn("${eliminated?' eliminated':''}${active?' active':''}", row)
        self.assertIn('.operative-status-row.active{border-color:var(--green)', CSS)

    def test_fit_modes_preserve_wound_prominence(self):
        fit = APP[APP.index('function fitOperativeStatusPanel'):APP.index('function scheduleOperativeStatusLayout')]
        self.assertLess(fit.index("add('two-column')"), fit.index("add('extra-compact')"))
        self.assertLess(fit.index("add('extra-compact')"), fit.index("add('allow-scroll')"))
        self.assertIn('.operative-status-section.two-column .operative-status-wounds{font-size:1rem}', CSS)
        self.assertIn('.operative-status-section.extra-compact .operative-status-wounds{font-size:1rem}', CSS)
        self.assertIn('overflow:hidden', re.search(r'\.operative-status-panel\{([^}]+)\}', CSS).group(1))

    def test_release_does_not_change_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.63';", APP)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
