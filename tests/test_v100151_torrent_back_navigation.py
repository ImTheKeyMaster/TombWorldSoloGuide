"""Regression for Experimental Torrent/Blast Back navigation after target checks."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_torrent_checked_targets_back_returns_to_weapon_selection():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
function slice(start,end){
  const a=app.indexOf(start),b=app.indexOf(end,a+start.length);
  assert(a>0&&b>a,'required production source markers');
  return app.slice(a,b);
}
const targetCheck=slice('  function showSecondaryTargetCheck(', '  function weaponRuleSequenceProgress(');
const wizardStart='  function showNpoAttackWizard(';
const wizardPart=slice(wizardStart,'    const profileControl=');
const wizard=new Function('ctx','with(ctx){'+wizardPart+'\n}\nreturn showNpoAttackWizard;}');
const block=slice('        const back=()=>{','        const resume=()=>resumeCombatAfterWeaponRuleCheck({');
let saved=0,backRouted=[],selectorShown=[],modalTitle='',modalMarkup='';
const profiles=[{name:'Focused',weaponId:'twin',profileId:'focused'},{name:'Sweeping',weaponId:'twin',profileId:'sweeping'}];
const target={id:'sergeant',type:'Sergeant',save:3,wounds:15,maxWounds:15};
const n={id:'crawler',type:'Canoptek Tomb Crawler'};
const inputs=[
 {value:'gunner',checked:false,onchange:null},
 {value:'blademaster',checked:false,onchange:null}
];
const controls={
 '#tabletopCheckConfirmed':{checked:false,onchange:null},
 '#confirmSecondaryTargets':{disabled:true,onclick:null},
 '#secondaryTargetsBack':{onclick:null}
};
const state={
 weaponRuleResolution:null,turningPoint:1,activationNumber:1,
 lastActivation:{action:'Shoot',combatDraft:{selecting:true,attackType:'shoot',targetId:target.id,profile:profiles[1]}}
};
const ctx={
 state,rollStarted:true,experimentalWeaponSelection:true,sequence:null,target,n,attackDice:[],onDone:()=>{},onCancel:()=>{},
 weaponRuleResumePending:false,
 save:()=>saved++,escapeHtml:x=>String(x),
 showModal:(title,html)=>{modalTitle=title;modalMarkup=html;},
 $:selector=>controls[selector],
 $$:selector=>selector==='[data-weapon-rule-target]'||selector==='[data-weapon-rule-target]:checked'?inputs.filter(x=>selector.endsWith(':checked')?x.checked:true):[],
 weaponRuleTargetOption:t=>'<label>'+t.label+'</label>',
 createWeaponRuleResolution:o=>({...o,orderedTargetIds:[o.primaryTargetId,...o.secondaryTargetIds],completedTargetIds:[]}),
 selectedNpoAttackTarget:()=>target,
 playerName:()=>target.type,
 npoAttackProfiles:()=>profiles,
 canonicalAttackProfile:x=>x,
 experimentalFeaturesEnabled:()=>true,
 document:{documentElement:{dataset:{ui:'tomb'}}},
 npoCombatGuidanceHtml:()=>'<p>Guide</p>',
 showExperimentalNpoWeaponSelection:(...args)=>selectorShown.push(args),
 isPvpMode:()=>false
};
const openWizard=wizard(ctx);
ctx.showNpoAttackWizard=(...args)=>{backRouted.push(args);openWizard(...args);};
const back=new Function('ctx','with(ctx){'+block+'\nreturn back;}')(ctx);
const secondary=new Function('ctx','with(ctx){'+targetCheck+'\nreturn showSecondaryTargetCheck;}')(ctx);
secondary({ruleId:'torrent',distance:1,attackerSide:'npo',attackerId:n.id,primaryTargetId:target.id,
 targets:[{id:'gunner',label:'Gunner',wounds:2,targetSide:'player'},{id:'blademaster',label:'Blademaster',wounds:7,targetSide:'player'}],
 weaponId:'twin',weaponName:'Twin gauss reapers',profileKey:'sweeping',profileName:'Sweeping',weaponRules:['torrent'],
 onContinue:()=>{},onBack:back});
assert.equal(modalTitle,'Torrent');
assert.match(modalMarkup,/secondaryTargetsBack/);
inputs[0].checked=true;inputs[1].checked=true;
controls['#tabletopCheckConfirmed'].checked=true;
controls['#tabletopCheckConfirmed'].onchange();
assert.equal(state.weaponRuleResolution.continueConfirmed,false);
assert.equal(state.weaponRuleResolution.orderedTargetIds.length,3,'two checked secondaries provisionally lock profile');
controls['#secondaryTargetsBack'].onclick();
assert.equal(state.weaponRuleResolution,null,'provisional target lock removed');
assert.equal(state.lastActivation.combatDraft.profile,profiles[1],'selected weapon preserved');
assert.equal(backRouted.length,1);
assert.deepEqual(backRouted[0].slice(4),[false,false,false,true],'force Experimental weapon selection');
assert.equal(selectorShown.length,1,'did not bounce back to Torrent');
assert.equal(selectorShown[0][3],1,'previous Sweeping profile selected');
assert.equal(ctx.rollStarted,false,'cancel pending roll state');
assert(saved>=2,'persist clearing the provisional rule state');

ctx.showNpoAttackWizard=(...args)=>{backRouted.push(args);};
function checkBack(rule,experimental,priorSequence=null){
  state.weaponRuleResolution=rule;
  ctx.experimentalWeaponSelection=experimental;
  ctx.sequence=priorSequence;
  back();
  return state.weaponRuleResolution;
}
const confirmed={primaryTargetId:target.id,continueConfirmed:true,orderedTargetIds:[target.id,'gunner'],completedTargetIds:[]};
assert.equal(checkBack(confirmed,true),confirmed,'confirmed multi-target state retained');
const completed={primaryTargetId:target.id,continueConfirmed:false,completedTargetIds:[target.id]};
assert.equal(checkBack(completed,true),completed,'completed results are preserved');
const otherTarget={primaryTargetId:'other',continueConfirmed:false};
assert.equal(checkBack(otherTarget,true),otherTarget,'unrelated attack state not discarded');
const stdPending={primaryTargetId:target.id,continueConfirmed:false};
assert.equal(checkBack(stdPending,false),stdPending,'Standard Mode never clears rule state');
assert.deepEqual(backRouted.at(-1).slice(4),[false,false,false,false],'Standard Mode does not force selector');
const seekLight={primaryTargetId:target.id,resolutionKey:'rule:seek',seekLightAnswer:'yes',continueConfirmed:false};
assert.equal(checkBack(seekLight,true),null,'unconfirmed Seek Light answer also cleared on Back');
state.lastActivation.combatDraft={selecting:true,attackType:'shoot',targetId:target.id,profile:profiles[0]};
ctx.experimentalWeaponSelection=true;ctx.sequence=null;
ctx.npoAttackProfiles=()=>[profiles[0]];
state.weaponRuleResolution=null;
ctx.showNpoAttackWizard=(...args)=>{backRouted.push(args);openWizard(...args);};
back();
assert.equal(selectorShown.at(-1)[3],0,'single profile Back returns to selection instead of repeating Torrent');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_change_is_opt_in_and_does_not_alter_combat_engine():
    wizard = APP.split("  function showNpoAttackWizard(", 1)[1].split("  function spinnerField(", 1)[0]
    assert "forceWeaponSelection=false" in wizard
    assert "experimentalFeaturesEnabled()&&document.documentElement.dataset.ui==='tomb'&&attackType==='shoot'" in wizard
    assert "forceWeaponSelection||availableProfiles.length>1" in wizard
    assert "pendingRule?.primaryTargetId===target.id&&!pendingRule.continueConfirmed" in wizard
    assert "!(pendingRule.completedTargetIds||[]).length" in wizard
    assert "!(sequence?.completedTargetIds||[]).length" in wizard
    assert "showNpoAttackWizard(n,attackDice,onDone,onCancel,false,false,false,experimentalWeaponSelection)" in wizard
    assert "showSecondaryTargetCheck({ruleId," in wizard
    assert "if(ruleId==='blast')" not in wizard
    assert "else if(rollingCombat)startAutomaticCombat(saved)" in wizard
    assert "runAutomaticCombatRolls({container:screen.dice" in wizard
    assert "createWeaponRuleResolution({" in APP


def test_version_and_saved_game_compatibility():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
