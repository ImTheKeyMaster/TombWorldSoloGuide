from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    offset = APP.index(start)
    return APP[offset:APP.index(end, offset)]


def resolve_next(*, player_finished, npo_finished, player_remaining, npo_remaining, last_side):
    """Executable specification of the availability matrix wired into app.js."""
    player_can_act = not player_finished and player_remaining > 0
    npo_can_act = not npo_finished and npo_remaining > 0
    if not player_can_act and not npo_can_act:
        return None
    if not player_can_act:
        return "npo"
    if not npo_can_act:
        return "player"
    return "npo" if last_side == "player" else "player"


def test_release_is_v9241_and_finished_state_is_backward_compatible():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 41)
    initial = source("const initialState", "const loadedSave")
    normalizer = source("function normalizeState", "function npoDefinition")
    assert "activationFinishedForTurningPoint:{player:false,npo:false}" in initial
    assert "player:raw.activationFinishedForTurningPoint?.player===true" in normalizer
    assert "npo:raw.activationFinishedForTurningPoint?.npo===true" in normalizer


def test_central_scheduler_uses_finished_state_and_eligible_models():
    scheduler = source("function setNextActivation", "const GRADE_CONFIG")
    assert "playerCanAct=!state.activationFinishedForTurningPoint.player&&playerOperativesRemaining()>0" in scheduler
    assert "npoCanAct=!state.activationFinishedForTurningPoint.npo&&readyNpos().length>0" in scheduler
    assert "return setNextActivation(completedSide==='player'?'npo':'player')" in scheduler
    assert "console.assert(!state.activationFinishedForTurningPoint[state.nextSide]" in scheduler

    assert resolve_next(player_finished=False, npo_finished=False, player_remaining=2, npo_remaining=2, last_side="player") == "npo"
    assert resolve_next(player_finished=False, npo_finished=False, player_remaining=2, npo_remaining=2, last_side="npo") == "player"
    assert resolve_next(player_finished=False, npo_finished=True, player_remaining=2, npo_remaining=2, last_side="player") == "player"
    assert resolve_next(player_finished=True, npo_finished=False, player_remaining=2, npo_remaining=2, last_side="npo") == "npo"
    assert resolve_next(player_finished=False, npo_finished=False, player_remaining=0, npo_remaining=2, last_side="npo") == "npo"
    assert resolve_next(player_finished=False, npo_finished=False, player_remaining=2, npo_remaining=0, last_side="player") == "player"
    assert resolve_next(player_finished=True, npo_finished=True, player_remaining=2, npo_remaining=2, last_side="npo") is None


def test_exact_solo_deathwatch_skip_then_eight_necrons_regression():
    player_finished = True
    npo_finished = False
    player_remaining = 0
    npo_remaining = 8
    scheduled = []

    for _ in range(8):
        side = resolve_next(
            player_finished=player_finished,
            npo_finished=npo_finished,
            player_remaining=player_remaining,
            npo_remaining=npo_remaining,
            last_side="player" if not scheduled else "npo",
        )
        scheduled.append(side)
        assert side == "npo"
        assert player_finished
        npo_remaining -= 1

    assert scheduled == ["npo"] * 8
    assert resolve_next(player_finished=True, npo_finished=False, player_remaining=0, npo_remaining=0, last_side="npo") is None
    assert "player" not in scheduled


def test_inverse_solo_and_both_pvp_skip_directions_repeat_only_eligible_side():
    solo_inverse = [
        resolve_next(player_finished=False, npo_finished=True, player_remaining=remaining, npo_remaining=0, last_side="player")
        for remaining in range(4, 0, -1)
    ]
    pvp_after_a_skip = [
        resolve_next(player_finished=True, npo_finished=False, player_remaining=0, npo_remaining=remaining, last_side="npo")
        for remaining in range(5, 0, -1)
    ]
    pvp_after_b_skip = [
        resolve_next(player_finished=False, npo_finished=True, player_remaining=remaining, npo_remaining=0, last_side="player")
        for remaining in range(5, 0, -1)
    ]
    assert solo_inverse == ["player"] * 4
    assert pvp_after_a_skip == ["npo"] * 5
    assert pvp_after_b_skip == ["player"] * 5
    assert resolve_next(player_finished=True, npo_finished=True, player_remaining=0, npo_remaining=0, last_side="npo") is None


def test_skip_persists_before_resolution_save_render_and_reload():
    transaction = source("function skipRemainingActivations(){", "function showCeaselessScuttling")
    flag_write = "state.activationFinishedForTurningPoint[side]=true"
    assert flag_write in transaction
    assert transaction.index(flag_write) < transaction.index("advanceAfterActivation(side)")
    assert transaction.index(flag_write) < transaction.index("save()") < transaction.index("render()")
    normalizer = source("function normalizeState", "function npoDefinition")
    assert "raw.activationFinishedForTurningPoint?.player===true" in normalizer
    assert "raw.activationFinishedForTurningPoint?.npo===true" in normalizer


def test_activation_card_guard_recomputes_instead_of_rendering_finished_side():
    card = source("function nextStepCard(){", "function missionStrategyPending")
    assert "setNextActivation(state.nextSide || state.initiative || 'player')" in card
    assert card.index("setNextActivation(state.nextSide || state.initiative || 'player')") < card.index("if(state.nextSide==='player'")
    assert "setNextActivation(state.nextSide==='player'?'npo':'player')" in card


def test_finished_flags_reset_only_when_next_turning_point_starts():
    start_turn = source("async function startTurningPoint", "async function continueTurningPointStart")
    assert "state.activationFinishedForTurningPoint={player:false,npo:false}" in start_turn
    assert start_turn.index("state.turningPoint++") < start_turn.index("state.activationFinishedForTurningPoint={player:false,npo:false}")
    post_activation_paths = [
        source("async function completeHumanPlayerActivation", "const PLAYER_ACTION_COSTS"),
        source("async function completePlayerActivation", "function npoName"),
        source("async function completeNpoActivation", "function applyNpoAttackDamage"),
    ]
    for path in post_activation_paths:
        assert "activationFinishedForTurningPoint={player:false,npo:false}" not in path
