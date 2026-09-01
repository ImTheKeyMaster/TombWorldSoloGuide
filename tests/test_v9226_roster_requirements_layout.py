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


def source_between(start, end):
    return APP.split(start, 1)[1].split(end, 1)[0]


ROSTER = source_between("if(stepId==='playerRoster')", "if(stepId==='options')")
VALIDATION = source_between("function playerRosterValidation", "function factionGuidanceHtml")
BINDINGS = source_between("function bindSetup(stepId)", "function advanceSetupStep")
RANDOM = source_between("function randomPlayerRoster", "function save()")


def test_requirements_panel_is_removed_and_headers_are_metadata_driven():
    assert "Roster Requirements" not in ROSTER
    assert "player-roster-summary" not in ROSTER
    assert "categorySelected" in ROSTER
    assert "rosterCategoryRequirementText(category)" in ROSTER
    assert "requiredCount:metadata.requiredCount" in ROSTER
    assert "maxCount:metadata.maxCount" in ROSTER
    for label in ("Veteran Sergeant", "Vox-Relay Beacon", "Specialists", "Troopers"):
        assert f"'{label}'" not in ROSTER
        assert f'"{label}"' not in ROSTER


def test_category_constraint_formatter_supports_all_metadata_combinations():
    helper = source_between(
        "function rosterCategoryRequirementText(category,accessible=false)",
        "function inlineOperativeList",
    )
    assert "category.requiredCount" in helper
    assert "category.maxCount" in helper
    assert "'required':'Req'" in helper
    assert "'maximum':'Max'" in helper
    assert "Exactly" not in helper
    assert "${categorySelected} selected" in ROSTER
    assert "constraints.length" in ROSTER
    assert "constraints.join(' · ')" in ROSTER


def test_category_constraint_formatter_runtime_output():
    helper = "function rosterCategoryRequirementText(category,accessible=false)" + source_between(
        "function rosterCategoryRequirementText(category,accessible=false)",
        "function inlineOperativeList",
    )
    script = f"""
{helper}
const categories = [
  {{requiredCount: 1, maxCount: 1}},
  {{maxCount: 9}},
  {{requiredCount: 2}},
  {{}}
];
console.log(JSON.stringify({{
  visible: categories.map(category => rosterCategoryRequirementText(category)),
  accessible: categories.map(category => rosterCategoryRequirementText(category, true))
}}));
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {
        "visible": [["Req 1", "Max 1"], ["Max 9"], ["Req 2"], []],
        "accessible": [["required 1", "maximum 1"], ["maximum 9"], ["required 2"], []],
    }


def test_spectre_category_metadata_produces_requested_statuses():
    team = json.loads((ROOT / "Player_Operatives" / "SpectreSquad.json").read_text())
    counts = {"leader": 1, "support": 1, "specialists": 4, "troopers": 5}
    statuses = {}
    for category in team["rosterCategories"]:
        parts = [f"{counts[category['id']]} selected"]
        if category.get("requiredCount"):
            parts.append(f"Req {category['requiredCount']}")
        if "maxCount" in category:
            parts.append(f"Max {category['maxCount']}")
        statuses[category["label"]] = " · ".join(parts)
    assert statuses == {
        "Veteran Sergeant": "1 selected · Req 1 · Max 1",
        "Vox-Relay Beacon": "1 selected · Req 1 · Max 1",
        "Specialists": "4 selected · Max 9",
        "Troopers": "5 selected · Max 9",
    }


def test_loadout_status_row_is_hidden_but_loadout_logic_and_names_remain():
    assert "Loadout choices:" not in ROSTER
    assert "Loadout choices:" in VALIDATION
    assert "selectionGroupMaximum" in VALIDATION
    assert "selectionGroupBlocked" in ROSTER
    assert "selectionGroupMaximum" in RANDOM
    assert "Choose only one loadout for each operative." in BINDINGS
    assert "playerName(o.id)" in ROSTER
    assert "inlineOperativeList" in ROSTER


def test_selected_roster_combines_existing_readiness_count_and_names():
    assert "selected-roster-summary" in ROSTER
    assert "Selected roster" in ROSTER
    assert "Roster Status:" in ROSTER
    assert "${valid?' ready':''}" in ROSTER
    assert "${valid?'✓ Ready':'Incomplete'}" in ROSTER
    assert "inlineOperativeList(selectedDefs.map(o=>escapeHtml(playerName(o.id))))" in ROSTER
    assert "const valid=validation.valid&&requiredLeaderSelected" in ROSTER
    assert "Roster Ready</button>" in ROSTER


def test_intrinsic_header_layout_wraps_only_when_needed():
    heading = re.search(r"\.roster-category-heading\{([^}]*)\}", CSS).group(1)
    title = re.search(r"\.roster-category-title\{([^}]*)\}", CSS).group(1)
    status = re.search(r"\.roster-category-status\{([^}]*)\}", CSS).group(1)
    assert "flex-wrap:wrap" in heading
    assert "min-width:max-content" in title
    assert "white-space:nowrap" in status
    assert "margin-left:auto" in status
    assert not re.search(r"@media[^{}]*\{[^{}]*\.roster-category-status", CSS)
    assert "viewport" not in ROSTER.lower()


def test_accordion_and_selection_enforcement_paths_remain():
    assert "data-roster-category-toggle" in ROSTER
    assert "aria-expanded" in ROSTER
    assert "aria-controls" in ROSTER
    assert "expandedRosterCategories" in BINDINGS
    assert "content.hidden=expanded" in BINDINGS
    assert "categoryBlocked" in ROSTER
    assert "selected.size>=maxRoster" in ROSTER
    assert "playerRosterValidation([...selected])" in ROSTER
    assert "randomPlayerRoster();save();render();" in BINDINGS
    assert "autoSelectRequiredPlayerOperatives()" in APP


def test_save_and_release_surfaces_are_v9226():
    expected = ".".join(map(str, (9, 2, 26)))
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert INDEX.count(f"?v={expected}") == 10
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
