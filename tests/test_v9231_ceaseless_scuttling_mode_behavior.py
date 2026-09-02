import json
import re
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def function_source(name):
    start = APP.index(f"  function {name}(")
    next_function = APP.find("\n  function ", start + 1)
    return APP[start : next_function if next_function >= 0 else len(APP)]


def ceaseless_result(roster, turning_point=2, resolved_turning_point=None):
    strategy_data = {}
    if resolved_turning_point is not None:
        strategy_data["ceaselessScuttlingTurningPoint"] = resolved_turning_point
    script = "\n".join(
        (
            "const MAX_NPOS=10;",
            f"const state={{turningPoint:{turning_point},roster:{json.dumps(roster)},strategyData:{json.dumps(strategy_data)}}};",
            function_source("ceaselessScuttlingAvailable").strip(),
            function_source("ceaselessScuttlingEligible").strip(),
            function_source("ceaselessScuttlingUnavailableReason").strip(),
            "console.log(JSON.stringify({available:ceaselessScuttlingAvailable(),eligible:ceaselessScuttlingEligible(),reason:ceaselessScuttlingUnavailableReason()}));",
        )
    )
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_rule_availability_is_distinct_and_follows_the_complete_battle_roster():
    available = function_source("ceaselessScuttlingAvailable")
    eligible = function_source("ceaselessScuttlingEligible")

    assert "roster.some(npo=>npo.type==='Canoptek Macrocyte Warrior')" in available
    assert "tombWorldVariant" not in available
    assert "ceaselessScuttlingAvailable(roster)" in eligible
    assert "turningPoint>1" in eligible
    assert "living<3" in eligible
    assert "deployed<MAX_NPOS" in eligible
    assert "ceaselessScuttlingTurningPoint!==turningPoint" in eligible


def test_rule_availability_runtime_covers_every_roster_lifecycle_state():
    assert ceaseless_result([]) == {"available": False, "eligible": False, "reason": ""}

    for battlefield_state, wounds in (
        ("deployed", 7),
        ("reserve", 7),
        ("out-of-action", 0),
    ):
        result = ceaseless_result(
            [
                {
                    "type": "Canoptek Macrocyte Warrior",
                    "battlefieldState": battlefield_state,
                    "wounds": wounds,
                }
            ]
        )
        assert result["available"] is True
        assert result["eligible"] is True


def test_rule_eligibility_runtime_reports_exact_temporary_blockers():
    three_warriors = [
        {
            "type": "Canoptek Macrocyte Warrior",
            "battlefieldState": "deployed",
            "wounds": 7,
        }
        for _ in range(3)
    ]
    assert ceaseless_result(three_warriors) == {
        "available": True,
        "eligible": False,
        "reason": "Unavailable: 3 of 3 Macrocyte Warriors remain.",
    }

    full_battlefield = [
        {
            "type": "Canoptek Macrocyte Warrior" if index == 0 else "Necron Warrior",
            "battlefieldState": "deployed",
            "wounds": 7,
        }
        for index in range(10)
    ]
    assert ceaseless_result(full_battlefield) == {
        "available": True,
        "eligible": False,
        "reason": "Unavailable: the battlefield already has the maximum 10 NPOs.",
    }

    resolved = ceaseless_result(
        [
            {
                "type": "Canoptek Macrocyte Warrior",
                "battlefieldState": "out-of-action",
                "wounds": 0,
            }
        ],
        resolved_turning_point=2,
    )
    assert resolved == {
        "available": True,
        "eligible": False,
        "reason": "Unavailable: A Ceaseless Scuttling was already resolved this Turning Point.",
    }


def test_roster_model_preserves_deployed_reserve_and_out_of_action_instances():
    create_npo = function_source("createNpo")
    active_npos = function_source("activeNpos")
    reserve_npos = function_source("reserveNpos")
    create_scuttling = function_source("createCeaselessScuttlingWarrior")

    assert "options.battlefieldState||(options.deployed===false?'reserve':'deployed')" in create_npo
    assert "battlefieldState==='deployed'" in active_npos
    assert "battlefieldState==='reserve'" in reserve_npos
    assert "npo.battlefieldState==='out-of-action'||npo.wounds<=0" in create_scuttling


def test_solo_only_shows_and_gates_an_eligible_pending_resolution():
    actions = function_source("strategyActionsStepHtml")
    pending = function_source("soloCeaselessScuttlingPending")
    can_leave = function_source("canLeaveStrategyActions")

    assert "!isPvpMode()&&ceaselessScuttlingEligible()" in pending
    assert "!soloCeaselessScuttlingPending()" in can_leave
    assert "state.turningPoint>1&&scuttlingAvailable&&(isPvpMode()||scuttlingEligible)" in actions
    assert "${isPvpMode()?'Use':'Resolve'} A Ceaseless Scuttling" in actions
    assert "disabled:actionsBlocked" in actions
    assert "Resolve A Ceaseless Scuttling before continuing." in actions
    assert "isPvpMode()?'Review optional Strategic Gambits.':'Resolve applicable Strategic Gambits.'" in actions
    assert "Decline" not in actions
    assert "Skip" not in actions


def test_pvp_keeps_optional_choice_and_reports_the_exact_primary_blocker():
    actions = function_source("strategyActionsStepHtml")
    reason = function_source("ceaselessScuttlingUnavailableReason")

    assert "${isPvpMode()?'Use':'Resolve'} A Ceaseless Scuttling" in actions
    assert "already resolved this Turning Point" in reason
    assert "of 3 Macrocyte Warriors remain" in reason
    assert "maximum ${MAX_NPOS} NPOs" in reason
    assert "three Warriors remain, or" not in APP


def test_solo_uses_generation_policy_and_only_requests_physical_input():
    modal = function_source("showCeaselessScuttling")
    policy = function_source("ceaselessScuttlingSoloWeaponId")

    assert "generatedWeaponId(generatedResult)" in policy
    assert "ceaselessScuttlingWeaponId" in policy
    assert "save()" in policy
    assert "ceaselessScuttlingSoloWeaponId()" in modal
    assert "isPvpMode()" in modal
    assert "scuttlingLoadout" in modal
    assert "New Canoptek Macrocyte Warrior" in modal
    assert "Valid NPO drop-zone setup location confirmed" in modal
    assert ">Confirm Setup</button>" in modal
    assert "createCeaselessScuttlingWarrior(isPvpMode()?$('#scuttlingLoadout').value:soloWeaponId)" in modal


def test_solo_can_report_that_no_legal_setup_location_exists():
    modal = function_source("showCeaselessScuttling")

    assert "isPvpMode()?'':'<button" in modal
    assert "No Legal Setup Location" in modal
    assert "$('#scuttlingNoLegalSetup')?.addEventListener" in modal
    assert "state.strategyData.ceaselessScuttlingTurningPoint=state.turningPoint" in modal
    assert "no legal NPO drop-zone location was available" in modal
    no_setup_handler = modal.split("$('#scuttlingNoLegalSetup')", 1)[1].split("});", 1)[0]
    assert "createCeaselessScuttlingWarrior" not in no_setup_handler
    assert "save();closeModal();render();" in no_setup_handler


def test_resolution_is_once_per_turning_point_and_restores_or_creates_once():
    create_scuttling = function_source("createCeaselessScuttlingWarrior")
    modal = function_source("showCeaselessScuttling")

    assert "if(!ceaselessScuttlingEligible())return null" in create_scuttling
    assert "const warrior=returned||createNpo" in create_scuttling
    assert "if(!returned)state.roster.push(warrior)" in create_scuttling
    assert "wounds:definition.wounds" in create_scuttling
    assert "ready:true" in create_scuttling
    assert "battlefieldState:'deployed'" in create_scuttling
    assert "warrior.order='Conceal'" in create_scuttling
    assert "warrior.createdBy='a-ceaseless-scuttling'" in create_scuttling
    assert "ceaselessScuttlingTurningPoint=state.turningPoint" in create_scuttling
    assert "activationHistory.unshift" in modal
    assert "data-close>Cancel" in modal


def test_release_and_save_compatibility_surfaces():
    expected_release = ".".join(("9", "2", "32"))
    assert CURRENT_APP_VERSION == expected_release
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert not re.search(r"9\.2\.31", "\n".join((APP, INDEX, WORKER)))
