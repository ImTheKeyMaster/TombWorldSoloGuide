import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class PlayerVariantNameTests(unittest.TestCase):
    def test_variant_names_are_formatted_for_display_without_changing_source_data(self):
        self.assertIn("function playerOperativeDisplayName(name)", APP)
        self.assertIn("replace(/ — (.+)$/", APP)

        source_variants = []
        for path in (ROOT / "Player_Operatives").glob("*.json"):
            data = json.loads(path.read_text())
            source_variants.extend(
                operative["name"]
                for operative in data.get("operatives", [])
                if " — " in operative.get("name", "")
            )

        self.assertTrue(source_variants)
        self.assertIn("Tempestor — Relic bolt pistol", source_variants)
        self.assertIn("Servo-Sentry — Grenade launcher", source_variants)

    def test_every_direct_player_operative_name_render_uses_display_formatter(self):
        expected_render_paths = (
            "escapeHtml(playerOperativeDisplayName(o.name))",
            "escapeHtml(playerOperativeDisplayName(operative.name))",
            "playerOperativeDisplayName(baseName)",
            "`Player — ${playerOperativeDisplayName(operative.name)}`",
        )
        for render_path in expected_render_paths:
            self.assertIn(render_path, APP)

        self.assertNotIn("escapeHtml(o.name)", APP)
        self.assertNotIn("escapeHtml(operative.name)", APP)


if __name__ == "__main__":
    unittest.main()
