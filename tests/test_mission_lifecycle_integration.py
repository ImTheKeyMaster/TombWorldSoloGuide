import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MissionLifecycleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def test_new_runtime_initializes_once_and_restored_runtime_does_not_replay(self):
        self.assertIn("const restoringRuntime=state.missionRuntime?.missionId===selectedMission.number", self.app)
        self.assertIn("if(!restoringRuntime)await executeMissionLifecycleHook('onMissionInitialized')", self.app)

    def test_all_gameplay_lifecycle_boundaries_use_generic_hooks(self):
        for hook in (
            "onStrategyPhaseReadyStep",
            "onPlayerActivationStarted",
            "onPlayerActivationCompleted",
            "onNpoActivationStarted",
            "onNpoActivationCompleted",
            "onTurningPointEnded",
            "onBattleEnded",
        ):
            self.assertIn(hook, self.app)
        self.assertNotIn("if(state.missionId==='04')", self.app)

    def test_ready_cancellation_stays_in_ready_flow_for_retry(self):
        self.assertIn("if(!missionReadyCompleted)", self.app)
        self.assertIn("state.strategyStage='mission-ready'", self.app)
        self.assertIn('id="retryMissionReady"', self.app)
        self.assertIn("if(outcomes===null)return false", self.app)

    def test_stable_context_and_activation_lock_prevent_duplicate_start_hooks(self):
        self.assertIn("turningPoint:state.turningPoint", self.app)
        self.assertIn("activationId:overrides.activationId??null", self.app)
        self.assertIn("if(missionActivationStarts.has(activationId))return", self.app)
        self.assertIn("missionActivationStarts.clear()", self.app)

    def test_activation_modals_close_before_completion_result_dialogs_open(self):
        player = self.app[self.app.index("async function completePlayerActivation"):self.app.index("function npoName")]
        npo = self.app[self.app.index("async function completeNpoActivation"):self.app.index("function applyNpoAttackDamage")]
        self.assertLess(player.index("closeModal()"), player.index("onPlayerActivationCompleted"))
        self.assertLess(npo.index("closeModal()"), npo.index("onNpoActivationCompleted"))

    def test_lifecycle_outcomes_use_existing_save_history_and_result_ui(self):
        self.assertIn("objectiveEngine.executeMissionHook(hookName,missionLifecycleContext(overrides))", self.app)
        self.assertIn("if(change)showMissionResult", self.app)
        self.assertIn("save();", self.app)
        self.assertNotIn("MISSION AUTOMATION UNAVAILABLE", self.app)
        self.assertNotIn("runtimeSchemaVersion", self.app)


if __name__ == "__main__":
    unittest.main()
