"""Runtime regression checks for operatives eliminated during an active action.

Execute with: python -m pytest tests/test_v100138_eliminated_activation.py
"""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_eliminated_operative_commits_current_action_and_finishes_activation():
    run_node(r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const src = fs.readFileSync('app.js','utf8');
function section(begin,end) {
  const start=src.indexOf(begin);
  const stop=src.indexOf(end,start+begin.length);
  assert(start>=0 && stop>start,'Missing source section: '+begin);
  return src.slice(start,stop);
}
const code=[
  section('  function activePlayerActivation(){','  function beginPlayerActivation('),
  section('  function commitHumanPlayerAction(','  function buildThreatCheckResult('),
  section('  async function completeHumanPlayerActivation(){','  const PLAYER_ACTION_COSTS='),
  section('  async function completePlayerActivation(stage={}){','  function npoName(')
].join('\n');

function scenario({wounds=0,casualty=true,pendingAction='melee',active=true,attack='melee',hot=false}={}) {
  const id='confidant', events=[];
  const activation={
    side:'player',operativeId:id,activationId:'act:confidant',
    committed:false,completed:false,remainingAp:2,startingAp:2,
    actionSequence:0,completedActionIds:[],resolvedActions:[],
    pendingAction:{activationId:'act:confidant',actionId:pendingAction,actionSequence:1,cost:1}
  };
  const state={
    missionId:'destroy-sarcophagus',threat:0,
    lastActivation:active?activation:null,combatState:{side:'player',stage:{}},
    playerCasualtyIds:casualty?[id]:[],playerActivatedIds:casualty?[id]:[],
    playerWounds:{confidant:wounds},activationNumber:3,activationHistory:[],
    playerReady:0,playerActivated:0,nextSide:'player',
    hotResolution:hot?{attackerSide:'player',attackerId:id,incapacitated:true}:null,
    missionActionContext:null
  };
  const result={
    attackType:attack,targetId:'tomb-crawler',targetName:'Tomb Crawler',
    damage:2,damageDealt:2,damageSuffered:7,committed:true,before:14,after:12
  };
  const stage={
    sequential:true,playerOperativeId:id,humanActionId:attack,
    humanActionName:attack==='melee'?'Fight':'Shoot',
    [attack]:true,threatRolls:{},pendingMeleeResults:attack==='melee'?[result]:[],
    pendingShootResults:attack==='shoot'?[result]:[]
  };
  const ctx={
    state,
    normalizeImpossiblePlayerCombat:s=>s,
    remainingPlayerOperatives:()=>wounds>0&&!casualty?[id]:[],
    playerCurrentWounds:id=>state.playerWounds[id],
    playerName:id=>id,
    pendingAttackResults:(s,type)=>type==='melee'?s.pendingMeleeResults||[]:s.pendingShootResults||[],
    playerOperativesRemaining:()=>wounds>0&&!casualty?1:0,
    save:()=>events.push('save'),
    acknowledgeCurrentDiceRequest:()=>events.push('acknowledge'),
    unawakenedScoutRooms:()=>[],
    log:message=>events.push('log'),
    expireActivationEffects:()=>events.push('expire'),
    advanceAfterActivation:side=>{state.nextSide='npo';events.push('advance:'+side)},
    closeModal:()=>events.push('close'),
    executeMissionLifecycleHook:async name=>events.push('hook:'+name),
    checkGameEnd:()=>false,
    render:()=>events.push('render'),
    renderHumanPlayerActionPicker:()=>events.push('SHOW_AP_SCREEN'),
    setThreat:n=>{state.threat+=n},
    missionActivationId:()=>activation.activationId,
    showToast:message=>events.push('TOAST:'+message),
    setNextActivation:side=>{state.nextSide=side},
    renderThreatCheckResult:()=>events.push('threat-check')
  };
  const handlers=new Function('ctx','with(ctx){'+code+'\nreturn {completePlayerActivation,finishingCurrentHumanPlayerAction};}')(ctx);
  return {handlers,stage,state,activation,events};
}

(async()=>{
  // Exact regression: a player dies during their own Fight, after spending one AP.
  const dead=scenario();
  assert(dead.handlers.finishingCurrentHumanPlayerAction(dead.stage,'confidant'));
  await dead.handlers.completePlayerActivation(dead.stage);
  await Promise.resolve();
  assert.equal(dead.activation.resolvedActions.length,1);
  assert.equal(dead.activation.resolvedActions[0].name,'Fight');
  assert.equal(dead.activation.committed,true);
  assert.equal(dead.state.lastActivation,null);
  assert.equal(dead.state.activationNumber,4);
  assert.equal(dead.state.playerActivatedIds.length,1);
  assert.equal(dead.state.activationHistory.length,1);
  assert.equal(dead.state.nextSide,'npo');
  assert.equal(dead.state.threat,1);
  assert(!dead.events.some(event=>event.startsWith('TOAST:')));
  assert(!dead.events.includes('SHOW_AP_SCREEN'));

  // A lethal shooting side-effect (Hot or retaliation) must finish identically.
  const shot=scenario({attack:'shoot',hot:true});
  await shot.handlers.completePlayerActivation(shot.stage);
  await Promise.resolve();
  assert.equal(shot.activation.resolvedActions[0].name,'Shoot');
  assert.equal(shot.state.lastActivation,null);
  assert.equal(shot.state.nextSide,'npo');

  // Surviving attackers still return to their remaining-AP choices.
  const healthy=scenario({wounds:4,casualty:false});
  await healthy.handlers.completePlayerActivation(healthy.stage);
  assert.equal(healthy.activation.committed,false);
  assert.equal(healthy.activation.remainingAp,1);
  assert(healthy.events.includes('SHOW_AP_SCREEN'));

  // A stale action must not be mistaken for the operative's current action.
  const mismatch=scenario({pendingAction:'move'});
  assert(!mismatch.handlers.finishingCurrentHumanPlayerAction(mismatch.stage,'confidant'));
  await mismatch.handlers.completePlayerActivation(mismatch.stage);
  await Promise.resolve();
  assert.equal(mismatch.state.lastActivation,null);
  assert(!mismatch.events.includes('SHOW_AP_SCREEN'));

  // Invalid attempts to start/resume without a current activation remain blocked.
  const invalid=scenario({active:false});
  await invalid.handlers.completePlayerActivation(invalid.stage);
  assert(invalid.events.some(event=>event.startsWith('TOAST:')));
  process.stdout.write('activation regression checks passed\n');
})().catch(error=>{console.error(error);process.exitCode=1});
""")


def test_eliminated_operative_cannot_reopen_ap_selection_after_resume():
    run_node(r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const src=fs.readFileSync('app.js','utf8');
const first='  function renderHumanPlayerActionPicker(){';
const last='  function playerSequentialStage(';
const begin=src.indexOf(first),end=src.indexOf(last,begin);
assert(begin>0&&end>begin);
const fragment=src.slice(begin,end);
const events=[];
const ctx={
  activePlayerActivation:()=>({operativeId:'confidant',remainingAp:1}),
  playerActivationOperativeEliminated:()=>true,
  completeHumanPlayerActivation:()=>{events.push('complete');return Promise.resolve();},
  showPlayerActivation:()=>events.push('pick-another-operative'),
  renderHumanActivationShell:()=>{throw Error('Eliminated operative offered AP actions')},
  state:{}
};
const run=new Function('ctx','with(ctx){'+fragment+'\nreturn renderHumanPlayerActionPicker;}')(ctx);
run();
assert.deepEqual(events,['complete']);
""")
