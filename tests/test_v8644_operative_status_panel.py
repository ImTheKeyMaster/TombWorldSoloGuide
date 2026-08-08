import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
CSS = (ROOT / 'styles.css').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()


class OperativeStatusPanelTests(unittest.TestCase):
    def test_version_and_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.44';", APP)
        self.assertIn('V8.6.44', INDEX)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)

    def test_central_accessible_read_only_panel(self):
        self.assertIn('id="operativeStatusPanel"', INDEX)
        self.assertIn('aria-label="Operative status"', INDEX)
        self.assertIn('<h2>NPO Operatives</h2>', APP)
        self.assertIn('<h2>Player Operatives</h2>', APP)
        self.assertNotRegex(APP, r'operative-status-row[^`]*<(?:button|input|select)')

    def test_toggle_accessibility_and_persistence(self):
        self.assertIn('aria-label="Show operative status" aria-pressed="false"', INDEX)
        self.assertIn("'tombWorldSoloGuide.showOperativeStatus'", APP)
        self.assertIn("setAttribute('aria-pressed',String(visible))", APP)
        self.assertIn("visible?'Hide operative status':'Show operative status'", APP)
        self.assertIn("localStorage.setItem(OPERATIVE_STATUS_PREFERENCE_KEY", APP)

    def test_visibility_is_game_and_large_landscape_only(self):
        self.assertIn("state.screen==='game'&&operativeStatusMedia.matches", APP)
        self.assertIn("'(min-width: 900px) and (orientation: landscape)'", APP)
        self.assertIn('@media (max-width:899px), (orientation:portrait)', CSS)

    def test_workspace_and_vertical_sections(self):
        self.assertIn('grid-template-columns:minmax(320px,390px) minmax(0,1fr)', CSS)
        self.assertIn('grid-template-rows:minmax(0,1fr) minmax(0,1fr)', CSS)
        self.assertLess(INDEX.index('operativeStatusPanel'), INDEX.index('id="app"'))

    def test_authoritative_status_and_wound_precedence(self):
        self.assertLess(APP.index("return {status:'ELIMINATED'", APP.index('function npoTrackerStatus')), APP.index("return {status:'ACTIVE'", APP.index('function npoTrackerStatus')))
        for status in ('ACTIVE', 'READY', 'ACTIVATED', 'DORMANT', 'ELIMINATED', 'RESERVE', 'ESCAPED', 'NOT IN PLAY'):
            self.assertIn(status, APP)
        self.assertIn("current<=0||current<=maximum/2?'severe':current<maximum?'wounded':''", APP)
        self.assertIn('<span>/${maximum}</span>', APP)

    def test_fit_first_progression_and_central_render(self):
        fit = APP[APP.index('function fitOperativeStatusPanel'):APP.index('function scheduleOperativeStatusLayout')]
        self.assertLess(fit.index("add('two-column')"), fit.index("add('extra-compact')"))
        self.assertLess(fit.index("add('extra-compact')"), fit.index("add('allow-scroll')"))
        render = APP[APP.index('function render()'):APP.index('function renderHome()')]
        self.assertEqual(render.count('renderOperativeStatusPanel();'), 1)
        self.assertIn('window.addEventListener(\'resize\',scheduleOperativeStatusLayout)', APP)


if __name__ == '__main__':
    unittest.main()
