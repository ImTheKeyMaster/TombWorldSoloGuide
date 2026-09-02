import json
import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
SCOUT = json.loads((ROOT / "Player_Operatives" / "ScoutSquad.json").read_text(encoding="utf-8"))
EXPECTED_VERSION = ".".join(map(str, (9, 2, 30)))


def test_forward_scouting_parent_is_authoritative_and_concise():
    parents = [rule for rule in SCOUT["factionRules"] if rule.get("forwardScoutingParent") is True]
    assert len(parents) == 1
    parent = parents[0]
    assert parent["name"] == "Forward Scouting"
    assert parent["timing"] == "End of Set Up Operatives"
    assert parent["selectionCount"] == 6
    assert "up to six Forward Scouting options" in parent["text"]
    assert "both players" in parent["text"]
    assert "initiative" in parent["text"]


def test_all_nine_options_are_data_driven_from_both_sources():
    faction_options = [rule for rule in SCOUT["factionRules"] if rule.get("forwardScoutingOption") is True]
    gambit_options = [rule for rule in SCOUT["strategicGambits"] if rule.get("forwardScoutingOption") is True]
    options = sorted(faction_options + gambit_options, key=lambda option: option["forwardScoutingOrder"])
    assert len(faction_options) == 7
    assert len(gambit_options) == 2
    assert [option["name"] for option in options] == [
        "Redeploy", "Reposition", "Trip Alarm", "Booby Trap", "Tactical Manoeuvre",
        "Diversion", "Devise Plan", "Designate Target", "Spy",
    ]
    assert len({option["id"] for option in options}) == 9
    assert [option["selectionLimit"] for option in options] == [1, 2, 2, 1, 1, 1, 1, 1, 1]
    assert all(option["timing"] and option["text"] for option in options)


def test_renderer_groups_options_without_hard_coded_option_copy():
    renderer = re.search(r"  function factionGuidanceHtml\(kind='rules'\)\{(.*?)\n  \}\n  function playerDisplayIdentity", APP, re.S).group(1)
    assert "playerTeamData?.factionRules" in renderer
    assert "playerTeamData?.strategicGambits" in renderer
    assert "entry.forwardScoutingOption===true" in renderer
    assert "entry.forwardScoutingParent===true" in renderer
    assert "entry.forwardScoutingOption!==true" in renderer
    assert "option.selectionLimit" in renderer
    for option in ("Redeploy", "Reposition", "Trip Alarm", "Booby Trap", "Tactical Manoeuvre",
                   "Diversion", "Devise Plan", "Designate Target", "Spy"):
        assert option not in renderer


def test_native_disclosure_is_collapsed_accessible_and_compact():
    assert '<details class="forward-scouting-disclosure">' in APP
    assert "<summary>" in APP
    assert "View ${count} scouting options" in APP
    assert "Hide ${count} scouting options" in APP
    assert '<details class="forward-scouting-disclosure" open>' not in APP
    assert 'class="forward-scouting-option"' in APP
    assert 'class="mission-rule forward-scouting-rule"' in APP
    assert '.forward-scouting-disclosure summary' in CSS
    assert 'min-height:48px' in CSS
    assert '.forward-scouting-options{border-left:' in CSS
    assert 'overflow-wrap:anywhere' in CSS


def test_strategic_gambits_remain_in_later_gameplay_with_usage_limits():
    gambits = {entry["name"]: entry for entry in SCOUT["strategicGambits"]}
    assert gambits["Tactical Manoeuvre"]["usageLimit"] == {"count": 2, "period": "battle"}
    assert gambits["Diversion"]["usageLimit"] == {"count": 1, "period": "battle"}
    assert "factionGuidanceHtml('gambits')" in APP
    assert "kind==='gambits'?(playerTeamData?.strategicGambits||[])" in APP


def test_other_team_guidance_and_deployment_paths_remain_generic():
    for filename in ("DeathWatch.json", "DeathKorps.json", "Kasrkin.json", "SpectreSquad.json", "TempestusAquilons.json"):
        team = json.loads((ROOT / "Player_Operatives" / filename).read_text(encoding="utf-8"))
        assert not any(rule.get("forwardScoutingOption") is True for rule in team.get("factionRules", []))
        assert not any(rule.get("forwardScoutingOption") is True for rule in team.get("strategicGambits", []))
    assert "${missionRoll}${factionGuidanceHtml()}${hasStartingNpos?" in APP
    assert 'id="playerDeployed" type="checkbox"' in APP
    assert "Resolve these rules on the tabletop; the Guide presents reminders without simulating positioning." in APP


def test_v9230_version_and_save_surfaces():
    assert CURRENT_APP_VERSION == EXPECTED_VERSION
    assert f"const APP_VERSION = '{EXPECTED_VERSION}';" in WORKER
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert f'<div class="version">V{EXPECTED_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={EXPECTED_VERSION}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{EXPECTED_VERSION}\n\n## v{EXPECTED_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
