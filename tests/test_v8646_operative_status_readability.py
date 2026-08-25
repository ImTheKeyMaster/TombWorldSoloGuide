from versioning import CURRENT_APP_VERSION
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()
SERVICE_WORKER = (ROOT / 'service-worker.js').read_text()


class OperativeStatusReadabilityTests(unittest.TestCase):
    def test_panel_width_scales_without_dominating_desktop(self):
        self.assertIn('grid-template-columns:clamp(360px,28vw,540px) minmax(0,1fr)', CSS)
        self.assertIn('grid-template-columns:clamp(300px,34vw,360px) minmax(0,1fr)', CSS)

    def test_names_and_types_wrap_instead_of_routine_ellipsis(self):
        name_rule = re.search(r'\.operative-status-row>strong\{([^}]+)\}', CSS).group(1)
        type_rule = re.search(r'\.operative-status-type\{([^}]+)\}', CSS).group(1)
        for rule in (name_rule, type_rule):
            self.assertNotIn('text-overflow:ellipsis', rule)
            self.assertNotIn('overflow:hidden', rule)
            self.assertIn('overflow-wrap:break-word', rule)
            self.assertIn('white-space:normal', rule)

    def test_two_columns_require_readable_card_width_per_section(self):
        fit = APP[APP.index('function fitOperativeStatusPanel'):APP.index('function scheduleOperativeStatusLayout')]
        self.assertIn('const minimumOperativeCardWidth=220', fit)
        self.assertIn('parseFloat(getComputedStyle(list).columnGap)||0', fit)
        self.assertIn('const twoColumnCardWidth=(list.clientWidth-twoColumnGap)/2', fit)
        self.assertIn('if(twoColumnCardWidth>=minimumOperativeCardWidth)', fit)
        self.assertIn('sections.forEach(section=>', fit)
        self.assertLess(fit.index('twoColumnCardWidth>=minimumOperativeCardWidth'), fit.index("add('two-column')"))
        self.assertLess(fit.index("add('extra-compact')"), fit.index("add('allow-scroll')"))

    def test_wounds_keep_prominent_stable_alignment(self):
        rule = re.search(r'\.operative-status-wounds\{([^}]+)\}', CSS).group(1)
        for declaration in ('font-size:clamp(1rem,1.35vw,1.22rem)', 'font-weight:950',
                            'font-variant-numeric:tabular-nums', 'white-space:nowrap', 'text-align:right'):
            self.assertIn(declaration, rule)

    def test_existing_state_behavior_and_save_schema_are_unchanged(self):
        self.assertIn("'tombWorldBattleGuide.showOperativeStatus'", APP)
        self.assertNotRegex(APP, r'operative-status-row[^`]*<(?:button|input|select)')
        self.assertIn('.operative-status-row.eliminated', CSS)
        self.assertIn('.operative-status-row.active', CSS)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_release_versions_are_current(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", SERVICE_WORKER)
        self.assertIn(f'V{CURRENT_APP_VERSION}', INDEX)
        self.assertNotIn('v=8.6.45', INDEX)


if __name__ == '__main__':
    unittest.main()
