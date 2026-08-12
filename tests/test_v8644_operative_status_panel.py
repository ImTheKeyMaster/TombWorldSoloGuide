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
        self.assertIn("const APP_VERSION = '8.6.58';", APP)
        self.assertIn('V8.6.58', INDEX)
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
        self.assertIn("'(min-width: 900px) and (orientation: landscape), (min-width: 900px) and (hover: hover) and (pointer: fine)'", APP)
        self.assertIn('(orientation:portrait) and (pointer:coarse)', CSS)

    def test_workspace_and_vertical_sections(self):
        self.assertIn('grid-template-columns:clamp(360px,28vw,540px) minmax(0,1fr)', CSS)
        self.assertIn('grid-template-rows:minmax(0,var(--status-npo-height,1fr)) minmax(0,var(--status-player-height,1fr))', CSS)
        self.assertLess(INDEX.index('operativeStatusPanel'), INDEX.index('id="app"'))

    def test_authoritative_status_and_wound_precedence(self):
        npo_status = APP[APP.index('function npoStatus'):APP.index('function playerStatus')]
        self.assertLess(npo_status.index("return 'ELIMINATED'"), npo_status.index("return 'ACTIVE'"))
        for status in ('ACTIVE', 'READY', 'ACTIVATED', 'DORMANT', 'ELIMINATED', 'RESERVE', 'ESCAPED', 'NOT IN PLAY'):
            self.assertIn(status, APP)
        wounds = APP[APP.index('function statusWoundsHtml'):APP.index('function operativeStatusRow')]
        self.assertNotIn('maximum/2', wounds)
        self.assertNotIn('wounded', wounds)
        self.assertIn('${current} / ${maximum}', wounds)

    def test_fit_first_progression_and_central_render(self):
        fit = APP[APP.index('function fitOperativeStatusPanel'):APP.index('function scheduleOperativeStatusLayout')]
        self.assertLess(fit.index("add('two-column')"), fit.index("add('extra-compact')"))
        self.assertLess(fit.index("add('extra-compact')"), fit.index("add('allow-scroll')"))
        render = APP[APP.index('function render()'):APP.index('function renderHome()')]
        self.assertEqual(render.count('renderOperativeStatusPanel();'), 1)
        self.assertIn('window.addEventListener(\'resize\',scheduleOperativeStatusLayout)', APP)

    def test_active_player_is_rendered_without_mutating_game_state(self):
        self.assertIn('function renderOperativeStatusPanel(activePlayerId=null)', APP)
        self.assertIn('renderOperativeStatusPanel(selectedId);', APP)
        activation = APP[APP.index('function showPlayerActivation'):APP.index('function readPlayerActivationStage')]
        self.assertNotIn('state.activePlayer', activation)


if __name__ == '__main__':
    unittest.main()
