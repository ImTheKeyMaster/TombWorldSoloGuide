from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parents[1]
APP = (ROOT / 'app.js').read_text()
CONTROLLER = (ROOT / 'dashboard/controller/dashboard-controller.js').read_text()
FEATURE = (ROOT / 'dashboard/controller/dashboard-feature.js').read_text()
PUBLISHER = (ROOT / 'dashboard/controller/dashboard-publisher.js').read_text()
SNAPSHOT = (ROOT / 'dashboard/controller/dashboard-snapshot.js').read_text()
PROTOCOL = (ROOT / 'dashboard/shared/dashboard-protocol.js').read_text()
DASHBOARD = (ROOT / 'dashboard/dashboard.js').read_text()


class DashboardStateTests(unittest.TestCase):
    def test_one_centralized_send_path_and_save_boundary(self):
        self.assertIn("dashboardFeature?.schedulePublish('committed-save')", APP)
        self.assertEqual(APP.count("schedulePublish('committed-save')"), 1)
        self.assertIn('controller.sendDashboardSnapshot(message)', PUBLISHER)
        game_sender_files = list((ROOT / 'dashboard/controller').glob('*.js'))
        direct_sends = [path.name for path in game_sender_files if '.send(' in path.read_text()]
        self.assertEqual(direct_sends, ['dashboard-controller.js'])

    def test_initial_request_debounce_duplicates_and_revisions(self):
        self.assertIn("debounceMs = 150", PUBLISHER)
        self.assertIn('content === lastContent', PUBLISHER)
        self.assertIn('revision + 1', PUBLISHER)
        self.assertIn("detail.status === 'connected'", FEATURE)
        self.assertIn('publishImmediately()', FEATURE)
        self.assertIn('REQUEST_SNAPSHOT', FEATURE + DASHBOARD)

    def test_schema_validation_and_stale_rejection(self):
        self.assertIn('DASHBOARD_SNAPSHOT_SCHEMA_VERSION = 1', PROTOCOL)
        self.assertIn('validateDashboardSnapshot(snapshot)', SNAPSHOT)
        self.assertIn('snapshot.revision <= currentRevision', DASHBOARD)
        self.assertIn('Incompatible game-state schema', DASHBOARD)

    def test_minimized_read_only_projection(self):
        for forbidden in ['randomState', 'transactionId', 'pairing', 'camera', 'innerHTML']:
            self.assertNotIn(forbidden, SNAPSHOT)
        self.assertIn('recentActivity', SNAPSHOT)
        self.assertIn('.slice(0, 10)', SNAPSHOT)
        self.assertIn('READ_ONLY_INBOUND_TYPES', PROTOCOL)
        inbound = PROTOCOL.split('const READ_ONLY_INBOUND_TYPES', 1)[1].split(']);', 1)[0]
        self.assertNotIn('HELLO_ACK', inbound)
        self.assertNotRegex(PROTOCOL, r"['\"](?:move|shoot|fight|activate)['\"]")

    def test_xss_safe_rendering_and_active_state_projection(self):
        self.assertIn('item.textContent = entry.text', DASHBOARD)
        self.assertIn('replaceChildren()', DASHBOARD)
        self.assertNotIn('.innerHTML', DASHBOARD)
        for field in ['turningPoint', 'threat', 'playerReady', 'activeNpoId', 'eventState', 'journal']:
            self.assertIn(field, APP)

    def test_game_logic_and_save_schema_are_unchanged(self):
        self.assertIn('const SAVE_VERSION = 3;', (ROOT / 'persistence.js').read_text())
        integration = APP.split('// DASHBOARD INTEGRATION START')
        self.assertGreaterEqual(len(integration), 4)
        self.assertIn("const APP_VERSION = '8.7.2';", APP)


if __name__ == '__main__':
    unittest.main()
