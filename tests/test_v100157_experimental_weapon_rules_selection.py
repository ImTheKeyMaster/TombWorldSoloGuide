"""Regression tests for Experimental weapon rules on selection (V10.0.157)."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def node_check(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_weapon_selection_dynamic_rules_and_mode_isolation():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const flag=src.slice(src.indexOf('  function previewWeaponRulesAtSelection('),src.indexOf('  function normalizedGuidanceMatchText('));
const chooser=src.slice(src.indexOf('  function showExperimentalNpoWeaponSelection('),src.indexOf('  function showNpoAttackConditionCheck('));

function simulate(preview,profiles){
 const select={value:profiles.length===1?'0':'',addEventListener(event,fn){this[event]=fn;}};
 const controls={'#experimentalNpoWeaponProfile':select,
 '#experimentalNpoWeaponGuidance':{innerHTML:''},'#experimentalNpoWeaponRules':{innerHTML:''},
 '#confirmExperimentalNpoWeapon':{disabled:true},'#cancelExperimentalNpoWeapon':{}};
 let markup='',chosen=null;
 const ctx={document:{documentElement:{dataset:{ui:'tomb',experimental:preview?'on':'off'}}},
 experimentalFeaturesEnabled:()=>preview,canonicalAttackProfile:x=>x,escapeHtml:x=>x,
 npoCombatGuidanceHtml:(n,{profile})=>'Guidance '+profile.id,
 weaponRulesHtml:profile=>profile?.rules?.length?'<section>Rules '+profile.id+'</section>':'',
 showModal:(title,html)=>{assert.equal(title,'Select Weapon');markup=html;},
 $:selector=>selector==='#experimentalNpoWeaponRules'&&!preview?null:controls[selector]};
 const fn=new Function('ctx','with(ctx){'+flag+chooser+'return showExperimentalNpoWeaponSelection;}')(ctx);
 fn({},profiles,'shoot',-1,i=>chosen=i,()=>{});
 return {markup,controls,select,get chosen(){return chosen;}};
}
const profiles=[{id:'focused',rules:['Piercing 1']},{id:'sweeping',rules:['Torrent 1']},{id:'none',rules:[]}];
let test=simulate(true,profiles);
assert.match(test.markup,/experimentalNpoWeaponGuidance.*experimentalNpoWeaponRules/s);
assert.equal(test.controls['#confirmExperimentalNpoWeapon'].disabled,true);
test.select.value='0';test.select.change();
assert.equal(test.controls['#experimentalNpoWeaponGuidance'].innerHTML,'Guidance focused');
assert.equal(test.controls['#experimentalNpoWeaponRules'].innerHTML,'<section>Rules focused</section>');
assert.equal(test.controls['#confirmExperimentalNpoWeapon'].disabled,false);
test.select.value='1';test.select.change();
assert.equal(test.controls['#experimentalNpoWeaponGuidance'].innerHTML,'Guidance sweeping');
assert.equal(test.controls['#experimentalNpoWeaponRules'].innerHTML,'<section>Rules sweeping</section>');
test.select.value='2';test.select.change();
assert.equal(test.controls['#experimentalNpoWeaponRules'].innerHTML,'');
test.controls['#confirmExperimentalNpoWeapon'].onclick();
assert.equal(test.chosen,2);
test=simulate(true,[{id:'single',rules:['Severe']}]);
assert.equal(test.controls['#confirmExperimentalNpoWeapon'].disabled,false);
assert.equal(test.controls['#experimentalNpoWeaponRules'].innerHTML,'<section>Rules single</section>');
test=simulate(false,profiles);
assert.doesNotMatch(test.markup,/experimentalNpoWeaponRules/);
test.select.value='0';test.select.change();
assert.equal(test.controls['#experimentalNpoWeaponGuidance'].innerHTML,'Guidance focused');
"""
    node_check(script)


def test_single_profile_necron_and_player_auto_skip_behaviors():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const wizard=src.slice(src.indexOf('  function showNpoAttackWizard('),src.indexOf('  function spinnerField('));
const choose=wizard.slice(wizard.indexOf('    const experimentalWeaponSelection='),wizard.indexOf('    const profileControl='));
function necron({preview=false,single=false,rule=false,guidance=false}={}){
 const calls=[],availableProfiles=single?[{rules:rule?['Piercing 1']:[]}]:[{rules:['Piercing 1']},{rules:['Torrent 1']}];
 const ctx={document:{documentElement:{dataset:{ui:'tomb'}}},attackType:'shoot',n:{},
 availableProfiles,initialProfile:single?availableProfiles[0]:null,
 weaponConfirmed:false,resumeGuided:false,locked:null,rollingCombat:false,sameCombat:false,
 forceWeaponSelection:false,selectedProfileIndex:single?0:-1,
 previewWeaponRulesAtSelection:()=>preview,weaponRulesHtml:p=>p?.rules?.length?'rules':'',
 npoCombatGuidanceHtml:()=>guidance?'guidance':'',
 showExperimentalNpoWeaponSelection:()=>calls.push('select')};
 new Function('ctx','with(ctx){'+choose+'}')(ctx);
 return calls.length;
}
assert.equal(necron({preview:true,single:true,rule:true}),1);
assert.equal(necron({preview:false,single:true,rule:true}),0);
assert.equal(necron({preview:true,single:true,rule:false}),0);
assert.equal(necron({preview:false,single:false,rule:true}),1);
assert.equal(necron({preview:true,single:false,rule:true}),1);
assert.equal(necron({preview:false,single:true,guidance:true}),1);

const player=src.slice(src.indexOf('  function showPendingPlayerAttackWizard('),src.indexOf('  function showPlayerCombatResolution('));
const fast=player.slice(player.indexOf('    const singleProfile=weapons.length===1'),player.lastIndexOf('\n  }'));
for(const preview of [false,true])for(const hasRules of [false,true]){
 const calls=[];
 const ctx={weapons:[{}],stage:{playerOperativeId:'p'},attackType:'shoot',
 singleTarget:{id:'t',type:'warrior'},npoDefinition:()=>({id:'warrior'}),activeNpos:()=>[],
 playerWeaponProfile:()=>({rules:hasRules?['Piercing 1']:[]}),weaponHasRule:()=>false,
 previewWeaponRulesAtSelection:()=>preview,weaponRulesHtml:profile=>profile?.rules?.length?'rules':'',
 isPvpMode:()=>false,darkDistance:false,showPlayerCombatResolution:()=>calls.push('auto'),
 onResolved:()=>{},onCancel:()=>{}};
 new Function('ctx','with(ctx){'+fast+'}')(ctx);
 assert.equal(calls.length,preview&&hasRules?0:1);
}
assert.match(player,/weaponRulesHtml\(profile,\{semanticHeading:true\}\)/);
"""
    node_check(script)


def test_combat_rules_hidden_only_in_preview():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const npo=src.slice(src.indexOf('  function showNpoAttackWizard('),src.indexOf('  function spinnerField('));
const presentation=npo.slice(npo.indexOf('    const guidance=npoCombatGuidanceHtml'),npo.indexOf('    const cancel=()=>'));
function renderNecron(preview){
 let opts=null;
 const ctx={n:{id:'n'},target:{id:'t',wounds:5,maxWounds:10,save:3},targetSide:'player',
 targetName:'Target',attackType:'shoot',initialProfile:{name:'Gun'},experimentalWeaponSelection:true,
 profileControl:'',willBeDone:'',enforcerQuestion:'',sequence:null,
 previewWeaponRulesAtSelection:()=>preview,
 npoCombatGuidanceHtml:()=>'<div>Guidance</div>',npoName:()=>'NPO',
 fightParticipantPortrait:()=>'',combatAttackLabel:()=>'4 dice',weaponRulesHtml:()=>'<section>Rules</section>',
 multiTargetAttackProgress:()=>'',weaponRuleSequenceProgress:()=>'',playerDefinition:()=>({wounds:5}),
 showSharedCombatResolutionScreen:args=>{opts=args;return {};}};
 new Function('ctx','with(ctx){'+presentation+'}')(ctx);
 return opts;
}
assert.equal(renderNecron(true).rulesHtml,'');
assert.match(renderNecron(false).rulesHtml,/npoCombatRules/);
const player=src.slice(src.indexOf('  function showPlayerCombatResolution('),src.indexOf('  function displayPendingPlayerCombat('));
assert.match(player,/rulesHtml:previewWeaponRulesAtSelection\(\)\?'':weaponRulesHtml\(profile\)/);
assert.match(src,/if\(rules\)rules.innerHTML=profile\?weaponRulesHtml\(profile\):''/);
"""
    node_check(script)


def test_shell_version_and_save_compatibility():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "return document.documentElement.dataset.ui==='tomb'&&experimentalFeaturesEnabled();" in APP
