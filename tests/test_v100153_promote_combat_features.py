"""Promoted Tomb UI features render the same with the Experimental toggle off or on."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_promoted_tomb_ui_is_not_gated_by_the_preview_toggle():
    assert APP.count("experimentalFeaturesEnabled()") == 2  # definition + panel checkbox
    # All approved portrait and promoted UI styling is shared by both modes.
    promoted_css = CSS.split('/* v10.0.171: Preview a consistent', 1)[0]
    assert '[data-experimental="on"]' not in promoted_css  # Existing approved features stay standard
    assert 'html[data-ui="tomb"] .experimental-fight-pool' in CSS
    assert 'html[data-ui="tomb"] .combat-resolution-modal .dedicated-combat-screen > #automaticCombat{order:2}' in CSS
    assert 'html[data-ui="tomb"] .combat-resolution-modal .multi-target-attack-progress{' in CSS
    assert "document.documentElement.dataset.ui==='tomb'?experimentalFightResolutionHtml" in APP
    assert "const experimentalWeaponSelection=document.documentElement.dataset.ui==='tomb'&&attackType==='shoot'" in APP
    assert "if(document.documentElement.dataset.ui!=='tomb'" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_standard_and_experimental_both_enter_necron_weapon_selector():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const start=app.indexOf('  function showNpoAttackWizard(');
const end=app.indexOf('    const profileControl=',start);
assert(start>0&&end>start);
const wizard=app.slice(start,end);
const target={id:'sergeant',type:'Space Marine',wounds:15,maxWounds:15,save:3};
const necron={id:'crawler',type:'Canoptek Tomb Crawler'};
const profiles=[
 {name:'Twin gauss reapers: Focused',weaponId:'twin',profileId:'focused'},
 {name:'Twin gauss reapers: Sweeping',weaponId:'twin',profileId:'sweeping'}
];
for(const enabled of [false,true]){
 const state={lastActivation:{action:'Shoot',combatDraft:null},weaponRuleResolution:null,roster:[]};
 const shown=[];
 const ctx={
   state,
   experimentalFeaturesEnabled:()=>enabled,
   document:{documentElement:{dataset:{ui:'tomb',experimental:enabled?'on':'off'}}},
   selectedNpoAttackTarget:()=>target,
   npoName:()=>necron.type,playerName:()=>target.type,npoAttackProfiles:()=>profiles,
   canonicalAttackProfile:p=>p,isPvpMode:()=>false,
   npoCombatGuidanceHtml:()=>'<div>Choose Sweeping when valid.</div>',
   showExperimentalNpoWeaponSelection:(...args)=>shown.push(args),
   save:()=>{},onCancel:()=>{}
 };
 const show=new Function('ctx','with(ctx){'+wizard+'\n}return showNpoAttackWizard;}')(ctx);
 show(necron,[],()=>{},()=>{});
 assert.equal(shown.length,1,'Necron selection must be presented in both modes');
 assert.equal(shown[0][3],-1,'no weapon silently preselected');
 assert.equal(state.lastActivation.combatDraft,null,'selection did not commit a combat draft');
}
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_future_experiments_remain_independent_and_versioned():
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert "function experimentalFeaturesEnabled(){" in APP
    assert "return document.documentElement.dataset.experimental==='on';" in APP
    assert "document.documentElement.dataset.experimental=enabled?'on':'off';" in APP
    assert "localStorage.setItem(EXPERIMENTAL_FEATURES_KEY,'on');" in APP
    assert "localStorage.removeItem(EXPERIMENTAL_FEATURES_KEY);" in APP
    assert "experimentalUiToggle.checked=experimentalFeaturesEnabled();" in APP
    assert "The approved green Deathwatch portraits are now standard" in INDEX
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
