#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationPr2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def test_official_generation_rows_cover_every_total_once(self):
        table_source = self.app.split("const npoGenerationTable = [", 1)[1].split("];", 1)[0]
        rows = [
            (int(minimum), int(maximum), operative, weapon_ids)
            for minimum, maximum, operative, weapon_ids in re.findall(
                r"min:(\d+),max:(\d+),type:'([^']+)',weaponIds:\[([^]]+)]", table_source
            )
        ]
        expected_types = {
            2: "Canoptek Scarab Swarm", 3: "Canoptek Scarab Swarm",
            4: "Canoptek Macrocyte", 5: "Canoptek Macrocyte", 6: "Canoptek Macrocyte",
            7: "Necron Warrior", 8: "Necron Warrior", 9: "Necron Warrior", 10: "Necron Warrior",
            11: "Canoptek Tomb Crawler", 12: "Canoptek Tomb Crawler",
        }
        actual = {}
        for minimum, maximum, operative, _ in rows:
            for total in range(minimum, maximum + 1):
                self.assertNotIn(total, actual)
                actual[total] = operative
        self.assertEqual(actual, expected_types)

    def test_printed_weapon_variants_are_stable_ids(self):
        for weapon_id in (
            "feeder-mandibles", "gauss-flayer", "gauss-reaper", "combat-attachment",
            "twin-gauss-reapers", "transdimensional-isolator", "claws",
            "gauss-scalpel", "tesla-caster", "claws-and-tail",
        ):
            self.assertIn(f"id:'{weapon_id}'", self.app)
        self.assertIn("weaponIds:['twin-gauss-reapers']", self.app)
        self.assertIn("weaponIds:['transdimensional-isolator']", self.app)
        self.assertIn("weaponId:generatedWeaponId(result)", self.app)

    def test_setup_and_reinforcements_share_one_table(self):
        self.assertEqual(self.app.count("const npoGenerationTable = ["), 1)
        self.assertEqual(self.app.count("function generationResult("), 1)
        self.assertIn("const result=rollNpo();", self.app)
        self.assertIn("function randomReinforcement(){return rollNpo();}", self.app)
        self.assertNotIn("const table=[", self.app)
        self.assertNotRegex(self.app, r"r<=\d+\?'Canoptek")

    def test_canonical_datacards_have_official_characteristics(self):
        expected = {
            "Canoptek Scarab Swarm": (6, 2, 5, 10, 40),
            "Necron Warrior": (5, 2, 4, 9, 32),
            "Canoptek Tomb Crawler": (5, 2, 3, 21, 50),
            "Canoptek Macrocyte": (7, 2, 4, 7, 28),
        }
        for operative, (move, apl, save, wounds, base_size) in expected.items():
            pattern = rf"name:'{re.escape(operative)}',type:'{re.escape(operative)}',move:{move},apl:{apl},save:{save},wounds:{wounds},baseSize:{base_size}"
            self.assertRegex(self.app, pattern)
        self.assertEqual(self.app.count("const npoDefinitions = {"), 1)

    def test_legacy_rosters_normalize_without_rerolls(self):
        normalize_source = self.app.split("function normalizeNpo(npo){", 1)[1].split("\n  }", 1)[0]
        self.assertIn("name:npo.name||definition.name", normalize_source)
        self.assertIn("Number(npo.wounds)", normalize_source)
        self.assertIn("Number(npo.maxWounds)", normalize_source)
        self.assertIn("definition.defaultWeaponId", normalize_source)
        self.assertIn("order:npo.order||'Conceal'", normalize_source)
        self.assertNotIn("roll(", normalize_source)
        self.assertIn("raw.roster.map(normalizeNpo)", self.app)

    def test_new_npos_store_conceal_separately_from_readiness(self):
        create_source = self.app.split("function createNpo(", 1)[1].split("\n  }", 1)[0]
        self.assertIn("weaponId,order:'Conceal'", create_source)
        self.assertIn("ready:options.ready??(battlefieldState==='deployed'&&!dormant)", create_source)
        self.assertIn("const dormant=battlefieldState==='deployed'", create_source)
        self.assertIn("ready:false,deployed:false", self.app)


if __name__ == "__main__":
    unittest.main()
