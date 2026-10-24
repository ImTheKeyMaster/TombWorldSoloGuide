"""Experimental-only unavailable Block explanation for Brutal attacks (v10.0.177)."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_brutal_notice_only_when_brutal_prevents_a_legal_normal_block():
    script = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const section=(from,to)=>{
  const i=source.indexOf(from);
  assert(i>=0,'Missing function: '+from);
  const j=source.indexOf(to,i);
  assert(j>i,'Missing boundary: '+to);
  return source.slice(i,j);
};
const code=[
  section('  function fightBlockTargets(','  function canFightBlock('),
  section('  function semanticFightActions(','  function fightRoleDamage('),
  section('  function experimentalFightPoolHtml(','  function renderFightResolution(){')
].join('\n');
const context={
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  unresolvedFightSuccesses:(fight,role)=>fight.successes[role].filter(die=>die.status==='unresolved'),
  weaponHasRule:(profile,rule)=>(profile.ruleIds||[]).includes(rule),
  isPvpMode:()=>false,
  escapeHtml:text=>String(text).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
  titleCaseRuleId:kind=>kind.charAt(0).toUpperCase()+kind.slice(1),
  fightParticipantPortrait:()=>'',fightLastResolutionHtml:()=>''
};
const {semanticFightActions,experimentalFightBlockUnavailableHtml,experimentalActionFirstFightHtml}=
  new Function('context','with(context){'+code+'\nreturn {semanticFightActions,experimentalFightBlockUnavailableHtml,experimentalActionFirstFightHtml};}')(context);
const success=(id,kind)=>({id,kind,status:'unresolved'});
const build=({
  own=[success('own-normal','normal')],
  enemy=[success('enemy-normal','normal'),success('enemy-critical','critical')],
  brutal=true,weapon='Claws',role='attacker'
}={})=>{
  const player={side:'player',label:'Gunner 2 (Plasma Gun)',wounds:7,maxWounds:7,profile:{name:'Bayonet',normal:2,crit:3,ruleIds:[]}};
  const opponent={side:'npo',label:'Canoptek Tomb Crawler 1',wounds:8,maxWounds:21,profile:{name:weapon,normal:4,crit:4,ruleIds:brutal?['brutal']:[]}};
  const fight={attacker:role==='attacker'?player:opponent,
               defender:role==='attacker'?opponent:player,
               turn:role,history:[],
               successes:{attacker:role==='attacker'?own:enemy,
                          defender:role==='attacker'?enemy:own}};
  const actions=semanticFightActions(fight,role);
  const card=experimentalActionFirstFightHtml(fight,role,fight[role],actions,1);
  return {fight,actions,card,notice:experimentalFightBlockUnavailableHtml(fight,role,actions)};
};

const brutal=build();
assert.equal(brutal.actions.blocks.length,0,'Brutal excludes normal blocks');
assert.match(brutal.notice,/BLOCK UNAVAILABLE/);
assert.match(brutal.notice,/Brutal \(Claws\)/);
assert.match(brutal.notice,/Only critical successes can Block/);
assert.match(brutal.notice,/You have no critical successes remaining/);
assert.match(brutal.card,/experimental-fight-block-unavailable/);
assert.match(brutal.card,/Deal 2 damage/);
assert.doesNotMatch(brutal.card,/data-exp-fight-choice="block"/);
assert.match(brutal.card,/Resolve Selected Action/);
assert.equal((brutal.card.match(/class="experimental-fight-block-unavailable"/g)||[]).length,1,
  'Notice must render exactly once');
assert.match(build({own:[success('a','normal'),success('b','normal')]}).notice,/BLOCK UNAVAILABLE/);
assert.match(build({role:'defender'}).notice,/BLOCK UNAVAILABLE/,'PVP and reverse roles use same logic');

const normal=build({brutal:false});
assert.equal(normal.actions.blocks.length,1,'Normal attack allows normal-vs-normal Block');
assert.equal(normal.notice,'');
assert.match(normal.card,/data-exp-fight-choice="block"/);
assert.doesNotMatch(normal.card,/BLOCK UNAVAILABLE/);

const ownCrit=build({own:[success('own-normal','normal'),success('own-critical','critical')]});
assert(ownCrit.actions.blocks.length>0,'Critical can Block Brutal attacks');
assert.equal(ownCrit.notice,'');
assert.doesNotMatch(ownCrit.card,/BLOCK UNAVAILABLE/);

const onlyEnemyCrit=build({enemy:[success('enemy-critical','critical')]});
assert.equal(onlyEnemyCrit.actions.blocks.length,0);
assert.equal(onlyEnemyCrit.notice,'','Do not attribute ordinary critical-block restriction to Brutal');
assert.doesNotMatch(onlyEnemyCrit.card,/BLOCK UNAVAILABLE/);

const enemySpent=build({enemy:[]});
assert.equal(enemySpent.notice,'','No enemy success to Block');
assert.doesNotMatch(enemySpent.card,/BLOCK UNAVAILABLE/);

const onlyOwnCritical=build({own:[success('own-critical','critical')]});
assert(onlyOwnCritical.actions.blocks.length>0);
assert.equal(onlyOwnCritical.notice,'');

const escaped=build({weapon:'Claws <Danger>'});
assert.match(escaped.notice,/Brutal \(Claws &lt;Danger>/);
assert.doesNotMatch(escaped.notice,/Claws <Danger>/);
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_display_is_experimental_only_and_versioned():
    assert CURRENT_APP_VERSION == "10.0.178"
    assert "experimentalFightBlockUnavailableHtml(fight,role,actions)" in APP
    assert "if(document.documentElement.dataset.ui==='tomb'&&document.documentElement.dataset.experimental==='on')" in APP
    assert "if(weaponHasRule(opponent.profile,'brutal')&&blocker.kind!=='critical')return [];" in APP
    portion = CSS.split("v10.0.177: only Experimental Fight resolution", 1)[1]
    assert 'html[data-ui="tomb"][data-experimental="on"] .experimental-fight-choice-screen .experimental-fight-block-unavailable' in portion
    assert "role=\"note\"" in APP
    assert "aria-labelledby=\"fightBlockUnavailableHeading\"" in APP
    assert "data-exp-fight-choice=\"block\"" in APP


def test_unavailable_block_slash_is_clipped_to_shield():
    """The slash cannot protrude beyond its shield at any rendered size."""
    import re

    icon = APP.split('function experimentalFightBlockUnavailableHtml(', 1)[1].split(
        '  function experimentalActionFirstFightHtml(', 1
    )[0]
    shield = (
        'M12 2 20 5.5V12c0 4.8-3.2 8.2-8 10-4.8-1.8-8-5.2-8-10V5.5L12 2Z'
    )
    assert '<clipPath id="experimentalFightBlockShieldClip">' in icon
    assert f'<path d="{shield}"/></clipPath>' in icon
    assert '<path d="m5 19 14-14" clip-path="url(#experimentalFightBlockShieldClip)"/>' in icon
    assert icon.index('clip-path="url(#experimentalFightBlockShieldClip)"') < icon.rindex(
        f'<path d="{shield}"/>'
    ), 'Draw the shield outline above the clipped diagonal'
    assert icon.count('experimentalFightBlockShieldClip') == 2
    assert 'experimentalFightBlockUnavailableHtml(fight,role,actions)' in APP
