from pathlib import Path
import subprocess
import json

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_version_and_save_key_are_consistent():
    assert CURRENT_APP_VERSION == ".".join(("9", "2", str(40 + 4)))
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in index
    assert index.count(f"?v={CURRENT_APP_VERSION}") == 10


def test_scout_status_uses_authoritative_global_blockers_and_ap_priority():
    state = section("function playerHumanActionState", "function renderHumanActivationShell")
    eligibility = section("function scoutRoomState", "function eligibleScoutRooms")
    assert state.index("action.cost>remaining") < state.index("action.id==='scoutRoom'")
    assert "Threat Level must be above 0" in eligibility
    assert "Clear a room first" in eligibility
    assert "All rooms scouted" in eligibility
    assert "'Available'" in eligibility
    assert "No eligible room" not in state


def test_scout_room_state_reacts_to_threat_scouting_and_known_npos():
    helpers = "function scoutRoomState" + section("function scoutRoomState", "async function performScoutRoom")
    script = f"""
const assert=require('assert').strict;
const rooms=[1,2,3].map(number=>({{id:`room-${{number}}`,label:`Room ${{number}}`}}));
let state={{threat:0,missionState:{{awakenedRooms:{{}},scoutedRoomIds:[]}}}},npos=[];
function missionEngine(){{return {{type:'scout',rooms}};}}
function activeNpos(){{return npos.filter(npo=>npo.deployed&&npo.wounds>0);}}
{helpers}
state.missionState.awakenedRooms['room-1']={{placementConfirmed:true,operativeIds:['npo-1']}};
state.missionState.awakenedRooms['room-2']={{placementConfirmed:true,operativeIds:['npo-2']}};
npos=[{{id:'npo-1',deployed:true,wounds:5}},{{id:'npo-2',deployed:false,wounds:0}}];
assert.equal(scoutRoomState().reason,'Threat Level must be above 0');
assert.deepEqual(eligibleScoutRooms(),[]);
state.threat=1;
assert.equal(scoutRoomState().reason,'Available');
assert.deepEqual(eligibleScoutRooms().map(room=>room.id),['room-2']);
npos[1]={{id:'npo-2',deployed:true,wounds:5}};
assert.equal(scoutRoomState().reason,'Clear a room first');
npos[0].wounds=0;
assert.deepEqual(eligibleScoutRooms().map(room=>room.id),['room-1']);
state.missionState.scoutedRoomIds=['room-1','room-2','room-3'];
assert.equal(scoutRoomState().reason,'All rooms scouted');
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_scout_eligibility_uses_tracked_room_npos_not_operative_location():
    eligibility = section("function scoutRoomState", "async function performScoutRoom")
    assert "progress.awakenedRooms?.[room.id]" in eligibility
    assert "awakening.operativeIds.some(id=>activeIds.has(id))" in eligibility
    assert "placementConfirmed" in eligibility
    assert "currentOperative.roomId" not in eligibility
    assert "activation.operativeId" not in eligibility


def test_only_mission_defined_non_drop_zone_rooms_feed_the_picker():
    mission = json.loads((ROOT / "Missions/05-scout-sub-crypt.json").read_text())
    awaken_rule = next(rule for rule in mission["rules"] if rule["name"] == "Awaken Rooms")
    assert "Excluding Player's drop-zone rooms" in awaken_rule["summary"]
    assert all(room["label"].startswith("Eligible room ") for room in mission["missionEngine"]["rooms"])
    eligibility = section("function scoutRoomState", "async function performScoutRoom")
    assert "missionEngine().rooms.filter" in eligibility


def test_room_picker_is_single_step_touch_friendly_and_cancel_safe():
    picker = section("function selectHumanPlayerAction", "function commitHumanPlayerAction")
    assert "Which room is this operative scouting?" in picker
    assert "Select the room this operative currently occupies." in picker
    assert "Only select it if the operative can legally perform Scout Room on the tabletop." in picker
    assert "Ready to scout" in picker
    assert "scout-room-choice" in picker
    assert "Are you sure?" not in picker
    assert "cancelScoutRoom').onclick=cancelCurrentHumanPlayerAction" in picker


def test_scout_commit_is_one_ap_idempotent_and_keeps_activation_continuity():
    scout = section("async function performScoutRoom", "async function performLocateItem")
    action = section("function commitHumanPlayerAction", "function pendingAttackResults")
    assert "eligibleScoutRooms().find(item=>item.id===roomId)" in scout
    assert "!canPerformScoutRoom(activation,operativeId,stage)" in scout
    assert "cancelCurrentHumanPlayerAction()" not in scout
    assert scout.index("eligibleScoutRooms().find") < scout.index("executeMissionAction")
    assert "commitHumanPlayerAction(stage,{deferContinuation:true,deferPersistence:true})" in scout
    assert "const ids=new Set(state.missionState.scoutedRoomIds||[]);ids.add(roomId)" in scout
    assert "performed Scout Room in ${room.label}" in scout
    assert "continueAfterCommittedHumanAction()" in scout
    assert "activation.remainingAp=before-pending.cost" in action
    assert "completedActionIds=[...(activation.completedActionIds||[]),pending.actionId]" in action


def test_scout_preflight_rejects_stale_or_duplicate_callbacks_before_mutation():
    preflight = section("function canPerformScoutRoom", "async function performScoutRoom")
    scout = section("async function performScoutRoom", "async function performLocateItem")
    assert "pending?.activationId===activation.activationId" in preflight
    assert "pending.actionId==='scoutRoom'" in preflight
    assert "completedActionIds||[]).includes('scoutRoom')" in preflight
    assert "pending.cost<=activation.remainingAp" in preflight
    assert scout.index("!canPerformScoutRoom(activation,operativeId,stage)") < scout.index("executeMissionAction")


def test_mission_details_report_known_room_state():
    details = section("scout:(engine,progress,{readOnly", "regroup:(engine,progress,{readOnly")
    assert "NPOs remain" in details
    assert "Unscouted · Clear" in details
    assert "Scouted" in details
