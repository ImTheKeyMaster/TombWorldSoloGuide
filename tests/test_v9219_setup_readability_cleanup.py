import json
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
MISSION_FILES = sorted((ROOT / "Missions").glob("0[1-6]-*.json"))
MISSIONS = [json.loads(path.read_text(encoding="utf-8")) for path in MISSION_FILES]


def source_between(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def test_roster_requirement_panel_was_replaced_by_safe_category_status_markup():
    roster = source_between("if(stepId==='playerRoster')", "if(stepId==='options')")
    assert "Roster Requirements" not in roster
    assert "roster-category-status" in roster
    assert "escapeHtml(categoryStatus)" in roster
    assert "escapeHtml(`${category.label}, ${accessibleStatus}`)" in roster


def test_every_supported_team_uses_the_shared_roster_renderer():
    manifest = json.loads((ROOT / "Player_Operatives" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["teams"]) >= 6
    assert APP.count("function rosterCategoryRequirementText(") == 1
    assert APP.count("rosterCategoryRequirementText(category") == 3
    for team in manifest["teams"]:
        team_path = ROOT / "Player_Operatives" / team["file"]
        assert team_path.is_file(), team_path
        assert json.loads(team_path.read_text(encoding="utf-8"))["teamName"]


def test_roster_validation_and_random_team_paths_are_unchanged():
    roster = source_between("if(stepId==='playerRoster')", "if(stepId==='options')")
    bindings = source_between("function bindSetup(stepId)", "function advanceSetupStep")
    assert "const validation=playerRosterValidation([...selected])" in roster
    assert "const valid=validation.valid&&requiredLeaderSelected" in roster
    assert '<button class="btn secondary" id="randomPlayerTeam">Random Team</button>' in roster
    assert "randomPlayerRoster();save();render();" in bindings


def test_redundant_starting_conceal_confirmation_is_absent_from_all_missions():
    for path, mission in zip(MISSION_FILES, MISSIONS):
        ids = [check["id"] for check in mission["setupChecks"]]
        assert "starting-conceal" not in ids, path
        assert all(check["label"] != "Give every starting NPO a Conceal order." for check in mission["setupChecks"])
    assert "starting-conceal" not in source_between("function setupContent(stepId)", "function bindSetup(stepId)")


def test_starting_npo_conceal_order_rules_remain_intact():
    assert all(mission["startingNpos"]["order"] == "Conceal" for mission in MISSIONS)
    create_npo = source_between("function createNpo(", "function generateRoster")
    assert "order:'Conceal'" in create_npo
    assert "order:npo.order||'Conceal'" in APP


def test_remaining_deployment_checks_still_gate_completion_and_check_all():
    deploy = source_between("if(stepId==='deploy'){", "const m=mission();")
    bindings = source_between("function bindSetup(stepId)", "function advanceSetupStep")
    assert "const requiredPlacementChecks=hasStartingNpos?placementChecks:otherPlacementChecks" in deploy
    assert "requiredPlacementChecks.every(check=>state.setupChecks[check.id])" in deploy
    assert "playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked" in deploy
    assert "state.setupChecks[deploymentCheck.id]&&allNposPlaced" in deploy
    assert "checkAllDeployment" in bindings
    assert "setStartingNposDeployed(true)" in bindings
    assert "dispatchEvent(new Event('change'" not in bindings
    for mission in MISSIONS:
        deploy_ids = {check["id"] for check in mission["setupChecks"] if check["stage"] == "deploy"}
        assert "starting-npos" in deploy_ids
        assert "initial-resources" in deploy_ids
    regroup = next(mission for mission in MISSIONS if mission["id"] == "regroup")
    assert "player-setup" in {check["id"] for check in regroup["setupChecks"]}


def test_zero_starting_npo_mission_keeps_its_existing_flow():
    scout = next(mission for mission in MISSIONS if mission["startingNpos"]["formula"] == "0")
    deploy = source_between("if(stepId==='deploy'){", "const m=mission();")
    assert scout["startingNpos"]["formula"] == "0"
    assert scout["startingNpos"]["order"] == "Conceal"
    assert "hasStartingNpos&&deploymentCheck" in deploy
    assert "hasStartingNpos?placementChecks:otherPlacementChecks" in deploy
    assert "This mission begins with no ${escapeHtml(opponentPluralLabel())} deployed." in deploy


def test_stale_setup_check_cleanup_remains_generic_and_save_schema_is_stable():
    cleanup = source_between("function missionSetupChecks(stage)", "function clearMissionSetupChecks")
    assert "currentIds=new Set(checks.map(check=>check.id))" in cleanup
    assert "filter(([id])=>currentIds.has(id))" in cleanup
    current_ids = {check["id"] for mission in MISSIONS for check in mission["setupChecks"]}
    stale_save = {"starting-conceal": True, "initial-resources": True}
    cleaned = {key: value for key, value in stale_save.items() if key in current_ids}
    assert cleaned == {"initial-resources": True}
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_v9219_release_surfaces_and_cache_are_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (9, 2, 19)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert "const CACHE_PREFIX = 'tomb-world-battle-guide-';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )
    assert "Starting NPOs still begin with Conceal orders automatically" in README
