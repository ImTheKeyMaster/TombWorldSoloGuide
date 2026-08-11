import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
MISSION = json.loads((ROOT / "Missions/02-demolition-protocol.json").read_text())


class MissionFeatureCardSpacingTests(unittest.TestCase):
    def test_release_version_is_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.51';", APP)
        self.assertIn("const APP_VERSION = '8.6.51';", WORKER)
        self.assertIn("V8.6.51", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.51"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.51", INDEX)

    def test_feature_labels_include_normal_space_before_number(self):
        labels = [feature["label"] for feature in MISSION["missionEngine"]["features"]]
        self.assertIn("Breach point 1", labels)
        self.assertIn("Hatchway 5", labels)
        self.assertNotIn("Breach point1", labels)
        self.assertNotIn("Hatchway5", labels)

    def test_label_and_status_are_separate_escaped_elements(self):
        self.assertIn('class="mission-feature-card__label">${escapeHtml(label)}</span>', APP)
        self.assertIn('class="mission-feature-card__status">${escapeHtml(status)}</span>', APP)
        self.assertIn("const status=completed.has(feature.id)?`Opened by ${openedBy==='operate-hatch'?'Operate Hatch':'Breach'}`:'Not opened';", APP)
        self.assertNotIn("1Opened", APP)
        self.assertNotIn("5Not", APP)

    def test_active_and_completed_cards_share_the_feature_card_renderer(self):
        renderers = APP.index("const missionProgressRenderers")
        start = APP.index("    sabotage:(engine,progress", renderers)
        end = APP.index("    transponder:(engine,progress", start)
        sabotage = APP[start:end]
        self.assertEqual(sabotage.count("featureCard(feature)"), 2)
        self.assertRegex(sabotage, r"readOnly\?`<div[^`]+\$\{featureCard\(feature\)\}")
        self.assertRegex(sabotage, r"`<label[^`]+\$\{featureCard\(feature\)\}</label>`")

    def test_status_is_block_below_label_and_wraps_at_spaces(self):
        self.assertRegex(STYLES, r"\.mission-feature-card__label\{[^}]*display:block[^}]*word-break:normal[^}]*\}")
        self.assertRegex(STYLES, r"\.mission-feature-card__status\{[^}]*display:block[^}]*margin-top:\.2rem[^}]*word-break:normal[^}]*\}")
        self.assertNotIn("white-space:nowrap", "\n".join(
            line for line in STYLES.splitlines() if "mission-feature-card__" in line
        ))

    def test_mobile_grid_remains_single_column_without_horizontal_overflow(self):
        self.assertIn("@media(max-width:520px)", STYLES)
        self.assertIn(".mission-objective-grid{grid-template-columns:1fr}", STYLES)
        self.assertIn(".mission-feature-card__text{min-width:0}", STYLES)

    def test_feature_order_and_completion_target_are_unchanged(self):
        engine = MISSION["missionEngine"]
        self.assertEqual(
            [feature["label"] for feature in engine["features"]],
            ["Breach point 1", "Breach point 2"] + [f"Hatchway {number}" for number in range(1, 10)],
        )
        self.assertEqual(engine["required"], 7)
        self.assertIn("completed.size", APP)
        self.assertIn("engine.required", APP)

    def test_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
