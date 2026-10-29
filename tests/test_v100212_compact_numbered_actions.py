"""v10.0.212: Match the mockup's compact numbered action cards, not exchange groups."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_per_action_numbers_and_concise_cards_for_each_history_size():
    code=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function fightResolutionRecordHtml(');
const b=s.indexOf('  function equivalentRemainingFightStrikes(',a);
let experimental=true,pvp=false;
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
 escapeHtml:String
};
const render=new Function('ctx','with(ctx){'+s.slice(a,b)+'return fightLastResolutionHtml;}')(ctx);
const history=[
 {role:'defender',type:'strike',successKind:'normal',damage:2,before:15,after:13},
 {role:'attacker',type:'block',successKind:'critical',blockedKinds:['normal']},
 {role:'attacker',type:'strike',successKind:'normal',damage:4,before:7,after:3},
 {role:'defender',type:'block',successKind:'normal',blockedKinds:['normal']},
 {role:'defender',type:'strike',successKind:'critical',damage:6,before:13,after:7}
];
const fight={attacker:{side:'player',label:'Blademaster'},defender:{side:'npo',label:'Canoptek Macrocyte Warrior 2'},history:[]};
assert.equal(render(fight),'');
for(let length=1;length<=history.length;length++){
 fight.history=structuredClone(history.slice(0,length));
 const html=render(fight);
 assert(html.includes('>EXCHANGE HISTORY<'));
 assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,length);
 assert.equal((html.match(/class="fight-exchange-number"/g)||[]).length,length);
 assert.deepEqual([...html.matchAll(/aria-label="Action (\d+):/g)].map(x=>Number(x[1])),Array.from({length},(_,i)=>i+1));
 assert.deepEqual([...html.matchAll(/class="fight-exchange-number"[^>]*>(\d+)<\/span>/g)].map(x=>Number(x[1])),Array.from({length},(_,i)=>i+1));
 assert(!html.includes('fight-exchange-group-number'));
 assert(!html.includes('fight-exchange-group is-latest'));
 assert(!html.includes('>NEXT EXCHANGE<'));
 assert(!html.includes('>Clear<'));
 assert.equal(html.includes('SWIPE TO REVIEW'),length>2);
 assert.deepEqual(fight.history,history.slice(0,length),'Rendering must not change saved fight actions');
}
let html=render(fight);
assert(html.indexOf('2 DAMAGE')<html.indexOf('BLOCKED'));
assert(html.indexOf('BLOCKED')<html.indexOf('4 DAMAGE'));
assert(html.indexOf('4 DAMAGE')<html.indexOf('6 DAMAGE'));
assert(html.includes('15 → 13 wounds'));
assert(html.includes('7 → 3 wounds'));
assert(html.includes('1 Normal Success canceled'));
assert(html.includes('YOUR ACTION'));
assert(html.includes('NPO ACTION'));
assert(html.includes('NPO RESPONSE'));
assert(html.includes('Canoptek Macrocyte Warrior 2'),'Full actor label is retained in the markup');
assert(html.includes('aria-label="Chronological fight actions, swipe horizontally to review"'));
const experimentalHtml=html;
experimental=false;
html=render(fight);
assert.equal(html,experimentalHtml,'Standard and Experimental share compact action history');
assert(html.includes('fight-exchange-number'));
assert(html.includes('fight-exchange-history'));
experimental=true;pvp=true;
html=render(fight);
assert(html.includes('fight-resolution-record'));
assert(!html.includes('fight-exchange-number'));
"""
    result=subprocess.run(["node","-e",code],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_mobile_card_density_and_explicit_scope():
    block=CSS.split("/* v10.0.212: Mockup-style compact",1)[1]
    assert 'html[data-ui="tomb"] .is-duel-layout' in block
    assert 'flex:0 0 clamp(94px,26vw,115px);' in block
    assert 'width:clamp(94px,26vw,115px);' in block
    assert 'min-height:130px;' in block
    assert '.fight-exchange-number{' in block
    assert '.fight-exchange-card:not(:last-child)::after' in block
    assert 'scroll-snap-align:start;' in block
    assert 'overflow-x:auto;' in block
    assert 'line-clamp:2;' in block
    assert '.experimental-fight-option' not in block
    assert '.experimental-fight-pool' not in block


def test_release_and_offline_cache():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,0,212)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    sw=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in sw
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
