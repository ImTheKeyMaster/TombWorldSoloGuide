'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const source=fs.readFileSync('app.js','utf8');
const block=(a,b)=>source.slice(source.indexOf(a),source.indexOf(b,source.indexOf(a)));
const start=block('let reconSetupFinishedFor=null;','async function continueTurningPointStart()');
const card=block('function nextStepCard(){','function missionStrategyPending()');
const make=new Function('ctx',`
const {state,save,render,showReconTracking,reconTrackingEnabled,modal,closeModal,showToast,missionEngine,threatGrade,destroyedNpoCount,processReadyStep,applyMissionReadyHooks,finishTurningPointStart,console}=ctx;
${start}
${card}
return {startTurningPoint,nextStepCard};
`);
function fixture({experimental=true,scan='ok',turn=0}={}){
  const state={turningPoint:turn,phase:'between',npoRuleState:{},playerCount:5,playerCasualtyIds:[],threat:0};
  const calls={scan:0,ready:0,finish:0,notices:0,close:0,warn:0};
  const modal={open:false};
  const api=make({state,save:()=>{},render:()=>{},reconTrackingEnabled:()=>experimental,modal,
    showReconTracking:()=>{calls.scan++;if(scan==='throw'){modal.open=true;throw Error('fixture failure');}return scan==='ok';},
    closeModal:()=>{calls.close++;modal.open=false;},showToast:()=>calls.notices++,console:{warn:()=>calls.warn++},
    missionEngine:()=>null,threatGrade:()=>0,destroyedNpoCount:()=>0,
    processReadyStep:()=>calls.ready++,applyMissionReadyHooks:async()=>true,finishTurningPointStart:async()=>{calls.finish++;state.phase='strategy';}});
  return {state,calls,...api};
}
(async()=>{
  let t=fixture();assert(t.nextStepCard().includes('startTpWithoutRecon'));
  await t.startTurningPoint();assert.equal(t.state.turningPoint,0);assert.equal(t.calls.scan,1);assert.equal(t.calls.ready,0);
  await t.startTurningPoint({skipRecon:true});assert.equal(t.state.turningPoint,1);assert.equal(t.calls.finish,1);assert.equal(t.calls.scan,1);
  for(const scan of ['throw','missing']){
    t=fixture({scan});await t.startTurningPoint();assert.equal(t.state.turningPoint,1);assert.equal(t.calls.notices,1);assert.equal(t.calls.ready,1);assert.equal(t.calls.finish,1);assert.equal(t.calls.warn,1);assert.equal(t.calls.close,scan==='throw'?1:0);
  }
  t=fixture({experimental:false});assert(!t.nextStepCard().includes('startTpWithoutRecon'));await t.startTurningPoint();assert.equal(t.state.turningPoint,1);assert.equal(t.calls.scan,0);
  t=fixture({turn:1});assert(!t.nextStepCard().includes('startTpWithoutRecon'));await t.startTurningPoint();assert.equal(t.state.turningPoint,2);assert.equal(t.calls.scan,0);
  t=fixture();await Promise.all([t.startTurningPoint({skipRecon:true}),t.startTurningPoint({skipRecon:true})]);assert.equal(t.state.turningPoint,1);assert.equal(t.calls.finish,1);
  console.log('Recon setup recovery regression checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
