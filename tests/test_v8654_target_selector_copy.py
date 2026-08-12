import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
SELECTOR = APP.split("function showActivationFeatureTargetSelection(stage,action){", 1)[1].split(
    "function showActivationBreachTargetSelection(stage)", 1
)[0]


class TargetSelectorCopyV8654Tests(unittest.TestCase):
    def test_breach_uses_breach_point_copy(self):
        self.assertIn("const targetLabel=isHatch?'Hatchway':'Breach point';", SELECTOR)
        self.assertIn("const targetPlaceholder=isHatch?'Select hatchway…':'Select breach point…';", SELECTOR)

    def test_operate_hatch_uses_hatchway_copy(self):
        self.assertIn("isHatch=action==='operate-hatch'", SELECTOR)
        self.assertIn("${targetLabel}</label>", SELECTOR)
        self.assertIn("${targetPlaceholder}</option>", SELECTOR)
        self.assertNotIn(">Target feature</label>", SELECTOR)
        self.assertNotIn(">Select target…</option>", SELECTOR)

    def test_target_filtering_is_unchanged(self):
        self.assertIn("featureType=isHatch?'hatchway':'breach-point'", SELECTOR)
        self.assertIn("const available=closedMissionFeatures(featureType);", SELECTOR)
        self.assertIn("available.some(feature=>feature.id===stage[targetKey])", SELECTOR)
        self.assertIn("available.find(item=>item.id===select.value)", SELECTOR)

    def test_action_behavior_is_unchanged(self):
        self.assertNotIn("commitMissionFeatureOpened", SELECTOR)
        self.assertIn(">Confirm Target</button>", SELECTOR)
        self.assertIn("if(confirm.disabled)return;", SELECTOR)
        self.assertIn("resolvePendingPlayerAttacks(nextStage);", SELECTOR)

    def test_release_version_and_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.56';", APP)
        self.assertIn("const APP_VERSION = '8.6.56';", WORKER)
        self.assertIn('<div class="version">V8.6.56</div>', INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.56"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.56", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
