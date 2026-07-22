import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MissionUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()
        cls.styles = (ROOT / "styles.css").read_text()

    def test_compact_hud_is_semantic_and_has_active_complete_and_neutral_states(self):
        self.assertIn('id="missionHud" type="button"', self.app)
        self.assertIn("model.completed?'✓ COMPLETE':`${model.value} / ${model.target}`", self.app)
        self.assertIn("model?(model.completed", self.app)
        self.assertIn(":'DETAILS'", self.app)
        self.assertIn("$('#missionHud')?.addEventListener('click',showMissionDetails)", self.app)
        self.assertIn("repeat(6,minmax(0,1fr))", self.styles)

    def test_hud_and_game_menu_share_one_details_dialog(self):
        self.assertEqual(len(re.findall(r"function showMissionDetails\(", self.app)), 1)
        self.assertIn("$('#menuMissionDetails').onclick=showMissionDetails", self.app)
        self.assertIn("objectiveEngine.getMissionDetailsModel()", self.app)
        self.assertIn("No mission activity yet.", self.app)
        self.assertIn("historyDisplayCount", self.app)
        self.assertIn("Completed during", self.app)

    def test_reusable_mission_dialog_flows_and_completion_wording(self):
        self.assertIn("function showMissionConfirmation(options,onConfirm)", self.app)
        self.assertIn("missionNumericError", self.app)
        self.assertIn("confirm.disabled=!valid", self.app)
        self.assertIn("livingPlayerOperativeCount()", self.app)
        self.assertIn("dice.map(value=>dieHtml({value}))", self.app)
        self.assertIn("function missionOperation(operationId)", self.app)
        self.assertNotIn("objectiveDefinition.hooks.onStrategyPhaseReadyStep?.flatMap", self.app)
        self.assertIn("change.before<model.target", self.app)
        self.assertIn("MISSION OBJECTIVE COMPLETE", self.app)
        self.assertIn("Continue the battle", self.app)
        self.assertNotIn("objectiveEngine.getMissionHudModel().completed)&&checkGameEnd", self.app)

    def test_modal_keyboard_focus_and_mobile_safety(self):
        self.assertIn("modal._returnFocus=active", self.app)
        self.assertIn("returnFocus?.isConnected", self.app)
        self.assertIn("event.key!=='Tab'", self.app)
        self.assertIn("event.key==='Enter'", self.app)
        self.assertIn("if(!missionDialogLocked)closeModal()", self.app)
        self.assertIn("overflow-x:hidden", self.styles)
        self.assertIn("overflow-wrap:anywhere", self.styles)
        self.assertIn(".hud .mission-hud{min-height:44px}", self.styles)

    def test_work_package_05_is_integrated_but_later_packages_remain_deferred(self):
        self.assertIn("onPlayerActivationStarted", self.app)
        self.assertIn("onPlayerActivationCompleted", self.app)
        self.assertNotIn("MISSION AUTOMATION UNAVAILABLE", self.app)
        self.assertNotIn("runtimeSchemaVersion", self.app)


if __name__ == "__main__":
    unittest.main()
