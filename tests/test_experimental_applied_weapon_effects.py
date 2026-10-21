"""Regression checks for Experimental-only applied shooting effects feedback."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
SW=(ROOT/'service-worker.js').read_text(encoding='utf-8')


def node_check(script):
    result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0, result.stderr or result.stdout


def test_applied_effects_are_derived_from_actual_dice_and_not_rule_list():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const snippet=app.slice(app.indexOf('  function experimentalAppliedWeaponEffectsEnabled('),app.indexOf('  function renderCombatResolution('));
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>true,
 escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'),
 weaponRuleValue:(p,id)=>Number((p.rules||[]).find(x=>x.startsWith('Piercing Crits '))?.split(' ')[2]||0),
 effectiveDefenseDiceCount:(p,d)=>Math.max(0,3-Math.max(Number(p.ap||0),d.some(x=>x.retained&&x.kind==='crit')?Number((p.rules||[]).find(x=>x.startsWith('Piercing Crits '))?.split(' ')[2]||0):0))
};
const api=new Function('ctx','with(ctx){'+snippet+'return {appliedWeaponEffectMessages,appliedWeaponEffectsHtml,experimentalAppliedWeaponEffectsEnabled};}')(ctx);
const base={attackType:'shoot',recordedOutcome:false,profile:{ap:1,rules:['Piercing 1','Severe']},saveDice:[{},{}],attackDice:[{value:4,kind:'crit',retained:true,severeConverted:true,originalKind:'hit'}],eventMessages:[]};
assert.deepEqual(api.appliedWeaponEffectMessages(base),[
 'Severe: 1 normal hit became a critical hit','Piercing 1: defense dice 3 → 2'
]);
assert.match(api.appliedWeaponEffectsHtml(base),/APPLIED EFFECTS/);
assert.match(api.appliedWeaponEffectsHtml(base),/<li>Severe/);
assert.match(api.appliedWeaponEffectsHtml(base),/<li>Piercing 1/);

const critical={...base,profile:{ap:1,rules:['Piercing 1','Piercing Crits 2','Severe']},saveDice:[{}],
 attackDice:[{value:6,kind:'crit',retained:true}]};
assert.deepEqual(api.appliedWeaponEffectMessages(critical),['Piercing Crits 2: defense dice 3 → 1']);
const nonCritical={...critical,attackDice:[{value:4,kind:'hit',retained:true}],saveDice:[{},{}]};
assert.deepEqual(api.appliedWeaponEffectMessages(nonCritical),['Piercing 1: defense dice 3 → 2']);

const noTrigger={...base,profile:{ap:0,rules:['Severe','Rending','Balanced']},attackDice:[{value:6,kind:'crit',retained:true}],saveDice:[{value:3,kind:'hit',retained:true}]};
assert.deepEqual(api.appliedWeaponEffectMessages(noTrigger),[]);
assert.equal(api.appliedWeaponEffectsHtml(noTrigger),'');
const missed={...noTrigger,attackDice:[{value:1,kind:'miss',retained:false}]};
assert.deepEqual(api.appliedWeaponEffectMessages(missed),[]);

const special={...base,profile:{ap:0,critThreshold:5,rules:['Accurate 1','Balanced','Ceaseless','Rending','Lethal 5+']},
 attackDice:[
 {value:4,kind:'hit',retained:true,automatic:'Accurate 1'},
 {value:4,kind:'crit',retained:true,rendingConverted:true,originalKind:'hit',rerolledBy:'balanced'},
 {value:5,kind:'crit',retained:true,rerolledBy:'ceaseless'}
 ],saveDice:[{value:2,kind:'miss',retained:false}],devastatingDamage:2,
 eventMessages:['Stun applied: Defender has -1 APL.']};
const messages=api.appliedWeaponEffectMessages(special);
for(const label of ['Rending: 1','Accurate: 1','Balanced: 1','Ceaseless: 1','Lethal 5+: 1','Devastating: 2','Stun: Defender'])
 assert.ok(messages.some(m=>m.startsWith(label)),label+' missing');
assert.equal(messages.filter(x=>x.startsWith('Piercing')).length,0);

const killed={...base,devastatingIncapacitated:true,devastatingDamage:4,saveDice:[]};
assert.deepEqual(api.appliedWeaponEffectMessages(killed),[
 'Severe: 1 normal hit became a critical hit','Devastating: 4 immediate damage from critical hits'
]);
assert.deepEqual(api.appliedWeaponEffectMessages({...base,attackType:'fight'}),[]);
assert.deepEqual(api.appliedWeaponEffectMessages({...base,recordedOutcome:true}),[]);
assert.deepEqual(api.appliedWeaponEffectMessages({...base,attackDice:[]}),[]);
const unsafe={...noTrigger,eventMessages:['Stun applied: <script>alert(1)</script>']};
assert.doesNotMatch(api.appliedWeaponEffectsHtml(unsafe),/<script>/);
assert.match(api.appliedWeaponEffectsHtml(unsafe),/&lt;script&gt;/);
"""
    node_check(script)


def test_experimental_presentation_only_and_no_duplicate_stun_or_severe():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const snippet=app.slice(app.indexOf('  function experimentalAppliedWeaponEffectsEnabled('),app.indexOf('  function combatAttackLabel('));
let preview=false,ui='tomb';
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>preview,
 weaponRuleValue:()=>0,effectiveDefenseDiceCount:(p,d)=>Math.max(0,3-Number(p.ap||0)),
 escapeHtml:s=>String(s),
 renderEliminationSummary:()=>'',combatAbilityReminder:()=>'',
 combatDiceStageHtml:(role,title,row,detail='')=>'<article class="'+role+'">'+row+detail+'</article>',
 severeAppliedHtml:()=>'<span>OLD SEVERE MESSAGE</span>',
 dieHtml:d=>'<die>'+d.value+'</die>',rollingDieHtml:()=>'<rolling-die/>',
};
const fn=new Function('ctx','with(ctx){'+snippet+'return renderCombatResolution;}')(ctx);
const combat={attackType:'shoot',profile:{ap:1,rules:['Piercing 1','Severe']},
 recordedOutcome:false,attackDice:[{value:4,kind:'crit',retained:true,severeConverted:true,originalKind:'hit'}],
 saveDice:[{value:3,kind:'hit',retained:true},{value:2,kind:'miss',retained:false}],
 severeApplied:true,eventMessages:['Stun applied: Test -1 APL','Other event retained'],
 normalRemaining:0,critRemaining:1,damage:4,before:5,after:1,defenderName:'Test',defenderSide:'npo'};
const standard=fn(combat,{showParticipants:false,animate:false});
assert.doesNotMatch(standard,/APPLIED EFFECTS/);
assert.match(standard,/OLD SEVERE MESSAGE/);
assert.match(standard,/Stun applied: Test -1 APL/);
preview=true;
const experimental=fn(combat,{showParticipants:false,animate:false});
assert.match(experimental,/APPLIED EFFECTS/);
assert.match(experimental,/Severe: 1 normal hit became a critical hit/);
assert.match(experimental,/Piercing 1: defense dice 3 → 2/);
assert.match(experimental,/Stun: Test -1 APL/);
assert.doesNotMatch(experimental,/OLD SEVERE MESSAGE|Stun applied: Test -1 APL/);
assert.match(experimental,/Other event retained/);
const noEffects=fn({...combat,profile:{ap:0},attackDice:[{value:1,kind:'miss',retained:false}],eventMessages:[]},{showParticipants:false,animate:false});
assert.doesNotMatch(noEffects,/APPLIED EFFECTS/);
const classic=ctx.document.documentElement.dataset;
classic.ui='classic';
assert.doesNotMatch(fn(combat,{showParticipants:false,animate:false}),/APPLIED EFFECTS/);
assert.match(fn(combat,{showParticipants:false,animate:false}),/OLD SEVERE MESSAGE/);
"""
    node_check(script)


def test_version_and_css_and_legacy_behavior_retained():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert '.applied-weapon-effects{' in CSS
    assert '.applied-weapon-effects li::before' in CSS
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "function experimentalFeaturesEnabled(){" in APP
    assert "function tombWeaponRulesAtSelection(){" in APP
