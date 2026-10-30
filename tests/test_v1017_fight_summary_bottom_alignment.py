"""v10.1.7: Solo Fight stats and dice align at bottom despite ACTING NOW."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")


def test_active_and_inactive_operatives_share_bottom_anchored_content():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const a=src.indexOf('  function experimentalFightPoolHtml(');
const b=src.indexOf('  function experimentalFightResolutionHtml(',a);
assert(a>=0&&b>a);
const ctx={
  escapeHtml:String,
  fightParticipantPortrait:(participant)=>'<span class="fight-portrait" data-model="'+participant.id+'"></span>',
  unresolvedFightSuccesses:(fight,role)=>fight.successes[role],
  dieHtml:({value})=>'<span class="die">'+value+'</span>',
};
const render=new Function('ctx','with(ctx){'+src.slice(a,b)+'return experimentalFightPoolHtml;}')(ctx);
const fight={
  turn:'attacker',
  attacker:{id:'marksman',label:'Marksman',side:'player',profile:{name:'Fists'},wounds:8,maxWounds:15,attackDice:[{value:4}]},
  defender:{id:'warrior',label:'Necron Warrior 8',side:'npo',profile:{name:'Combat attachment'},wounds:9,maxWounds:9,attackDice:[{value:4}]},
  successes:{
    attacker:[{id:'a',kind:'normal',dieIndex:0}],
    defender:[{id:'b',kind:'normal',dieIndex:0}],
  }
};
const left=render(fight,'attacker'),right=render(fight,'defender');
for (const html of [left,right]) {
  assert(html.includes('<div class="experimental-fight-pool-details">'));
  assert(html.includes('class="experimental-fight-card-name"'));
  assert(html.includes('class="experimental-fight-card-weapon"'));
  assert(html.includes('class="experimental-fight-card-wounds"'));
  assert(html.includes('experimental-fight-card-dice'));
  assert(html.indexOf('experimental-fight-card-status')<html.indexOf('experimental-fight-card-name'));
  assert(html.indexOf('experimental-fight-card-name')<html.indexOf('experimental-fight-card-wounds'));
  assert(html.indexOf('experimental-fight-card-wounds')<html.indexOf('experimental-fight-card-dice'));
}
assert(left.includes('experimental-fight-card-status is-acting'));
assert(!right.includes('experimental-fight-card-status is-acting'));
assert(left.includes('ACTING NOW'));
assert(right.includes('NECRON'));
assert(left.includes('data-model="marksman"'));
assert(right.includes('data-model="warrior"'));
fight.turn='defender';
const nextLeft=render(fight,'attacker'),nextRight=render(fight,'defender');
assert(!nextLeft.includes('experimental-fight-card-status is-acting'));
assert(nextRight.includes('experimental-fight-card-status is-acting'));
assert(nextLeft.includes('experimental-fight-card-dice'));
assert(nextRight.includes('experimental-fight-card-dice'));
"""
    p=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr or p.stdout


def test_css_bottom_anchors_stats_but_does_not_change_portrait_or_vs():
    block=CSS.split("/* v10.1.7: Bottom-align Solo Fight",1)[1]
    prefix='html[data-ui="tomb"] .experimental-fight-choice-screen.is-duel-layout '
    assert prefix+'.experimental-fight-pools{\n  align-items:stretch;\n}' in block
    assert prefix+'.experimental-fight-pool{\n  display:flex;\n  flex-direction:column;\n}' in block
    assert prefix+'.experimental-fight-pool-details{' in block
    assert "display:flex;" in block and "flex:1;" in block and "flex-direction:column;" in block
    assert prefix+'.experimental-fight-card-status{\n  align-self:flex-start;\n  flex:none;\n}' in block
    assert prefix+'.experimental-fight-card-name{\n  margin-top:auto;\n}' in block
    assert "fight-portrait{" not in block
    assert "experimental-fight-versus{" not in block
    assert "[data-experimental" not in block
    assert "is-duel-layout" in block
    assert "grid-template-columns:repeat(5,minmax(0,1fr))" in CSS


def test_offline_assets_use_release_version():
    assert tuple(map(int,CURRENT_APP_VERSION.split(".")))>=(10,1,7)
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"styles.css?v={CURRENT_APP_VERSION}" in index
    assert f"app.js?v={CURRENT_APP_VERSION}" in index
    assert f"V{CURRENT_APP_VERSION}" in index
