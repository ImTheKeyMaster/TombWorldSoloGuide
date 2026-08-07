from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
APP = (ROOT / 'app.js').read_text()
CONFIG = (ROOT / 'dashboard/shared/dashboard-config.js').read_text()
CONTROLLER = (ROOT / 'dashboard/controller/dashboard-controller.js').read_text()
DASHBOARD = (ROOT / 'dashboard/dashboard.js').read_text()
ONLINE = (ROOT / 'dashboard/controller/dashboard-online.js').read_text()
PROTOCOL = (ROOT / 'dashboard/shared/dashboard-protocol.js').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()


class DashboardLifecycleTests(unittest.TestCase):
    def test_feature_disabled_boundary_and_save_version(self):
        self.assertIn('if (!DASHBOARD_CONFIG.featureEnabled) return false', (ROOT / 'dashboard/controller/dashboard-feature.js').read_text())
        self.assertIn('DASHBOARD_FEATURE_ENABLED = true', CONFIG)
        self.assertIn('const SAVE_VERSION = 3;', (ROOT / 'persistence.js').read_text())

    def test_online_home_and_game_menu_gating(self):
        self.assertIn('if (!navigator.onLine)', ONLINE)
        self.assertIn("cache: 'no-store'", ONLINE)
        self.assertIn("id=\"setupDashboardBtn\" hidden", APP)
        self.assertIn('canContinue&&available', APP)
        self.assertIn('Network unavailable', APP)

    def test_generation_cleanup_and_repair(self):
        self.assertIn('generation += 1', CONTROLLER)
        self.assertIn('token !== generation', CONTROLLER)
        self.assertIn("connection.connectionState === 'disconnected'", CONTROLLER)
        self.assertIn("next === 'failed'", CONTROLLER)
        self.assertIn('activeChannels.forEach', CONTROLLER)
        self.assertIn('responseApplied', CONTROLLER)
        self.assertIn('Disconnect Dashboard', APP)
        self.assertIn('Reestablish Pairing', APP)

    def test_reload_and_snapshot_safety(self):
        self.assertIn('COGITATOR LINK LOST', DASHBOARD)
        self.assertIn("sessionStorage.setItem('tomb-world-dashboard-snapshot'", DASHBOARD)
        self.assertIn('snapshot.revision <= currentRevision', DASHBOARD)
        self.assertNotIn('.innerHTML', DASHBOARD)

    def test_protocol_and_size_violations(self):
        self.assertIn('MAXIMUM_ACCEPTED_MESSAGE_SIZE', PROTOCOL)
        self.assertIn('maximumProtocolViolations', CONTROLLER + DASHBOARD)
        self.assertIn('dataChannel.close()', CONTROLLER)

    def test_service_worker_isolation(self):
        precache = WORKER.split('const PRECACHE_ASSETS = [', 1)[1].split('];', 1)[0]
        self.assertNotIn('dashboard/', precache)
        dashboard_branch = WORKER.split('// DASHBOARD INTEGRATION START', 1)[1].split('// DASHBOARD INTEGRATION END', 1)[0]
        self.assertIn("fetch(request, {cache: 'no-store'})", dashboard_branch)
        self.assertNotIn('cache.match', dashboard_branch)


if __name__ == '__main__':
    unittest.main()
