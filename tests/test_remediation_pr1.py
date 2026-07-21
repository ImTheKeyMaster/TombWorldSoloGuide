#!/usr/bin/env python3
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSION_DIR = ROOT / "Missions"


class RemediationPr1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((MISSION_DIR / "manifest.json").read_text())
        cls.missions = {
            entry["id"]: json.loads((MISSION_DIR / entry["file"]).read_text())
            for entry in cls.manifest["missions"]
        }
        cls.app = (ROOT / "app.js").read_text()

    def test_six_missions_and_official_maps_are_available(self):
        self.assertEqual(len(self.manifest["missions"]), 6)
        self.assertEqual([m["number"] for m in self.missions.values()], ["01", "02", "03", "04", "05", "06"])
        for mission in self.missions.values():
            self.assertTrue((ROOT / "Assets" / "Maps" / f"mission-{mission['number']}.png").is_file())
            self.assertTrue(mission["map"]["walls"])

    def test_each_mission_has_stable_specific_setup_checks(self):
        all_id_sets = []
        for mission in self.missions.values():
            checks = mission["setupChecks"]
            ids = [check["id"] for check in checks]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+", check_id) for check_id in ids))
            self.assertTrue(all(check["label"].strip() for check in checks))
            self.assertIn("initial-resources", ids)
            all_id_sets.append(tuple(ids))
        self.assertGreater(len(set(all_id_sets)), 1)

    def test_placement_checks_follow_roster_generation(self):
        placement_ids = {"starting-npos", "starting-conceal", "player-setup", "initial-resources"}
        for mission in self.missions.values():
            by_id = {check["id"]: check for check in mission["setupChecks"]}
            self.assertTrue(all(check["stage"] in {"killzone", "deploy"} for check in mission["setupChecks"]))
            self.assertTrue(all(by_id[check_id]["stage"] == "deploy" for check_id in placement_ids & by_id.keys()))
            self.assertEqual(by_id["map-and-deployment"]["stage"], "killzone")
        self.assertIn("const placementChecks=missionSetupChecks('deploy')", self.app)
        self.assertIn("allNposPlaced&&allPlacementChecked", self.app)
        self.assertIn("generateRoster();clearMissionSetupChecks('deploy')", self.app)
        self.assertLess(self.app.index("if(stepId==='npoRoster')"), self.app.index("if(stepId==='deploy')"))

    def test_official_mission_specific_conditions_are_explicit(self):
        text = lambda mission_id: " ".join(c["label"] for c in self.missions[mission_id]["setupChecks"]).lower()
        for mission_id, mission in self.missions.items():
            mission_text = text(mission_id)
            self.assertIn("mission", mission_text)
            self.assertIn("conceal", mission_text)
            self.assertIn("2cp total", mission_text)
            self.assertIn("up to four equipment options", mission_text)
            self.assertIn("tabletop play", mission_text)
        self.assertIn("spread evenly across the rooms containing objective markers", text("recover-transponder"))
        self.assertIn("three locations shown", text("recover-transponder"))
        self.assertIn("half, rounding down, in the sarcophagus room", text("destroy-sarcophagus"))
        self.assertNotIn("spread evenly", text("scout-sub-crypt"))
        self.assertIn("no npos are set up before the battle", text("scout-sub-crypt"))

    def test_setup_uses_ids_and_normalizes_legacy_arrays(self):
        self.assertIn("data-check=\"${escapeHtml(check.id)}\"", self.app)
        self.assertIn("!Array.isArray(raw.setupChecks)", self.app)
        self.assertIn("currentIds.has(id)", self.app)
        self.assertIn("state.setupChecks={}", self.app)
        self.assertNotIn("state.setupChecks[Number(c.dataset.check)]", self.app)
        self.assertRegex(self.app, r"const allChecked=checks\.length>0&&checks\.every\(check=>state\.setupChecks\[check\.id\]\)")

    def test_roster_scope_and_turning_point_one_baseline(self):
        self.assertIn("does not validate every team-building restriction", self.app)
        self.assertIn("Cooperative team splitting is not currently supported", self.app)
        self.assertIn("state.turningPoint=0", self.app)
        self.assertIn("state.turningPoint++;", self.app)
        self.assertIn("if(state.turningPoint===1||state.threat===0)", self.app)
        self.assertTrue(all(m["firstTurningPointInitiative"] == "player" for m in self.missions.values()))
        self.assertIn("const STORAGE_KEY = 'tombWorldSoloGuide.v1';", self.app)

    def test_version_and_cache_busters_match(self):
        expected = "4.6.1"
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / "service-worker.js").read_text())
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"styles.css?v={expected}", index)
        self.assertIn(f"app.js?v={expected}", index)
        self.assertIn(f"V{expected}", index)
        self.assertTrue((ROOT / "README.md").read_text().startswith(f"# Tomb World Solo Guide v{expected}"))


if __name__ == "__main__":
    unittest.main()
