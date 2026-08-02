import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


def function_body(name):
    match = re.search(rf"  (?:async )?function {name}\([^\n]*", APP)
    if not match:
        return ""
    end = APP.find("\n  function ", match.end())
    async_end = APP.find("\n  async function ", match.end())
    ends = [value for value in (end, async_end) if value >= 0]
    return APP[match.start():min(ends) if ends else len(APP)]


class TurningPointLimitTests(unittest.TestCase):
    def test_01_authoritative_limit_is_four(self):
        self.assertIn("const MAX_TURNING_POINTS = 4;", APP)

    def test_02_start_guard_precedes_increment(self):
        body = function_body("startTurningPoint")
        self.assertLess(body.index("state.turningPoint>=MAX_TURNING_POINTS"), body.index("state.turningPoint++"))

    def test_03_guard_resolves_and_returns(self):
        body = function_body("startTurningPoint")
        guarded = body[:body.index("state.turningPoint++")]
        self.assertIn("await resolveTurningPointLimit()", guarded)
        self.assertIn("return", guarded)

    def test_04_guard_cannot_initialize_strategy_or_side_effects(self):
        body = function_body("startTurningPoint")
        guarded = body[:body.index("state.turningPoint++")]
        for forbidden in ("strategyData=", "determineInitiative", "processEventStage", "processReinforcementStage", "activationHistory=[]"):
            self.assertNotIn(forbidden, guarded)

    def test_05_turning_points_one_through_four_use_normal_increment(self):
        body = function_body("startTurningPoint")
        self.assertIn("state.turningPoint++", body)
        self.assertIn("finishTurningPointStart()", body)

    def test_06_turning_point_three_still_enters_between(self):
        binding = function_body("bindPlay")
        self.assertIn("state.phase='between'", binding)
        self.assertIn("state.turningPoint>=MAX_TURNING_POINTS", binding)

    def test_07_turning_point_four_uses_final_resolution(self):
        binding = function_body("bindPlay")
        self.assertIn("if(state.turningPoint>=MAX_TURNING_POINTS){await resolveTurningPointLimit();return;}", binding)

    def test_08_between_screen_never_builds_fifth_start_control(self):
        body = function_body("nextStepCard")
        self.assertLess(body.index("state.turningPoint>=MAX_TURNING_POINTS"), body.index('id="startTp"'))
        self.assertIn("No further Turning Point can begin.", body)
        self.assertNotIn("resolveTurningPointLimit", body)
        self.assertIn("void resolveTurningPointLimit()", function_body("bindPlay"))

    def test_09_final_sequence_runs_hook_cleanup_then_outcome(self):
        body = function_body("resolveTurningPointLimit")
        self.assertLess(body.index("onTurningPointEnded"), body.index("completeTurningPointCleanup"))
        self.assertLess(body.index("completeTurningPointCleanup"), body.index("missionOutcome('turning-point-limit')"))

    def test_10_turning_point_four_events_expire(self):
        body = function_body("completeTurningPointCleanup")
        self.assertIn("expiresAfterTurningPoint!==state.turningPoint", body)

    def test_11_final_outcome_uses_canonical_completion(self):
        body = function_body("resolveTurningPointLimit")
        self.assertIn("completeMission(outcome)", body)

    def test_12_guided_final_screen_is_persisted(self):
        body = function_body("resolveTurningPointLimit")
        self.assertIn("state.finalResolution.pending=true", body)
        self.assertIn("save();render()", body)

    def test_13_guided_actions_use_canonical_completion(self):
        body = function_body("renderGame")
        self.assertIn("completeMission('victory')", body)
        self.assertIn("completeMission('defeat')", body)

    def test_14_guided_screen_is_accessible(self):
        body = function_body("renderGame")
        self.assertIn('class="battle-result battle-result--${resultClass}"', body)
        self.assertIn('aria-label="Record mission victory"', body)
        self.assertIn('aria-label="Record mission defeat"', body)
        self.assertIn("$('#recordFinalDefeat')?.focus()", body)

    def test_15_battle_end_hook_and_journal_are_idempotent(self):
        body = function_body("finalizeMissionCompletion")
        self.assertIn("battleEndHookComplete", body)
        self.assertIn("resultLogged", body)
        self.assertLess(body.index("onBattleEnded"), body.index("battleEndHookComplete=true"))

    def test_16_turning_point_end_hook_is_idempotent(self):
        body = function_body("resolveTurningPointLimit")
        self.assertIn("if(turningPointLimitPending)return false", body)
        self.assertIn("if(!state.finalResolution.turningPointEnded)", body)
        self.assertIn("state.finalResolution.turningPointEnded=true", body)

    def test_17_bugged_save_is_clamped_and_transients_are_cleared(self):
        body = function_body("normalizeState")
        self.assertIn("Math.min(boundedInteger(raw.turningPoint,0,999),MAX_TURNING_POINTS)", body)
        for fragment in ("merged.strategyData=null", "merged.combatState=null", "merged.activationHistory=[]", "merged.reinforcementState={turningPoint:MAX_TURNING_POINTS"):
            self.assertIn(fragment, body)

    def test_18_bugged_save_preserves_roster_and_mission_progress(self):
        body = function_body("normalizeState")
        correction = body[body.index("if(invalidTurningPoint)"):body.index("const importedDormancy")]
        self.assertNotIn("merged.roster=[]", correction)
        self.assertNotIn("merged.missionState=null", correction)

    def test_19_bugged_save_correction_journal_is_once(self):
        body = function_body("normalizeState")
        self.assertIn("if(!merged.finalResolution.invalidSaveCorrected)", body)
        self.assertIn("Battle corrected to the ${MAX_TURNING_POINTS}-Turning-Point limit", body)

    def test_20_invalid_turning_point_events_are_removed(self):
        body = function_body("normalizeState")
        self.assertIn("event.startedTurningPoint<=MAX_TURNING_POINTS", body)
        self.assertIn("event.expiresAfterTurningPoint>MAX_TURNING_POINTS", body)

    def test_21_correction_does_not_invoke_npo_migration_notice(self):
        correction = function_body("normalizeState")
        self.assertNotIn("showMigrationNotice", correction)
        self.assertNotIn("requiresRegeneration", correction[correction.index("if(invalidTurningPoint)"):])

    def test_22_escape_has_limit_victory_and_defeat(self):
        body = APP[APP.index("escape:(engine"):APP.index("sabotage:(engine")]
        self.assertIn("'victory':'defeat'", body)
        self.assertIn("timing==='turning-point-limit'?'defeat':null", body)

    def test_23_sabotage_has_limit_victory_and_defeat(self):
        self.assertRegex(APP, r"sabotage:.*\?'victory':timing==='turning-point-limit'\?'defeat':null")

    def test_24_transponder_has_limit_victory_and_defeat(self):
        self.assertRegex(APP, r"transponder:.*\?'victory':timing==='turning-point-limit'\?'defeat':null")

    def test_25_destruction_uses_tracked_official_threshold(self):
        self.assertRegex(APP, r"destruction:\(engine,progress,timing\)=>progress\.destruction>=engine\.required\?'victory'")
        mission = (ROOT / "Missions/04-destroy-sarcophagus.json").read_text()
        self.assertIn('"required": 20', mission)

    def test_26_scout_has_limit_victory_and_defeat(self):
        self.assertRegex(APP, r"scout:.*\?'victory':timing==='turning-point-limit'\?'defeat':null")

    def test_27_regroup_has_limit_victory_and_defeat(self):
        body = APP[APP.index("regroup:(engine"):APP.index("function missionOutcome")]
        self.assertIn("'turning-point-limit'", body)
        self.assertIn("?'victory':timing==='turning-point-limit'?'defeat':null", body)

    def test_28_early_outcomes_and_elimination_remain(self):
        body = function_body("missionOutcome")
        self.assertIn("livingPlayerOperativeCount()===0", body)
        self.assertIn("engine?.type!=='escape'", body)
        self.assertIn("timing='immediate'", body)

    def test_29_pending_resolution_survives_normalization_and_export(self):
        normalization = function_body("normalizeState")
        self.assertIn("pending:Boolean(importedFinalResolution.pending)", normalization)
        self.assertIn("createPersistedSave(state)", function_body("exportSave"))

    def test_30_application_displays_version_756(self):
        self.assertIn("const APP_VERSION = '8.6.22';", APP)
        self.assertIn("const APP_VERSION = '8.6.22';", WORKER)
        self.assertIn("V8.6.22", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.22"))
        self.assertIn("## v8.6.22", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.22", INDEX)


if __name__ == "__main__":
    unittest.main()
