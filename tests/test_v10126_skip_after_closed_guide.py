"""Regression: Skip Remaining works after closing a clean player activation guide."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"app.js").read_text(encoding="utf-8")
INDEX=(ROOT/"index.html").read_text(encoding="utf-8")
WORKER=(ROOT/"service-worker.js").read_text(encoding="utf-8")
README=(ROOT/"README.md").read_text(encoding="utf-8")


def test_skip_after_close_and_active_action_safety():
    # Execute the production skip helpers and real alternating-side scheduler,
    # not a hand-coded substitute for the app's conditions.
    js=r"""
const fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const extract=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
const visibility=extract('function canSkipUnstartedPlayerActivation()','function destroyedNpoCount()');
const scheduler=extract('function setNextActivation(preferredSide)','const GRADE_CONFIG');
const skip=extract('let skipRemainingActivationsPending=false;','function showCeaselessScuttling()');
const harness=new Function('ctx',`
const {state,readyNpos,playerOperativesRemaining,isPvpMode,selectedPlayerTeamName,
 escapeHtml,activePlayerActivation,remainingPlayerOperatives,showModal,$,log,
 save,closeModal,render,playerName,resumeCheckpointedGameplayContext}=ctx;
const activationSideName=side=>side==='npo'?'Necron':selectedPlayerTeamName();
const activationModelLabel=(side,{plural=false}={})=>side==='npo'
 ?(plural?'Necrons':'a Necron'):(plural?'Deathwatch Operatives':'a Deathwatch Operative');
${visibility}
${scheduler}
${skip}
return {canSkipRemainingActivations,confirmSkipRemainingActivations,skipRemainingActivations,
 skipRemainingActivationsControl};
`);
function scenario({actions=[],pending=null,sequence=0,side='player',transient=null}={}){
  const saved={writes:0,rendered:0,modals:[],logs:[],resumes:0};
  const state={
    phase:'firefight',completed:false,gameEnd:false,nextSide:side,
    lastActivation:side==='player'?{side:'player',operativeId:'disruptor',committed:false,
      completed:false,resolvedActions:actions,completedActionIds:actions.map(a=>a.id),
      pendingAction:pending,actionSequence:sequence}:null,
    playerActivated:4,npoActivated:2,
    playerActivatedIds:['headtaker','sergeant','aegis','gunner'],playerReady:2,
    activationFinishedForTurningPoint:{player:false,npo:false},
    pendingDice:null,combatState:transient,fightState:null,
    missionActionContext:null,weaponRuleResolution:null,hotResolution:null
  };
  const all=['headtaker','sergeant','aegis','gunner','disruptor','demolisher'];
  const remaining=()=>all.filter(id=>!state.playerActivatedIds.includes(id));
  const npos=Array.from({length:8},(_,i)=>({id:'necron-'+i,ready:true}));
  const nodes={};
  const ctx={
    state,readyNpos:()=>npos.filter(n=>n.ready),playerOperativesRemaining:()=>remaining().length,
    isPvpMode:()=>false,selectedPlayerTeamName:()=> 'Deathwatch',escapeHtml:String,
    activePlayerActivation:()=>state.lastActivation?.side==='player'&&!state.lastActivation.committed
      ?state.lastActivation:null,
    remainingPlayerOperatives:remaining,showModal:(title,message)=>saved.modals.push({title,message}),
    $:selector=>nodes[selector]??={},log:msg=>saved.logs.push(msg),
    save:()=>saved.writes++,closeModal:()=>{},render:()=>saved.rendered++,
    playerName:id=>id==='disruptor'?'Disruptor':id,
    resumeCheckpointedGameplayContext:()=>saved.resumes++
  };
  return {app:harness(ctx),state,npos,saved,nodes};
}
const check=(condition,msg)=>{if(!condition)throw Error(msg);};
const clean=scenario();
check(clean.app.canSkipRemainingActivations(),'Untouched activation should permit Skip Remaining');
check(clean.app.skipRemainingActivationsControl().includes('Skip Remaining Deathwatch'),
  'Skip control should be visible for a clean active player activation');
clean.app.confirmSkipRemainingActivations();
check(clean.saved.modals.at(-1).message.includes('current, untouched activation'),
  'Confirmation should disclose that current activation is skipped');
check(clean.app.skipRemainingActivations(),'Confirmed skip was ignored');
check(clean.state.lastActivation===null,'Untouched locked activation left active');
check(clean.state.playerReady===0&&clean.state.playerActivatedIds.includes('disruptor')
  &&clean.state.playerActivatedIds.includes('demolisher'),'Remaining operatives were not skipped');
check(clean.state.nextSide==='npo'&&clean.state.phase==='firefight','Necrons did not continue');
check(clean.state.playerActivated===4&&clean.npos.every(n=>n.ready),
  'Skip changed completed activation count or Necron readiness');
check(clean.saved.writes===1&&clean.saved.rendered===1,'Skip did not persist and render once');

const acted=scenario({actions:[{id:'move'}],sequence:1});
check(!acted.app.canSkipRemainingActivations(),'Recorded player actions must block discard');
acted.app.confirmSkipRemainingActivations();
check(acted.saved.modals.at(-1).title==='Activation in Progress',
  'No explanatory dialog after attempting an unsafe skip');
check(acted.app.skipRemainingActivations()===false&&acted.saved.writes===0
  &&acted.state.lastActivation,'Recorded activation was silently discarded');
acted.nodes['#resumeActivationBeforeSkip'].onclick();
check(acted.saved.resumes===1,'Resume Activation button is not wired');

const pending=scenario({pending:{id:'shoot'}});
check(!pending.app.canSkipRemainingActivations(),'Pending player action must block skip');
const combat=scenario({transient:{side:'player'}});
check(!combat.app.canSkipRemainingActivations(),'Unresolved combat must still block skip');

const necrons=scenario({side:'npo'});
check(necrons.app.canSkipRemainingActivations(),'Original Necron skip eligibility regressed');
necrons.app.skipRemainingActivations();
check(necrons.npos.every(n=>!n.ready)&&necrons.state.nextSide==='player'
  &&necrons.state.activationFinishedForTurningPoint.npo,'Necron skip flow changed');
console.log('Skip after Close Guide and dirty activation guards passed');
"""
    result=subprocess.run(["node","-e",js],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr or result.stdout


def test_release_version_and_save_key_unchanged():
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
