import json
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def mission(number, slug):
    return json.loads((ROOT / "Missions" / f"{number}-{slug}.json").read_text(encoding="utf-8"))


def test_release_version_and_save_key_are_consistent():
    assert CURRENT_APP_VERSION == ".".join(("9", "2", str(40 + 3)))
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in (ROOT / "service-worker.js").read_text()
    index = (ROOT / "index.html").read_text()
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in index
    assert "9.2.42" not in index


def test_each_mission_declares_its_action_guide_metadata():
    expected = {
        ("01", "shifting-labyrinth"): None,
        ("02", "demolition-protocol"): None,
        ("03", "recover-transponder"): {"id": "pickUpMarker", "displayLabel": "Pick Up Marker", "apCost": 1},
        ("04", "destroy-sarcophagus"): {"existingAction": "breach", "displayLabel": "Breach Sarcophagus"},
        ("05", "scout-sub-crypt"): {"id": "scoutRoom", "displayLabel": "Scout Room", "apCost": 1},
        ("06", "regroup"): None,
    }
    for identity, action in expected.items():
        assert mission(*identity)["actionGuide"]["missionAction"] == action


def test_catalog_has_no_generic_action_or_destroy_sarcophagus_duplicate():
    catalog = APP.split("function playerHumanActionCatalog", 1)[1].split("function playerHumanActionState", 1)[0]
    assert "Mission Action" not in catalog
    assert catalog.count("{id:'breach'") == 1
    assert "id:'breachSarcophagus'" not in catalog
    assert "existingAction==='breach'" in catalog
    assert "cost:breachApCost(operative)" in catalog


def test_destroy_sarcophagus_keeps_breach_identity_cost_and_restrictions():
    selection = APP.split("function selectHumanPlayerAction", 1)[1].split("function commitHumanPlayerAction", 1)[0]
    state = APP.split("function playerHumanActionState", 1)[1].split("function renderHumanActivationShell", 1)[0]
    assert "action.id==='breach'" in selection
    assert "beginBreachSarcophagus(stage)" in selection
    assert "record.id==='breach'&&record.apCost===1" in state
    assert "action.id==='breach'&&action.cost===1" in state
    assert "return breachApCost(playerDefinition(operativeId))" in APP


def test_scout_room_uses_normal_one_ap_transaction_and_existing_engine_action():
    scout = APP.split("async function performScoutRoom", 1)[1].split("async function performLocateItem", 1)[0]
    assert "missionEngine().actions?.recordScout" in scout
    assert "objectiveEngine.executeMissionAction" in scout
    assert "commitHumanPlayerAction(stage,{deferContinuation:true,deferPersistence:true})" in scout
    assert "performed Scout Room" in scout
    assert "missionAction.apCost" in APP


def test_generic_player_facing_action_label_is_removed():
    assert "name:'Mission Action'" not in APP
    assert ">Mission Action<" not in APP
