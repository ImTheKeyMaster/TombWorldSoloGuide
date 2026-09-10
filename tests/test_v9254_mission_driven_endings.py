"""Deterministic source-level acceptance checks for the mission-driven battle-ending release."""
import json
import subprocess
from pathlib import Path
from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
README = (ROOT / "README.md").read_text()


def source(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_shifting_labyrinth_waits_for_all_removed_and_uses_half_or_more():
    helper = "function shiftingLabyrinthResult" + source(
        "function shiftingLabyrinthResult", "function missionOutcomeExplanation"
    )
    cases = [
        {"total": 5, "escaped": 3, "casualties": 0, "outcome": None},
        {"total": 5, "escaped": 3, "casualties": 2, "outcome": "victory"},
        {"total": 5, "escaped": 2, "casualties": 3, "outcome": "defeat"},
        {"total": 4, "escaped": 2, "casualties": 2, "outcome": "victory"},
        {"total": 4, "escaped": 1, "casualties": 3, "outcome": "defeat"},
        {"total": 3, "escaped": 2, "casualties": 0, "outcome": None},
        {"total": 3, "escaped": 2, "casualties": 1, "outcome": "victory"},
    ]
    script = f"""
const cases={json.dumps(cases)};
{helper}
const results=cases.map(test=>{{
  globalThis.state={{
    playerRoster:Array.from({{length:test.total}},(_,index)=>`operative-${{index+1}}`),
    playerCasualtyIds:Array.from({{length:test.casualties}},(_,index)=>`operative-${{test.total-index}}`),
    missionState:{{escapedIds:Array.from({{length:test.escaped}},(_,index)=>`operative-${{index+1}}`)}}
  }};
  return shiftingLabyrinthResult();
}});
process.stdout.write(JSON.stringify(results));
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    results = json.loads(completed.stdout)
    assert [result["outcome"] for result in results] == [case["outcome"] for case in cases]
    assert [result["requiredEscapes"] for result in results] == [3, 3, 3, 2, 2, 2, 2]


def test_escape_result_copy_comes_from_the_same_threshold_calculation():
    explanation = source("function missionOutcomeExplanation", "const missionOutcomeEvaluators")
    assert "const result=shiftingLabyrinthResult()" in explanation
    assert "result.escaped>=result.requiredEscapes" in explanation
    assert "${result.escaped} of ${result.total} operatives escaped" in explanation
    assert "Fewer than half of" in explanation and "At least half of" in explanation


def test_all_six_evaluators_are_mission_driven():
    helper = "function shiftingLabyrinthResult" + source(
        "function shiftingLabyrinthResult", "function missionOutcomeExplanation"
    )
    evaluators = "const missionOutcomeEvaluators" + source(
        "const missionOutcomeEvaluators", "function missionOutcome"
    )
    script = f"""
let state={{playerRoster:['one'],playerCasualtyIds:[],missionState:{{escapedIds:[]}}}};
function freshMissionState(){{return state.missionState;}}
function inPlayLivingPlayerOperativeIds(){{return state.survivors||[];}}
{helper}
{evaluators}
const outcomes={{
  escapeIncomplete:missionOutcomeEvaluators.escape({{}},{{escapedIds:[]}},'end-turning-point'),
  sabotageIncomplete:missionOutcomeEvaluators.sabotage({{required:7}},{{completedFeatureIds:Array(6)}},'end-turning-point'),
  sabotageVictory:missionOutcomeEvaluators.sabotage({{required:7}},{{completedFeatureIds:Array(7)}},'immediate'),
  transponderIncomplete:missionOutcomeEvaluators.transponder({{}},{{escaped:false}},'end-turning-point'),
  transponderVictory:missionOutcomeEvaluators.transponder({{}},{{escaped:true}},'immediate'),
  destructionIncomplete:missionOutcomeEvaluators.destruction({{required:20}},{{destruction:19}},'end-turning-point'),
  destructionVictory:missionOutcomeEvaluators.destruction({{required:20}},{{destruction:20}},'immediate'),
  scoutIncomplete:missionOutcomeEvaluators.scout({{required:3}},{{scoutedRoomIds:Array(2)}},'end-turning-point'),
  scoutVictory:missionOutcomeEvaluators.scout({{required:3}},{{scoutedRoomIds:Array(3)}},'immediate')
}};
state.survivors=['one'];
outcomes.regroupIncomplete=missionOutcomeEvaluators.regroup({{}},{{operativeChecks:{{one:{{inDropZone:false,outsideNpoControl:true,nearPlayer:true}}}}}},'end-turning-point');
outcomes.regroupVictory=missionOutcomeEvaluators.regroup({{}},{{operativeChecks:{{one:{{inDropZone:true,outsideNpoControl:true,nearPlayer:true}}}}}},'end-turning-point');
state.survivors=[];
outcomes.regroupEmpty=missionOutcomeEvaluators.regroup({{}},{{operativeChecks:{{}}}},'end-turning-point');
process.stdout.write(JSON.stringify(outcomes));
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    assert json.loads(completed.stdout) == {
        "escapeIncomplete": None,
        "sabotageIncomplete": None,
        "sabotageVictory": "victory",
        "transponderIncomplete": None,
        "transponderVictory": "victory",
        "destructionIncomplete": None,
        "destructionVictory": "victory",
        "scoutIncomplete": None,
        "scoutVictory": "victory",
        "regroupIncomplete": None,
        "regroupVictory": "victory",
        "regroupEmpty": None,
    }


def test_elimination_defeat_precedes_regroup_and_other_objectives():
    outcome = source("function missionOutcome(timing='immediate')", "let battleEndHookPending")
    assert outcome.index("livingPlayerOperativeCount()===0") < outcome.index("missionOutcomeEvaluators")
    assert "engine?.type!=='escape'" in outcome


def test_legacy_tp4_limit_defeat_is_only_repaired_when_unambiguous():
    normalize = source("function normalizeState(raw)", "function npoDefinition")
    assert "const obsoleteLimitDefeat=" in normalize
    for guard in ("merged.turningPoint===4", "merged.gameEnd==='defeat'", "merged.finalResolution.turningPointEnded", "livingSavedPlayers>0", "!objectiveWasAchieved"):
        assert guard in normalize
    assert "merged.gameEnd=null;merged.completed=false;merged.phase='between'" in normalize
    assert "Battle restored because Tomb World Joint Ops does not automatically end after Turning Point 4." in normalize


def test_battle_complete_requires_a_committed_outcome():
    predicate = source("function isBattleComplete()", "function bindCommon")
    assert "Boolean(state.gameEnd)" in predicate
    assert "finalResolution" not in predicate
    render = source("function renderGame()", "function missionHudHtml")
    assert "if(state.gameEnd){" in render
    assert "finalResolution?.pending" not in render


def test_version_surfaces_and_release_notes():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 54)
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    index = (ROOT / "index.html").read_text()
    worker = (ROOT / "service-worker.js").read_text()
    assert f"V{CURRENT_APP_VERSION}" in index and index.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_tp5_and_tp6_execute_the_production_start_and_strategy_pipeline():
    start = "async function startTurningPoint" + source(
        "async function startTurningPoint", "async function continueTurningPointStart"
    )
    finish = "async function finishTurningPointStart" + source(
        "async function finishTurningPointStart", "function completeStrategyStage"
    )
    script = f"""
const calls=[];
let state={{
  turningPoint:4,finalResolution:{{}},npoRuleState:{{reanimatedTargetIds:['old'],incapacitationTriggers:['old']}},
  missionState:{{}},threat:6,playerCount:2,playerCasualtyIds:[],playerActivatedIds:['old'],
  activationFinishedForTurningPoint:{{player:true,npo:true}},activationHistory:['old'],
  eventState:{{}},roster:[]
}};
function missionEngine(){{return {{type:'sabotage'}};}}
function threatGrade(){{return 2;}}
function destroyedNpoCount(){{return 1;}}
function processReadyStep(){{calls.push(`ready:${{state.turningPoint}}`);state.strategyPipeline.current='initiative';}}
async function applyMissionReadyHooks(){{calls.push(`mission-ready:${{state.turningPoint}}`);return true;}}
async function determineInitiative(){{calls.push(`initiative:${{state.turningPoint}}`);state.strategyData.playerRoll=6;state.strategyData.npoRoll=1;state.strategyPipeline.current='event';}}
async function processEventStage(){{calls.push(`event:${{state.turningPoint}}`);state.strategyPipeline.current='reinforcement';}}
async function beginCurrentEvent(){{throw new Error('unexpected restored event');}}
function processReinforcementStage(){{calls.push(`reinforcement:${{state.turningPoint}}`);state.strategyData.reinforcements=['one'];}}
function log(message){{calls.push(message);}}
function save(){{calls.push(`save:${{state.turningPoint}}`);}}
function render(){{calls.push(`render:${{state.turningPoint}}`);}}
{finish}
{start}
(async()=>{{
  await startTurningPoint();
  const tp5={{turningPoint:state.turningPoint,phase:state.phase,activationNumber:state.activationNumber,history:state.activationHistory.length,activated:state.playerActivatedIds.length}};
  state.phase='between';
  await startTurningPoint();
  const tp6={{turningPoint:state.turningPoint,phase:state.phase,activationNumber:state.activationNumber,history:state.activationHistory.length,activated:state.playerActivatedIds.length}};
  process.stdout.write(JSON.stringify({{calls,tp5,tp6}}));
}})().catch(error=>{{console.error(error);process.exit(1);}});
"""
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    result = json.loads(completed.stdout)
    assert result["tp5"] == {"turningPoint": 5, "phase": "strategy", "activationNumber": 0, "history": 0, "activated": 0}
    assert result["tp6"] == {"turningPoint": 6, "phase": "strategy", "activationNumber": 0, "history": 0, "activated": 0}
    for turning_point in (5, 6):
        for stage in ("ready", "mission-ready", "initiative", "event", "reinforcement"):
            assert f"{stage}:{turning_point}" in result["calls"]
        assert any(entry.startswith(f"Turning Point {turning_point} started.") for entry in result["calls"])
