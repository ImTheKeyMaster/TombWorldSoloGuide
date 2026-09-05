from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
MISSION = (ROOT / "Missions" / "05-scout-sub-crypt.json").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_and_initial_scout_state_are_current():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 47)
    assert '"formula": "0"' in MISSION
    factory = section("const missionStateFactories", "function eventDefinition")
    assert "awakenedRooms:{}" in factory
    assert "scoutedRoomIds:[]" in factory
    assert "pendingAwakening:null" in factory


def test_room_lifecycle_and_pending_selection_are_persisted_separately():
    normalization = section("function normalizeMissionState", "const inertVariantHooks")
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    for field in ("roomId", "awakened:true", "scouted:", "awakeningTurningPoint", "awakeningSource", "generatedNpoIds", "awakeningRoll"):
        assert field in normalization + awakening
    assert "pendingAwakening" in normalization
    assert "state.missionState.pendingAwakening=null" in awakening
    assert "scoutedRoomIds" not in awakening


def test_open_and_entry_use_one_immediate_awakening_transaction():
    picker = section("function unawakenedScoutRooms", "async function performAwakenRoom")
    commit = section("function commitHumanPlayerAction", "function continueAfterCommittedHumanAction")
    shell = section("function renderHumanActivationShell", "function canCommitHumanPlayerAction")
    assert "DID THIS OPEN A ROOM FOR THE FIRST TIME?" in picker
    assert "YES... SELECT ROOM" in picker
    assert "WHICH ROOM WAS ENTERED FOR THE FIRST TIME?" in picker
    assert "FIRST ROOM ENTRY" in shell
    assert "['hatch','breach'].includes(pending.actionId)" in commit
    assert "showFirstOpenPrompt" in commit
    assert "beginRoomAwakeningSelection('first-entry')" in APP


def test_spawn_formula_uses_committed_d3_current_grade_and_both_caps():
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    assert "await missionDiceTotal(outcome,'awakenRoll'" in awakening
    assert "grade=threatGrade(),uncappedCount=awakenRoll+grade,requestedCount=Math.min(5,uncappedCount)" in awakening
    assert awakening.count("threatGrade()") == 1
    assert "activeNpos().length<MAX_NPOS" in awakening
    assert "availableGenerationResult()" in awakening
    assert "resolveVariantNpoRequest" in awakening
    assert "sourceRoomId=roomId" in awakening


def test_ready_dormant_and_live_scheduler_integration():
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    threat = section("function setThreat", "function escapeHtml")
    scheduler = section("function setNextActivation", "function advanceAfterActivation")
    assert "ready:state.threat>0,dormant:state.threat===0" in awakening
    assert "state.activationFinishedForTurningPoint.npo=false" in awakening
    assert "npo.dormant=false;npo.ready=true" in threat
    assert "Threat is no longer 0. Dormant NPOs became Ready." in threat
    assert "readyNpos().length>0" in scheduler
    assert "readyNpoCountAtFirefightStart" not in APP


def test_cleanup_is_display_only_and_scout_room_remains_the_only_scout_commit():
    display = section("scout:(engine,progress,{readOnly", "regroup:(engine,progress,{readOnly")
    scout = section("async function performScoutRoom", "async function performLocateItem")
    assert "Unopened" in display
    assert "Awakened · Unscouted" in display
    assert "when the room is clear on the tabletop" in display
    assert "data-awaken-room" not in display
    assert "First Open / Entry" not in display
    assert "Correct Legacy Placement" in display
    assert "scoutedRoomIds" in scout
    assert "commitHumanPlayerAction" in scout


def test_awakening_battle_record_is_explicit_and_idempotent():
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    assert "if(state.missionState?.awakenedRooms?.[roomId])" in awakening
    assert "Scout Sub-Crypt awakening roll: D3" in awakening
    assert "is Awakened and remains Unscouted" in awakening
    assert "blocked by the NPO cap or available model inventory" in awakening


def test_selected_room_transaction_resumes_before_selection_and_does_not_infer_clearance():
    normalization = section("function normalizeMissionState", "const inertVariantHooks")
    resume = section("async function resumeCheckpointedGameplayContext", "async function missionDiceTotal")
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    eligibility = section("function scoutRoomState", "function eligibleScoutRooms")
    assert "['select','resolving'].includes(raw.pendingAwakening.phase)" in normalization
    assert resume.index("resumeMissionActionContext()") < resume.index("pendingAwakening?.phase==='select'")
    assert "phase:'resolving',roomId" in awakening
    assert "activeNpos" not in eligibility
    assert "operativeIds.some" not in eligibility


def test_exact_breach_awakening_regression_executes_current_scheduler_state():
    awakening_helpers = "function unawakenedScoutRooms" + section(
        "function unawakenedScoutRooms", "async function performAuspexCalibration"
    )
    scheduler = "function setNextActivation" + section(
        "function setNextActivation", "function advanceAfterActivation"
    )
    script = f"""
const assert=require('assert').strict;
const MAX_NPOS=10;
const rooms=[1,2,3].map(number=>({{id:`room-${{number}}`,label:`Eligible Room ${{number}}`}}));
let state={{
  missionId:'scout-sub-crypt',turningPoint:1,threat:1,roster:[],journal:[],
  missionState:{{awakenedRooms:{{}},scoutedRoomIds:[],pendingAwakening:{{phase:'select',source:'breach',operativeId:'aegis'}}}},
  missionActionContext:null,activationFinishedForTurningPoint:{{player:false,npo:false}},nextSide:'player'
}};
let generated=0;
const missionEngine=()=>({{type:'scout',rooms,actions:{{awakenRoom:'awakenRoom'}}}});
const missionLifecycleContext=()=>({{}});
const objectiveEngine={{executeMissionAction:async()=>({{results:{{awakenRoll:{{dice:[2]}}}}}})}};
const runMissionEvent=callback=>callback();
const missionDiceTotal=async()=>2;
const threatGrade=()=>state.threat===0?0:1;
const activeNpos=()=>state.roster.filter(npo=>npo.deployed&&npo.wounds>0);
const readyNpos=()=>activeNpos().filter(npo=>npo.ready&&!npo.dormant);
const availableGenerationResult=()=>({{type:'Necron Warrior',weaponId:'gauss-flayer'}});
const replaceMissionRequestedNpo=value=>value;
const resolveVariantNpoRequest=value=>value;
const createNpo=(type,name,options)=>({{id:`npo-${{++generated}}`,type,name,wounds:10,battlefieldState:'deployed',...options}});
const save=()=>true;
const acknowledgeCurrentDiceRequest=()=>{{}};
const activePlayerActivation=()=>({{activationId:'activation-1'}});
const renderHumanPlayerActionPicker=()=>{{}};
const closeModal=()=>{{}};
const render=()=>{{}};
const playerName=()=> 'Aegis';
const log=text=>state.journal.unshift({{text}});
const playerOperativesRemaining=()=>0;
{awakening_helpers}
{scheduler}
(async()=>{{
  await performAwakenRoom('room-1');
  assert.equal(state.roster.length,3);
  assert.equal(readyNpos().length,3);
  assert.equal(state.missionState.awakenedRooms['room-1'].awakeningRoll,2);
  assert.equal(state.missionState.awakenedRooms['room-1'].threatGrade,1);
  assert.equal(state.missionState.awakenedRooms['room-1'].count,3);
  assert.equal(state.missionState.awakenedRooms['room-1'].scouted,false);
  assert.deepEqual(state.missionState.scoutedRoomIds,[]);
  state.activationFinishedForTurningPoint.player=true;
  assert.equal(setNextActivation('npo'),'npo');
  assert.equal(state.phase,undefined);
  assert.equal(state.nextSide,'npo');
}})().catch(error=>{{console.error(error);process.exitCode=1;}});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_variant_generation_and_cleanup_pending_guard_are_preserved():
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    cleanup = section("function nextStepCard", "function missionStrategyPending")
    bindings = section("function bindPlay", "let skipRemainingActivationsPending")
    assert "setupCrownworldCrawlerPair" in awakening
    assert "pair.npos.forEach" in awakening
    assert "ready:state.threat>0,dormant:state.threat===0" in awakening
    assert "sourceRoomId:roomId" in awakening
    assert "awakeningPending=Boolean(state.missionState?.pendingAwakening)" in cleanup
    assert "Room awakening incomplete." in cleanup
    assert 'id="resolvePendingAwakening"' in cleanup
    assert "showAwakenedRoomSelector" in bindings
    assert "if(state.missionState?.pendingAwakening)return" in bindings


def test_legacy_placement_recovery_applies_current_readiness_and_provenance():
    bindings = section("function bindMissionProgressControls", "async function narrateVisibleGradeMilestone")
    assert "npo.ready=state.threat>0" in bindings
    assert "npo.dormant=state.threat===0" in bindings
    assert "npo.sourceRoomId=npo.sourceRoomId||button.dataset.confirmRoomPlacement" in bindings
    assert "state.activationFinishedForTurningPoint.npo=false" in bindings


def test_room_awakening_continuation_does_not_enter_activation_from_cleanup():
    flow = section("function continueAfterRoomAwakeningBookkeeping", "function beginRoomAwakeningSelection")
    assert "if(activePlayerActivation())return renderHumanPlayerActionPicker()" in flow
    assert "closeModal();render();return true" in flow
    assert "cancelPendingAwakening" in flow
    assert "state.missionState.pendingAwakening=null;save();continueAfterRoomAwakeningBookkeeping()" in flow
