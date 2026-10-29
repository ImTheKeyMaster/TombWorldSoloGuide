"""v10.0.208: A horizontal exchange is a row of actions, not a vertical pile."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_small_numbered_action_cards_are_horizontally_swipeable():
    css=CSS.split("/* v10.0.212: Mockup-style compact",1)[1]
    assert '.is-duel-layout .fight-exchange-history{' in css
    assert 'display:flex;' in css
    assert 'flex-direction:row;' in css
    assert 'overflow-x:auto;' in css
    assert 'flex:0 0 clamp(94px,26vw,115px);' in css
    assert 'scroll-snap-align:start;' in css
    assert '.fight-exchange-number{' in css
    assert '.fight-exchange-card:not(:last-child)::after' in css
    assert 'html[data-ui="tomb"][data-experimental="on"] .is-duel-layout' in css
    assert 'html[data-ui="tomb"] .experimental-fight-choice-screen' in CSS
    assert "experimental-fight-versus" in APP


def test_actions_remain_chronological_and_standard_is_unchanged():
    js=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const start=s.indexOf('  function fightResolutionRecordHtml(');
const end=s.indexOf('  function equivalentRemainingFightStrikes(',start);
let preview=true;
const ctx={
 document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>preview,isPvpMode:()=>false,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),escapeHtml:String
};
const render=new Function('ctx','with(ctx){'+s.slice(start,end)+'return fightLastResolutionHtml;}')(ctx);
const fight={
 attacker:{side:'player',label:'Horde-Slayer'},
 defender:{side:'npo',label:'Necron Warrior 8'},
 history:[
  {role:'attacker',type:'strike',successKind:'normal',damage:3,before:6,after:3},
  {role:'defender',type:'block',successKind:'critical',blockedKinds:['normal']},
  {role:'defender',type:'strike',successKind:'critical',damage:4,before:18,after:14}
 ]
};
const html=render(fight);
assert.equal((html.match(/class="fight-exchange-number"/g)||[]).length,3);
assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,3);
assert.deepEqual([...html.matchAll(/aria-label="Action (\d+):/g)].map(m=>m[1]),['1','2','3']);
assert(!html.includes('fight-exchange-group-number'));
assert(html.indexOf('3 DAMAGE')<html.indexOf('BLOCKED'));
assert(html.indexOf('BLOCKED')<html.indexOf('4 DAMAGE'));
assert(html.includes('3 DAMAGE'));
assert(html.includes('6 → 3 wounds'),'Compact strike still shows the wound delta');
assert(html.includes('Horde-Slayer') && html.includes('Necron Warrior 8'),'Both actors remain identified');
assert(html.includes('1 Normal Success canceled'),'Block outcome remains explicit');
assert(html.includes('NPO RESPONSE'));
preview=false;
const standard=render(fight);
assert(standard.includes('fight-resolution-record'));
assert(!standard.includes('fight-exchange-history'));
assert.equal(fight.history.length,3);
"""
    result=subprocess.run(["node","-e",js],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_release_version_is_consistent():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,0,208)
    for source in (APP,(ROOT/"service-worker.js").read_text(encoding="utf-8")):
        assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in source
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
