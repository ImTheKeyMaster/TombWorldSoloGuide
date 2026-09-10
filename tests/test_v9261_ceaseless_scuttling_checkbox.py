import json
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


def test_release_surfaces_move_from_confirmed_baseline_to_v9261():
    assert "d2292eb v9.2.60" in subprocess.run(
        ["git", "log", "-10", "--oneline"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 61)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )


def test_solo_card_is_an_accessible_tabletop_confirmation_not_an_action_modal():
    actions = function_source("strategyActionsStepHtml")
    binding = function_source("bindPlay")
    modal = function_source("showCeaselessScuttling")

    assert 'for="scuttlingPlacement"' in actions
    assert 'id="scuttlingPlacement" type="checkbox"' in actions
    assert "Macrocyte Warrior set up" in actions
    assert "Set up another Macrocyte Warrior ready with a Conceal order" in actions
    assert "Resolve A Ceaseless Scuttling" not in actions
    assert "confirmSoloCeaselessScuttlingSetup()" in binding
    assert "if(!isPvpMode()||!ceaselessScuttlingEligible())return" in modal
    assert "scuttlingLoadout" in modal
    assert "Confirm Setup" in modal


def test_solo_confirmation_commits_once_and_keeps_existing_creation_rules():
    create = function_source("createCeaselessScuttlingWarrior")
    confirm = function_source("confirmSoloCeaselessScuttlingSetup")
    script = "\n".join(
        (
            "const state={turningPoint:2,strategyData:{},activationHistory:[]};",
            "let creations=0,saves=0,renders=0;",
            "const isPvpMode=()=>false;",
            "const ceaselessScuttlingEligible=()=>state.strategyData.ceaselessScuttlingTurningPoint!==state.turningPoint;",
            "const ceaselessScuttlingSoloWeaponId=()=>\"synaptic-discharger\";",
            "const createCeaselessScuttlingWarrior=weaponId=>{if(!ceaselessScuttlingEligible())return null;creations++;state.strategyData.ceaselessScuttlingTurningPoint=state.turningPoint;return {id:\"npo-1\",name:\"Macrocyte\",weaponId};};",
            "const npoName=warrior=>warrior.name;",
            "const save=()=>saves++; const render=()=>renders++;",
            "const requestAnimationFrame=callback=>callback(); const $=()=>null;",
            confirm.strip(),
            "const first=confirmSoloCeaselessScuttlingSetup();",
            "const second=confirmSoloCeaselessScuttlingSetup();",
            "console.log(JSON.stringify({first,second,creations,saves,renders,history:state.activationHistory.length,marker:state.strategyData.ceaselessScuttlingTurningPoint}));",
        )
    )
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)

    assert json.loads(result.stdout) == {
        "first": True,
        "second": False,
        "creations": 1,
        "saves": 1,
        "renders": 1,
        "history": 1,
        "marker": 2,
    }
    assert "if(!ceaselessScuttlingEligible())return null" in create
    assert "ready:true" in create
    assert "battlefieldState:'deployed'" in create
    assert "warrior.order='Conceal'" in create
    assert "warrior.createdBy='a-ceaseless-scuttling'" in create
    assert "createCeaselessScuttlingWarrior(ceaselessScuttlingSoloWeaponId())" in confirm


def test_gating_completion_exception_pvp_and_save_contract_are_preserved():
    actions = function_source("strategyActionsStepHtml")
    no_setup = function_source("resolveCeaselessScuttlingWithoutSetup")
    pending = function_source("soloCeaselessScuttlingPending")

    assert "!isPvpMode()&&ceaselessScuttlingEligible()" in pending
    assert "disabled:actionsBlocked" in actions
    assert "No legal setup location" in actions
    assert "createCeaselessScuttlingWarrior" not in no_setup
    assert "ceaselessScuttlingTurningPoint=state.turningPoint" in no_setup
    assert ">Use A Ceaseless Scuttling</button>" in actions
    assert "scuttlingLoadout" in function_source("showCeaselessScuttling")
    assert "deployed<MAX_NPOS" in function_source("ceaselessScuttlingEligible")
    assert "ceaselessScuttlingAvailable(roster)" in function_source("ceaselessScuttlingEligible")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
