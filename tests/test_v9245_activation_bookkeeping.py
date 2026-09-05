from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_version_and_persistent_save_key_are_consistent():
    assert CURRENT_APP_VERSION == ".".join(("9", "2", str(40 + 5)))
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / "service-worker.js").read_text()


def test_generic_special_actions_and_other_damage_are_absent_from_action_catalog():
    groups = section("const HUMAN_ACTION_GROUPS", "function activePlayerActivation")
    catalog = section("function playerHumanActionCatalog", "function playerHumanActionState")
    assert "Special Actions" not in groups
    assert "group:'special'" not in catalog
    assert "name:'Other Damage'" not in catalog
    assert "id:'damage'" not in catalog


def test_only_nonempty_groups_render_and_footer_follows_groups_without_placeholder():
    shell = section("function renderHumanActivationShell", "function showApplyOtherDamage")
    assert "if(!items.length)return ''" in shell
    assert ".filter(Boolean).join('')" in shell
    assert "No special actions" not in shell
    assert shell.index('<div class="activation-groups">${groups}</div>') < shell.index("End Activation")


def test_damage_bookkeeping_is_outside_action_list_and_has_no_ap_or_history_transaction():
    shell = section("function renderHumanActivationShell", "function showApplyOtherDamage")
    damage = section("function showApplyOtherDamage", "function renderHumanPlayerActionPicker")
    assert 'class="activation-bookkeeping"' in shell
    assert 'id="applyOtherDamage"' in shell
    bookkeeping_button = shell.split('id="applyOtherDamage"', 1)[1].split("</button>", 1)[0]
    assert "data-human-action" not in bookkeeping_button
    assert "AP" not in bookkeeping_button
    assert "adjustPlayerWounds(activation.operativeId,-amount)" in damage
    for mutation in ("remainingAp", "completedActionIds", "resolvedActions", "pendingAction", "actionSequence"):
        assert mutation not in damage
    assert "valueAsNumber" in damage
    assert "!Number.isInteger(amount)||amount<1||amount>wounds" in damage
    assert "Enter a whole number from 1 to ${wounds}." in damage


def test_bookkeeping_uses_existing_wound_and_incapacitation_state():
    adjustment = "function adjustPlayerWounds" + section("function adjustPlayerWounds", "function adjustWounds")
    assert "state.playerWounds[id]=wounds" in adjustment
    assert "if(wounds===0)" in adjustment
    assert "casualties.add(id)" in adjustment
    assert "state.playerActivatedIds.push(id)" in adjustment
    assert "save();render();" in adjustment


def test_operative_group_is_available_but_no_placeholder_action_is_invented():
    groups = section("const HUMAN_ACTION_GROUPS", "function activePlayerActivation")
    catalog = section("function playerHumanActionCatalog", "function playerHumanActionState")
    assert "label:'Operative Actions'" in groups
    assert "group:'operative'" not in catalog
    assert "operative.actions" not in catalog


def test_other_damage_does_not_change_action_legality_or_ap_behaviorally():
    source = "function playerHumanActionState" + section("function playerHumanActionState", "function renderHumanActivationShell")
    script = f"""
const assert=require('assert').strict;
{source}
const activation={{remainingAp:3,completedActionIds:[],resolvedActions:[],operativeId:'p1'}};
const playerAttackWeapons=()=>[{{}}],hasValidPlayerCombatTargets=()=>true;
const state={{missionId:null}},mission=()=>null,closedMissionFeatures=()=>[],scoutRoomState=()=>({{reason:'Available'}});
for(const id of ['charge','shoot','melee']){{
  const result=playerHumanActionState({{id,cost:1}},activation);
  assert.equal(result.disabled,false);
}}
assert.equal(activation.remainingAp,3);
assert.deepEqual(activation.completedActionIds,[]);
assert.deepEqual(activation.resolvedActions,[]);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_standard_and_mission_action_definitions_are_unchanged():
    catalog = section("function playerHumanActionCatalog", "function playerHumanActionState")
    for action in (
        "{id:'move',name:'Reposition',group:'movement',cost:1}",
        "{id:'dash',name:'Dash',group:'movement',cost:1}",
        "{id:'charge',name:'Charge',group:'movement',cost:1}",
        "{id:'fallBack',name:'Fall Back',group:'movement',cost:2}",
        "{id:'shoot',name:'Shoot',group:'combat',cost:1}",
        "{id:'melee',name:'Fight',group:'combat',cost:1}",
        "{id:'hatch',name:'Operate Hatch',group:'mission',cost:1}",
    ):
        assert action in catalog
    assert "cost:breachApCost(operative)" in catalog
    assert "missionAction.id,name:missionAction.displayLabel,group:'mission',cost:missionAction.apCost" in catalog
