"""Promoted Fight Resolution renders identically in Standard and Experimental Tomb UI."""

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
const first=source.indexOf('  function experimentalFightPoolHtml(');
const last=source.indexOf('  async function rollFightParticipant(',first);
assert(first>0&&last>first);
const sourceCode=source.slice(first,last);
const success=(id,kind)=>({id,kind,value:kind==='critical'?6:4,status:'unresolved'});
let tombStandard=null;
for(const mode of ['tomb','classic']){
  for(const enabled of [false,true]){
    const hit=success('hit','normal'),enemy=success('enemy','normal');
    const fight={
      attacker:{side:'player',id:'gunner-flamer',label:'Gunner (Flamer)',
        wounds:7,maxWounds:7,profile:{name:'Bayonet'}},
      defender:{side:'npo',id:'crawler',label:'Canoptek Tomb Crawler',
        wounds:21,maxWounds:21,profile:{name:'Claws'}},
      successes:{attacker:[hit],defender:[enemy]},turn:'attacker',
      history:[],completed:false,blockCapacity:{attacker:1}
    };
    let html='';
    const confirm={disabled:true};
    const ctx={
      state:{fightState:fight},
      document:{documentElement:{dataset:{ui:mode,experimental:enabled?'on':'off'}}},
      experimentalFeaturesEnabled:()=>enabled,
      dieHtml:d=>`<div class="die ${d.kind}" data-face="${d.value}"></div>`,
      isPvpMode:()=>false,
      unresolvedFightSuccesses:(f,role)=>f.successes[role].filter(x=>x.status==='unresolved'),
      otherFightRole:role=>role==='attacker'?'defender':'attacker',
      equivalentRemainingFightStrikes:()=>null,
      semanticFightActions:()=>({strikes:[{success:hit,damage:2}],
        blocks:[{blocker:hit,target:enemy}]}),
      titleCaseRuleId:v=>v[0].toUpperCase()+v.slice(1),
      escapeHtml:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
      fightParticipantPortrait:(p,role)=>'<span class="fight-portrait fight-portrait-'+role+'"></span>',
      fightPoolHtml:(f,role)=>'<section class="fight-pool legacy-'+role+'"></section>',
      fightLastResolutionHtml:()=>'<section class="fight-last-resolution">EXCHANGE</section>',
      showModal:(title,body)=>{assert.equal(title,'Fight Resolution');html=body;},
      modal:{querySelector:()=>null,querySelectorAll:()=>[]},
      scaleFightPortraits:()=>{},
      $:id=>id==='#confirmExperimentalFightChoice'?confirm:null,
      $$:()=>[],
      commitFightStrike:()=>true,commitFightBlock:()=>true,
      showFightBlockSelection:()=>{},
      finishFight:()=>{},save:()=>{}
    };
    const render=new Function('ctx','with(ctx){'+sourceCode+
      '\nreturn renderFightResolution;}')(ctx);
    render();
    if(mode==='tomb'){
      assert.match(html,/experimental-fight-choice-screen/);
      assert.match(html,/fight-portrait-attacker/);
      assert.match(html,/fight-portrait-defender/);
      assert.match(html,/id="fightStrikeHeading"/);
      assert.match(html,/id="fightBlockHeading"/);
      assert.match(html,/data-exp-fight-choice="strike"/);
      assert.match(html,/data-exp-fight-choice="block"/);
      assert.match(html,/Confirm your action/);
      assert.match(html,/experimental-fight-card-dice/);
      assert.match(html,/class="die hit"/);
      assert.match(html,/Unresolved successes: 0 critical, 1 normal/);
      assert.match(html,/How Fight Resolution works/);
      assert.doesNotMatch(html,/BLOCK UNAVAILABLE/);
      if(tombStandard===null)tombStandard=html;
      else assert.equal(html,tombStandard,
        'Standard and Experimental must render exactly the same Fight Resolution');
    }else{
      assert.doesNotMatch(html,/experimental-fight-choice-screen/);
      assert.match(html,/fight-action/);
      assert.match(html,/data-fight-strike="hit"/);
      assert.match(html,/data-fight-blocker="hit"/);
    }
  }
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


def test_classic_legacy_template_and_gameplay_are_unchanged():
    src = APP.split("  function renderFightResolution(){", 1)[1].split(
        "  async function rollFightParticipant(", 1
    )[0]
    assert "document.documentElement.dataset.ui==='tomb'" in src
    assert ':\u0060<div class="fight-sequence"><p>${intro}</p>' in src
    assert "You and the NPO alternate resolving one success." in src
    assert "Choose how ${escapeHtml(participant.label)} uses one of its unresolved successes." in src
    assert "Damage and Blocks commit immediately." in src
    original_pool = APP.split("  function fightPoolHtml(", 1)[1].split("  function fightDiePresentation(", 1)[0]
    assert "★ Critical × ${critical}" in original_pool
    assert "● Normal × ${normal}" in original_pool
    assert "semanticFightActions(fight,role)" in src
    assert "soloNpoFightDecision(fight,role)" in src
    assert "commitFightStrike(fight,role,button.dataset.fightStrike)" in src
    assert "commitFightBlock(fight,role,button.dataset.fightBlocker,[button.dataset.fightBlockTarget])" in src
    assert "showFightBlockSelection(fight,role,button.dataset.fightBlocker,button.dataset.fightBlockTarget)" in src


def test_shared_portrait_css_cannot_leak_into_classic_or_other_screens():
    section = CSS.split("opt-in compact Fight Resolution. Standard markup and styles untouched. */", 1)[1]
    assert "pointer-events:none;" in section
    assert ".experimental-fight-pool .experimental-fight-card-wounds" in section
    assert ".experimental-fight-pool .experimental-fight-card-successes" in section
    assert "html[data-ui=\"tomb\"]" in section
    assert "experimental-fight-pool" in section
    assert "@media(max-width:390px)" in section


def test_version_and_offline_cache_are_consistent():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in SW
    assert f"V{CURRENT_APP_VERSION}" in HTML
    assert f"app.js?v={CURRENT_APP_VERSION}" in HTML
    assert f"styles.css?v={CURRENT_APP_VERSION}" in HTML


def test_narrow_iphone_columns_work_in_both_tomb_modes():
    narrow = CSS.split("single-column fallback in Experimental Fight Resolution only. */", 1)[1]
    assert "@media(max-width:374px)" in narrow
    assert '.experimental-fight-pools{\n    grid-template-columns:repeat(2,minmax(0,1fr));' in narrow
    assert 'html[data-ui="tomb"] .experimental-fight-pools' in narrow
    assert ".fight-pools{grid-template-columns:1fr}" in CSS
    assert "@media(max-width:390px)" in CSS
    assert 'html[data-ui="tomb"] #modal:not(.human-activation-modal)' in CSS
    assert 'overflow-y:auto;' in CSS
