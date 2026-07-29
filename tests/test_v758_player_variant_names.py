import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PlayerVariantNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.operatives = []
        for path in (ROOT / "Player_Operatives").glob("*.json"):
            data = json.loads(path.read_text())
            cls.operatives.extend(data.get("operatives", []))

    def test_all_player_variant_names_use_parentheses(self):
        names = [operative["name"] for operative in self.operatives]
        self.assertFalse([name for name in names if " — " in name])
        self.assertIn("Servo-Sentry (Grenade Launcher)", names)
        self.assertIn("Tempestor (Relic Bolt Pistol)", names)
        self.assertIn("Gunner (Plasma)", names)
        self.assertIn("Gunner (Melta)", names)
        self.assertIn("Gunner (Flamer)", names)

    def test_non_variant_names_remain_unchanged(self):
        names = [operative["name"] for operative in self.operatives]
        self.assertIn("Trooper", names)
        self.assertIn("Precursor", names)

if __name__ == "__main__":
    unittest.main()
