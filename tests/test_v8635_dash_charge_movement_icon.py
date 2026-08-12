import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
SERVICE_WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class DashChargeMovementIconTests(unittest.TestCase):
    def test_dash_and_charge_share_new_movement_geometry(self):
        self.assertIn("Charge:'charge-movement'", APP)
        self.assertIn("Dash:npoMovementIcons.dash", APP)
        self.assertIn("'Fall Back':'charge'", APP)
        self.assertEqual(APP.count("if(type==='movement'||type==='charge-movement')return `<svg"), 1)

    def test_movement_icon_geometry_and_inherited_color(self):
        icon = APP.split("if(type==='movement'||type==='charge-movement')return `<svg", 1)[1].split("</svg>`;", 1)[0]
        self.assertIn('fill="currentColor"', icon)
        self.assertIn('stroke="currentColor"', icon)
        self.assertIn('<circle cx="4" cy="16" r="3" stroke="none" />', icon)
        self.assertIn('<circle cx="28" cy="16" r="3" fill="none" stroke-width="2" />', icon)
        self.assertIn('<line x1="7" y1="16" x2="25" y2="16"', icon)
        self.assertEqual(icon.count('<path d="M'), 3)
        self.assertIn('aria-hidden="true"', icon)
        self.assertIn('focusable="false"', icon)

    def test_release_version_is_current_and_save_version_is_unchanged(self):
        self.assertIn("const APP_VERSION = '8.6.57';", APP)
        self.assertIn("const APP_VERSION = '8.6.57';", SERVICE_WORKER)
        self.assertIn('<div class="version">V8.6.57</div>', INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.57"))
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
