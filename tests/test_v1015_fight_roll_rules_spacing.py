"""Fight Roll Weapon Rules spacing regression coverage for v10.1.5."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_both_fight_roll_weapon_rules_blocks_stay_in_place():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const begin=source.indexOf('  function fightWeaponRulesHtml(');
const end=source.indexOf('  function fightResolutionRecordHtml(', begin);
assert(begin>0 && end>begin);
let html='';
const ctx={
  escapeHtml:String,
  weaponRulesHtml:()=>'<section class="weapon-rules"><h3>Weapon Rules</h3><ul><li>Brutal</li></ul></section>',
  fightRollParticipantHtml:(f,role)=>'<section class="fight-roll-pool" data-role="'+role+'"></section>',
  showModal:(title,body)=>{assert.equal(title,'Fight Roll');html=body;},
  $:()=>({}),
  renderFightResolution:()=>{},
  settleAnimatedDice:()=>{},
};
const render=new Function('ctx','with(ctx){'+source.slice(begin,end)+'return renderFightRoll;}')(ctx);
const fight={
  attacker:{label:'Demolisher',profile:{name:'Heavy thunder hammer'},attackDice:[]},
  defender:{label:'Canoptek Tomb Crawler',profile:{name:'Claws'},attackDice:[]}
};
render(fight);
assert(html.includes('<div class="fight-roll">'));
assert.equal((html.match(/class="fight-weapon-rules"/g)||[]).length,2);
assert.equal((html.match(/<h3>Weapon Rules<\/h3>/g)||[]).length,2);
assert(html.indexOf('<strong>Demolisher</strong>')<html.indexOf('Weapon Rules'));
assert(html.indexOf('<strong>Canoptek Tomb Crawler</strong>')>html.indexOf('<strong>Demolisher</strong>'));
assert(html.includes('Resolve Strike or Block'));
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_spacing_is_reduced_only_on_fight_roll_and_applies_to_both_modes():
    section=CSS.split("/* v10.1.5: Reduce dead space",1)[1]
    assert ".fight-roll>.fight-weapon-rules>.weapon-rules{" in section
    assert "margin:3px 0 4px;" in section
    assert ".fight-roll>.fight-weapon-rules>.weapon-rules>h3{" in section
    assert "margin:0 0 5px;" in section
    assert '.weapon-rules{margin:14px 0;padding:12px 14px;' in CSS
    # No Experimental/Standard gating. Other weapon rules and roll dice
    # retain their existing styling.
    assert "[data-experimental" not in section
    assert ".fight-roll-pool .dice-row{margin:9px 0}" in CSS


def test_pwa_cache_and_version_consistency():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,1,5)
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"app.js?v={CURRENT_APP_VERSION}" in index
    assert f"styles.css?v={CURRENT_APP_VERSION}" in index
    assert f"V{CURRENT_APP_VERSION}" in index
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
