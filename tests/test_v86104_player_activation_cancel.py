from versioning import CURRENT_APP_VERSION
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


class PlayerActivationCancelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activation = re.search(
            r"function showPlayerActivation\(stage=\{\}\).*?\n  function readPlayerActivationStage",
            APP,
            re.S,
        ).group()
        cls.fieldset = cls.activation.split(
            '<fieldset id="playerActivationControls"', 1
        )[1].split("</fieldset>", 1)[0]
        cls.actions = cls.activation.split("</fieldset>", 1)[1].split(
            "`,undefined,'player-activation'", 1
        )[0]

    def test_initial_controls_are_inactive_and_accessibly_disabled(self):
        self.assertIn("class=\"${selectedId?'':'inactive'}\"", self.activation)
        self.assertIn("aria-disabled=\"${selectedId?'false':'true'}\"", self.activation)
        self.assertRegex(
            STYLES,
            r"#playerActivationControls\.inactive\s*\{[^}]*pointer-events\s*:\s*none",
        )
        for control_id in (
            "eaMove", "eaDash", "eaCharge", "eaFallBack", "eaShoot",
            "eaMelee", "eaDamage", "eaHatch", "eaBreach", "eaObjective", "eaPass",
        ):
            self.assertNotIn(f'id="{control_id}"', self.actions)

    def test_cancel_is_enabled_and_outside_inactive_fieldset(self):
        self.assertNotIn('id="cancelPlayerActivation"', self.fieldset)
        self.assertIn('id="cancelPlayerActivation"', self.actions)
        cancel_tag = self.actions.split('id="cancelPlayerActivation"', 1)[0].rsplit("<button", 1)[1]
        self.assertNotIn("disabled", cancel_tag)
        self.assertNotIn("aria-disabled", cancel_tag)

    def test_complete_activation_requires_an_operative(self):
        self.assertNotIn('id="confirmPlayer"', self.fieldset)
        self.assertIn(
            'id="confirmPlayer" ${selectedId?\'\':\'disabled\'}', self.actions
        )
        self.assertIn(
            "$('#confirmPlayer').disabled=!current.playerOperativeId || used>apl || conflicts.length>0;",
            self.activation,
        )

    def test_selection_enables_controls_and_preserves_validation(self):
        self.assertIn("aria-disabled=\"${selectedId?'false':'true'}\"", self.activation)
        self.assertIn("const conflicts=playerActionConflicts(current);", self.activation)
        self.assertIn("used>apl || conflicts.length>0", self.activation)
        self.assertNotIn("disabled", self.actions.split('id="cancelPlayerActivation"', 1)[0].rsplit("<button", 1)[1])

    def test_cancel_abandons_unconfirmed_stage_without_gameplay_changes(self):
        self.assertIn("$('#cancelPlayerActivation').onclick=()=>{closeModal();render();};", self.activation)
        cancel_handler = self.activation.split(
            "$('#cancelPlayerActivation').onclick=", 1
        )[1].split("$('#confirmPlayer').onclick=", 1)[0]
        self.assertNotRegex(
            cancel_handler,
            r"resolvePendingPlayerAttacks|playerReady|activated|damage|playerActionCost|save\(|Turning Point",
        )

    def test_release_version_and_save_schema(self):
        self.assertEqual((8, 6, 104), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        self.assertIn(
            f"Version {CURRENT_APP_VERSION} - Player Activation Cancel Fix", README
        )
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
