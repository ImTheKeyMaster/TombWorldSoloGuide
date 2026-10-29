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
assert(upgraded.includes('aria-label="Fight exchange history"'));
assert(upgraded.includes('aria-label="Action 1:'));
assert.equal((upgraded.match(/class="fight-exchange-number"/g)||[]).length,2);
assert(!upgraded.includes('class="fight-exchange-group"'));
const npoStart=upgraded.indexOf('class="fight-exchange-card fight-exchange-npo"');
const npoShield=npoStart>=0?upgraded.slice(npoStart,upgraded.indexOf('</svg>',npoStart)+6):'';
assert(npoShield,'The block exchange should render a shield SVG');
assert(npoShield.includes('M12 2 21 5.5V12'),'Normal Block shield outline remains intact');
assert(npoShield.includes('M12 5.5 6.3 7.7V12'),'Normal Block half-filled shield detail is retained');
assert(!npoShield.includes('m5 19 14-14'),'Block exchange must not use unavailable slash');
assert(!npoShield.includes('clip-path'),'Block exchange icon must be a plain shield');

fight.history=[fight.history[0]];
assert.equal((api.fightLastResolutionHtml(fight).match(/class="fight-exchange-card /g)||[]).length,1);
fight.history=[{role:'defender',type:'strike',successKind:'critical',damage:2,before:8,after:6}];
assert(api.fightLastResolutionHtml(fight).includes('NPO ACTION'));
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
    assert "fight-exchange-group-number" in block
    assert "fight-exchange-label" in block
    for unwanted in ("amber", "yellow", "#ffcc", "#ffc", "#f4b"):
        assert unwanted not in block.lower()
    # Existing Standard rules still own the original markup and numbered action headings.
    assert 'return `<div class="fight-resolution-record">' in APP
    assert "experimentalFeaturesEnabled()?'':'<span class=" in APP

def test_release_version_and_cache_are_synchronized():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 199)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / "service-worker.js").read_text()
    index=(ROOT / "index.html").read_text()
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in index
    assert f"styles.css?v={CURRENT_APP_VERSION}" in index
    assert f"app.js?v={CURRENT_APP_VERSION}" in index

def test_unavailable_block_retains_its_slash_separately_from_exchange_shield():
    unavailable_start = APP.index("  function experimentalFightBlockUnavailableHtml(")
    unavailable_end = APP.index("  function experimentalActionFirstFightHtml(", unavailable_start)
    unavailable = APP[unavailable_start:unavailable_end]
    exchange_start = APP.index("  function experimentalFightExchangeRecordHtml(")
    exchange_end = APP.index("  function fightLastResolutionHtml(", exchange_start)
    exchange = APP[exchange_start:exchange_end]
    assert 'clip-path="url(#experimentalFightBlockShieldClip)"' in unavailable
    assert '<path d="m5 19 14-14"' in unavailable
    assert '<path d="m5 19 14-14"' not in exchange
    assert 'fill="currentColor"' in exchange
    assert 'fill="#092319"' in exchange

