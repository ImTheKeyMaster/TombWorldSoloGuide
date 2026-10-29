"""Experimental solo Fight Resolution duel layout, not a gameplay change."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def node(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout


def test_duel_markup_is_only_in_experimental_solo_and_selection_is_preserved():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const start=s.indexOf('  function experimentalActionFirstFightHtml(');
const end=s.indexOf('  function bindExperimentalActionFirstFight(',start);
assert(start>0&&end>start);
const factory=new Function('ctx','with(ctx){'+s.slice(start,end)+'return experimentalActionFirstFightHtml;}');
const fight={attacker:{side:'player',label:'Gunner'},defender:{side:'npo',label:'Scarab Swarm'}};
const actions={strikes:[
  {success:{id:'norm',kind:'normal'},damage:3},
  {success:{id:'crit',kind:'critical'},damage:4}
],blocks:[{blocker:{id:'crit',kind:'critical'},target:{id:'enemy-crit',kind:'critical'}}]};
let experimental=true,pvp=false;
const ctx={
  experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
  otherFightRole:r=>r==='attacker'?'defender':'attacker',
  experimentalFightPoolHtml:(f,role)=>'<section data-role="'+role+'"></section>',
  fightLastResolutionHtml:()=>'<section class="fight-exchange-history"></section>',
  experimentalFightStrikeAdvice:()=>'',titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
  escapeHtml:String,experimentalFightBlockUnavailableHtml:()=>'<section class="experimental-fight-block-unavailable"></section>'
};
const render=()=>factory(ctx)(fight,'attacker',fight.attacker,actions,1);
const preview=render();
assert(preview.includes('class="experimental-fight-versus"'));
assert(preview.includes('experimental-fight-choice-screen is-duel-layout'));
assert(preview.includes('class="experimental-fight-choice-columns"'));
assert.equal((preview.match(/data-exp-fight-choice="strike"/g)||[]).length,2);
assert.equal((preview.match(/data-exp-fight-choice="block"/g)||[]).length,1);
assert(preview.includes('data-fight-block-target="enemy-crit"'));
assert(preview.includes('id="confirmExperimentalFightChoice" disabled'));
assert(preview.includes('aria-pressed="false"'));
experimental=false;
const standard=render();
for(const marker of ['is-duel-layout','experimental-fight-versus','experimental-fight-choice-columns']){
  assert(!standard.includes(marker),'Standard must not include '+marker);
}
experimental=true;pvp=true;
const versus=render();
assert(!versus.includes('is-duel-layout'),'PvP not opted in');
assert(!versus.includes('experimental-fight-versus'),'PvP VS remains unchanged');
actions.blocks=[];
pvp=false;
const unavailable=render();
assert(unavailable.includes('experimental-fight-block-unavailable'));
""")


def test_exchange_cards_remain_grouped_and_chronological():
    node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function fightResolutionRecordHtml(');
const b=s.indexOf('  function equivalentRemainingFightStrikes(',a);
const make=new Function('ctx','with(ctx){'+s.slice(a,b)+'return fightLastResolutionHtml;}');
let experimental=true,pvp=false;
const ctx={document:{documentElement:{dataset:{ui:'tomb'}}},
 experimentalFeaturesEnabled:()=>experimental,isPvpMode:()=>pvp,
 otherFightRole:r=>r==='attacker'?'defender':'attacker',
 titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),escapeHtml:String};
const render=make(ctx);
const fight={attacker:{side:'player',label:'Gunner'},defender:{side:'npo',label:'Scarab Swarm'},history:[
 {role:'defender',type:'strike',successKind:'normal',damage:1,before:13,after:12},
 {role:'attacker',type:'block',successKind:'critical',blockedKinds:['critical']},
 {role:'attacker',type:'strike',successKind:'normal',damage:3,before:7,after:4}
]};
const html=render(fight);
assert(html.includes('tabindex="0"'),'Swipeable history is keyboard accessible');
assert(html.includes('SWIPE TO REVIEW'));
assert.deepEqual([...html.matchAll(/aria-label="Action (\d+):/g)].map(m=>m[1]),['1','2','3']);
assert.equal((html.match(/class="fight-exchange-card /g)||[]).length,3);
assert.equal((html.match(/class="fight-exchange-number"/g)||[]).length,3);
assert(html.indexOf('1 DAMAGE')<html.indexOf('BLOCKED'));
assert(html.indexOf('BLOCKED')<html.indexOf('3 DAMAGE'));
assert.equal(fight.history.length,3);
experimental=false;
assert(!render(fight).includes('fight-exchange-history'),'Standard history remains untouched');
experimental=true;pvp=true;
assert(!render(fight).includes('fight-exchange-history'),'PvP history remains untouched');
""")


def test_horizontal_scrolling_and_responsive_two_column_css():
    assert 'exchangeHistory.scrollLeft=exchangeHistory.scrollWidth-exchangeHistory.clientWidth' in APP
    assert 'else exchangeHistory.scrollTop=exchangeHistory.scrollHeight' in APP
    block=CSS.split('/* v10.0.206: Fight Resolution concept 3, opt-in Experimental Solo only.',1)[1]
    assert 'grid-auto-flow:column' in block
    assert 'overflow-x:auto;overflow-y:hidden' in block
    assert 'scroll-snap-type:x proximity' in block
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in block
    assert '.experimental-fight-versus::before' in block
    assert '.experimental-fight-choice-columns' in block
    assert 'html[data-ui="tomb"][data-experimental="on"] .is-duel-layout' in block
    assert 'max-width:360px' in block


def test_release_version():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,0,206)
    for source in (APP,SW):
        assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in source
    assert f'V{CURRENT_APP_VERSION}' in INDEX
    assert f'app.js?v={CURRENT_APP_VERSION}' in INDEX
