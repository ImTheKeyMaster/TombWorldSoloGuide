from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def test_release_surfaces_are_v9239_without_save_key_or_schema_change():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 39)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")


def test_visibility_uses_generic_objective_and_unresolved_activation_state():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "state.phase!=='firefight'" in visibility
    assert "state.completed||state.gameEnd" in visibility
    assert "playerOperativesRemaining()<=0&&readyNpos().length<=0" in visibility
    assert "objectiveEngine?.getMissionHudModel().completed" in visibility
    assert "activation&&!activation.committed&&!activation.completed" in visibility
    for pending in ("state.pendingDice", "state.combatState", "state.fightState", "state.missionActionContext", "state.weaponRuleResolution", "state.hotResolution"):
        assert pending in visibility
    assert APP.count("Skip Remaining Activations</button>") == 1
    assert ".skip-remaining-activations{width:100%;margin-top:10px}" in STYLES


def test_confirmation_has_exact_copy_one_step_and_back_is_non_mutating():
    confirmation = source("function confirmSkipRemainingActivations", "function skipRemainingActivations")
    assert "SKIP REMAINING ACTIVATIONS?" in confirmation
    assert "All unactivated operatives and NPOs will be treated as finished for this Turning Point. You will continue to the end-of-turn steps." in confirmation
    assert "data-close data-dialog-focus>BACK" in confirmation
    assert 'id="confirmSkipRemainingActivations">SKIP ACTIVATIONS' in confirmation
    assert ".onclick=skipRemainingActivations" in confirmation
    assert "save()" not in confirmation
    assert "state." not in confirmation.split("showModal", 1)[1]


def test_skip_is_single_tracker_transaction_without_gameplay_hooks_or_ai():
    transaction = source("function skipRemainingActivations(){", "function showCeaselessScuttling")
    assert "skipRemainingActivationsPending||!canSkipRemainingActivations()" in transaction
    assert "skipRemainingActivationsPending=true" in transaction
    assert "state.playerActivatedIds=[...new Set" in transaction
    assert "unresolvedNpos.forEach(npo=>{npo.ready=false;})" in transaction
    assert "state.npoActivated+=unresolvedNpos.length" in transaction
    assert "state.activationNumber+=unresolvedPlayerIds.length+unresolvedNpos.length" in transaction
    assert "state.phase='end'" in transaction
    assert "state.nextSide=null" in transaction
    assert "log('Remaining activations skipped.')" in transaction
    assert transaction.index("save()") < transaction.index("render()")
    for forbidden in ("executeMissionLifecycleHook", "completePlayerActivation", "completeNpoActivation", "continueNpoActivation", "commitHumanPlayerAction", "requestDiceResults", "setThreat("):
        assert forbidden not in transaction


def test_score_cleanup_remains_manual_and_next_turn_uses_normal_reset():
    end_card = source("if(state.phase==='end'){", "setNextActivation(state.nextSide")
    start_turn = source("async function startTurningPoint", "async function continueTurningPointStart")
    assert "Score and clean up" in end_card
    assert 'id="endChecked" type="checkbox"' in end_card
    assert 'id="finishTp" disabled' in end_card
    assert "playerActivatedIds=[]" in start_turn
    assert "state.playerActivated=0;state.npoActivated=0" in start_turn
    assert "processReadyStep()" in start_turn


def test_immediate_transponder_victory_and_regressions_remain_intact():
    escape = source("let transponderEscapePending", "function handleTransponderCarrierIncapacitation")
    outcome = source("if(state.gameEnd){", "if(state.finalResolution?.pending")
    assert "completeMission('victory')" in escape
    assert "confirmSkipRemainingActivations" not in escape
    assert "requestAnimationFrame(()=>{resetOutcomeScroll();" in outcome
    assert "Assets/Maps/mission-${missionNumber}.png?v=${APP_VERSION}" in APP
