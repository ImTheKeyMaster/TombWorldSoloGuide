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
    assert "## v9.2.60\n\n**Version 9.2.60**" in README
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
    available = function_source("ceaselessScuttlingAvailable")
    eligible = function_source("ceaselessScuttlingEligible")
    create = function_source("createCeaselessScuttlingWarrior")
    confirm = function_source("confirmSoloCeaselessScuttlingSetup")
    script = "\n".join(
        (
            "const MAX_NPOS=10;",
            "const state={turningPoint:2,strategyData:{},activationHistory:[],roster:[{id:'original',type:'Canoptek Macrocyte Warrior',wounds:7,battlefieldState:'deployed'}]};",
            "let creations=0,saves=0,renders=0,logs=0;",
            "const isPvpMode=()=>false;",
            "const ceaselessScuttlingSoloWeaponId=()=>\"synaptic-discharger\";",
            "const definition={type:'Canoptek Macrocyte Warrior',name:'Macrocyte Warrior',wounds:7,loadoutOptions:[{id:'synaptic-discharger',name:'Synaptic discharger'}]};",
            "const npoDefinition=()=>definition;",
            "const createNpo=(type,name,options)=>{creations++;return {id:'npo-1',type,name,weaponId:options.weaponId,wounds:7,ready:options.ready,dormant:options.dormant,deployed:true,battlefieldState:'deployed'};};",
            "const npoName=warrior=>warrior.name; const log=()=>logs++;",
            "const save=()=>saves++; const render=()=>renders++;",
            "const requestAnimationFrame=callback=>callback(); const $=()=>null;",
            available.strip(),
            eligible.strip(),
            create.strip(),
            confirm.strip(),
            "const first=confirmSoloCeaselessScuttlingSetup();",
            "const second=confirmSoloCeaselessScuttlingSetup();",
            "const warrior=state.roster.find(item=>item.createdBy==='a-ceaseless-scuttling');",
            "console.log(JSON.stringify({first,second,creations,saves,renders,logs,history:state.activationHistory.length,marker:state.strategyData.ceaselessScuttlingTurningPoint,generated:state.roster.filter(item=>item.createdBy==='a-ceaseless-scuttling').length,warrior}));",
        )
    )
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)

    assert json.loads(result.stdout) == {
        "first": True,
        "second": False,
        "creations": 1,
        "saves": 1,
        "renders": 1,
        "logs": 1,
        "history": 1,
        "marker": 2,
        "generated": 1,
        "warrior": {
            "id": "npo-1",
            "type": "Canoptek Macrocyte Warrior",
            "name": "Macrocyte Warrior",
            "weaponId": "synaptic-discharger",
            "wounds": 7,
            "ready": True,
            "dormant": False,
            "deployed": True,
            "battlefieldState": "deployed",
            "createdBy": "a-ceaseless-scuttling",
            "order": "Conceal",
        },
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
