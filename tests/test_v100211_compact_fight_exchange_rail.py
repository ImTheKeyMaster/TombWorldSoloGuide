"""v10.0.211: Experimental exchanges form a flat, compact mockup-style rail."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def run_js(code):
    result=subprocess.run(["node","-e",code],cwd=ROOT,text=True,capture_output=True,timeout=30)
    assert result.returncode==0, result.stderr or result.stdout


def test_compact_timeline_retains_true_order_history_and_block_semantics():
    run_js(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const a=source.indexOf('  function fightResolutionRecordHtml(');
const b=source.indexOf('  function equivalentRemainingFightStrikes(',a);
let experimental=true,pvp=false;
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 titleCaseRuleId:s=>s.charAt(0).toUpperCase()+s.slice(1),escapeHtml:String
};
const render=new Function('ctx','with(ctx){'+source.slice(a,b)+'return fightLastResolutionHtml;}')(ctx);
const history=[
 {role:'defender',type:'strike',successKind:'normal',damage:1,before:15,after:14},
 {role:'attacker',type:'block',successKind:'critical',blockedKinds:['normal']},
 {role:'attacker',type:'strike',successKind:'normal',damage:4,before:7,after:3},
 {role:'defender',type:'block',successKind:'normal',blockedKinds:['normal']},
 {role:'defender',type:'strike',successKind:'critical',damage:6,before:14,after:8}
];
const fight={attacker:{side:'player',label:'Blademaster'},defender:{side:'npo',label:'Canoptek Macrocyte Warrior 2'},history:[]};
assert.equal(render(fight),'');
fight.history=structuredClone(history);
let html=render(fight);
assert.deepEqual([...html.matchAll(/aria-label="Action (\d+):/g)].map(m=>m[1]),['1','2','3','4','5']);
assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,5);
assert.equal((html.match(/class="fight-exchange-number"/g)||[]).length,5);
assert(!html.includes('fight-exchange-group is-latest'));
assert.equal((html.match(/class="fight-exchange-actor"/g)||[]).length,5);
assert.equal((html.match(/class="fight-exchange-outcome"/g)||[]).length,5);
assert(html.includes('SWIPE TO REVIEW'));
assert(html.includes('tabindex="0"'));
assert(html.indexOf('1 DAMAGE')<html.indexOf('BLOCKED'));
assert(html.indexOf('BLOCKED')<html.indexOf('4 DAMAGE'));
assert(html.indexOf('4 DAMAGE')<html.indexOf('6 DAMAGE'));
assert(html.includes('7 → 3 wounds'));
assert(html.includes('1 Normal Success canceled'));
assert(html.includes('Canoptek Macrocyte Warrior 2'));
assert(html.includes('NPO ACTION')&&html.includes('NPO RESPONSE')&&html.includes('YOUR ACTION'));
assert(!html.includes('Dealt 4 damage to Canoptek'),'Old redundant verbose descriptions removed');
assert.deepEqual(fight.history,history,'Rendering cannot mutate saved fight data');
// In-progress exchange with one action is shown immediately rather than omitted.
fight.history=[history[0]];
html=render(fight);
assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,1);
assert.equal((html.match(/class="fight-exchange-number"/g)||[]).length,1);
assert(!html.includes('SWIPE TO REVIEW'));
experimental=false;
assert(render(fight).includes('fight-exchange-card'),'Standard shares promoted timeline');
experimental=true;
assert(render(fight).includes('fight-exchange-card'));
experimental=true;pvp=true;
assert(!render(fight).includes('fight-exchange-card'),'PvP unchanged');
""")


def test_horizontal_rail_uses_small_individually_numbered_cards():
    block=CSS.split("/* v10.0.212: Mockup-style compact",1)[1].split("/* v10.0.214: Faction rules",1)[0]
    prefix='html[data-ui="tomb"] .is-duel-layout'
    assert prefix in block
    assert '.fight-exchange-history{' in block
    assert 'display:flex;' in block
    assert 'flex-direction:row;' in block
    assert 'flex:0 0 clamp(94px,26vw,115px);' in block
    assert '.fight-exchange-number{' in block
    assert 'overflow-x:auto;' in block
    assert '.experimental-fight-option' not in block
    assert '.experimental-fight-pool' not in block
    assert 'exchangeHistory.scrollLeft=exchangeHistory.scrollWidth-exchangeHistory.clientWidth' in APP


def test_pwa_version_updated_without_affecting_persistence():
    assert tuple(map(int,CURRENT_APP_VERSION.split('.'))) >= (10,0,211)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT/"service-worker.js").read_text()
    index=(ROOT/"index.html").read_text()
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
