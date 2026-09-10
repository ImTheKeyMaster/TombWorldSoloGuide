import json
import re
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
ENGINE = (ROOT / "event-effects.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
RELEASE_VERSION = ".".join(("9", "2", "63"))


def function_source(name, next_name):
    match = re.search(
        rf"((?:async )?function {name}\b.*?)\n  (?:async )?function {next_name}\b",
        APP,
        re.DOTALL,
    )
    assert match, name
    return match.group(1)


def run_node(script):
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)


def event_state(*definition_ids, turning_point=2):
    return {
        "turningPoint": turning_point,
        "eventState": {
            "active": [
                {
                    "definitionId": definition_id,
                    "instanceId": f"{definition_id}-1",
                    "startedTurningPoint": turning_point,
                    "expiresAfterTurningPoint": turning_point,
                }
                for definition_id in definition_ids
            ]
        },
    }


def event_policy(state, **context):
    expression = (
        "const e=require('./event-effects.js');"
        f"process.stdout.write(JSON.stringify(e.effectiveAttackRerolls({json.dumps(state)},{json.dumps(context)})));"
    )
    result = subprocess.run(
        ["node", "-e", expression], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def test_release_surfaces_and_compatibility_constants():
    assert CURRENT_APP_VERSION == RELEASE_VERSION
    assert "## v9.2.62" in README
    assert f"const APP_VERSION = '{RELEASE_VERSION}';" in WORKER
    assert f'<div class="version">V{RELEASE_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={RELEASE_VERSION}") == 10
    assert f"analytics.js?release={RELEASE_VERSION}" in INDEX
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_event_engine_remains_the_authority_and_preserves_defence_rerolls():
    state = event_state("dark-of-the-tomb")
    blocked = event_policy(
        state, turningPoint=2, attackerSide="player", attackType="shoot", moreThanEight=True
    )
    assert blocked["attackDice"] is False
    assert blocked["defenceDice"] is True
    assert "Dark of the Tomb: Attack dice cannot be rerolled at this distance." in blocked["messages"]


def test_short_range_melee_npo_and_expired_event_policies_remain_allowed():
    state = event_state("dark-of-the-tomb")
    contexts = (
        {"turningPoint": 2, "attackerSide": "player", "attackType": "shoot", "moreThanEight": False},
        {"turningPoint": 2, "attackerSide": "player", "attackType": "melee", "moreThanEight": True},
        {"turningPoint": 2, "attackerSide": "npo", "attackType": "shoot", "moreThanEight": True},
        {"turningPoint": 2, "attackerSide": "npo", "attackType": "melee", "moreThanEight": True},
        {"turningPoint": 3, "attackerSide": "player", "attackType": "shoot", "moreThanEight": True},
    )
    assert all(event_policy(state, **context)["attackDice"] for context in contexts)


def test_prohibited_policy_returns_balanced_ceaseless_pool_unchanged_and_complete():
    script = "\n".join(
        (
            function_source("weaponHasRule", "normalizedWeaponRuleId"),
            function_source("weaponRuleRerollsComplete", "applyWeaponRuleRerolls"),
            function_source("applyWeaponRuleRerolls", "weaponHasRule"),
            "const profile={rules:['Balanced','Ceaseless']};",
            "const original=[{value:1,kind:'miss'},{value:2,kind:'miss'},{value:4,kind:'hit'},{value:6,kind:'crit'}];",
            "(async()=>{const result=await applyWeaponRuleRerolls(original,profile,{attackerSide:'player',rerollPolicy:{attackDice:false}});",
            "if(JSON.stringify(result)!==JSON.stringify(original))process.exit(1);",
            "if(result.some(d=>d.rerolledBy||d.rerollRulesResolved))process.exit(2);",
            "if(!weaponRuleRerollsComplete(result,profile,{attackDice:false}))process.exit(3);",
            "if(weaponRuleRerollsComplete(result,profile,{attackDice:true}))process.exit(4);})();",
        )
    )
    run_node(script)


def test_policy_is_propagated_through_fresh_and_restored_shared_attack_paths():
    request = function_source("requestAttackDiceForProfile", "requestDefenseDice")
    shared = function_source("runAutomaticCombatRolls", "retainedDiceTotals")
    player = APP.split("function showPlayerCombatResolution", 1)[1].split(
        "async function previewPendingPlayerAttack", 1
    )[0]
    assert "rerollPolicy" in request
    assert "applyWeaponRuleRerolls(dice,profile" in request
    assert "weaponRuleRerollsComplete(rolledAttackDice,profile,rerollPolicy)" in shared
    assert "applyWeaponRuleRerolls(rolledAttackDice,profile" in shared
    assert "requestAttackDiceForProfile(profile" in shared
    assert "rerollPolicy:rerolls" in player
    assert "transaction.definitionAnswers.moreThanEight" in player


def test_permission_gate_precedes_every_reroll_mechanism_and_request():
    rerolls = function_source("applyWeaponRuleRerolls", "weaponHasRule")
    gate = rerolls.index("if(rerollPolicy?.attackDice===false)return updated")
    assert gate < rerolls.index("chooseHumanWeaponReroll")
    assert gate < rerolls.index("beneficialRerollChoice")
    assert gate < rerolls.index("requestDiceResults")
    assert gate < rerolls.index("rerolledBy:ruleId")
    assert "dark-of-the-tomb" not in rerolls
    assert "command" not in rerolls.lower()


def test_distance_answer_and_original_attack_pool_remain_checkpointed_for_resume():
    player = APP.split("function showPlayerCombatResolution", 1)[1].split(
        "async function previewPendingPlayerAttack", 1
    )[0]
    assert "transaction.definitionAnswers.moreThanEight===undefined" in player
    assert "moreThanEight:transaction.definitionAnswers.moreThanEight" in player
    assert "rolledAttackDice:committedAttackDice" in player
    assert "attackDice:diceDraft.attackDice" in player
    assert "weaponRuleRerollsComplete(rolledAttackDice,profile,rerollPolicy)" in APP


def test_existing_tabletop_question_and_release_note_are_preserved():
    assert "Target is more than 8 inches away" in APP
    assert "Required for Dark of the Tomb because the Guide cannot measure tabletop distance." in APP
    assert "### Dark of the Tomb Reroll Enforcement" in README
    assert "other Guide-managed attack rerolls now obey the event's shared reroll permission" in README
