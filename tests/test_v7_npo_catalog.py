#!/usr/bin/env python3
from versioning import CURRENT_APP_VERSION
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V7NpoCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()
        cls.catalog = cls.app.split("const npoDefinitions = {", 1)[1].split(
            "\n  };\n\n  // Official 2D6 table", 1
        )[0]
        cls.entries = re.findall(r"id:'([^']+)',name:'([^']+)',type:'([^']+)',faction:'([^']+)',physicalQuantity:(\d+)", cls.catalog)

    def test_active_catalog_is_exactly_the_seven_boxed_set_types(self):
        expected = [
            ("canoptek-scarab-swarm", "Canoptek Scarab Swarm", "Canoptek Scarab Swarm", "Necron Host", "3"),
            ("necron-warrior", "Necron Warrior", "Necron Warrior", "Necron Host", "10"),
            ("canoptek-tomb-crawler", "Canoptek Tomb Crawler", "Canoptek Tomb Crawler", "Canoptek Circle", "2"),
            ("geomancer", "Geomancer", "Geomancer", "Canoptek Circle", "1"),
            ("canoptek-macrocyte-warrior", "Canoptek Macrocyte Warrior", "Canoptek Macrocyte Warrior", "Canoptek Circle", "3"),
            ("canoptek-macrocyte-accelerator", "Canoptek Macrocyte Accelerator", "Canoptek Macrocyte Accelerator", "Canoptek Circle", "1"),
            ("canoptek-macrocyte-reanimator", "Canoptek Macrocyte Reanimator", "Canoptek Macrocyte Reanimator", "Canoptek Circle", "1"),
        ]
        self.assertCountEqual(self.entries, expected)
        self.assertEqual(len(self.entries), 7)

    def test_retired_types_are_not_active_or_selectable(self):
        self.assertNotRegex(self.catalog, r"name:'Canoptek Macrocyte',type:'Canoptek Macrocyte'")
        selector = self.app.split("function showAddNpo()", 1)[1].split("function adjustPlayerWounds", 1)[0]
        self.assertIn("Object.keys(npoDefinitions)", selector)
        self.assertNotIn("Canoptek Macrocyte'", selector)

    def test_loadouts_are_metadata_not_separate_operative_types(self):
        self.assertIn("loadoutOptions:[{id:'twin-gauss-reapers',name:'Twin gauss reapers and claws'},{id:'transdimensional-isolator',name:'Transdimensional isolator and claws'}]", self.catalog)
        self.assertIn("loadoutOptions:[{id:'gauss-scalpel',name:'Gauss scalpel and claws & tail'},{id:'tesla-caster',name:'Tesla caster and claws & tail'}]", self.catalog)
        active_names = {name for _, name, _, _, _ in self.entries}
        for unsupported_type in ("Gauss Tomb Crawler", "Isolator Tomb Crawler", "Tesla Warrior"):
            self.assertNotIn(unsupported_type, active_names)

    def test_catalog_does_not_require_npo_images(self):
        self.assertNotRegex(self.catalog, r"(?:image|portrait)(?:Path)?:")
        roster_card = self.app.split("function npoRosterCard", 1)[1].split("function operativeCard", 1)[0]
        self.assertNotIn("<img", roster_card)
        self.assertIn("!hasProfile?'PROFILE PENDING'", roster_card)
        self.assertIn("const save=Number.isFinite(n.save)?`${n.save}+`:'—'", roster_card)
        self.assertIn("const wounds=hasProfile?`${n.wounds}/${n.maxWounds}`:'—'", roster_card)

    def test_displayed_application_version_is_7_0_0(self):
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"V{CURRENT_APP_VERSION}", index)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", self.app)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", (ROOT / "service-worker.js").read_text())


if __name__ == "__main__":
    unittest.main()
