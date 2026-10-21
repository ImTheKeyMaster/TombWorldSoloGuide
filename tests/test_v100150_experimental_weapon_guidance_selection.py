"""Experimental-only weapon selection guidance and Standard Mode isolation."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_necron_selection_guidance_updates_when_profile_changes_and_confirm_is_explicit():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const snippet=(a,b)=>app.slice(app.indexOf('  '+a),app.indexOf('  '+b,app.indexOf('  '+a)));
const guidance=snippet('function normalizedGuidanceMatchText(', 'function recordedCombat(');
const selection=snippet('function showExperimentalNpoWeaponSelection(', 'function showNpoAttackWizard(');
let markup='',title='',continued=[],cancelled=0,showCalls=0;
const controls=Object.fromEntries(['#experimentalNpoWeaponProfile','#experimentalNpoWeaponGuidance','#confirmExperimentalNpoWeapon','#cancelExperimentalNpoWeapon'].map(id=>[id,{value:'',innerHTML:'',disabled:true,onclick:null,listeners:{},addEventListener(event,handler){this.listeners[event]=handler;}}]));
const definition={
  id:'crawler',
  abilities:[{id:'weapon-sentinel',name:'Weapon Sentinel',text:'Keep its cover save.'}],
  behavior:{weaponGuidance:{text:'Use Sweeping if two enemies are close.',attackType:'shoot',weaponId:'twin',profileId:'sweep'}},
  rangedWeapons:[{id:'twin',name:'Twin gauss reapers',profiles:[{id:'sweep',name:'Sweeping'},{id:'focused',name:'Focused'}]}]
};
const ctx={
  $:id=>controls[id],
  showModal:(name,value)=>{title=name;markup=value;showCalls++;},
  escapeHtml:x=>String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
  canonicalAttackProfile:x=>x,
  npoDefinition:()=>definition,
  activeNpos:()=>[],
  isPvpMode:()=>false,
  STAGE3_RULE_TEXT:{engrammatic:'Remind player.'}
};
const api=new Function('ctx','with(ctx){'+guidance+selection+'\nreturn {showExperimentalNpoWeaponSelection,npoCombatGuidanceHtml};}')(ctx);
const profiles=[{name:'Sweeping',weaponId:'twin',profileId:'sweep'},{name:'Focused',weaponId:'twin',profileId:'focused'}];
const npo={type:'Canoptek Tomb Crawler',wounds:21,maxWounds:21};
api.showExperimentalNpoWeaponSelection(npo,profiles,'shoot',-1,index=>continued.push(index),()=>{cancelled++;});
assert.equal(title,'Select Weapon');
assert.match(markup,/experimentalNpoWeaponProfile/);
assert.match(markup,/experimentalNpoWeaponGuidance/);
assert.match(markup,/Continue to Combat/);
assert.match(markup,/Choose a profile/);
assert.equal(controls['#confirmExperimentalNpoWeapon'].disabled,true);
assert.equal(controls['#experimentalNpoWeaponGuidance'].innerHTML,'');
controls['#experimentalNpoWeaponProfile'].value='0';
controls['#experimentalNpoWeaponProfile'].listeners.change();
assert.match(controls['#experimentalNpoWeaponGuidance'].innerHTML,/Use Sweeping/);
assert.match(controls['#experimentalNpoWeaponGuidance'].innerHTML,/Weapon Sentinel/);
assert.equal(controls['#confirmExperimentalNpoWeapon'].disabled,false);
controls['#experimentalNpoWeaponProfile'].value='1';
controls['#experimentalNpoWeaponProfile'].listeners.change();
assert.doesNotMatch(controls['#experimentalNpoWeaponGuidance'].innerHTML,/Use Sweeping/);
assert.match(controls['#experimentalNpoWeaponGuidance'].innerHTML,/Weapon Sentinel/);
controls['#confirmExperimentalNpoWeapon'].onclick();
assert.deepEqual(continued,[1],'Confirmed profile must be the currently selected weapon');
controls['#cancelExperimentalNpoWeapon'].onclick();
assert.equal(cancelled,1);
assert.equal(showCalls,1);
assert.match(api.npoCombatGuidanceHtml(npo,{attackType:'shoot',profile:profiles[1]}),/Use Sweeping/,'Original non-strict guidance remains unchanged for Standard Mode');
assert.doesNotMatch(api.npoCombatGuidanceHtml(npo,{attackType:'shoot',profile:profiles[1],matchProfile:true}),/Use Sweeping/);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_experimental_selection_precedes_combat_only_when_needed():
    wizard = source("  function showNpoAttackWizard(", "  function spinnerField(")
    assert "weaponConfirmed=false" in wizard
    assert "experimentalFeaturesEnabled()&&document.documentElement.dataset.ui==='tomb'&&attackType==='shoot'" in wizard
    assert "!weaponConfirmed&&!resumeGuided&&!locked&&!rollingCombat&&!sameCombat" in wizard
    assert "forceWeaponSelection||availableProfiles.length>1||npoCombatGuidanceHtml(n,{attackType,profile:initialProfile})" in wizard
    assert "showExperimentalNpoWeaponSelection(n,availableProfiles,attackType,selectedProfileIndex,index=>" in wizard
    assert "combatDraft:{selecting:true,attackType,targetId:target.id,targetName:targetName,profile}" in wizard
    assert "showNpoAttackWizard(n,attackDice,onDone,onCancel,false,false,true)" in wizard
    assert "if(sequence){state.weaponRuleResolution=null;state.npoAttackTargetId=null;}" in wizard
    assert "const profileControl=!experimentalWeaponSelection&&availableProfiles.length>1" in wizard
    assert "guidanceHtml:experimentalWeaponSelection?'':" in wizard
    assert "rulesHtml:`<div id=\"npoCombatRules\">" in wizard
    assert "else if(rollingCombat)startAutomaticCombat(saved)" in wizard
    assert "else if(selectingCombat){" in wizard
    assert "if(weapon)weapon.textContent=profile.name" in wizard
    assert "if(rules)rules.innerHTML=weaponRulesHtml(profile)" in wizard


def test_player_weapon_selection_and_standard_guidance_preserved():
    player = source("  function showPendingPlayerAttackWizard(", "  function showPlayerCombatResolution(")
    assert 'id="playerWeaponSelect"' in player
    assert "weaponSelect.addEventListener('change',renderChoices)" in player
    assert "weaponRulesHtml(profile,{semanticHeading:true})" in player
    assert "const singleProfile=weapons.length===1?" in player
    shared = source("  function showSharedCombatResolutionScreen(", "  function showCombatResumeRecovery(")
    assert "${guidanceHtml}" in shared and "${rulesHtml}" in shared
    assert "guidanceHtml:experimentalWeaponSelection?'':" in APP
    assert "npoCombatGuidanceHtml(n,{attackType,profile})" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert ".dedicated-combat-screen" in CSS


def test_release_version_consistency():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
