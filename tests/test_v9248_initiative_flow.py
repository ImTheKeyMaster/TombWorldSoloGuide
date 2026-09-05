"""Behavioral regression coverage for the corrected initiative state machine."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def function_source(name):
    marker = f"function {name}("
    start = APP.index(marker)
    if APP[max(0, start - 6):start] == "async ":
        start -= 6
    brace = APP.index("{", start)
    depth = 0
    quote = None
    escaped = False
    template_expression_depth = 0
    for index in range(brace, len(APP)):
        char = APP[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote and not (quote == "`" and template_expression_depth):
                quote = None
            elif quote == "`" and char == "$" and APP[index:index + 2] == "${":
                template_expression_depth += 1
            elif quote == "`" and char == "}" and template_expression_depth:
                template_expression_depth -= 1
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return APP[start:index + 1]
    raise AssertionError(f"Could not extract {name}")


def run_node(body):
    result = subprocess.run(
        ["node", "-e", body], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)


MISSION_HELPER = function_source("missionFirstInitiative")
ROLL_INITIATIVE = function_source("rollInitiative")
SET_NEXT = function_source("setNextActivation")
ADVANCE = function_source("advanceAfterActivation")
BEGIN_FIREFIGHT = function_source("beginFirefight")
REQUEST_DICE = function_source("requestDiceResults")


def initiative_run(*, turning_point, threat, mission_side="player", dice=(), existing=None, mode="solo"):
    state = existing or {"turningPoint": turning_point, "threat": threat, "strategyData": {}}
    script = f"""
const state={json.dumps(state)};
const selectedMission={{firstTurningPointInitiative:{json.dumps(mission_side)}}};
const requests=[]; const saves=[]; const acknowledgements=[];
const supplied={json.dumps(list(dice))};
const mission=()=>selectedMission;
const selectedPlayerTeamName=()=> 'Test Team';
const save=()=>{{saves.push(JSON.parse(JSON.stringify(state)));return true;}};
const acknowledgeDiceRequest=key=>{{acknowledgements.push(key);return true;}};
const requestDiceResults=async request=>{{requests.push({{...request,mode:{json.dumps(mode)}}});return [supplied.shift()];}};
{MISSION_HELPER}
{ROLL_INITIATIVE}
(async()=>{{await rollInitiative();process.stdout.write(JSON.stringify({{state,requests,saves,acknowledgements,remaining:supplied}}));}})().catch(error=>{{console.error(error);process.exit(1);}});
"""
    return run_node(script)


def test_tp1_player_and_npo_are_mission_defined_without_dice():
    for side in ("player", "npo"):
        result = initiative_run(turning_point=1, threat=9, mission_side=side, dice=[6, 6])
        assert result["requests"] == []
        assert result["state"]["strategyData"]["suggestedInitiative"] == side
        assert result["state"]["initiative"] == side
        assert result["state"]["strategyData"]["initiativeMode"] == "automatic"


def test_tp1_missing_metadata_falls_back_and_invalid_metadata_is_rejected():
    missing = initiative_run(turning_point=1, threat=0, mission_side=None)
    assert missing["state"]["strategyData"]["suggestedInitiative"] == "player"
    script = f"const mission=()=>({{firstTurningPointInitiative:'invalid'}});{MISSION_HELPER}; missionFirstInitiative();"
    failed = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert failed.returncode != 0
    assert "Invalid firstTurningPointInitiative" in failed.stderr


def test_tp2_threat_zero_and_nonzero_request_both_d6_and_resolve_each_winner():
    cases = ((0, [6, 2], "player"), (8, [1, 5], "npo"))
    for threat, dice, winner in cases:
        result = initiative_run(turning_point=2, threat=threat, dice=dice)
        assert [request["count"] for request in result["requests"]] == [1, 1]
        assert [request["sides"] for request in result["requests"]] == [6, 6]
        assert [request["resumeData"]["side"] for request in result["requests"]] == ["player", "necrons"]
        assert result["state"]["strategyData"]["suggestedInitiative"] == winner
        assert result["state"]["initiative"] == winner


def test_tie_rerolls_both_sides_and_retains_the_tied_round():
    result = initiative_run(turning_point=3, threat=0, dice=[4, 4, 2, 6], mode="pvp")
    assert [request["requestKey"] for request in result["requests"]] == [
        "initiative:tp3:round1:player", "initiative:tp3:round1:necrons",
        "initiative:tp3:round2:player", "initiative:tp3:round2:necrons",
    ]
    assert result["state"]["strategyData"]["initiativeRolls"] == [{"playerRoll": 4, "npoRoll": 4}]
    assert result["state"]["strategyData"]["playerRoll"] == 2
    assert result["state"]["strategyData"]["npoRoll"] == 6
    assert result["state"]["strategyData"]["suggestedInitiative"] == "npo"


def test_partial_pvp_result_resumes_without_duplicating_player_die():
    existing = {"turningPoint": 2, "threat": 4, "strategyData": {"playerRoll": 5, "npoRoll": None, "initiativeRolls": []}}
    result = initiative_run(turning_point=2, threat=4, dice=[2], existing=existing, mode="pvp")
    assert [request["resumeData"]["side"] for request in result["requests"]] == ["necrons"]
    assert result["state"]["strategyData"]["playerRoll"] == 5
    assert result["state"]["strategyData"]["suggestedInitiative"] == "player"


def test_resolved_state_survives_serialization_and_does_not_reroll():
    resolved = initiative_run(turning_point=2, threat=6, dice=[2, 5], mode="solo")["state"]
    loaded = json.loads(json.dumps(resolved))
    rerendered = initiative_run(turning_point=2, threat=6, dice=[], existing=loaded, mode="pvp")
    assert rerendered["requests"] == []
    assert rerendered["state"]["strategyData"]["suggestedInitiative"] == "npo"


def test_solo_and_pvp_use_the_same_initiative_requests():
    solo = initiative_run(turning_point=2, threat=3, dice=[5, 1], mode="solo")
    pvp = initiative_run(turning_point=2, threat=3, dice=[5, 1], mode="pvp")
    assert [r["requestKey"] for r in solo["requests"]] == [r["requestKey"] for r in pvp["requests"]]
    assert solo["state"]["strategyData"] == pvp["state"]["strategyData"]


def test_dice_provider_keeps_established_solo_and_pvp_entry_mechanisms():
    script = f"""
let pvp=false; const calls=[]; const state={{pendingDice:null}};
const validateDiceRequest=request=>request;
const isPvpMode=()=>pvp;
const rollDice=(count,sides)=>{{calls.push(['solo',count,sides]);return [3];}};
const pendingDiceMatches=()=>true;
const requestManualDiceResults=(request,values=[])=>{{calls.push(['pvp',request.requestKey,values]);return Promise.resolve([4]);}};
{REQUEST_DICE}
(async()=>{{const solo=await requestDiceResults({{count:1,sides:6,requestKey:'solo'}});pvp=true;const manual=await requestDiceResults({{count:1,sides:6,requestKey:'pvp'}});process.stdout.write(JSON.stringify({{solo,manual,calls}}));}})();
"""
    result = run_node(script)
    assert result == {"solo": [3], "manual": [4], "calls": [["solo", 1, 6], ["pvp", "pvp", []]]}


def test_resolved_side_drives_first_activation_alternation_fallback_and_one_record():
    script = f"""
const state={{initiative:'player',phase:'strategy',strategyStage:'summary',nextSide:'player',activationFinishedForTurningPoint:{{player:false,npo:false}}}};
let playerRemaining=1,npoRemaining=1; const records=[]; let saveCount=0,renderCount=0;
const playerOperativesRemaining=()=>playerRemaining;
const readyNpos=()=>Array.from({{length:npoRemaining}},()=>({{}}));
const log=message=>records.push(message);const save=()=>{{saveCount++;}};const render=()=>{{renderCount++;}};
{SET_NEXT}
{ADVANCE}
{BEGIN_FIREFIGHT}
beginFirefight('npo'); const first=state.nextSide; beginFirefight('player'); const second=advanceAfterActivation('npo');
playerRemaining=0; const fallback=setNextActivation('player');
process.stdout.write(JSON.stringify({{state,first,second,fallback,records,saveCount,renderCount}}));
"""
    result = run_node(script)
    assert result["state"]["initiative"] == "npo"
    assert result["first"] == "npo"
    assert result["second"] == "player"
    assert result["fallback"] == "npo"
    assert result["records"] == ["NPOs begin the Firefight Phase with initiative."]
