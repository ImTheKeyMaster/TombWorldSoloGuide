#!/usr/bin/env python3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RemediationPr9StabilizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_shared_normalizers_replace_repeated_validation(self):
        for helper in ("isRecord", "boundedInteger", "normalizeIdList"):
            self.assertIn(f"const {helper}", self.app)
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("merged.turningPoint=boundedInteger(raw.turningPoint,0,999)", normalize)
        self.assertIn("merged.threat=boundedInteger(raw.threat,0,15)", normalize)

    def test_corrupted_top_level_and_npo_data_recover_safely(self):
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("raw=isRecord(raw)?raw:{}", normalize)
        self.assertIn("map(normalizeNpo).filter(Boolean)", normalize)
        npo = self.source("function normalizeNpo(npo)", "function mission()")
        self.assertIn("if(!isRecord(npo))return null", npo)
        self.assertIn("if(!definition)return null", npo)

    def test_event_and_reinforcement_corruption_is_bounded(self):
        normalize = self.source("function normalizeState(raw)", "function npoDefinition")
        self.assertIn("normalizeIdList(importedEvents.available,validInstances)", normalize)
        self.assertIn("normalizeIdList(importedEvents.used,validInstances)", normalize)
        self.assertIn("reinforcementStatus==='placement'&&!reinforcementIds.length?'idle'", normalize)
        self.assertIn("!reinforcementIds.includes(id)", normalize)
        self.assertIn("npo.battlefieldState==='reserve'", normalize)
        self.assertIn("boundedInteger(importedReinforcements.blocked,0,MAX_NPOS)", normalize)

    def test_all_mission_state_variants_have_defensive_defaults(self):
        normalize = self.source("function normalizeMissionState", "const initialState")
        self.assertIn("if(!m)return isRecord(rawMissionState)?{...rawMissionState}:null", normalize)
        for field in ("escapedIds", "completedFeatureIds", "sites", "destruction", "awakenedRooms", "operativeChecks"):
            self.assertIn(field, normalize)
        self.assertIn("normalizeIdList(raw.completedFeatureIds", normalize)
        self.assertIn("normalizeIdList(raw.scoutedRoomIds", normalize)

    def test_persistence_keeps_the_legacy_key_and_handles_storage_failures(self):
        self.assertIn("const STORAGE_KEY = 'tombWorldSoloGuide.v1'", self.app)
        save = self.source("function save()", "function load()")
        self.assertIn("localStorage.setItem(STORAGE_KEY,JSON.stringify(createPersistedSave(state)))", save)
        self.assertIn("The game could not be saved", save)
        load = self.source("function load()", "function normalizeState")
        self.assertIn("return migrateSave(parsed)", load)
        self.assertNotIn("if(!data.version)", self.app)

    def test_invalid_saved_mission_recovers_to_setup(self):
        recovery = self.source("function recoverInvalidMission()", "function normalizeState")
        self.assertIn("if(!state.missionId||missionDefinition(state.missionId))return false", recovery)
        self.assertIn("The saved mission is unavailable. Select a mission to continue.", recovery)
        self.assertEqual(self.app.count("recoverInvalidMission();"), 2)
        self.assertIn("missionRecovered=recoverInvalidMission()", self.app)

    def test_version_and_cache_identifiers_are_synchronized(self):
        expected = "6.1.0"
        self.assertIn(f"const APP_VERSION = '{expected}';", self.app)
        index = (ROOT / "index.html").read_text()
        self.assertIn(f"styles.css?v={expected}", index)
        self.assertIn(f"app.js?v={expected}", index)
        self.assertIn(f"V{expected}", index)
        self.assertIn(f"const APP_VERSION = '{expected}';", (ROOT / "service-worker.js").read_text())
        self.assertIn(f"## v{expected}", (ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
