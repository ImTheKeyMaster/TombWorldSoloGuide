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
        self.assertIn("reposition:'movement',dash:'movement',repositionToShoot:'relocate-to-shoot',dashToShoot:'relocate-to-shoot'", APP)
        self.assertIn("if(enablesShoot&&['reposition','dash'].includes(actionId))", APP)
        self.assertIn("Reposition:npoMovementIcons.reposition,Dash:npoMovementIcons.dash", APP)

    def test_completed_enable_shoot_questions_keep_the_relocate_icon(self):
        self.assertIn("movementIntentId:q.movementIntent?.id||null", APP)

    def test_icon_asset_uses_original_green_and_requested_geometry(self):
        self.assertIn('fill="#76f5a8" stroke="#76f5a8"', ICON)
        self.assertIn('<circle cx="4" cy="16" r="3" stroke="none"/>', ICON)
        self.assertIn('<path d="M7 16h18"', ICON)
        self.assertEqual(ICON.count('3.5Z'), 3)
        self.assertIn('<circle cx="28" cy="16" r="3" fill="none" stroke-width="2"/>', ICON)
        self.assertIn('<circle cx="28" cy="16" r="1"', ICON)

    def test_movement_icons_share_bright_green_sizing(self):
        styles = (ROOT / 'styles.css').read_text()
        self.assertIn('.npo-question-icon--movement{display:block;width:42px;height:42px;flex:0 0 42px;align-self:center;object-fit:contain;color:#76f5a8}', styles)
        self.assertIn('.npo-question-complete .npo-question-icon--movement{width:30px;height:30px;flex:0 0 30px;color:#76f5a8}', styles)
        self.assertIn('class="npo-question-icon npo-question-icon--movement" src="Assets/Icons/relocate-to-shoot.svg"', APP)

    def test_movement_confirmation_uses_the_semantic_question_icon(self):
        self.assertIn("iconForNpoQuestion({action:displayAction,movementIntent:state.lastActivation?.movementIntent})", APP)

    def test_asset_is_rendered_and_precached(self):
        self.assertIn('src="Assets/Icons/relocate-to-shoot.svg"', APP)
        self.assertIn("'./Assets/Icons/relocate-to-shoot.svg'", SERVICE_WORKER)

    def test_release_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.39';", APP)
        self.assertIn("const APP_VERSION = '8.6.39';", SERVICE_WORKER)
        self.assertIn('<div class="version">V8.6.39</div>', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.39'))


if __name__ == "__main__":
    unittest.main()
