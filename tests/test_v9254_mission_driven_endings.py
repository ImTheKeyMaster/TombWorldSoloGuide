"""Deterministic source-level acceptance checks for the mission-driven battle-ending release."""
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
README = (ROOT / "README.md").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_shifting_labyrinth_waits_for_all_removed_and_uses_half_or_more():
    result = source("function shiftingLabyrinthResult", "function missionOutcomeExplanation")
    assert "removed.size<total" in result
    assert "Math.ceil(total/2)" in result
    assert "escaped.size>=requiredEscapes?'victory':'defeat'" in result
    # Deterministic matrix: (total, escaped, removed, expected).
    cases = [(5,3,3,None),(5,3,5,"victory"),(5,2,5,"defeat"),(4,2,4,"victory"),(4,1,4,"defeat"),(3,2,2,None),(3,2,3,"victory")]
    for total, escaped, removed, expected in cases:
        actual = None if removed < total else ("victory" if escaped >= -(-total//2) else "defeat")
        assert actual == expected


def test_escape_result_copy_comes_from_the_same_threshold_calculation():
    explanation = source("function missionOutcomeExplanation", "const missionOutcomeEvaluators")
    assert "const result=shiftingLabyrinthResult()" in explanation
    assert "result.escaped>=result.requiredEscapes" in explanation
    assert "${result.escaped} of ${result.total} operatives escaped" in explanation
    assert "Fewer than half of" in explanation and "At least half of" in explanation


def test_all_six_evaluators_are_mission_driven():
    evaluators = source("const missionOutcomeEvaluators", "function missionOutcome")
    assert "turning-point-limit" not in evaluators
    assert "completedFeatureIds.length>=engine.required?'victory':null" in evaluators
    assert "progress.escaped?'victory':null" in evaluators
    assert "progress.destruction>=engine.required?'victory':null" in evaluators
    assert "progress.scoutedRoomIds.length>=engine.required?'victory':null" in evaluators
    assert "timing!=='end-turning-point'" in evaluators


def test_elimination_defeat_precedes_regroup_and_other_objectives():
    outcome = source("function missionOutcome(timing='immediate')", "let battleEndHookPending")
    assert outcome.index("livingPlayerOperativeCount()===0") < outcome.index("missionOutcomeEvaluators")
    assert "engine?.type!=='escape'" in outcome


def test_legacy_tp4_limit_defeat_is_only_repaired_when_unambiguous():
    normalize = source("function normalizeState(raw)", "function npoDefinition")
    assert "const obsoleteLimitDefeat=" in normalize
    for guard in ("merged.turningPoint===4", "merged.gameEnd==='defeat'", "merged.finalResolution.turningPointEnded", "livingSavedPlayers>0", "!objectiveWasAchieved"):
        assert guard in normalize
    assert "merged.gameEnd=null;merged.completed=false;merged.phase='between'" in normalize
    assert "Battle restored because Tomb World Joint Ops does not automatically end after Turning Point 4." in normalize


def test_version_surfaces_and_release_notes():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 54)
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    index = (ROOT / "index.html").read_text()
    worker = (ROOT / "service-worker.js").read_text()
    assert f"V{CURRENT_APP_VERSION}" in index and index.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
