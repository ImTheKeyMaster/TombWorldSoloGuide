from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
MISSION = (ROOT / "Missions" / "05-scout-sub-crypt.json").read_text(encoding="utf-8")


def section(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_release_and_initial_scout_state_are_current():
    assert CURRENT_APP_VERSION == ".".join(("9", "2", str(40 + 7)))
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
    assert "const grade=threatGrade(),requestedCount=Math.min(5,awakenRoll+threatGrade())" in awakening
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
    assert "Awakened · ${roomCondition}" in display
    assert "Unscouted · NPOs remain" in display
    assert "data-awaken-room" not in display
    assert "First Open / Entry" not in display
    assert "scoutedRoomIds" in scout
    assert "commitHumanPlayerAction" in scout


def test_awakening_battle_record_is_explicit_and_idempotent():
    awakening = section("async function performAwakenRoom", "async function performAuspexCalibration")
    assert "if(state.missionState?.awakenedRooms?.[roomId])" in awakening
    assert "Scout Sub-Crypt awakening roll: D3" in awakening
    assert "is Awakened and remains Unscouted" in awakening
    assert "blocked by the NPO cap or available model inventory" in awakening
