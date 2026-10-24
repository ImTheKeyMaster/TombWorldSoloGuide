"""Standard/Experimental parity for approved Action First Fight and Block guidance."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_standard_and_experimental_same_block_guidance_classic_preserved():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
function section(start,end){
 const a=src.indexOf(start),b=src.indexOf(end,a+start.length);
 assert(a>=0&&b>a,'Missing source: '+start);
 return src.slice(a,b);
}
const code=[
 section('  function fightBlockTargets(','  function canFightBlock('),
 section('  function semanticFightActions(','  function fightRoleDamage('),
 section('  function experimentalFightPoolHtml(','  async function rollFightParticipant(')
].join('\n');
const die=(id,kind)=>({id,kind,status:'unresolved'});
const cases=[
 {label:'critical-only',own:[die('own-normal','normal')],enemy:[die('enemy-crit','critical')],
   brutal:false,expected:/The enemy has only critical successes/},
 {label:'brutal',own:[die('own-normal','normal')],enemy:[die('enemy-normal','normal'),die('enemy-crit','critical')],
   brutal:true,expected:/Brutal \(Claws\)/},
 {label:'no-target',own:[die('own-normal','normal')],enemy:[],
   brutal:false,expected:/No unresolved enemy successes remain to cancel/},
 {label:'legal-critical',own:[die('own-crit','critical')],enemy:[die('enemy-crit','critical')],
   brutal:true,expected:null},
 {label:'legal-normal',own:[die('own-normal','normal')],enemy:[die('enemy-normal','normal')],
   brutal:false,expected:null},
 {label:'legal-mixed',own:[die('own-normal','normal'),die('own-crit','critical')],
   enemy:[die('enemy-normal','normal'),die('enemy-crit','critical')],brutal:false,expected:null}
];
function output(test,ui,experimental,role='attacker'){
 const player={side:'player',label:'Disruptor',wounds:13,maxWounds:13,profile:{name:'Fists',normal:3,crit:4}};
 const npo={side:'npo',label:'Necron Warrior 2',wounds:9,maxWounds:9,
  profile:{name:'Claws',normal:2,crit:4,ruleIds:test.brutal?['brutal']:[]}};
 const fight={
  attacker:role==='attacker'?player:npo,
  defender:role==='attacker'?npo:player,
  turn:role,history:[],completed:false,blockCapacity:{attacker:1,defender:1},
  successes:{attacker:role==='attacker'?test.own:test.enemy,
    defender:role==='attacker'?test.enemy:test.own}
 };
 let markup='';
 const confirm={disabled:true};
 const ctx={
  state:{fightState:fight},
  document:{documentElement:{dataset:{ui,experimental}}},
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  unresolvedFightSuccesses:(f,role)=>f.successes[role].filter(s=>s.status==='unresolved'),
  weaponHasRule:(profile,rule)=>(profile.ruleIds||[]).includes(rule),
  equivalentRemainingFightStrikes:()=>null,
  isPvpMode:()=>false,
  escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
  titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
  fightParticipantPortrait:()=>'',fightLastResolutionHtml:()=>'',fightPoolHtml:()=>'<div class="legacy-pool"></div>',
  showModal:(name,html)=>{assert.equal(name,'Fight Resolution');markup=html;},
  modal:{querySelectorAll:()=>[]},
  $:selector=>selector==='#confirmExperimentalFightChoice'?confirm:null,
  $$:()=>[],finishFight:()=>{},save:()=>{}
 };
 const render=new Function('ctx','with(ctx){'+code+'\nreturn renderFightResolution;}')(ctx);
 render();
 return {markup,confirm};
}
for(const test of cases){
 for(const role of ['attacker','defender']){
  const standard=output(test,'tomb','off',role);
  const experiment=output(test,'tomb','on',role);
  assert.equal(standard.markup,experiment.markup,'Mode mismatch: '+test.label+' '+role);
  assert.match(standard.markup,/experimental-fight-choice-screen/);
  assert.match(standard.markup,/data-exp-fight-choice="strike"/);
  assert.match(standard.markup,/Resolve Selected Action/);
  assert.equal(standard.confirm.disabled,true,'Action still requires selection');
  if(test.expected){
   assert.match(standard.markup,/BLOCK UNAVAILABLE/,test.label);
   assert.match(standard.markup,test.expected,test.label);
   assert.doesNotMatch(standard.markup,/data-exp-fight-choice="block"/);
   assert.equal((standard.markup.match(/BLOCK UNAVAILABLE/g)||[]).length,1);
  }else{
   assert.doesNotMatch(standard.markup,/BLOCK UNAVAILABLE/,test.label);
   assert.match(standard.markup,/data-exp-fight-choice="block"/);
  }
 }
}
const classic=output(cases[0],'classic','off');
assert.doesNotMatch(classic.markup,/experimental-fight-choice-screen|BLOCK UNAVAILABLE/);
assert.match(classic.markup,/fight-action/);
assert.match(classic.markup,/data-fight-strike/);
"""
    run = subprocess.run(["node", "-e", script], cwd=ROOT,
                         text=True, capture_output=True, timeout=30)
    assert run.returncode == 0, run.stderr or run.stdout


def test_approved_styles_have_no_experimental_gate():
    render = APP.split("  function renderFightResolution(){",1)[1].split(
        "  async function rollFightParticipant(",1)[0]
    assert "if(document.documentElement.dataset.ui==='tomb'){" in render
    assert "dataset.experimental" not in render
    assert "experimentalActionFirstFightHtml(fight,role,participant,actions,capacity)" in render
    assert "bindExperimentalActionFirstFight(fight,role,capacity)" in render
    styles = CSS.split("/* v10.0.175/180: Approved Action First Fight choices",1)[1]
    assert '[data-experimental="on"]' not in styles
    assert 'html[data-ui="tomb"] .experimental-fight-choice-screen' in styles
    assert "BLOCK UNAVAILABLE" in APP
    assert "experimentalFightBlockUnavailableHtml(fight,role,actions)" in APP
    assert "function experimentalFeaturesEnabled()" in APP


def test_version_and_persistence():
    index=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in index
    assert f'app.js?v={CURRENT_APP_VERSION}' in index
    assert f'styles.css?v={CURRENT_APP_VERSION}' in index
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
