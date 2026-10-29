"""Regression coverage for the v10.0.199 Experimental-only fight exchange redesign.

Standard mode must render the previous markup, and no Fight mechanics change.
"""
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")

def node(source):
    completed = subprocess.run(
        ["node", "-e", source], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout

def test_standard_and_experimental_fight_history_render_independently():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  function fightResolutionRecordHtml(');
const b=source.indexOf('  function equivalentRemainingFightStrikes(',a);
assert(a>0&&b>a);
let experimental=false,pvp=false;
const ctx={
  document:{documentElement:{dataset:{ui:'tomb'}}},
  isPvpMode:()=>pvp,experimentalFeaturesEnabled:()=>experimental,
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  titleCaseRuleId:value=>String(value)[0].toUpperCase()+String(value).slice(1),
  escapeHtml:value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;'),
};
const api=new Function('ctx','with(ctx){'+source.slice(a,b)+'return {fightLastResolutionHtml};}')(ctx);
const fight={
  attacker:{side:'player',label:'Demolisher'},
  defender:{side:'npo',label:'Canoptek Scarab Swarm 2'},
  history:[
    {role:'attacker',type:'strike',successKind:'normal',damage:6,before:10,after:4},
    {role:'defender',type:'block',successKind:'critical',blockedKinds:['normal']},
  ],
};
const standard=api.fightLastResolutionHtml(fight);
assert(standard.includes('fight-resolution-record'));
assert(standard.includes('YOU STRUCK'));
assert(!standard.includes('fight-exchange-card'));
experimental=true;
const upgraded=api.fightLastResolutionHtml(fight);
assert.equal((upgraded.match(/class="fight-exchange-card /g)||[]).length,2);
assert(upgraded.includes('fight-exchange-player'));
assert(upgraded.includes('fight-exchange-npo'));
assert(upgraded.includes('YOUR ACTION')&&upgraded.includes('NPO RESPONSE'));
assert(upgraded.includes('6 DAMAGE')&&upgraded.includes('BLOCKED'));
assert(upgraded.includes('Normal Success')&&upgraded.includes('Critical Success'));
assert(upgraded.includes('10 → 4 wounds'));
assert(upgraded.includes('aria-label="Last exchange"'));
fight.history=[fight.history[0]];
assert.equal((api.fightLastResolutionHtml(fight).match(/class="fight-exchange-card /g)||[]).length,1);
fight.history=[{role:'defender',type:'strike',successKind:'critical',damage:2,before:8,after:6}];
assert(api.fightLastResolutionHtml(fight).includes('NPO RESPONSE'));
assert(api.fightLastResolutionHtml(fight).includes('2 DAMAGE'));
fight.history=[
  {role:'attacker',type:'strike',successKind:'normal',damage:6,before:10,after:4},
  {role:'defender',type:'block',successKind:'critical',blockedKinds:['normal']},
];
pvp=true;
assert(!api.fightLastResolutionHtml(fight).includes('fight-exchange-card'));
assert(api.fightLastResolutionHtml(fight).includes('fight-resolution-record'));
""")

def test_step_circles_are_removed_only_in_experimental_mode():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  function experimentalActionFirstFightHtml(');
const b=source.indexOf('  function bindExperimentalActionFirstFight(',a);
assert(a>0&&b>a);
let enabled=false;
const ctx={
  experimentalFeaturesEnabled:()=>enabled,isPvpMode:()=>false,
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  experimentalFightPoolHtml:()=>'<div></div>',
  fightLastResolutionHtml:()=>'',experimentalFightBlockUnavailableHtml:()=> '',
  escapeHtml:String,titleCaseRuleId:String,
};
const render=new Function('ctx','with(ctx){'+source.slice(a,b)+'return experimentalActionFirstFightHtml;}')(ctx);
const fight={attacker:{side:'player',label:'Demolisher'},defender:{side:'npo',label:'Scarab'}};
const actions={strikes:[],blocks:[]};
const baseline=render(fight,'attacker',fight.attacker,actions,1);
assert.equal((baseline.match(/experimental-fight-step-number/g)||[]).length,2);
assert(baseline.includes('Choose your action')&&baseline.includes('Confirm your action'));
enabled=true;
const newHtml=render(fight,'attacker',fight.attacker,actions,1);
assert(!newHtml.includes('experimental-fight-step-number'));
assert(newHtml.includes('Choose your action')&&newHtml.includes('Confirm your action'));
assert(newHtml.includes('confirmExperimentalFightChoice'));
""")

def test_styles_are_experimental_only_and_use_no_amber():
    start=CSS.index("/* v10.0.199: Experimental-only last exchange timeline.")
    end=CSS.index("/* v10.0.175/180: Approved Action First Fight",start)
    block=CSS[start:end]
    assert "html[data-ui=\"tomb\"][data-experimental=\"on\"]" in block
    assert "fight-exchange-player" in block and "fight-exchange-npo" in block
    assert "--exchange-accent:var(--text)" in block
    assert "--exchange-accent:var(--green)" in block
    assert "fight-exchange-number" in block
    for unwanted in ("amber", "yellow", "#ffcc", "#ffc", "#f4b"):
        assert unwanted not in block.lower()
    # Existing Standard rules still own the original markup and numbered action headings.
    assert 'return `<div class="fight-resolution-record">' in APP
    assert "experimentalFeaturesEnabled()?'':'<span class=" in APP

def test_release_version_and_cache_are_synchronized():
    assert CURRENT_APP_VERSION == "10.0.199"
    assert "const APP_VERSION = '10.0.199';" in APP
    assert "const APP_VERSION = '10.0.199';" in (ROOT / "service-worker.js").read_text()
    index=(ROOT / "index.html").read_text()
    assert '<div class="version">V10.0.199</div>' in index
    assert "styles.css?v=10.0.199" in index
    assert "app.js?v=10.0.199" in index
