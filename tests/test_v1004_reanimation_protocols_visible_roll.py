from pathlib import Path

import pytest

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
ENGINE = (ROOT / "event-effects.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


PIPELINE = source("function applyPendingPlayerDamage", "function showReanimationProtocolsResolution")
PRESENTATION = source("function showReanimationProtocolsResolution", "function finalDiscardedFailedAttackDice")
ANIMATOR = source("function settleAnimatedDice", "function projectedNpoWounds")


def test_solo_roll_is_event_specific_and_visibly_animated():
    assert "if(!isPvpMode()&&!transaction.acknowledged)" in PIPELINE
    assert "showReanimationProtocolsResolution(stage,n,transaction)" in PIPELINE
    assert "rollingDieHtml()" in PRESENTATION
    assert "animated-roll" in PRESENTATION
    assert "settleAnimatedDice" in PRESENTATION
    assert "DICE_ROLL_ANIMATION_MS" in ANIMATOR
    assert "TombWorldDiceSfx.play()" in ANIMATOR
    assert "dice.map(dieHtml)" in ANIMATOR
    assert "classList.replace('animated-roll','settled')" in ANIMATOR
    assert "id=\"continueReanimationProtocols\" disabled" in PRESENTATION
    assert "button.disabled=false" in PRESENTATION
    assert "requestDiceResults" not in PRESENTATION


def test_all_d6_outcomes_reuse_the_existing_threshold_and_messages():
    assert "succeeded=transaction.roll>=4" in PRESENTATION
    assert "${succeeded?'REANIMATED':'REANIMATION FAILED'}" in PRESENTATION
    assert "${succeeded?'returns with 1 wound.':'is incapacitated.'}" in PRESENTATION
    assert "if(transaction.roll>=4)" in PIPELINE
    assert "pending.after=1" in PIPELINE
    assert "pending.discardRemainingAttackDice=true" in PIPELINE
    assert "n.ready=false" in PIPELINE
    assert "applyTemporaryAplModifier" in PIPELINE
    assert "n.preventIncapacitationActionId=state.activationNumber" in PIPELINE
    assert "once-per-Turning-Point attempt was consumed" in PIPELINE


@pytest.mark.parametrize("roll,succeeds", [(1, False), (2, False), (3, False), (4, True), (5, True), (6, True)])
def test_reanimation_threshold_covers_every_d6_result(roll, succeeds):
    assert (roll >= 4) is succeeds
    assert "transaction.roll>=4" in PIPELINE


def test_roll_and_continue_are_transactional_and_idempotent():
    assert "eventTransaction(`incapacitation:${incapacitationId}:reanimation-protocols`" in PIPELINE
    assert "if(!Number.isInteger(transaction.roll))" in PIPELINE
    assert "transaction.roll=value;delete transaction.requesting;save()" in PIPELINE
    assert PIPELINE.count("requestDiceResults({count:1,sides:6,title:'REANIMATION PROTOCOLS'") == 1
    assert "if(button.disabled||transaction.acknowledged)return" in PRESENTATION
    assert "transaction.acknowledged=true" in PRESENTATION
    assert "if(!save()){transaction.acknowledged=false;button.disabled=false;return;}" in PRESENTATION
    assert PRESENTATION.index("transaction.acknowledged=true") < PRESENTATION.index("applyPendingPlayerDamage(stage)")
    assert "state.eventState.reanimationAttempts[eventAttemptKey]" in PIPELINE
    assert "transaction.committed=true" in PIPELINE


def test_per_npo_limit_activity_and_multiple_effect_ordering_remain_authoritative():
    assert "`${context.turningPoint}:${context.npoId}`" in ENGINE
    assert "if(consumed)return context" in ENGINE
    assert "startedTurningPoint===turningPoint" in ENGINE
    assert "expiresAfterTurningPoint>=turningPoint" in ENGINE
    assert "pipelineTransaction.firstSourceId" in PIPELINE
    assert "showIncapacitationOrderChoice" in PIPELINE
    assert "'macrocyte-reanimate'" in PIPELINE
    assert "'tomb-world-event:reanimation-protocols'" in PIPELINE
    assert "offerReanimateForPendingDamage" in PIPELINE


def test_pvp_remains_manual_and_no_turn_end_roll_was_added():
    provider = source("async function requestDiceResults", "function pendingDiceContextIsCurrent")
    assert "if(!isPvpMode())return rollDice" in provider
    assert "return requestManualDiceResults" in provider
    assert "!isPvpMode()&&!transaction.acknowledged" in PIPELINE
    assert "requestDiceResults" not in source("$('#finishTp')", "function confirmSkipRemainingActivations")


def test_battle_log_only_records_the_committed_result():
    success_log = "Reanimation Protocols event: ${npoName(n)} rolled ${transaction.roll} and reanimated with 1 wound"
    failure_log = "Reanimation Protocols event: ${npoName(n)} rolled ${transaction.roll}; its once-per-Turning-Point attempt was consumed."
    assert success_log in PIPELINE
    assert failure_log in PIPELINE
    assert PIPELINE.index("transaction.committed=true") < PIPELINE.index(success_log)


def test_v1004_release_surfaces_and_save_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 4)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "### Visible Reanimation Protocols Rolls" in README
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
