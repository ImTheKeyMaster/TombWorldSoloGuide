"""v10.1.28: Resume the Strategy Phase when reinforcements outnumber reserve models."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def run_node(script):
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=20
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


PICKER = source("function randomReinforcement", "function nextNpo")
REINFORCEMENT = source("function processReinforcementStage", "function reinforcementTriggered")
RESUME = source("async function finishTurningPointStart", "function completeStrategyStage")

FIXTURE = r"""
const assert=require('node:assert/strict');
const MAX_NPOS=10;
const npoGenerationTable=[{type:'Necron Warrior',weaponIds:['gauss-flayer']}];
let state;
let creationAttempts=0;
let variantReplacementType=null;
let saves=0, renders=0;
const journal=[];
const experimentalNpoMiniatureReuseEnabled=()=>false;
const gradeConfig=grade=>({reinforcements:grade});
const threatGrade=()=>3;
const reinforcementTriggered=()=>state.strategyPipeline.current==='reinforcement'&&state.turningPoint>1&&state.strategyData.grade>0;
const activeNpos=()=>state.roster.filter(npo=>npo.battlefieldState==='deployed'&&npo.wounds>0);
const reserveNpos=()=>state.roster.filter(npo=>npo.battlefieldState==='reserve'&&npo.wounds>0);
const npoInventory=()=>({'Necron Warrior':{remaining:0},'Royal Warden':{remaining:0}});
const rollNpo=()=>({type:'Necron Warrior',weaponId:'gauss-flayer'});
const roll=()=>1;
const generatedWeaponId=()=> 'gauss-flayer';
const tombWorldVariantHook=(_,request)=>variantReplacementType?{...request,type:variantReplacementType}:request;
const resolveVariantNpoRequest=request=>request;
const lowestAvailableNpoInstances=()=>[];
const createNpo=()=>{creationAttempts++;throw new Error('No physical model remains available');};
const commitNpoRoster=()=>true;
const completeStrategyStage=(stage,next)=>{state.strategyPipeline.completed.push(stage);state.strategyPipeline.current=next;};
const save=()=>{saves++;};
const render=()=>{renders++;};
const log=message=>journal.push(message);
function reset(){
  state={
    phase:'strategy',strategyStage:'event',turningPoint:5,threat:15,
    roster:[
      {id:'warrior-1',type:'Necron Warrior',wounds:9,battlefieldState:'reserve'},
      {id:'warrior-2',type:'Necron Warrior',wounds:9,battlefieldState:'reserve'}
    ],
    strategyPipeline:{current:'reinforcement',completed:['ready','initiative','event']},
    strategyData:{
      grade:3,eventPending:false,events:[
        {instanceId:'countertemporal-shifting-1',status:'resolved'},
        {instanceId:'reanimation-protocols-1',status:'resolved'}
      ],reinforcements:[]
    },
    reinforcementState:{status:'idle',operativeIds:[],blockedOperativeIds:[]},
    startingNpoGeneration:{reserveNpoIds:['warrior-1','warrior-2']},
    newIds:[]
  };
  creationAttempts=0;variantReplacementType=null;saves=0;renders=0;journal.length=0;
}
"""
CODE = FIXTURE + "\n" + PICKER + "\n" + REINFORCEMENT + "\n" + RESUME


def test_two_reserve_necrons_not_allocated_multiple_times_for_grade_three():
    run_node(CODE + r"""
reset();
processReinforcementStage();
assert.deepEqual(state.reinforcementState.operativeIds,['warrior-1','warrior-2']);
assert.equal(state.strategyData.actualReinforcements,2);
assert.equal(state.reinforcementState.blocked,1);
assert.equal(state.reinforcementState.blockedByInventory,1);
assert.equal(state.reinforcementState.status,'placement');
assert.equal(state.strategyPipeline.current,'complete');
assert.equal(creationAttempts,0);
assert.equal(new Set(state.reinforcementState.operativeIds).size,2);
assert.deepEqual(state.startingNpoGeneration.reserveNpoIds,[]);
""")


def test_saved_turning_point_five_with_two_resolved_events_can_resume():
    run_node(CODE + r"""
(async()=>{
  reset();
  const events=JSON.stringify(state.strategyData.events);
  assert.equal(await finishTurningPointStart(),true);
  assert.equal(state.phase,'strategy');
  assert.equal(state.strategyStage,'summary');
  assert.equal(state.strategyPipeline.current,'complete');
  assert.equal(state.strategyData.actualReinforcements,2);
  assert.equal(state.strategyData.blocked,1);
  assert.equal(JSON.stringify(state.strategyData.events),events);
  assert.equal(creationAttempts,0);
  assert.equal(renders,1);
  assert.equal(journal.length,1);
})().catch(error=>{console.error(error);process.exitCode=1;});
""")


def test_unavailable_variant_replacement_blocks_without_corrupting_reserves():
    run_node(CODE + r"""
reset();
variantReplacementType='Royal Warden';
processReinforcementStage();
assert.deepEqual(state.reinforcementState.operativeIds,[]);
assert.equal(state.reinforcementState.blockedByInventory,3);
assert.equal(state.reinforcementState.status,'blocked');
assert.equal(state.strategyPipeline.current,'complete');
assert.equal(creationAttempts,0);
assert.deepEqual(state.startingNpoGeneration.reserveNpoIds,['warrior-1','warrior-2']);
""")


def test_reinforcement_exception_is_caught_and_state_remains_recoverable():
    """Even unexpected generation errors should not become unhandled button failures."""
    run_node(CODE.replace("const threatGrade=()=>3;", "const threatGrade=()=>{throw Error('unexpected');};") + r"""
(async()=>{
  reset();
  assert.equal(await finishTurningPointStart(),false);
  assert.equal(state.strategyStage,'event');
  assert.equal(state.strategyPipeline.current,'reinforcement');
  assert.equal(renders,1);
  assert.equal(saves,1);
})().catch(error=>{console.error(error);process.exitCode=1;});
""")
