"""v10.0.201 Experimental Fight exchanges: chronological action order, one number
per exchange, and the same normal-Block shield used by the action chooser.
"""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def run_node(code):
    result = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_exchange_pairs_stay_chronological_even_when_npo_moves_first():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const begin=source.indexOf('  function fightResolutionRecordHtml(');
const end=source.indexOf('  function equivalentRemainingFightStrikes(',begin);
let preview=true;
const ctx={
  document:{documentElement:{dataset:{ui:'tomb'}}},experimentalFeaturesEnabled:()=>preview,
  isPvpMode:()=>false,
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  titleCaseRuleId:s=>s.charAt(0).toUpperCase()+s.slice(1),
  escapeHtml:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;'),
};
const render=new Function('ctx','with(ctx){'+source.slice(begin,end)+'return fightLastResolutionHtml;}')(ctx);
const npo={role:'defender',type:'strike',successKind:'normal',damage:4,before:6,after:2};
const player={role:'attacker',type:'block',successKind:'critical',blockedKinds:['normal']};
const nextNpo={role:'defender',type:'block',successKind:'normal',blockedKinds:['normal']};
const nextPlayer={role:'attacker',type:'strike',successKind:'normal',damage:3,before:9,after:6};
const fight={attacker:{side:'player',label:'Bombard'},defender:{side:'npo',label:'Flayed One 1'},history:[]};
const matchCount=(html,re)=>(html.match(re)||[]).length;
const groups=html=>[...html.matchAll(/aria-label="Action (\d+):/g)].map(match=>match[1]);
const recordPositions=html=>({npo:html.indexOf('fight-exchange-npo'),you:html.indexOf('fight-exchange-player')});
fight.history=[npo];
let html=render(fight);
assert.deepEqual(groups(html),['1']);
assert(html.includes('NPO ACTION'));
assert.equal(matchCount(html,/class="fight-exchange-card /g),1);
fight.history.push(player);
html=render(fight);
assert.deepEqual(groups(html),['1','2']);
assert.equal(matchCount(html,/class="fight-exchange-card /g),2);
assert(recordPositions(html).npo<recordPositions(html).you);
assert(html.includes('NPO ACTION')&&html.includes('YOUR ACTION'));
assert(html.includes('4 DAMAGE')&&html.includes('BLOCKED'));
assert.equal(matchCount(html,/class="fight-exchange-number"/g),2);
assert(!html.includes('class="fight-exchange-group-number"'));
fight.history.push(nextNpo);
html=render(fight);
assert.deepEqual(groups(html),['1','2','3']);
assert.equal(matchCount(html,/class="fight-exchange-card /g),3);
assert(html.includes('4 DAMAGE'),'Earlier exchange must remain visible');
assert(html.indexOf('4 DAMAGE')<html.indexOf('3 DAMAGE')||!html.includes('3 DAMAGE'));
assert.equal(matchCount(html,/class="fight-exchange-number"/g),3);
fight.history.push(nextPlayer);
html=render(fight);
assert.deepEqual(groups(html),['1','2','3','4']);
assert.equal(matchCount(html,/class="fight-exchange-card /g),4);
assert(recordPositions(html).npo<recordPositions(html).you);
assert(html.includes('3 DAMAGE'));
assert(html.includes('4 DAMAGE'));
assert(html.indexOf('4 DAMAGE')<html.indexOf('3 DAMAGE'));
assert.equal(matchCount(html,/class="fight-exchange-number"/g),4);
assert.equal(fight.history.length,4,'Rendering must not mutate saved action history');
preview=false;
html=render(fight);
assert(html.includes('fight-resolution-record'),'Standard still uses its original renderer');
assert(!html.includes('fight-exchange-group-number'));
""")


def test_player_first_still_orders_player_before_npo_and_numbers_exchange():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const begin=source.indexOf('  function fightResolutionRecordHtml(');
const end=source.indexOf('  function equivalentRemainingFightStrikes(',begin);
const ctx={
  document:{documentElement:{dataset:{ui:'tomb'}}},experimentalFeaturesEnabled:()=>true,
  isPvpMode:()=>false,otherFightRole:role=>role==='attacker'?'defender':'attacker',
  titleCaseRuleId:s=>s.charAt(0).toUpperCase()+s.slice(1),escapeHtml:String
};
const render=new Function('ctx','with(ctx){'+source.slice(begin,end)+'return fightLastResolutionHtml;}')(ctx);
const fight={
  attacker:{side:'player',label:'Demolisher'},defender:{side:'npo',label:'Scarab Swarm'},
  history:[{role:'attacker',type:'strike',successKind:'normal',damage:6,before:10,after:4},
           {role:'defender',type:'block',successKind:'critical',blockedKinds:['normal']}]
};
const html=render(fight);
assert(html.indexOf('fight-exchange-player')<html.indexOf('fight-exchange-npo'));
assert(html.includes('NPO RESPONSE'));
assert(html.includes('aria-label="Exchange 1"'));
assert((html.match(/class="fight-exchange-number"/g)||[]).length===2);
""")


def test_normal_block_shield_is_reused_and_unavailable_shield_is_untouched():
    exchange = APP.split('  function experimentalFightExchangeRecordHtml(', 1)[1].split('  function fightLastResolutionHtml(', 1)[0]
    chooser = APP.split('  function experimentalActionFirstFightHtml(', 1)[1].split('  function bindExperimentalActionFirstFight(', 1)[0]
    unavailable = APP.split('  function experimentalFightBlockUnavailableHtml(', 1)[1].split('  function experimentalActionFirstFightHtml(', 1)[0]
    half_filled_path = '<path d="M12 5.5 6.3 7.7V12c0 3.5 2 6 5.7 7.6V5.5Z" fill="#092319"/>'
    assert half_filled_path in exchange
    assert half_filled_path in chooser
    assert 'fill="currentColor"' in exchange
    assert 'stroke-width="1.8"' in unavailable
    assert 'clip-path="url(#experimentalFightBlockShieldClip)"' in unavailable
    assert '<path d="m5 19 14-14"' not in exchange


def test_action_marker_belongs_to_each_compact_card():
    block = CSS.split('/* v10.0.212: Mockup-style compact',1)[1]
    assert '.fight-exchange-number{' in block
    assert 'flex:0 0 clamp(94px,26vw,115px);' in block
    assert 'scroll-snap-align:start;' in block
    assert 'html[data-ui="tomb"][data-experimental="on"]' in block
    renderer = APP.split('  function experimentalFightExchangeRecordHtml(',1)[1].split('  function fightLastResolutionHtml(',1)[0]
    assert 'position+1' in renderer
    assert 'fight-exchange-number' in renderer
    assert 'fight-exchange-group-number' not in renderer


def test_current_version():
    assert tuple(map(int, CURRENT_APP_VERSION.split('.'))) >= (10, 0, 201)
