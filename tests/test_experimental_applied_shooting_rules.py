"""Experimental-only audit of weapon rule effects in shooting result screens."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'styles.css').read_text(encoding='utf-8')
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
SW = (ROOT / 'service-worker.js').read_text(encoding='utf-8')


def node_check(script):
    run = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr or run.stdout


def test_applied_rule_feedback_uses_real_dice_and_mechanics():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const take=(first,second)=>src.slice(src.indexOf('  function '+first+'('),src.indexOf('  function '+second+'(',src.indexOf('  function '+first+'(')));
const rules=take('weaponHasRule','normalizedWeaponRuleId')
 +take('normalizedWeaponRuleId','normalizedWeaponRuleWarningKey')
 +take('weaponRuleValue','effectiveDefenseDiceCount')
 +take('effectiveDefenseDiceCount','automaticWeaponRuleMessages');
const feedback=take('appliedShootingRuleMessages','renderCombatResolution');
const context={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>true,
 escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
};
const api=new Function('ctx','with(ctx){'+rules+feedback+'return {appliedShootingRuleMessages,experimentalAppliedShootingRulesHtml};}')(context);
const die=(value,kind='hit',props={})=>({value,kind,retained:kind!=='miss',...props});
const render=(profile,dice,saves=3,more={})=>{
 const combat={attackType:'shoot',recordedOutcome:false,profile,
 attackDice:dice,saveDice:Array.from({length:saves},()=>die(2,'miss')), ...more};
 return {messages:api.appliedShootingRuleMessages(combat),html:api.experimentalAppliedShootingRulesHtml(combat)};
};
const piercing=render({ap:1,rules:['Piercing 1']},[die(4)],2);
assert.deepEqual(piercing.messages,['Piercing 1: defense dice 3 → 2.']);
assert.match(piercing.html,/RULES APPLIED/);
const severe=render({ap:0,rules:['Severe']},[die(4,'crit',{severeConverted:true})]);
assert.equal(severe.messages.length,1);
assert.match(severe.messages[0],/Severe: 1 normal success became a critical success/);
assert.deepEqual(render({ap:0,rules:['Severe']},[die(6,'crit')]).messages,[],
  'Merely having Severe does not mean it changed the roll');
const critPiercing=render({ap:1,rules:['Piercing 1','Piercing Crits 2']},[die(6,'crit')],1);
assert.deepEqual(critPiercing.messages,['Piercing Crits 2: defense dice 3 → 1.']);
assert.deepEqual(render({ap:1,rules:['Piercing 1','Piercing Crits 2']},[die(4)],2).messages,
 ['Piercing 1: defense dice 3 → 2.']);
const devastating=render({ap:1,rules:['Piercing 1','Devastating 3']},[die(6,'crit')],0,
 {devastatingDamage:3,devastatingIncapacitated:true});
assert.deepEqual(devastating.messages,['Devastating 3: 3 immediate damage from critical successes.']);
assert.equal(render({ap:0,rules:[]},[die(4)]).html,'','No effect means no panel');
assert.match(render({critThreshold:5,rules:['Lethal 5+']},[die(5,'crit')]).html,/Lethal 5\+/);
assert.match(render({rules:['Rending']},[die(4,'crit',{rendingConverted:true})]).html,/Rending/);
assert.match(render({rules:['Accurate 1']},[die(3,'hit',{automatic:'Accurate 1'})]).html,/Accurate/);
assert.match(render({rules:['Balanced']},[die(5,'hit',{rerolledBy:'balanced'})]).html,/Balanced/);
assert.match(render({rules:['Ceaseless']},[die(5,'hit',{rerolledBy:'ceaseless'})]).html,/Ceaseless/);
assert.equal(api.experimentalAppliedShootingRulesHtml({
 ...{attackType:'shoot',recordedOutcome:true,profile:{ap:1,rules:['Piercing 1']}},
 attackDice:[die(4)],saveDice:[die(2,'miss'),die(3,'hit')]
}),'','Physical-tabletop resolution must not infer effects');
assert.equal(api.experimentalAppliedShootingRulesHtml({
 attackType:'fight',recordedOutcome:false,profile:{ap:1,rules:['Piercing 1']},
 attackDice:[die(4)],saveDice:[die(2,'miss'),die(3,'hit')]
}),'','Only shooting screens are in scope');
context.experimentalFeaturesEnabled=()=>false;
assert.equal(api.experimentalAppliedShootingRulesHtml({
 attackType:'shoot',recordedOutcome:false,profile:{ap:1,rules:['Piercing 1']},
 attackDice:[die(4)],saveDice:[die(2,'miss'),die(3,'hit')]
}),'','Standard mode remains unchanged');
context.experimentalFeaturesEnabled=()=>true;
context.document.documentElement.dataset.ui='classic';
assert.equal(api.experimentalAppliedShootingRulesHtml({
 attackType:'shoot',recordedOutcome:false,profile:{ap:1,rules:['Piercing 1']},
 attackDice:[die(4)],saveDice:[die(2,'miss'),die(3,'hit')]
}),'','Classic UI remains unchanged');
"""
    node_check(script)


def test_results_keep_damage_eliminations_and_standard_severe_feedback():
    screen = APP.split('  function renderCombatResolution(', 1)[1].split('  function combatAttackLabel(', 1)[0]
    assert '${experimentalAppliedShootingRulesHtml(combat)}' in screen
    assert "experimentalAppliedShootingRulesHtml(combat)?'':severeAppliedHtml(combat.attackDice,combat.severeApplied)" in screen
    assert '${elimination}' in screen
    assert '${combat.damage}' in screen
    assert '${combat.before} → ${combat.after}' in screen
    assert "function experimentalFeaturesEnabled(){" in APP
    assert 'html[data-ui="tomb"][data-experimental="on"] .combat-applied-rules' in CSS


def test_version_and_persistence_unchanged():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
