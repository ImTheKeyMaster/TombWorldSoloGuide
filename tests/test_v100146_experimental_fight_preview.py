"""Experimental-only Fight Resolution preview and Standard Mode isolation."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")


def test_both_rendering_modes_and_strike_action_runtime():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  function experimentalFightPoolHtml(');
const end=source.indexOf('  async function rollFightParticipant(',start);
assert(start>0&&end>start);
const code=source.slice(start,end);
for(const enabled of [false,true]){
  const hit={id:'hit',kind:'normal',status:'unresolved'};
  const defend={id:'defend',kind:'normal',status:'unresolved'};
  const fight={
    attacker:{side:'player',id:'gunner-flamer',label:'Gunner (Flamer)',wounds:7,maxWounds:7,profile:{name:'Bayonet'}},
    defender:{side:'npo',id:'crawler',label:'Canoptek Tomb Crawler',wounds:21,maxWounds:21,profile:{name:'Claws'}},
    successes:{attacker:[hit],defender:[defend]},turn:'attacker',history:[],completed:false,
    blockCapacity:{attacker:1}
  };
  let html='',strikes=0,blocks=0,shieldSelections=0;
  const strikeControls=[{dataset:{fightStrike:'hit'}}];
  const blockControls=[{dataset:{fightBlocker:'hit',fightBlockTarget:'defend'}}];
  const ctx={
    state:{fightState:fight},document:{documentElement:{dataset:{ui:'tomb'}}},
    experimentalFeaturesEnabled:()=>enabled,isPvpMode:()=>false,
    unresolvedFightSuccesses:(f,role)=>f.successes[role].filter(x=>x.status==='unresolved'),
    equivalentRemainingFightStrikes:()=>null,
    semanticFightActions:()=>({strikes:[{success:hit,damage:2}],blocks:[{blocker:hit,target:defend}]}),
    titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
    escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
    fightParticipantPortrait:(participant,role)=>'<span class="fight-portrait fight-portrait-'+role+'"><svg class="fight-portrait-artwork"></svg></span>',
    fightPoolHtml:(f,role)=>'<section class="fight-pool legacy-'+role+'">ORIGINAL CARD</section>',
    fightLastResolutionHtml:()=>'<section class="fight-last-resolution">EXCHANGE</section>',
    showModal:(title,value)=>{assert.equal(title,'Fight Resolution');html=value;},modal:{},
    $$:s=>s==='[data-fight-strike]'?strikeControls:s==='[data-fight-blocker]'?blockControls:[],
    commitFightStrike:()=>{strikes++;fight.completed=true;return true;},
    commitFightBlock:()=>{blocks++;fight.completed=true;return true;},
    showFightBlockSelection:()=>{shieldSelections++;},
    finishFight:()=>{},save:()=>{}
  };
  const render=new Function('ctx','with(ctx){'+code+'\nreturn renderFightResolution;}')(ctx);
  render();
  assert.match(html,/data-fight-strike="hit"/);
  assert.match(html,/data-fight-blocker="hit"/);
  assert.match(html,/id="fightStrikeHeading"/);
  assert.match(html,/id="fightBlockHeading"/);
  assert.equal(typeof strikeControls[0].onclick,'function');
  assert.equal(typeof blockControls[0].onclick,'function');
  if(enabled){
    assert.match(html,/experimental-fight-sequence/);
    assert.equal((html.match(/experimental-fight-pool-details/g)||[]).length,2);
    assert.match(html,/fight-portrait-attacker/);
    assert.match(html,/fight-portrait-defender/);
    assert.match(html,/Your Turn/);
    assert.match(html,/Gunner \(Flamer\)/);
    assert.match(html,/7\/7/);
    assert.match(html,/21\/21/);
    assert.match(html,/Crits 0/);
    assert.match(html,/Normal 1/);
    assert.doesNotMatch(html,/★|●/);
    assert.match(html,/How Fight Resolution works/);
  }else{
    assert.match(html,/legacy-attacker/);
    assert.match(html,/legacy-defender/);
    assert.match(html,/★ Critical × 0/);
    assert.match(html,/● Normal × 1/);
    assert.match(html,/Gunner \(Flamer\)'s Turn/);
    assert.match(html,/You and the NPO alternate resolving one success/);
    assert.match(html,/Choose one success to resolve. Damage and Blocks commit immediately/);
    assert.doesNotMatch(html,/experimental-fight-sequence/);
  }
  strikeControls[0].onclick();
  assert.equal(strikes,1,'Strike must call the existing engine exactly once');
  assert.equal(blocks,0,'Strike must not invoke Block');
  fight.completed=false;
  blockControls[0].onclick();
  assert.equal(blocks,1,'Regular Block must call the existing engine exactly once');
  assert.equal(strikes,1,'Block must not invoke Strike');
  fight.completed=false;
  fight.blockCapacity.attacker=2;
  render();
  assert.match(html,/BLOCK · SHIELD/);
  blockControls[0].onclick();
  assert.equal(shieldSelections,1,'Shield must use existing target-selection flow');
  assert.equal(blocks,1,'Shield selection must not directly commit a Block');
}
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_pvp_and_shield_instruction_remains_unambiguous():
    src = APP.split("  function experimentalFightResolutionHtml(", 1)[1].split(
        "  function renderFightResolution(){", 1
    )[0]
    assert "const soloPlayerTurn=!isPvpMode()&&participant.side==='player';" in src
    assert "'Your Turn'" in src
    assert "Starting with the attacker, players alternate resolving one success" in src
    assert "capacity>1?'BLOCK · SHIELD':'BLOCK'" in src
    assert "showFightBlockSelection" in APP
    assert "fightLastResolutionHtml(fight)" in src


def test_standard_template_and_gameplay_are_unchanged():
    src = APP.split("  function renderFightResolution(){", 1)[1].split(
        "  async function rollFightParticipant(", 1
    )[0]
    assert "experimentalFeaturesEnabled()&&document.documentElement.dataset.ui==='tomb'" in src
    assert ':\u0060<div class="fight-sequence"><p>${intro}</p>' in src
    assert "You and the NPO alternate resolving one success." in src
    assert "Choose how ${escapeHtml(participant.label)} uses one of its unresolved successes." in src
    assert "Damage and Blocks commit immediately." in src
    assert "semanticFightActions(fight,role)" in src
    assert "soloNpoFightDecision(fight,role)" in src
    assert "commitFightStrike(fight,role,button.dataset.fightStrike)" in src
    assert "commitFightBlock(fight,role,button.dataset.fightBlocker,[button.dataset.fightBlockTarget])" in src
    assert "showFightBlockSelection(fight,role,button.dataset.fightBlocker,button.dataset.fightBlockTarget)" in src


def test_preview_css_cannot_leak_into_standard_or_other_screens():
    section = CSS.split("opt-in compact Fight Resolution. Standard markup and styles untouched. */", 1)[1]
    assert "pointer-events:none;" in section
    assert ".experimental-fight-pool .experimental-fight-card-wounds" in section
    assert ".experimental-fight-pool .experimental-fight-card-successes" in section
    assert "html[data-ui=\"tomb\"][data-experimental=\"on\"]" in section
    assert "experimental-fight-pool" in section
    assert "@media(max-width:390px)" in section


def test_version_and_offline_cache_are_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML


def test_narrow_iphone_columns_are_experimental_only():
    narrow = CSS.split("single-column fallback in Experimental Fight Resolution only. */", 1)[1]
    assert "@media(max-width:374px)" in narrow
    assert '.experimental-fight-pools{\n    grid-template-columns:repeat(2,minmax(0,1fr));' in narrow
    assert 'html[data-ui="tomb"][data-experimental="on"] .experimental-fight-pools' in narrow
    assert ".fight-pools{grid-template-columns:1fr}" in CSS
    assert "@media(max-width:390px)" in CSS
    assert 'html[data-ui="tomb"] #modal:not(.human-activation-modal)' in CSS
    assert 'overflow-y:auto;' in CSS
