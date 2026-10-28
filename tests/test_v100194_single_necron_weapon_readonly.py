"""Single Necron weapon choices render read-only, multiple choices remain selectable."""

from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_necron_weapon_selection_single_and_multiple_profiles_in_both_tomb_modes():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function showExperimentalNpoWeaponSelection(');
const end=source.indexOf('  function showNpoAttackConditionCheck(',start);
assert(start>0&&end>start);
const render=new Function('ctx','with(ctx){'+source.slice(start,end)+'return showExperimentalNpoWeaponSelection;}');

function simulate(profiles,{preview=false,selected=-1,showRules=true}={}){
 const select={value:profiles.length===1?'0':selected<0?'':String(selected),listeners:{},
  addEventListener(name,fn){this.listeners[name]=fn;}};
 const elements={
   '#experimentalNpoWeaponProfile':select,
   '#experimentalNpoWeaponGuidance':{innerHTML:''},
   '#experimentalNpoWeaponRules':showRules?{innerHTML:''}:null,
   '#confirmExperimentalNpoWeapon':{disabled:true},
   '#cancelExperimentalNpoWeapon':{}
 };
 let title='',markup='',confirmed=[],cancelled=0;
 const escape=x=>String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
 const ctx={
  document:{documentElement:{dataset:{ui:'tomb',experimental:preview?'on':'off'}}},
  $:id=>elements[id],escapeHtml:escape,canonicalAttackProfile:p=>p,
  tombWeaponRulesAtSelection:()=>showRules,
  npoCombatGuidanceHtml:(n,{profile})=>'<p>Advice '+profile.name+'</p>',
  weaponRulesHtml:profile=>'<p>Rule '+profile.name+'</p>',
  showModal:(name,html)=>{title=name;markup=html;}
 };
 render(ctx)({type:'Necron Warrior'},profiles,'shoot',selected,i=>confirmed.push(i),()=>{cancelled++;});
 return {title,markup,elements,select,confirmed,get cancelled(){return cancelled;}};
}
for(const preview of [false,true]){
 let t=simulate([{name:'Gauss flayer',id:'gauss'}],{preview});
 assert.equal(t.title,'Select Weapon');
 assert.doesNotMatch(t.markup,/terrain-shooting-hint|Terrain &amp; cover/i);
 assert.match(t.markup,/class="readonly-select">Gauss flayer<\/div>/);
 assert.match(t.markup,/<input type="hidden" id="experimentalNpoWeaponProfile" value="0">/);
 assert.doesNotMatch(t.markup,/<select\b/i,'no native iOS dropdown on one choice');
 assert.doesNotMatch(t.markup,/Choose a profile\.\.\./);
 assert.match(t.markup,/Only one weapon profile/);
 assert.match(t.elements['#experimentalNpoWeaponGuidance'].innerHTML,/Advice Gauss flayer/);
 assert.match(t.elements['#experimentalNpoWeaponRules'].innerHTML,/Rule Gauss flayer/);
 assert.equal(t.elements['#confirmExperimentalNpoWeapon'].disabled,false);
 assert.equal(t.select.listeners.change,undefined);
 t.elements['#confirmExperimentalNpoWeapon'].onclick();
 assert.deepEqual(t.confirmed,[0]);
 t.elements['#cancelExperimentalNpoWeapon'].onclick();
 assert.equal(t.cancelled,1);

 t=simulate([{name:'Gauss flayer'}],{preview,showRules:false});
 assert.doesNotMatch(t.markup,/experimentalNpoWeaponRules/);
 assert.equal(t.elements['#confirmExperimentalNpoWeapon'].disabled,false);

 t=simulate([{name:'Focused'},{name:'Sweeping'}],{preview});
 assert.match(t.markup,/<select id="experimentalNpoWeaponProfile">/);
 assert.match(t.markup,/Choose a profile\.\.\./);
 assert.equal(t.elements['#confirmExperimentalNpoWeapon'].disabled,true);
 assert.equal(typeof t.select.listeners.change,'function');
 t.select.value='1';
 t.select.listeners.change();
 assert.match(t.elements['#experimentalNpoWeaponGuidance'].innerHTML,/Advice Sweeping/);
 assert.match(t.elements['#experimentalNpoWeaponRules'].innerHTML,/Rule Sweeping/);
 assert.equal(t.elements['#confirmExperimentalNpoWeapon'].disabled,false);
 t.elements['#confirmExperimentalNpoWeapon'].onclick();
 assert.deepEqual(t.confirmed,[1]);

 t=simulate([{name:'Focused'},{name:'Sweeping'}],{preview,selected:0});
 assert.equal(t.elements['#confirmExperimentalNpoWeapon'].disabled,false);
 assert.match(t.elements['#experimentalNpoWeaponRules'].innerHTML,/Rule Focused/);
 t.elements['#confirmExperimentalNpoWeapon'].onclick();
 assert.deepEqual(t.confirmed,[0]);
}
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0, result.stderr or result.stdout


def test_existing_player_selector_and_combat_state_unchanged():
    assert 'const weaponControl=weapons.length===1' in APP
    assert 'class="readonly-select"' in APP
    assert "weaponSelect.addEventListener('change',renderChoices)" in APP
    assert 'const experimentalWeaponSelection=document.documentElement.dataset.ui===\'tomb\'&&attackType===\'shoot\'' in APP
    assert 'showExperimentalNpoWeaponSelection(n,availableProfiles,attackType,selectedProfileIndex,index=>' in APP
    assert "if(rules)rules.innerHTML=profile?weaponRulesHtml(profile):''" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert ".readonly-select{" in CSS


def test_version_and_offline_cache_consistency():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML
    assert (ROOT/"README.md").read_text(encoding="utf-8").startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
