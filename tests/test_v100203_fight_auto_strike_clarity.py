"""v10.0.203: show why automatic Fight strikes eliminate an NPO, without changing damage rules."""
import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text()
CSS=(ROOT/"styles.css").read_text()

def js(src):
    p=subprocess.run(["node","-e",src],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr or p.stdout

def test_three_successes_critical_four_then_two_automatic_normals():
    js(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function commitFightStrike('),b=s.indexOf('  function soloNpoFightDecision(',a);
const ctx={
  unresolvedFightSuccesses:(f,r)=>f.successes[r].filter(x=>x.status==='unresolved'),
  otherFightRole:r=>r==='attacker'?'defender':'attacker',
  isDeathwatchPlayerTeam:()=>false,pendingPlayerNpoFightIncapacitation:()=>false,
  setFightOperativeWounds:()=>{},resolveFightShock:()=>null,
  advanceFightTurn:f=>{let other=f.turn==='attacker'?'defender':'attacker';
    if(f.successes[other].some(x=>x.status==='unresolved'))f.turn=other;
    else if(!f.successes[f.turn].some(x=>x.status==='unresolved'))f.completed=true;},
  qualifyingWhirlingStrike:()=>false,qualifyingHorrifyingFlaying:()=>false,
  state:{roster:[]},save:()=>{}
};
const commit=new Function('ctx','with(ctx){'+s.slice(a,b)+'return commitFightStrike;}')(ctx);
const fight={id:'f',turn:'attacker',history:[],resolutionIndex:0,completed:false,ruleTriggers:{},
  attacker:{id:'horde-slayer',side:'player',profile:{normal:3,crit:4},wounds:18},
  defender:{id:'necron',side:'npo',profile:{normal:3,crit:4},wounds:9},
  successes:{attacker:[
    {id:'crit',kind:'critical',status:'unresolved'},
    {id:'normal1',kind:'normal',status:'unresolved'},
    {id:'normal2',kind:'normal',status:'unresolved'}],defender:[]}};
assert(commit(fight,'attacker','crit'));
assert.equal(fight.defender.wounds,5);
assert(commit(fight,'attacker','normal1',{automatic:true}));
assert.equal(fight.defender.wounds,2);
assert(commit(fight,'attacker','normal2',{automatic:true}));
assert.equal(fight.defender.wounds,0);
assert.equal(fight.completed,true);
assert.deepEqual(fight.history.map(x=>x.damage),[4,3,3]);
assert.deepEqual(fight.history.map(x=>x.before-x.after),[4,3,2]);
assert.deepEqual(fight.history.map(x=>!!x.automatic),[false,true,true]);
assert.equal(fight.history.reduce((total,x)=>total+x.before-x.after,0),9);
""")

def test_preview_explains_follow_up_but_not_mixed_strikes_or_standard():
    js(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function experimentalFightAutomaticStrikePreview('),
      b=s.indexOf('  function experimentalFightBlockUnavailableHtml(',a);
let on=true;
const ctx={
  experimentalFeaturesEnabled:()=>on,isPvpMode:()=>false,
  otherFightRole:r=>r==='attacker'?'defender':'attacker',
  titleCaseRuleId:x=>x.charAt(0).toUpperCase()+x.slice(1),
  unresolvedFightSuccesses:(f,r)=>f.successes[r].filter(x=>x.status==='unresolved')
};
const preview=new Function('ctx','with(ctx){'+s.slice(a,b)+'return experimentalFightAutomaticStrikePreview;}')(ctx);
const f={attacker:{profile:{normal:3,crit:4}},defender:{wounds:9},successes:{
 attacker:[{id:'crit',kind:'critical',status:'unresolved'},
  {id:'n1',kind:'normal',status:'unresolved'},{id:'n2',kind:'normal',status:'unresolved'}],
 defender:[]}};
assert(preview(f,'attacker',f.successes.attacker[0],4).includes('2 Normal Successes auto-strike for 3 each'));
assert(preview(f,'attacker',f.successes.attacker[0],4).includes('Combined damage 10 eliminates this 9-wound target'));
assert.equal(preview(f,'attacker',f.successes.attacker[1],3),'');
f.successes.defender=[{id:'enemy',kind:'normal',status:'unresolved'}];
assert.equal(preview(f,'attacker',f.successes.attacker[0],4),'');
f.successes.defender=[];on=false;
assert.equal(preview(f,'attacker',f.successes.attacker[0],4),'');
""")

def test_result_breakdown_distinguishes_chosen_automatic_and_effective_damage():
    js(r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),s=fs.readFileSync('app.js','utf8');
const a=s.indexOf('  function experimentalFightAutomaticStrikeResultHtml('),
      b=s.indexOf('  function renderFightResult(',a);
let on=true,pvp=false;
const ctx={experimentalFeaturesEnabled:()=>on,isPvpMode:()=>pvp,
  document:{documentElement:{dataset:{ui:'tomb'}}},
  escapeHtml:String,titleCaseRuleId:x=>x.charAt(0).toUpperCase()+x.slice(1)};
const html=new Function('ctx','with(ctx){'+s.slice(a,b)+'return experimentalFightAutomaticStrikeResultHtml;}')(ctx);
const result={attackerName:'Horde-Slayer',defenderName:'Necron Warrior 2',fightHistory:[
 {type:'strike',role:'attacker',successKind:'critical',damage:4,before:9,after:5},
 {type:'strike',role:'attacker',successKind:'normal',damage:3,before:5,after:2,automatic:true},
 {type:'strike',role:'attacker',successKind:'normal',damage:3,before:2,after:0,automatic:true}]};
const output=html(result);
assert(output.includes('STRIKES RESOLVED'));
assert(output.includes('automatically resolved 2 additional Strikes'));
assert(output.includes('CHOSEN · Horde-Slayer · Critical Strike'));
assert.equal((output.match(/AUTO · Horde-Slayer · Normal Strike/g)||[]).length,2);
assert(output.includes('4 damage · 9 → 5 wounds'));
assert(output.includes('3 damage · 5 → 2 wounds'));
assert(output.includes('2 applied (3 potential) · 2 → 0 wounds'));
assert.equal(html(result),output);
on=false;assert.equal(html(result),'');
on=true;pvp=true;assert.equal(html(result),'');
pvp=false;assert.equal(html({...result,fightHistory:result.fightHistory.slice(0,1)}),'');
""")

def test_saved_game_and_standard_mode_compatibility():
    assert "function commitFightStrike(fight,role,successId,{automatic=false}={})" in APP
    assert "...(automatic?{automatic:true}:{})" in APP
    assert "history:Array.isArray(fight.history)?fight.history.filter(isRecord).map(item=>({...item})):[]" in APP
    assert "if(human&&automaticStrikes){commitFightStrike(fight,role,automaticStrikes[0].id,{automatic:true});" in APP
    assert "experimentalFightAutomaticStrikeResultHtml(result)" in APP
    assert 'html[data-ui="tomb"][data-experimental="on"] .fight-auto-strike-result' in CSS
    assert CURRENT_APP_VERSION=="10.0.203"
    assert "const APP_VERSION = '10.0.203';" in APP
    assert "const APP_VERSION = '10.0.203';" in (ROOT/"service-worker.js").read_text()
    assert "V10.0.203" in (ROOT/"index.html").read_text()
