"""Regression coverage for clarified Shield Block target selection (v10.1.2)."""
from pathlib import Path
import subprocess
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def test_shield_target_selection_and_commit_runtime():
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const slice=(start,end)=>{
  const a=app.indexOf('  function '+start+'(');
  const b=app.indexOf('  function '+end+'(',a+10);
  assert(a>0&&b>a,'Missing '+start);
  return app.slice(a,b);
};
const code=[
  slice('fightBlockTargets','canFightBlock'),
  slice('commitFightBlock','soloNpoFightDecision'),
  slice('showFightBlockSelection','semanticFightActions')
].join('\n');
const calls={};
const modal={};
let markup='',inputs=[],button,rendered=0,saved=0;
const context={
  otherFightRole:role=>role==='attacker'?'defender':'attacker',
  unresolvedFightSuccesses:(fight,role)=>fight.successes[role].filter(item=>item.status==='unresolved'),
  weaponHasRule:(profile,key)=>(profile.rules||[]).includes(key),
  titleCaseRuleId:s=>s[0].toUpperCase()+s.slice(1),
  escapeHtml:s=>String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;'),
  showModal:(title,html)=>{
    assert.equal(title,'Shield Block');markup=html;
    inputs=[...markup.matchAll(/<input type="checkbox" name="shieldBlockTarget" value="([^"]+)"(.*?)>/g)].map(m=>({value:m[1],checked:/\bchecked\b/.test(m[2])}));
    button={disabled:/id="commitShieldBlock" disabled/.test(markup)};
  },
  $$:()=>inputs,
  $:()=>button,
  modal,
  advanceFightTurn:fight=>{
    fight.turn='defender';
  },
  save:()=>{saved++},
  renderFightResolution:()=>{rendered++}
};
const api=new Function('ctx','with(ctx){'+code+
  'return {showFightBlockSelection,commitFightBlock,fightBlockTargets};}')(context);
const success=(id,kind)=>({id,kind,status:'unresolved'});
const make=(player='critical',enemies=['normal','critical'],capacity=2,brutal=false)=>({
  turn:'attacker',completed:false,resolutionIndex:0,history:[],
  blockCapacity:{attacker:capacity},
  attacker:{profile:{rules:[]}},
  defender:{profile:{rules:brutal?['brutal']:[]}},
  successes:{attacker:[success('own',player)],defender:enemies.map((kind,i)=>success('enemy'+i,kind))}
});
// The screenshot scenario: one critical Shield Block cancels both enemy dice.
let f=make();
api.showFightBlockSelection(f,'attacker','own','enemy0');
assert.match(markup,/You're using your <strong>Critical Success<\/strong> to block up to 2 enemy successes/);
assert.match(markup,/Select enemy successes to cancel:/);
assert.match(markup,/Enemy successes to cancel/);
assert.deepEqual(inputs.map(i=>i.checked),[true,true]);
assert.equal(button.disabled,false);
button.onclick();
assert.equal(f.successes.attacker[0].status,'blocked');
assert.deepEqual(f.successes.defender.map(s=>s.status),['blocked','blocked']);
assert.deepEqual(f.history[0].blockedKinds,['normal','critical']);
assert.equal(f.history.length,1,'one critical success spends one action blocking both');
assert.equal(rendered,1);
assert.equal(saved,1);
// Both selections can be edited before confirmation.
f=make();
api.showFightBlockSelection(f,'attacker','own','enemy1');
inputs[0].checked=false;inputs[0].onchange();
assert.equal(button.disabled,false);
button.onclick();
assert.equal(f.successes.defender[0].status,'unresolved');
assert.equal(f.successes.defender[1].status,'blocked');
f=make();
api.showFightBlockSelection(f,'attacker','own','enemy0');
inputs.forEach(i=>{i.checked=false;i.onchange()});
assert.equal(button.disabled,true,'no target selected should disable action');
// More than two legal enemies: preserve the initial choice; do not guess a second.
f=make('critical',['normal','critical','normal']);
api.showFightBlockSelection(f,'attacker','own','enemy1');
assert.deepEqual(inputs.map(i=>i.checked),[false,true,false]);
inputs[0].checked=true;inputs[0].onchange();
inputs[2].checked=true;inputs[2].onchange();
assert.deepEqual(inputs.map(i=>i.checked),[true,true,false],'cannot exceed capacity');
button.onclick();
assert.deepEqual(f.history[0].blockedSuccessIds,['enemy0','enemy1']);
// One legal target is selected automatically, even if the suggested target is stale.
f=make('normal',['normal','critical'],2);
api.showFightBlockSelection(f,'attacker','own','enemy1');
assert.match(markup,/your <strong>Normal Success<\/strong>/);
assert.deepEqual(inputs.map(i=>i.value),['enemy0']);
assert.deepEqual(inputs.map(i=>i.checked),[true]);
button.onclick();
assert.equal(f.successes.defender[0].status,'blocked');
assert.equal(f.successes.defender[1].status,'unresolved');
// Brutal prevents normal blocker entirely; a critical block is still legal.
f=make('normal',['normal','critical'],2,true);
assert.deepEqual(api.fightBlockTargets(f,'attacker',f.successes.attacker[0]),[]);
f=make('critical',['normal','critical'],2,true);
assert.equal(api.fightBlockTargets(f,'attacker',f.successes.attacker[0]).length,2);
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_release_and_shared_fight_flow_remain_intact():
    assert tuple(map(int,CURRENT_APP_VERSION.split("."))) >= (10,1,2)
    assert "function shieldBlockCapacity(participant)" in APP
    assert "function soloNpoFightDecision(fight,role)" in APP
    assert "function experimentalActionFirstFightHtml(fight,role,participant,actions,capacity)" in APP
    assert "if(commitFightBlock(fight,role,blockerId,selected))renderFightResolution()" in APP
    assert "const defaultIds=legal.length<=capacity" in APP
    assert "const preselected=new Set(defaultIds);" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"app.js?v={CURRENT_APP_VERSION}" in html
    assert f"styles.css?v={CURRENT_APP_VERSION}" in html
    assert f"V{CURRENT_APP_VERSION}" in html
