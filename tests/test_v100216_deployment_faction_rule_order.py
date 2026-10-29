"""Keep deployment checklist ahead of collapsible faction-rule guidance in Solo and PvP."""
from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def deployment_source():
    return APP.split("    if(stepId==='deploy'){", 1)[1].split(
        "    const m=mission();", 1
    )[0]


def test_deployment_checklist_comes_before_faction_rules_and_navigation():
    deployment = deployment_source()
    assert deployment.count("${factionGuidanceHtml()}") == 1, (
        "Rules should appear only once on the deployment screen"
    )
    elements = (
        "${missionRoll}",
        "${rerollControl}",
        'id="checkAllDeployment"',
        'class="checklist deployment-checklist"',
        "${deploymentRow}",
        "${setupChecklistHtml(otherPlacementChecks)}",
        'id="playerDeployed"',
        '</span></label></div>${factionGuidanceHtml()}',
        'class="wizard-actions"',
        'id="setupBack"',
        'id="setupNext"',
    )
    positions = []
    for element in elements:
        position = deployment.index(element)
        positions.append(position)
    assert positions == sorted(positions), (
        "Show the mission roll, all deployment checks, faction rules, then navigation"
    )


def test_guidance_is_not_conditional_on_starting_npos_or_team():
    deployment = deployment_source()
    # In zero-starting-NPO missions the bulk action disappears, but the
    # same player deployment checkbox and faction disclosures remain visible.
    assert "const hasStartingNpos=generation.deployedNpoIds.length>0;" in deployment
    assert '${hasStartingNpos?`<div class="setup-bulk-row"' in deployment
    assert "id=\"npoDeployed\"" in deployment
    assert "id=\"playerDeployed\"" in deployment
    assert "${factionGuidanceHtml()}" in deployment
    assert "const npoDeploymentSatisfied=!hasStartingNpos||allNposPlaced;" in deployment
    assert "playerValid&&state.playerDeployed&&npoDeploymentSatisfied&&allPlacementChecked" in deployment


def test_rules_still_use_collapsible_faction_guidance_and_setup_handlers():
    guidance = APP.split("  function factionGuidanceHtml(", 1)[1].split(
        "  function playerDisplayIdentity(", 1
    )[0]
    assert '<details class="mission-rule faction-rule-disclosure">' in guidance
    assert "forwardScoutingParent" in guidance
    assert 'faction-rule-disclosure' in guidance
    assert "Resolve these rules on the tabletop" in guidance
    setup_handlers = APP.split("  function bindSetup(", 1)[1].split(
        "\n  function ", 1
    )[0]
    assert "checkAllDeployment" in setup_handlers
    assert "playerDeployed" in setup_handlers
    assert "setupNext" in setup_handlers


def test_version_and_syntax_synchronized_without_save_changes():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 216)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f"V{CURRENT_APP_VERSION}" in html
    assert f"app.js?v={CURRENT_APP_VERSION}" in html
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    parsed = subprocess.run(
        ["node", "--check", "app.js"], cwd=ROOT, text=True,
        capture_output=True, timeout=30
    )
    assert parsed.returncode == 0, parsed.stderr
