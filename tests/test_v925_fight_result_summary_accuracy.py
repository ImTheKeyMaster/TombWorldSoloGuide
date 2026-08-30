"""Focused acceptance coverage for mathematically complete Fight summaries."""
from pathlib import Path
import json
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


def body(name):
    match = re.search(rf"  (?:async )?function {re.escape(name)}\([^\n]*\)\{{", APP)
    assert match, name
    depth = 0
    for index in range(APP.find("){", match.start()) + 1, len(APP)):
        if APP[index] == "{":
            depth += 1
        elif APP[index] == "}":
            depth -= 1
            if depth == 0:
                return APP[match.start():index + 1]
    raise AssertionError(name)


def run_summary(fight, result):
    script = f"""
function titleCaseRuleId(value){{return String(value).replace(/^./,char=>char.toUpperCase());}}
function otherFightRole(role){{return role==='attacker'?'defender':'attacker';}}
{body('fightResultExplanation')}
const output=fightResultExplanation({json.dumps(fight)},{json.dumps(result)});
process.stdout.write(JSON.stringify(output));
"""
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
    return completed.stdout


def participant(label, retained=1):
    return {"label": label, "attackDice": [{"retained": True}] * retained}


def test_playtest_summary_reconciles_both_totals_and_keeps_block_separate():
    fight = {
        "attacker": participant("Canoptek Scarab Swarm"),
        "defender": participant("Aegis"),
        "history": [
            {"type": "strike", "role": "attacker", "before": 15, "after": 14},
            {"type": "block", "role": "defender", "blockedKinds": ["normal"]},
            {"type": "strike", "role": "defender", "before": 10, "after": 6},
            {"type": "strike", "role": "attacker", "before": 14, "after": 12},
            {"type": "strike", "role": "attacker", "before": 12, "after": 10},
        ],
    }
    summary = run_summary(fight, {"attackerDamageDealt": 5, "defenderDamageDealt": 4})
    assert "Aegis blocked 1 Canoptek Scarab Swarm Normal Success." in summary
    assert "Canoptek Scarab Swarm dealt 5 total Strike damage." in summary
    assert "Aegis dealt 4 total Strike damage." in summary
    assert "struck for 1" not in summary and "then struck for 2" not in summary


def test_zero_and_one_sided_damage_are_explicit_without_inventing_zero_strikes():
    both_zero = {"attacker": participant("A", 0), "defender": participant("D", 0), "history": []}
    assert "No damage was dealt." in run_summary(both_zero, {"attackerDamageDealt": 0, "defenderDamageDealt": 0})
    attacker_zero = {"attacker": participant("A", 0), "defender": participant("D"), "history": []}
    output = run_summary(attacker_zero, {"attackerDamageDealt": 0, "defenderDamageDealt": 5})
    assert "A retained no successes." in output and "D dealt 5 total Strike damage." in output
    assert "A dealt 0" not in output
    defender_zero = {"attacker": participant("A"), "defender": participant("D", 0), "history": []}
    output = run_summary(defender_zero, {"attackerDamageDealt": 6, "defenderDamageDealt": 0})
    assert "D retained no successes." in output and "A dealt 6 total Strike damage." in output


def test_blocks_are_compact_for_multiple_successes_and_both_roles():
    fight = {
        "attacker": participant("Scarab"), "defender": participant("Aegis"),
        "history": [
            {"type": "block", "role": "defender", "blockedKinds": ["normal", "normal"]},
            {"type": "block", "role": "attacker", "blockedKinds": ["critical"]},
        ],
    }
    output = run_summary(fight, {"attackerDamageDealt": 0, "defenderDamageDealt": 0})
    assert "Aegis blocked 2 Scarab Normal Successes." in output
    assert "Scarab blocked 1 Aegis Critical Success." in output
    assert "No damage was dealt." in output


def test_summary_has_no_partial_strike_selection_or_truncation():
    explanation = body("fightResultExplanation")
    assert "strikes[0]" not in explanation
    assert "strikes.at(-1)" not in explanation
    assert "slice(0,3)" not in explanation
    assert "entry.type==='block'" in explanation
    assert "attackerDamageDealt>0" in explanation
    assert "defenderDamageDealt>0" in explanation


def test_v1_result_is_rebuilt_as_v2_without_replaying_fight():
    finish = body("finishFight")
    result = body("buildFightResult")
    assert "resultVersion:2" in result
    assert "fight.result?.resultVersion===2" in finish
    assert "!fight.resultCommitted||!completeResult" in finish
    assert "commitFightStrike" not in finish and "commitFightBlock" not in finish
    assert "!fight.resultLogged" in finish


def test_release_and_save_versions():
    expected = ".".join(map(str, (9, 2, 5)))
    assert CURRENT_APP_VERSION == expected
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()
    assert f"const APP_VERSION = '{expected}';" in (ROOT / "service-worker.js").read_text()
    assert f"tomb-world-battle-guide-{expected}" == f"tomb-world-battle-guide-{CURRENT_APP_VERSION}"
