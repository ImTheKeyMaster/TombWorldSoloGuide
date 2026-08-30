import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(f"function {start}", 1)[1].split(f"function {end}", 1)[0]


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)


def player_action_states(completed, remaining=3):
    return run_node(
        f"""
const fs=require('fs'),app=fs.readFileSync('app.js','utf8');
const extract=(start,end)=>app.slice(app.indexOf(start),app.indexOf(end,app.indexOf(start)));
const activePlayerActivation=()=>null;
const playerAttackWeapons=()=>[{{name:'weapon'}}],hasValidPlayerCombatTargets=()=>true;
const state={{missionId:null}};
const activation={{operativeId:'p1',remainingAp:{remaining},completedActionIds:{json.dumps(completed)},resolvedActions:[]}};
eval(extract('function playerHumanActionState','function renderHumanActivationShell'));
console.log(JSON.stringify({{
 shoot:playerHumanActionState({{id:'shoot',cost:1}},activation),
 fight:playerHumanActionState({{id:'melee',cost:1}},activation),
 charge:playerHumanActionState({{id:'charge',cost:1}},activation),
 reposition:playerHumanActionState({{id:'move',cost:1}},activation),
 dash:playerHumanActionState({{id:'dash',cost:1}},activation),
 fallBack:playerHumanActionState({{id:'fallBack',cost:2}},activation)
}}));
"""
    )


def test_player_shoot_and_fight_are_available_after_each_other():
    after_shoot = player_action_states(["shoot"], 2)
    assert after_shoot["shoot"]["status"] == "Used"
    assert after_shoot["fight"] == {
        "status": "Available", "disabled": False, "reason": "Available"
    }

    after_fight = player_action_states(["melee"], 2)
    assert after_fight["fight"]["status"] == "Used"
    assert after_fight["shoot"] == {
        "status": "Available", "disabled": False, "reason": "Available"
    }


def test_shoot_charge_fight_sequence_spends_and_records_each_action_once():
    completed = []
    remaining = 3
    for action in ("shoot", "charge", "melee"):
        states = player_action_states(completed, remaining)
        key = "fight" if action == "melee" else action
        assert states[key]["status"] == "Available"
        completed.append(action)
        remaining -= 1
    assert completed == ["shoot", "charge", "melee"]
    assert len(completed) == len(set(completed))
    assert remaining == 0


def test_commit_guards_same_action_and_spends_ap_exactly_once():
    commit = section("commitHumanPlayerAction", "confirmEndHumanPlayerActivation")
    assert "completedActionIds||[]).includes(pending.actionId)" in commit
    assert "activation.remainingAp=before-pending.cost" in commit
    assert "activation.completedActionIds=[...(activation.completedActionIds||[]),pending.actionId]" in commit
    assert "activation.resolvedActions=[...(activation.resolvedActions||[])" in commit


def test_player_combat_availability_has_no_geometry_state_or_confirmation():
    legality = section("playerHumanActionState", "renderHumanActivationShell")
    selection = section("selectHumanPlayerAction", "commitHumanPlayerAction")
    forbidden = (
        "inEnemyControlRange", "chargeEndedInControlRange", "fightTargetAvailable",
        "physicalControlRangeState", "Confirm tabletop target legality",
        "Are you within Control Range?", "Is this target within Control Range?",
    )
    for text in forbidden:
        assert text not in legality
        assert text not in selection
    assert "showPendingPlayerAttackWizard" in selection
    assert "hasValidPlayerCombatTargets({})" in legality


def test_target_selection_remains_human_legality_confirmation_without_generic_prompt():
    wizard = section("showPendingPlayerAttackWizard", "showPlayerCombatResolution")
    assert "Select the target and attack profile before rolling." in wizard
    assert 'id="combatTarget"' in wizard
    assert "Confirm tabletop target legality" not in APP
    assert "Is this target within Control Range?" not in APP


def test_cancelled_shoot_or_fight_changes_no_authoritative_activation_values():
    cancel = section("cancelCurrentHumanPlayerAction", "selectHumanPlayerAction")
    assert "activation.pendingAction=null" in cancel
    assert "remainingAp" not in cancel
    assert "completedActionIds" not in cancel
    assert "resolvedActions" not in cancel
    selection = section("selectHumanPlayerAction", "commitHumanPlayerAction")
    assert "showPendingPlayerAttackWizard(stage,action.id" in selection
    assert "cancelCurrentHumanPlayerAction" in selection


def test_movement_conflicts_remain_and_shoot_does_not_disable_charge():
    assert player_action_states(["shoot"], 2)["charge"]["status"] == "Available"
    after_charge = player_action_states(["charge"], 2)
    assert after_charge["reposition"]["status"] == "Unavailable"
    assert after_charge["dash"]["status"] == "Unavailable"
    assert after_charge["fallBack"]["status"] == "Unavailable"
    for completed in (["move"], ["dash"], ["fallBack"]):
        assert player_action_states(completed, 2)["charge"]["status"] == "Unavailable"


def test_pvp_human_necrons_use_shared_shell_without_shoot_fight_conflict():
    legality = section("filterLegalNpoActions", "rankLegalNpoActions")
    picker = section("renderHumanNpoActionPicker", "selectHumanNpoAction")
    assert "cost>remainingAp||completed.has(id)" in legality
    assert "completed.has('fight')" not in legality
    assert "completed.has('shoot')" not in legality
    assert "Unavailable after Shoot" not in picker
    assert "Unavailable after Fight" not in picker
    assert "renderHumanActivationShell" in picker
    assert "currentContext.hasValidFightTarget" not in picker
    assert "currentContext.hasValidShootTarget" not in picker


def test_solo_ai_keeps_feasibility_questions_but_no_blanket_combat_conflict():
    inquiries = APP.split("const NPO_ACTION_INQUIRIES=", 1)[1].split(
        "function npoMovementFocus", 1
    )[0]
    legality = section("filterLegalNpoActions", "rankLegalNpoActions")
    movement = section("npoMovementInquiry", "npoMovementInstruction")
    assert "Is a valid Player operative currently within this NPO’s control range?" in inquiries
    assert "Does this NPO currently have a Player operative it can Shoot without moving?" in inquiries
    assert "hasValidFightTarget" in APP and "hasValidShootTarget" in APP
    assert "completed.has('fight')" not in legality
    assert "completed.has('shoot')" not in legality
    assert "includes('shoot')&&!(activation?.completedActionIds||[]).includes('fight')" not in movement
    assert "includes('fight')&&!(activation?.completedActionIds||[]).includes('shoot')" not in movement
    ranking = section("rankLegalNpoActions", "recommendedNpoActions")
    assert "'flayed-one':['Fight','Charge','Reposition','Dash']" in ranking
    assert "'hexmark-destroyer':['Fall Back','Shoot','Reposition','Dash','Fight']" in ranking


def test_special_free_and_reactive_action_semantics_are_unchanged():
    assert "Multi-Threat Eliminator" in APP
    assert "The Hexmark can perform a free Shoot against the attacking operative." in APP
    assert "flesh-hunger" in APP
    assert "costs 0 AP, starts no activation, and grants no attack" in APP
    assert "No Fight or Shoot was granted" in APP


def test_reload_recalculates_legality_without_new_geometry_persistence():
    normalize = section("normalizeState", "save")
    assert "completedActionIds:Array.isArray(merged.lastActivation.completedActionIds)" in normalize
    assert player_action_states(["shoot"], 2)["fight"]["status"] == "Available"
    assert player_action_states(["melee"], 2)["shoot"]["status"] == "Available"
    assert "chargeEndedInControlRange" not in APP
    assert "physicalControlRangeState" not in APP
    assert "fightTargetAvailable" not in APP


def test_release_surfaces_and_persistence_versions_remain_v921_compatible():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 1)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ):
        assert f"{asset}?v={CURRENT_APP_VERSION}" in INDEX
    assert "tomb-world-battle-guide-" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "Shoot → Charge → Fight is supported" in README
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "localStorage.clear()" not in APP
