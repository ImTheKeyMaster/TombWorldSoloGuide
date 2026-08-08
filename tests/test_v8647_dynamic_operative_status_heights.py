import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
README = (ROOT / 'README.md').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()
SERVICE_WORKER = (ROOT / 'service-worker.js').read_text()


class DynamicOperativeStatusHeightTests(unittest.TestCase):
    def setUp(self):
        self.fit = APP[APP.index('function fitOperativeStatusPanel'):APP.index('function scheduleOperativeStatusLayout')]

    def test_sections_have_independent_dynamic_grid_tracks(self):
        panel = re.search(r'\.operative-status-panel\{([^}]+)\}', CSS).group(1)
        self.assertIn('--status-npo-height', panel)
        self.assertIn('--status-player-height', panel)
        self.assertNotIn('minmax(0,1fr) minmax(0,1fr)', panel)
        self.assertIn('operative-status-section npo', APP)
        self.assertIn('operative-status-section player', APP)

    def test_natural_content_heights_are_measured_against_available_height(self):
        self.assertIn('const availableHeight=operativeStatusPanel.clientHeight', self.fit)
        self.assertIn('row.getBoundingClientRect().bottom-listTop', self.fit)
        self.assertIn('listHeightNeeded(list)+sectionChromeHeight(section)', self.fit)
        self.assertNotIn('section.offsetHeight-list.clientHeight', self.fit)
        self.assertIn('if(needs[0]+needs[1]<=availableHeight)', self.fit)
        self.assertIn('heights[0]+=availableHeight-needs[0]-needs[1]', self.fit)

    def test_smaller_section_is_satisfied_before_larger_overflowing_section(self):
        self.assertIn("index===0?1:2", self.fit)
        self.assertIn("sort((a,b)=>(needs[a]-minimums[a])-(needs[b]-minimums[b]))", self.fit)
        self.assertIn("--status-npo-height',`${heights[0]}px`", self.fit)
        self.assertIn("--status-player-height',`${heights[1]}px`", self.fit)

    def test_minimums_are_scaled_when_the_panel_is_too_short(self):
        self.assertIn('if(minimumTotal>availableHeight)', self.fit)
        self.assertIn('height*availableHeight/minimumTotal', self.fit)
        self.assertIn('availableHeight-heights[0]-heights[1]', self.fit)

    def test_scrolling_is_only_enabled_after_dynamic_allocation(self):
        allocation = self.fit.index("--status-player-height',`${heights[1]}px`")
        scrolling = self.fit.index("add('allow-scroll')")
        self.assertLess(allocation, scrolling)
        self.assertIn('list.scrollHeight>list.clientHeight+1', self.fit)
        self.assertIn('.operative-status-section.allow-scroll .operative-status-list{overflow-y:auto', CSS)

    def test_card_and_status_styling_remains_present(self):
        for selector in ('.operative-status-row{', '.operative-status-wounds{',
                         '.operative-status-row.active{', '.operative-status-row.eliminated{'):
            self.assertIn(selector, CSS)

    def test_release_version_and_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.48';", APP)
        self.assertIn("const APP_VERSION = '8.6.48';", SERVICE_WORKER)
        self.assertIn('V8.6.48', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.48'))
        self.assertIn('## v8.6.47', README)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
