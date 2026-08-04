import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
MISSION = json.loads((ROOT / "Missions/02-demolition-protocol.json").read_text())


class TestV8626OperateHatchMissionSync(unittest.TestCase):
    @staticmethod
    def function(name):
        start = APP.index(f"function {name}(")
        end = APP.find("\n  function ", start + 1)
        return APP[start:end if end >= 0 else len(APP)]

    def test_01_operate_hatch_only_closed_hatchways(self):
        helper = self.function("closedMissionFeatures")
        self.assertIn("featureType===featureType", helper)
        self.assertIn("!opened.has(feature.id)", helper)
        self.assertIn("closedMissionFeatures('hatchway')", APP)

    def test_02_operate_hatch_excludes_breach_points(self):
        selector = self.function("showActivationFeatureTargetSelection")
        self.assertIn("isHatch?'hatchway':'breach-point'", selector)

    def test_03_breach_only_closed_breach_points(self):
        self.assertIn("closedMissionFeatures('breach-point')", APP)
        self.assertIn("showActivationFeatureTargetSelection(finalStage,'breach')", APP)

    def test_04_distinct_target_fields(self):
        self.assertIn("isHatch?'hatchTargetId':'breachTargetId'", APP)

    def test_05_selection_does_not_commit(self):
        self.assertNotIn("commitMissionFeatureOpened", self.function("showActivationFeatureTargetSelection"))

    def test_06_completion_uses_one_canonical_updater(self):
        self.assertEqual(APP.count("function commitMissionFeatureOpened("), 1)
        self.assertIn("commitMissionFeatureOpened", self.function("completePlayerActivation"))

    def test_07_unique_objective_value(self):
        updater = self.function("commitMissionFeatureOpened")
        self.assertIn("new Set(progress.completedFeatureIds||[])", updater)
        self.assertIn("setObjectiveValue('sabotagedFeatures',after", updater)

    def test_08_mission_map_uses_canonical_state(self):
        self.assertIn("data-mission-feature", APP)
        self.assertIn("source:'mission-map'", APP)

    def test_09_dashboard_and_details_use_objective_engine(self):
        self.assertIn("objectiveEngine?.getMissionHudModel()", APP)
        self.assertIn("${objective.value} / ${objective.target}", APP)

    def test_10_recent_activity_identifies_operate_hatch(self):
        self.assertIn("used ${actionLabel} on`:'Opened'} ${feature.label}", APP)
        self.assertIn("openedBy==='operate-hatch'?'Operate Hatch':'Breach'", APP)

    def test_11_mission_history_identifies_operate_hatch(self):
        updater = self.function("commitMissionFeatureOpened")
        self.assertIn("recordMissionHistory", updater)
        self.assertIn("openedBy,source,operativeId", updater)

    def test_12_double_completion_is_idempotent(self):
        updater = self.function("commitMissionFeatureOpened")
        self.assertIn("progress.featureTransactions[transactionKey]", updater)
        self.assertIn("history.some(entry=>entry.id===historyId)", updater)
        complete = self.function("completePlayerActivation")
        self.assertIn("`${activationId}:${item.action}`", complete)
        self.assertIn("missionStateSnapshot", complete)

    def test_13_refresh_preserves_pending_without_commit(self):
        reader = self.function("readPlayerActivationStage")
        for field in ("hatchTargetId", "hatchFeatureType", "hatchTransactionId"):
            self.assertIn(field, reader)
        self.assertIn("state.combatState={side:'player',stage:nextStage};\n      save();", APP)

    def test_14_refresh_after_commit_does_not_recommit(self):
        complete = self.function("completePlayerActivation")
        self.assertIn("stage.missionFeatureCommitted", complete)
        self.assertIn("const replayed=", complete)

    def test_15_map_opened_hatchway_is_ineligible(self):
        self.assertIn("completedFeatureIds", self.function("closedMissionFeatures"))

    def test_16_replayed_transaction_is_idempotent(self):
        self.assertIn("featureTransactions?.[transactionId]===feature.id", APP)

    def test_17_invalid_targets_are_rejected(self):
        updater = self.function("commitMissionFeatureOpened")
        self.assertIn("return {status:'invalid-target'}", updater)
        self.assertIn("identity?.featureType===item.featureType", APP)
        self.assertIn("already-open", updater)

    def test_18_no_targets_disable_actions(self):
        self.assertIn("!closedMissionFeatures('hatchway').length?'disabled':''", APP)
        self.assertIn("No closed ${isHatch?'hatchways':'breach points'} remain", APP)

    def test_19_existing_breach_behavior_uses_shared_path(self):
        self.assertIn("openedBy:item.action", self.function("completePlayerActivation"))
        self.assertIn("function showActivationBreachTargetSelection(stage)", APP)
        self.assertIn("isHatch&&nextStage.breach&&!nextStage.breachTargetId", APP)

    def test_20_v8625_save_shape_loads(self):
        self.assertIn("normalizePendingAttackResultLists(raw.combatState.stage)", APP)
        self.assertIn("normalizeMissionState(raw?.missionState", APP)

    def test_21_save_version_remains_three(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_22_active_release_references(self):
        self.assertIn("const APP_VERSION = '8.6.37';", APP)
        self.assertIn("const APP_VERSION = '8.6.37';", WORKER)
        self.assertIn("V8.6.37", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.37"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.37", INDEX)
        self.assertEqual(MISSION["missionEngine"]["required"], 7)


if __name__ == "__main__":
    unittest.main()
