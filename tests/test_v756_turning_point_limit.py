"""Regression coverage replacing the invalid v7.5.6 four-TP rule tests.

The Tomb World Joint Ops sequence ends battles when each mission specifies, not
at a global Turning Point limit.
"""
from versioning import CURRENT_APP_VERSION
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_no_global_turning_point_limit_remains():
    for obsolete in ("MAX_TURNING_POINTS", "turning-point-limit", "resolveTurningPointLimit"):
        assert obsolete not in APP


def test_turning_points_are_not_clamped_during_save_normalization():
    normalize = source("function normalizeState(raw)", "function npoDefinition")
    assert "merged.turningPoint=boundedInteger(raw.turningPoint,0,999)" in normalize
    assert "Math.min(boundedInteger(raw.turningPoint" not in normalize


def test_tp4_cleanup_uses_the_normal_between_turning_point_path():
    binding = source("$('#finishTp')?.addEventListener", "$('#newGameFromPlay')")
    assert "executeMissionLifecycleHook('onTurningPointEnded')" in binding
    assert "checkGameEnd('end-turning-point')" in binding
    assert "state.phase='between'" in binding
    assert "turningPoint>=4" not in binding


def test_tp5_and_tp6_use_the_ordinary_strategy_pipeline():
    start = source("async function startTurningPoint()", "async function continueTurningPointStart")
    for behavior in ("state.turningPoint++", "processReadyStep()", "applyMissionReadyHooks()", "finishTurningPointStart()"):
        assert behavior in start
    finish = source("async function finishTurningPointStart()", "function completeStrategyStage")
    for behavior in ("determineInitiative()", "processEventStage()", "processReinforcementStage()", "Turning Point ${state.turningPoint} started"):
        assert behavior in finish
    assert "state.turningPoint" not in start.split("state.turningPoint++", 1)[0]


def test_between_ui_has_no_maximum_and_names_the_next_turning_point():
    card = source("function nextStepCard()", "function turnOverview")
    assert "Start Turning Point ${state.turningPoint+1}" in card
    assert 'id="startTp"' in card
    assert "BATTLE COMPLETE" not in card


def test_version_is_current_release():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 54)
