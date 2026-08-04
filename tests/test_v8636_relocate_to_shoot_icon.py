import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
ICON = (ROOT / "Assets/Icons/relocate-to-shoot.svg").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
SERVICE_WORKER = (ROOT / "service-worker.js").read_text()


class RelocateToShootIconTests(unittest.TestCase):
    def test_only_enable_shoot_movement_questions_use_the_new_icon(self):
        self.assertIn("if(question?.movementIntent?.purpose==='enable-shoot')return 'relocate-to-shoot';", APP)
        self.assertIn("if(question.concernsControlRange)return 'radar';", APP)
        self.assertIn("Reposition:'objective',Dash:'movement'", APP)

    def test_icon_asset_uses_original_green_and_requested_geometry(self):
        self.assertIn('fill="#76f5a8" stroke="#76f5a8"', ICON)
        self.assertIn('<circle cx="4" cy="16" r="3" stroke="none"/>', ICON)
        self.assertIn('<path d="M7 16h18"', ICON)
        self.assertEqual(ICON.count('3.5Z'), 3)
        self.assertIn('<circle cx="28" cy="16" r="3" fill="none" stroke-width="2"/>', ICON)
        self.assertIn('<circle cx="28" cy="16" r="1"', ICON)

    def test_asset_is_rendered_and_precached(self):
        self.assertIn('src="Assets/Icons/relocate-to-shoot.svg"', APP)
        self.assertIn("'./Assets/Icons/relocate-to-shoot.svg'", SERVICE_WORKER)

    def test_release_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.37';", APP)
        self.assertIn("const APP_VERSION = '8.6.37';", SERVICE_WORKER)
        self.assertIn('<div class="version">V8.6.37</div>', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.37'))


if __name__ == "__main__":
    unittest.main()
