from pathlib import Path
import json
import subprocess

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    offset = APP.index(start)
    return APP[offset:APP.index(end, offset)]


def evaluate_breach_cost(operative):
    helpers = source("function structuredTextValues", "function breachSarcophagusApCost")
    script = f"{helpers}\nprocess.stdout.write(String(breachApCost({json.dumps(operative)})));"
    return int(subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout)


def test_release_is_v9242_without_changing_save_key():
    assert CURRENT_APP_VERSION == ".".join(("9", "2", str(40 + 2)))
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_breach_catalog_uses_selected_operative_cost_and_existing_action():
    catalog = source("function playerHumanActionCatalog", "function playerHumanActionState")
    assert "{id:'breach',name:'Breach',group:'mission',cost:breachApCost(operative)}" in catalog
    assert catalog.count("id:'breach'") == 1
    assert "{id:'breach',name:'Breach',group:'mission',cost:1}" not in catalog


def test_breach_reduction_uses_structured_datacard_and_weapon_data():
    qualification = source("function operativeQualifiesForBreachReduction", "function breachApCost")
    assert "const {weapons=[], ...datacard}=operative" in qualification
    assert "structuredTextValues(datacard)" in qualification
    assert r"\bbreach marker\b|\bgrenadier\b|\bmine\b" in qualification
    assert "structuredTextValues(weapon.rules)" in qualification
    assert r"^Piercing(?: Crits)? 2(?:\s|$)" in qualification
    assert r"^(?:Blast|Torrent)(?:\s|$)" in qualification
    assert "hasQualifyingRule&&!hasExcludedRule" in qualification
    assert "textContent" not in qualification
    assert "querySelector" not in qualification


def test_reduction_is_binary_and_cost_never_drops_below_one():
    cost = source("function breachApCost", "function breachSarcophagusApCost")
    assert "return operativeQualifiesForBreachReduction(operative)?1:2" in cost
    assert "--" not in cost
    assert "reduce(" not in cost


def test_breach_cost_matrix_covers_each_qualification_and_weapon_exclusion():
    ordinary = {"name": "Trooper", "abilities": [], "weapons": []}
    qualifiers = (
        {"abilities": [{"text": "Place a breach marker."}]},
        {"role": "Grenadier"},
        {"abilities": [{"name": "Melta Mine"}]},
        {"weapons": [{"rules": ["Piercing 2"]}]},
        {"weapons": [{"rules": ["Piercing Crits 2"]}]},
        {"role": "Grenadier", "abilities": [{"name": "Mine"}], "weapons": [{"rules": ["Piercing 2"]}]},
    )
    assert evaluate_breach_cost(ordinary) == 2
    assert all(evaluate_breach_cost({**ordinary, **qualifier}) == 1 for qualifier in qualifiers)
    assert evaluate_breach_cost({"weapons": [{"rules": ["Piercing 2", "Blast 2\""]}]}) == 2
    assert evaluate_breach_cost({"weapons": [{"rules": ["Piercing Crits 2", "Torrent 1\""]}]}) == 2
    assert evaluate_breach_cost({
        "weapons": [
            {"rules": ["Piercing 2", "Blast 2\""]},
            {"rules": ["Piercing Crits 2"]},
        ]
    }) == 1


def test_existing_breach_resolution_effects_are_unchanged():
    completion = source("async function completePlayerActivation", "function npoName")
    assert "if(stage.breach){\n      inc++;" in completion
    assert "commitHumanPlayerAction(stage)" in completion
    assert "stage.missionFeatureCommitted=true" in completion
