import json
import re
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
MISSION_FILES = sorted((ROOT / "Missions").glob("0[1-6]-*.json"))
MISSIONS = [json.loads(path.read_text(encoding="utf-8")) for path in MISSION_FILES]


def source_between(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


def render_requirements(*requirements):
    escape_html = re.search(r"  function escapeHtml\(s\)\{.*\}", APP).group(0)
    formatter = "function rosterRequirementHtml" + source_between(
        "function rosterRequirementHtml", "function inlineOperativeList"
    )
    script = f"""
{escape_html}
{formatter}
console.log(JSON.stringify({json.dumps(requirements)}.map(rosterRequirementHtml)));
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_shared_roster_requirements_use_safe_semantic_label_value_markup():
    helper = source_between("function rosterRequirementHtml(requirement)", "function inlineOperativeList")
    roster = source_between("if(stepId==='playerRoster')", "if(stepId==='options')")
    assert "Roster Requirements" in roster
    assert "text.indexOf(':')" in helper
    assert "text.slice(0,colonIndex+1)" in helper
    assert "text.slice(colonIndex+1)" in helper
    assert helper.count("escapeHtml(") == 3
    assert "<strong>${escapeHtml(text.slice(0,colonIndex+1))}</strong>" in helper
    assert "<span>${escapeHtml(text.slice(colonIndex+1))}</span>" in helper
    assert "if(colonIndex<0)return escapeHtml(text)" in helper
    assert "requirements.map(requirement=>`<li>${rosterRequirementHtml(requirement)}</li>`)" in roster
    assert "requirements.map(requirement=>`<li>${escapeHtml(requirement)}</li>`)" not in roster


def test_roster_requirement_formatter_behavior():
    assert render_requirements(
        "Leader: 1 of 1 required",
        "Rule: value: detail",
        "Unsafe <label>: 1 & ready",
        "No colon <unsafe>",
    ) == [
        "<strong>Leader:</strong><span> 1 of 1 required</span>",
        "<strong>Rule:</strong><span> value: detail</span>",
        "<strong>Unsafe &lt;label&gt;:</strong><span> 1 &amp; ready</span>",
        "No colon &lt;unsafe&gt;",
    ]


def test_all_requirement_labels_and_values_are_still_generated_unchanged():
    roster = source_between("if(stepId==='playerRoster')", "if(stepId==='options')")
    for unchanged_source in (
        "Required Gravis: ${gravisCount} of 1",
        "Maximum Gunners: ${gunnerCount} of ${maxGunners}",
        "Required Leader: ${selectedLeaderCount} of ${requiredLeaderCount}",
        "Required Troopers: ${trooperCount} of ${mandatoryTroopers}",
        "Total Operatives: ${selected.size} of ${maxRoster}",
    ):
        assert unchanged_source in roster
    # Category-driven teams supply labels such as Leader and Troopers through
    # the same validation output and the same generic formatter.
    assert "validation.requirements" in roster
    assert "requirements.splice(0,requirements.length,...validation.requirements)" in roster


def test_only_roster_requirement_labels_are_heavy():
    assert ".player-roster-summary li{color:var(--muted);font-weight:400}" in CSS
    assert ".player-roster-summary li strong{font-weight:800}" in CSS
    assert not re.search(r"\.player-roster-summary li\{[^}]*font-weight:800", CSS)


def test_every_supported_team_uses_the_shared_roster_renderer():
    manifest = json.loads((ROOT / "Player_Operatives" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["teams"]) >= 6
    assert APP.count("function rosterRequirementHtml(") == 1
    assert APP.count("rosterRequirementHtml(requirement)") == 2
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
    assert "checkbox.dispatchEvent(new Event('change',{bubbles:true}))" in bindings
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
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 19)
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
