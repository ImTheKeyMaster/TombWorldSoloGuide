"""Guard against shooting or melee without an explicitly selected weapon.

Regression for a late activation action following earlier Fights, where the empty
weapon option must never be coerced to the first ranged weapon.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
WIZARD = APP.split("function showPendingPlayerAttackWizard(", 1)[1].split("function showPlayerCombatResolution(", 1)[0]


def test_blank_weapon_is_rejected_at_selection_and_action_boundary():
    assert 'id="openCombatResolution" disabled>Continue' in WIZARD
    assert WIZARD.count("selectedPlayerWeaponIndex(weaponSelect.value,weapons)") == 2
    assert "const weapon=weaponIndex<0?null:weapons[weaponIndex];" in WIZARD
    assert "if(!weapon){" in WIZARD
    action = WIZARD.split("$('#openCombatResolution').onclick=()=>{", 1)[1]
    assert action.index("if(!weapon){") < action.index("playerWeaponProfile(weapon,")
    assert action.index("if(!weapon){") < action.index("pending.cost=required")
    assert "Select a weapon before continuing." in action
    assert "projectedNpoWounds(n.id,stage)>0" in action
    assert "if(!target){" in action
    assert "Select an available target before continuing." in action


def test_selector_and_continue_guard_execute_for_blank_multi_and_single_weapons():
    script = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const app = fs.readFileSync('app.js', 'utf8');
const helperStart = app.indexOf('  function selectedPlayerWeaponIndex(');
const wizardStart = app.indexOf('  function showPendingPlayerAttackWizard(', helperStart);
assert(helperStart >= 0 && wizardStart > helperStart);
const select = new Function(app.slice(helperStart, wizardStart) + 'return selectedPlayerWeaponIndex;')();
const weapons = [{name:'Bolt pistol'}, {name:'Heavy bolter'}];
for (const value of ['', ' ', '01', '-1', '1.0', 'Infinity', 'undefined', '2', '9007199254740992']) {
    assert.equal(select(value, weapons), -1, 'invalid weapon index: '+value);
}
assert.equal(select('0', weapons), 0);
assert.equal(select('1', weapons), 1);
assert.equal(select(undefined, weapons), -1);
assert.equal(select('', [weapons[0]]), -1);
assert.equal(select('0', [weapons[0]]), 0);

const handlerMarker = "    $('#openCombatResolution').onclick=()=>{";
const actionStart = app.indexOf(handlerMarker, wizardStart);
const actionEnd = app.indexOf("      const pending=activePlayerActivation()?.pendingAction;", actionStart);
assert(actionStart > wizardStart && actionEnd > actionStart);
const guardCode = app.slice(actionStart + handlerMarker.length, actionEnd);
const guard = new Function('ctx', 'with(ctx){' + guardCode + "return 'accepted';}");
function run(value, targetId='scarab') {
    const record={toasts:[],profileCalls:0,choiceRenders:0,focusCount:0};
    const ctx={
        activeNpos:()=>[{id:'scarab'}],
        targetSelect:{value:targetId},
        projectedNpoWounds:()=>10,
        selectedPlayerWeaponIndex:select,
        weaponSelect:{value,tagName:'SELECT',focus:()=>record.focusCount++},
        weapons,stage:{playerOperativeId:'sharpshooter'},attackType:'shoot',
        renderChoices:()=>record.choiceRenders++,
        showToast:msg=>record.toasts.push(msg),
        playerWeaponProfile:()=>{record.profileCalls++;return {weaponId:'good'};}
    };
    record.result=guard(ctx);
    return record;
}
for(const invalid of ['', 'bad', '2']) {
    const res=run(invalid);
    assert.equal(res.result,undefined);
    assert.equal(res.profileCalls,0);
    assert.deepEqual(res.toasts,['Select a weapon before continuing.']);
}
let ok=run('0');
assert.equal(ok.result,'accepted');
assert.equal(ok.profileCalls,1);
assert.equal(ok.toasts.length,0);
ok=run('1');
assert.equal(ok.result,'accepted');
assert.equal(ok.profileCalls,1);
let missingTarget=run('0','missing');
assert.equal(missingTarget.result,undefined);
assert.equal(missingTarget.profileCalls,0);
assert.deepEqual(missingTarget.toasts,['Select an available target before continuing.']);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_js_syntax_is_valid():
    result = subprocess.run(["node", "--check", "app.js"], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout
