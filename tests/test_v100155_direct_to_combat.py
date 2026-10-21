"""Regression coverage for v10.0.155 direct-to-combat weapon selection."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
SW=(ROOT/'service-worker.js').read_text(encoding='utf-8')


def node_check(script):
    result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0, result.stderr or result.stdout


def test_selected_weapon_skips_redundant_confirmation():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const wizard=app.slice(app.indexOf('  function showNpoAttackWizard('),app.indexOf('  function spinnerField('));
const tail=wizard.slice(wizard.indexOf('    if(sameCombat)void displayCombat('),wizard.indexOf('    return {...screen,startAutomaticCombat};'));
function run(opts={}){
 const called=[],screen={continueButton:{disabled:true,onclick:null,textContent:''}};
 const ctx={
  $:()=>null,screen,sameCombat:Boolean(opts.same),rollingCombat:Boolean(opts.rolling),
  resumeGuided:Boolean(opts.resumed),experimentalWeaponSelection:!opts.classic,
  selectingCombat:Boolean(opts.selected),availableProfiles:opts.single?[{}]:[{},{}],
  locked:opts.locked?{}:null,willBeDone:opts.will?'question':'',
  isPvpMode:()=>Boolean(opts.pvp),displayCombat:()=>called.push('display'),
  startAutomaticCombat:()=>called.push('start'),saved:{},animateCombat:false
 };
 new Function('ctx','with(ctx){'+tail+'}')(ctx);
 return {called,screen};
}
assert.deepEqual(run({selected:true}).called,['start']);
assert.deepEqual(run({selected:true,pvp:true}).called,['start']);
assert.deepEqual(run({single:true}).called,['start']);
assert.deepEqual(run({single:true,will:true}).called,['start']);
assert.deepEqual(run({locked:true}).called,['start']);
assert.deepEqual(run({rolling:true,selected:true}).called,['start']);
assert.deepEqual(run({same:true,selected:true}).called,['display']);
assert.deepEqual(run({selected:true,resumed:true}).called,[]);
const classic=run({classic:true,selected:true});
assert.deepEqual(classic.called,[]);
assert.equal(typeof classic.screen.continueButton.onclick,'function');
"""
    node_check(script)


def test_event_conditions_use_compact_question_and_keep_answers():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const helper=app.slice(app.indexOf('  function showNpoAttackConditionCheck('),app.indexOf('  function showNpoAttackWizard('));
const controls={
 '#backNpoAttackConditions':{},'#confirmNpoAttackConditions':{},
 '#sameRoomAsC1':{checked:true},'#sameRoomAsRoyalWarden':{checked:false}
};
let title='',markup='',answers=null,backs=0;
const show=new Function('ctx','with(ctx){'+helper+'return showNpoAttackConditionCheck;}')({
 showModal:(t,m)=>{title=t;markup=m;},$:id=>controls[id]
});
show({willBeDone:'<input id="sameRoomAsC1">',onBack:()=>backs++,onContinue:a=>answers=a});
assert.equal(title,'Attack conditions');
assert.doesNotMatch(markup,/Resolve Combat|Defender|Attack dice/);
controls['#confirmNpoAttackConditions'].onclick();
assert.deepEqual(answers,{sameRoomAsC1:true});
controls['#backNpoAttackConditions'].onclick();
assert.equal(backs,1);
show({enforcerQuestion:'<input id="sameRoomAsRoyalWarden">',onBack:()=>{},onContinue:a=>answers=a});
controls['#confirmNpoAttackConditions'].onclick();
assert.deepEqual(answers,{sameRoomAsRoyalWarden:false});
"""
    node_check(script)


def test_blast_and_torrent_rule_steps_are_not_skipped():
    wizard=APP.split('  function showNpoAttackWizard(',1)[1].split('  function spinnerField(',1)[0]
    assert "else if(experimentalWeaponSelection&&!resumeGuided&&(selectingCombat||availableProfiles.length===1))startAutomaticCombat();" in wizard
    assert wizard.index("else if(experimentalWeaponSelection&&!resumeGuided&&")<wizard.index("else if(availableProfiles.length===1&&willBeDone)")
    assert "showSecondaryTargetCheck({ruleId,distance:" in wizard
    assert "showSeekLightCheck({target,resolutionKey" in wizard
    assert "resumeCombatAfterWeaponRuleCheck({" in wizard
    assert "if(!restoredRoll&&!guidedConfirmed&&!state.weaponRuleResolution?.continueConfirmed)" in wizard
    assert "Object.assign(conditions.definitionAnswers,answers);" in wizard
    assert "showNpoAttackWizard(n,attackDice,onDone,onCancel,false,false,true);" in wizard
    assert "if(locked)cancel();else showNpoAttackWizard(n,attackDice,onDone,onCancel,false,false,false,true);" in wizard
    assert "runAutomaticCombatRolls({container:screen.dice" in wizard
    assert "else if(rollingCombat)startAutomaticCombat(saved)" in wizard
    assert "else if(locked&&!resumeGuided)startAutomaticCombat();" in wizard
    assert "experimentalWeaponSelection?'':" in wizard


def test_version_and_standard_experimental_access():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in HTML
    assert "function experimentalFeaturesEnabled(){" in APP
