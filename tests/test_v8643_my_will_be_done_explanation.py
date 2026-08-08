import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class MyWillBeDoneExplanationTests(unittest.TestCase):
    def test_event_keeps_official_effect_and_adds_automation_explanation(self):
        definition = re.search(
            r"'my-will-be-done':\{(?P<body>[^\n]+)\}", APP
        ).group("body")
        self.assertIn(
            "text:'Until the end of the turning point, while an NPO is in the same room as the sarcophagus, its weapons have Accurate 1.'",
            definition,
        )
        self.assertIn(
            "resultText:'Effect active until the end of this Turning Point. When an NPO attacks, the app will ask whether it is in the same room as the sarcophagus and automatically apply Accurate 1 if applicable.'",
            definition,
        )

    def test_other_activate_events_keep_the_generic_status_fallback(self):
        activation = APP.split("if(type==='activate')", 1)[1].split("if(type==='chittering-drone')", 1)[0]
        self.assertIn(
            "eventDefinitions[event.definitionId]?.resultText||'Effect active until the end of this Turning Point.'",
            activation,
        )

    def test_existing_same_room_accurate_automation_is_preserved(self):
        self.assertIn('Is this NPO in the same room as the sarcophagus?', APP)
        self.assertIn("EventEffects.effectiveWeaponProfile(state,profile", APP)
        engine = (ROOT / "event-effects.js").read_text()
        self.assertIn("context.attackerSide!=='npo'||context.sameRoomAsC1!==true", engine)
        self.assertIn("profile.rules.push('Accurate 1')", engine)

    def test_release_version_is_consistent_without_save_schema_change(self):
        self.assertIn("const APP_VERSION = '8.6.49';", APP)
        self.assertIn("const APP_VERSION = '8.6.49';", (ROOT / "service-worker.js").read_text())
        self.assertIn('<div class="version">V8.6.49</div>', (ROOT / "index.html").read_text())
        self.assertTrue((ROOT / "README.md").read_text().startswith('# Tomb World Solo Guide v8.6.49'))
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
