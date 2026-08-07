import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
APP = (ROOT / "app.js").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
INDEX = (DASHBOARD / "index.html").read_text()
CONFIG = (DASHBOARD / "shared" / "dashboard-config.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class DashboardFoundationTests(unittest.TestCase):
    def test_dashboard_page_references_only_dashboard_assets(self):
        references = re.findall(r'(?:src|href)="([^"]+)"', INDEX)
        self.assertTrue(references)
        self.assertTrue(all(not reference.startswith(("/", "../")) for reference in references))
        for reference in references:
            self.assertTrue((DASHBOARD / reference).is_file(), reference)

    def test_dashboard_page_does_not_load_root_application_files(self):
        self.assertNotIn("../app.js", INDEX)
        self.assertNotIn("../styles.css", INDEX)
        self.assertNotRegex(INDEX, r'["\']/?(?:app\.js|styles\.css)')

    def test_dashboard_is_not_precached(self):
        precache = WORKER.split("const PRECACHE_ASSETS = [", 1)[1].split("];", 1)[0]
        self.assertNotIn("dashboard/", precache)

    def test_dashboard_requests_are_network_only(self):
        dashboard_branch = WORKER.split("// DASHBOARD INTEGRATION START", 1)[1].split("// DASHBOARD INTEGRATION END", 1)[0]
        self.assertIn("fetch(request, {cache: 'no-store'})", dashboard_branch)
        self.assertNotRegex(dashboard_branch, r"caches?\.(?:open|match)")
        fetch_handler = WORKER.split("self.addEventListener('fetch'", 1)[1]
        self.assertLess(fetch_handler.index("/\\/dashboard"), fetch_handler.index("request.mode === 'navigate'"))

    def test_online_check_cannot_use_app_shell_fallback(self):
        self.assertIn("/dashboard(?:\\/|$)/", WORKER)
        self.assertNotIn("APP_SHELL", WORKER.split("// DASHBOARD INTEGRATION START", 1)[1].split("// DASHBOARD INTEGRATION END", 1)[0])

    def test_feature_switch_is_centralized(self):
        dashboard_javascript = "\n".join(path.read_text() for path in DASHBOARD.rglob("*.js"))
        self.assertEqual(dashboard_javascript.count("export const DASHBOARD_FEATURE_ENABLED"), 1)
        self.assertIn("export const DASHBOARD_FEATURE_ENABLED = true;", CONFIG)

    def test_normal_startup_does_not_create_or_load_webrtc(self):
        self.assertNotIn("RTCPeerConnection", APP)
        self.assertIn("import('./dashboard/controller/dashboard-feature.js')", APP)
        self.assertNotRegex(APP, r'(?m)^\s*(?:void\s+|await\s+)?requestDashboardFeature\s*\(')

    def test_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_event_rechecks_remain_eligibility_gated(self):
        online = (DASHBOARD / "controller" / "dashboard-online.js").read_text()
        feature = (DASHBOARD / "controller" / "dashboard-feature.js").read_text()
        self.assertIn("if (shouldRecheckAvailability())", online)
        self.assertIn("setDashboardOnlineEligibility(checkEligibility)", feature)


if __name__ == "__main__":
    unittest.main()
