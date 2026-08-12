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


class TestV8625ActivationBreachMissionSync(unittest.TestCase):
    def test_01_version(self):
        self.assertIn("const APP_VERSION = '8.6.58';", APP)
        self.assertIn("V8.6.58", INDEX)
        self.assertIn("const APP_VERSION = '8.6.58';", WORKER)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.58"))

    def test_02_one_canonical_updater(self):
        self.assertEqual(APP.count("function commitMissionFeatureOpened("), 1)
        self.assertGreaterEqual(APP.count("commitMissionFeatureOpened("), 3)

    def test_03_hatchway_activation_target(self): self.assertIn("isHatch?'hatchTargetId':'breachTargetId'", APP)
    def test_04_breach_point_identity(self): self.assertIn("?'breach-point':'hatchway'", APP)
    def test_05_opened_by_breach(self): self.assertIn("openedBy='breach'", APP)
    def test_06_progress_uses_unique_ids(self): self.assertIn("const ids=new Set(progress.completedFeatureIds||[])", APP)
    def test_07_mission_details_uses_objective(self): self.assertIn("${objective.value} / ${objective.target}", APP)
    def test_08_dashboard_uses_hud_model(self): self.assertIn("objectiveEngine?.getMissionHudModel()", APP)
    def test_09_map_opened_status(self): self.assertIn("?'Operate Hatch':'Breach'", APP)
    def test_10_specific_recent_activity(self): self.assertIn("used ${actionLabel} on`:'Opened'} ${feature.label}", APP)
    def test_11_second_feature_counts(self): self.assertIn("const before=completedFeatureIds.length-1,after=completedFeatureIds.length", APP)
    def test_12_reopen_is_noop(self): self.assertIn("return {status:'already-open',feature}", APP)
    def test_13_rapid_commit_progress_dedup(self): self.assertIn("progress.featureTransactions[transactionKey]", APP)
    def test_14_rapid_commit_history_dedup(self): self.assertIn("history.some(entry=>entry.id===historyId)", APP)
    def test_15_selection_does_not_commit(self): self.assertNotIn("commitMissionFeatureOpened", self._function("showActivationBreachTargetSelection"))
    def test_16_cancel_returns_without_commit(self): self.assertIn("cancelActivationBreach').onclick=()=>showPlayerActivation", APP)
    def test_17_close_preserves_pending_stage(self): self.assertIn("state.combatState={side:'player',stage:{...stage,[targetKey]:pendingId,[typeKey]:featureType}}", APP)
    def test_18_commit_at_activation_completion(self):
        activation = self._function("completePlayerActivation")
        self.assertIn("commitMissionFeatureOpened", activation)
        self.assertLess(activation.index("commitMissionFeatureOpened"), activation.index("advanceAfterActivation('player')"))
    def test_19_failed_lookup_or_commit_recovers_atomically(self):
        updater = self._function("commitMissionFeatureOpened")
        self.assertIn("runtimeSnapshot", updater)
        self.assertIn("restoreMissionRuntime", updater)
        self.assertIn("target unavailable", APP)
    def test_20_refresh_before_commit(self): self.assertIn("breachTargetId:previous.breachTargetId||null", APP)
    def test_21_refresh_after_commit(self): self.assertIn("missionFeatureCommitted:Boolean(previous.missionFeatureCommitted)", APP)
    def test_22_update_app_uses_persisted_state(self): self.assertIn("waitingWorker.postMessage({type:'SKIP_WAITING'})", APP)
    def test_23_manual_map_uses_shared_helper(self): self.assertIn("source:'mission-map'", APP)
    def test_24_manual_correction_decrements_once(self): self.assertIn("delta:-1", APP)
    def test_25_corrected_feature_can_reopen(self): self.assertIn("delete state.missionState.featureOpenDetails?.[input.dataset.missionFeature]", APP)
    def test_26_seven_features_complete(self):
        self.assertEqual(MISSION["missionEngine"]["required"], 7)
        self.assertIn("checkGameEnd();", self._function("completePlayerActivation"))
    def test_27_battle_complete_uses_canonical_progress(self): self.assertIn("${missionProgressHtml(true)}", APP)
    def test_28_export_import_preserves_state(self):
        self.assertIn("createPersistedSave(state)", APP)
        self.assertIn("normalizeMissionState(raw?.missionState", APP)
    def test_29_other_missions_are_scoped_out(self): self.assertIn("selectedMission?.id!=='demolition-protocol'", APP)
    def test_30_save_version_unchanged(self): self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
    def test_31_release_notes(self): self.assertIn("Version 8.6.25 - Sync Breach Actions with Mission Progress", README)

    @staticmethod
    def _function(name):
        start = APP.index(f"function {name}(")
        next_function = APP.find("\n  function ", start + 1)
        return APP[start: next_function if next_function >= 0 else len(APP)]


if __name__ == "__main__":
    unittest.main()
