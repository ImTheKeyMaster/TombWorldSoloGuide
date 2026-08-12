import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
ICON = (ROOT / "Assets/Icons/move-to-shoot.svg").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
SERVICE_WORKER = (ROOT / "service-worker.js").read_text()


class MoveToShootIconTests(unittest.TestCase):
    def test_only_enable_shoot_movement_questions_use_the_new_icon(self):
        self.assertIn("reposition:'movement',dash:'movement',repositionToShoot:'moveToShoot',dashToShoot:'moveToShoot'", APP)
        self.assertIn("if(enablesShoot&&['reposition','dash'].includes(actionId))", APP)
        self.assertIn("Reposition:npoMovementIcons.reposition,Dash:npoMovementIcons.dash", APP)

    def test_completed_enable_shoot_questions_keep_the_move_to_shoot_icon(self):
        self.assertIn("movementIntentId:q.movementIntent?.id||null", APP)

    def test_icon_asset_uses_fixed_green_and_requested_movement_geometry(self):
        self.assertIn('fill="#76f5a8" stroke="#76f5a8"', ICON)
        self.assertIn('id="movement-start"', ICON)
        self.assertIn('id="movement-line"', ICON)
        self.assertEqual(ICON.count('id="chevron-'), 3)

    def test_destination_is_a_complete_six_element_reticle(self):
        for element_id in (
            'reticle-outer-ring', 'reticle-center-point', 'reticle-top-arm',
            'reticle-bottom-arm', 'reticle-left-arm', 'reticle-right-arm'
        ):
            self.assertIn(f'id="{element_id}"', ICON)
        self.assertIn('<circle id="reticle-outer-ring" cx="35" cy="16" r="4" fill="none" stroke-width="2"/>', ICON)

    def test_movement_icons_share_bright_green_sizing(self):
        styles = (ROOT / 'styles.css').read_text()
        self.assertIn('.npo-question-icon--movement{display:block;width:42px;height:42px;flex:0 0 42px;align-self:center;object-fit:contain;color:#76f5a8}', styles)
        self.assertIn('.npo-question-complete .npo-question-icon--movement{width:30px;height:30px;flex:0 0 30px;color:var(--muted)}', styles)
        self.assertIn('class="npo-question-icon npo-question-icon--movement is-move-to-shoot"', APP)

    def test_movement_confirmation_uses_the_semantic_question_icon(self):
        self.assertIn("iconForNpoQuestion({action:displayAction,movementIntent:state.lastActivation?.movementIntent})", APP)

    def test_asset_artwork_is_rendered_inline_and_precached(self):
        self.assertIn('viewBox="0 0 42 32" fill="none" aria-hidden="true" focusable="false"', APP)
        self.assertIn("'./Assets/Icons/move-to-shoot.svg'", SERVICE_WORKER)

    def test_release_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.59';", APP)
        self.assertIn("const APP_VERSION = '8.6.59';", SERVICE_WORKER)
        self.assertIn('<div class="version">V8.6.59</div>', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.59'))


if __name__ == "__main__":
    unittest.main()
