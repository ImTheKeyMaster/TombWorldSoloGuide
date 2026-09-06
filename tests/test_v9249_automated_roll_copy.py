import json
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def mission(number, slug):
    return json.loads((ROOT / "Missions" / f"{number}-{slug}.json").read_text(encoding="utf-8"))


def definition(number, slug):
    return json.loads(
        (ROOT / "Missions" / f"definition-{number}-{slug}.json").read_text(encoding="utf-8")
    )


def rule(data, name):
    return next(item for item in data["rules"] if item["name"] == name)["summary"]


def setup(data, check_id="starting-npos"):
    return next(item for item in data["setupChecks"] if item["id"] == check_id)["label"]


def action(data, action_id):
    return next(item for item in data["actions"] if item["id"] == action_id)


def test_release_version_surfaces_are_9249():
    expected = ".".join(map(str, (9, 2, 49)))
    assert CURRENT_APP_VERSION == expected
    assert f"const APP_VERSION = '{expected}';" in (ROOT / "service-worker.js").read_text()
    assert f'<div class="version">V{expected}</div>' in (ROOT / "index.html").read_text()
    assert (ROOT / "README.md").read_text().startswith(
        f"# Tomb World Battle Guide v{expected}\n\n## v{expected}"
    )
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_known_automated_mission_rules_name_the_guide_and_preserve_dice_notation():
    mission_01 = mission("01", "shifting-labyrinth")
    mission_03 = mission("03", "recover-transponder")
    mission_04 = mission("04", "destroy-sarcophagus")
    mission_05 = mission("05", "scout-sub-crypt")

    expected = {
        "auspex": (rule(mission_01, "Auspex Calibration"), "D3+3"),
        "locate": (rule(mission_03, "Locate Item"), "D3"),
        "breach": (rule(mission_04, "Sarcophagus"), "2D6"),
        "repair": (rule(mission_04, "Nanoscarab Repair"), "D6"),
        "awaken": (rule(mission_05, "Awaken Rooms"), "D3"),
    }
    for text, notation in expected.values():
        assert "Guide automatically" in text
        assert notation in text
    assert "Roll D3:" not in expected["auspex"][0]
    assert "rolls the direction result and the D3+3 distance" in expected["auspex"][0]
    assert "only one unresolved marker remains" in expected["locate"][0]
    assert "without a roll" in expected["locate"][0]


def test_automated_action_descriptions_name_the_guide():
    locate = action(definition("03", "recover-transponder"), "searchTransponder")
    breach = action(definition("04", "destroy-sarcophagus"), "breachSarcophagus")
    awaken = action(definition("05", "scout-sub-crypt"), "awakenRoom")
    for item in (locate, breach, awaken):
        assert "Guide automatically" in item["description"]
    assert "D3" in locate["description"] and "2D6" in breach["description"]
    assert "D3" in awaken["description"] and "maximum of 5" in awaken["description"]


def test_starting_npo_copy_names_the_guide_and_formulas_are_unchanged():
    missions = {
        "01-shifting-labyrinth": "2D3+3",
        "02-demolition-protocol": "2D3+3",
        "03-recover-transponder": "2D3+3",
        "04-destroy-sarcophagus": "D3+6",
        "06-regroup": "2D3+3",
    }
    for key, formula in missions.items():
        number, slug = key.split("-", 1)
        data = mission(number, slug)
        assert data["startingNpos"]["formula"] == formula
        assert f"Guide automatically generates the {formula} starting NPO roster" in setup(data)


def test_mission_dice_operations_and_comparisons_are_unchanged():
    mission_01 = definition("01", "shifting-labyrinth")
    mission_03 = definition("03", "recover-transponder")
    mission_04 = definition("04", "destroy-sarcophagus")
    mission_05 = definition("05", "scout-sub-crypt")
    auspex = action(mission_01, "auspexCalibration")["operations"]
    locate = action(mission_03, "searchTransponder")
    breach = action(mission_04, "breachSarcophagus")
    repair = mission_04["hooks"]["onStrategyPhaseReadyStep"][0]["operations"]
    awaken = action(mission_05, "awakenRoom")

    assert [item["dice"] for item in auspex] == [{"count": 1, "sides": 3}] * 2
    assert locate["diceExpression"] == "1D3"
    assert locate["comparison"] == "roll > otherRemainingMarkerCount"
    assert next(item for item in breach["operations"] if item["id"] == "breachRoll")["dice"] == {
        "count": 2,
        "sides": 6,
    }
    assert next(item for item in repair if item.get("id") == "repairRoll")["dice"] == {
        "count": 1,
        "sides": 6,
    }
    assert next(item for item in awaken["operations"] if item["id"] == "awakenRoll")["dice"] == {
        "count": 1,
        "sides": 3,
    }


def test_initiative_reinforcement_and_phasing_ownership_copy_matches_runtime():
    assert "automatically rolls one D6 for each side to determine initiative after Turning Point 1" in APP
    assert "The Guide automatically determined and generated this Turning Point’s reinforcements" in APP
    assert "Randomly determine an open hatchway" in APP
    phasing = rule(mission("06", "regroup"), "Phasing Points")
    assert "randomly determined open hatchway" in phasing
    assert "Guide automatically" not in phasing


def test_focused_copy_audit_rejects_old_bare_imperatives():
    automated_copy = [
        rule(mission("01", "shifting-labyrinth"), "Auspex Calibration"),
        rule(mission("03", "recover-transponder"), "Locate Item"),
        rule(mission("04", "destroy-sarcophagus"), "Nanoscarab Repair"),
        action(definition("03", "recover-transponder"), "searchTransponder")["description"],
        action(definition("04", "destroy-sarcophagus"), "breachSarcophagus")["description"],
        action(definition("05", "scout-sub-crypt"), "awakenRoom")["description"],
    ]
    for text in automated_copy:
        assert not text.startswith(("Roll D3", "Roll D6", "Roll 2D6"))


def test_other_automated_reference_rules_name_the_guide():
    automated_rules = (
        "the Guide automatically rolls D3 and restores that many lost wounds",
        "The Guide automatically rolls 2D6 separately for each selected operative",
        "the Guide automatically rolls D3 before removal",
        "The Guide automatically rolls 3D3 and restores that many wounds",
        "The Guide automatically selects and tests eligible Player operatives",
        "The Guide automatically selects two random Player operatives",
        "the Guide automatically rolls one D6. On 4+",
        "the Guide automatically rolls one D6. On 5+",
        "the Guide automatically rolls D3 and restores that result plus 2 wounds",
        "The Guide automatically rolls D3 to determine the maximum number of open hatchways",
    )
    for expected_copy in automated_rules:
        assert expected_copy in APP
    assert "Close one breach and up to that many open hatchways" in APP
