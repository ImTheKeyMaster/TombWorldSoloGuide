from pathlib import Path
import json
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def test_release_surfaces_are_v9240_without_save_key_or_schema_change():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 40)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")


def test_visibility_uses_generic_phase_and_unresolved_activation_state():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "state.phase!=='firefight'" in visibility
    assert "state.completed||state.gameEnd" in visibility
    assert "playerOperativesRemaining()<=0&&readyNpos().length<=0" in visibility
    assert "objectiveEngine" not in visibility
    assert "getMissionHudModel" not in visibility
    assert "activation&&!activation.committed&&!activation.completed" in visibility
    for pending in ("state.pendingDice", "state.combatState", "state.fightState", "state.missionActionContext", "state.weaponRuleResolution", "state.hotResolution"):
        assert pending in visibility
    assert APP.count("Skip Remaining Activations</button>") == 1
    assert ".skip-remaining-activations{width:100%;margin-top:10px}" in STYLES


def test_player_and_npo_main_cards_place_shared_skip_control_after_primary_action():
    cards = source("function nextStepCard(){", "function missionStrategyPending")
    player_primary = '<button class="btn primary big-action" id="playerActivation">Activate an Operative</button>'
    npo_primary = '<button class="btn primary big-action" id="npoActivation">'
    assert player_primary + "${skipRemainingActivationsControl()}" in cards
    assert npo_primary in cards
    assert cards.count("${skipRemainingActivationsControl()}") == 2
    assert cards.index(player_primary) < cards.index("${skipRemainingActivationsControl()}")


def test_visibility_is_independent_of_zero_partial_or_complete_mission_progress():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    for mission_progress in ("0 / 7", "3 / 7", "7 / 7"):
        assert mission_progress not in visibility
    assert "playerOperativesRemaining()<=0&&readyNpos().length<=0" in visibility
    assert "state.phase!=='firefight'||state.completed||state.gameEnd" in visibility


def test_visibility_covers_player_only_npo_only_and_no_remaining_activations():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    assert "playerOperativesRemaining()<=0&&readyNpos().length<=0" in visibility
    assert "playerOperativesRemaining()<=0||readyNpos().length<=0" not in visibility


def test_visibility_runtime_matrix_covers_phase_outcome_eligibility_and_safety():
    visibility = source("function canSkipRemainingActivations", "function skipRemainingActivationsControl")
    scenarios = [
        ({"phase": "firefight", "players": 2, "npos": 0}, True),
        ({"phase": "firefight", "players": 0, "npos": 2}, True),
        ({"phase": "firefight", "players": 0, "npos": 0}, False),
        ({"phase": "strategy", "players": 2, "npos": 2}, False),
        ({"phase": "end", "players": 2, "npos": 2}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "completed": True}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "gameEnd": "victory"}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "gameEnd": "defeat"}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "pendingDice": True}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "combatState": True}, False),
        ({"phase": "firefight", "players": 2, "npos": 2, "lastActivation": {"committed": False, "completed": False}}, False),
    ]
    script = f"""
const scenarios = {json.dumps(scenarios)};
for (const [input, expected] of scenarios) {{
  const state = {{completed:false, gameEnd:null, lastActivation:null, pendingDice:null,
    combatState:null, fightState:null, missionActionContext:null,
    weaponRuleResolution:null, hotResolution:null, ...input}};
  const playerOperativesRemaining = () => input.players;
  const readyNpos = () => Array(input.npos).fill({{ready:true}});
  {visibility}
  if (canSkipRemainingActivations() !== expected) process.exit(1);
}}
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


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
