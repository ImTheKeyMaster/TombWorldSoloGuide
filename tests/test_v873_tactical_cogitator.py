from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
HTML = (ROOT / 'dashboard/index.html').read_text()
CSS = (ROOT / 'dashboard/dashboard.css').read_text()
JS = (ROOT / 'dashboard/dashboard.js').read_text()


class TacticalCogitatorTests(unittest.TestCase):
    def test_expected_regions_exist(self):
        for region in ['status-strip', 'mission-panel', 'activation-panel', 'events-panel',
                       'activity-panel', 'roster-panel', 'narrative-panel']:
            self.assertIn(region, HTML)

    def test_snapshot_values_map_to_regions_and_safe_states(self):
        for field in ['battle.turningPoint', 'threat.level', 'mission.name',
                      'currentActivation', 'activeEvents', 'recentActivity',
                      'playerOperatives', 'npoOperatives']:
            self.assertIn(field, JS)
        for state in ['waiting', 'connected', 'complete', 'interrupted', 'incompatible']:
            self.assertIn(state, HTML + JS)
        self.assertIn('No Current Activation', HTML)
        self.assertIn('No active events detected', HTML)
        self.assertIn('No battle activity recorded', HTML)
        self.assertIn('data-player-summary', HTML)
        self.assertIn("states = ['ready', 'active', 'activated', 'incapacitated', 'dormant', 'retired']", JS)
        self.assertIn('event.effect', JS)

    def test_isolated_local_assets_only(self):
        self.assertNotIn('styles.css', HTML.replace('dashboard.css', ''))
        self.assertNotIn('http://', HTML + CSS)
        self.assertNotIn('https://', HTML + CSS)
        self.assertNotRegex(CSS, r'url\([^)]*mockup')
        self.assertNotRegex(CSS, r'background(?:-image)?:[^;]*url\(')
        self.assertIn('assets/tactical-operative.svg', HTML)
        self.assertIn('assets/objective-terrain.svg', HTML)

    def test_safe_text_and_reduced_motion(self):
        self.assertNotIn('innerHTML', JS)
        self.assertIn('textContent', JS)
        self.assertIn('replaceChildren', JS)
        self.assertIn('@media(prefers-reduced-motion:reduce)', CSS)
        self.assertIn('animation:none!important', CSS)


if __name__ == '__main__':
    unittest.main()
