"""Regression coverage for restoring a saved Fight before global state exists."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NORMALIZER = "function normalizeFightState(" + APP.split(
    "function normalizeFightState(", 1
)[1].split("  function otherFightRole(", 1)[0]


def test_saved_fight_uses_the_normalized_roster():
    assert "normalizeFightState(raw.fightState,merged.roster)" in APP
    assert "function normalizeFightState(fight,roster)" in NORMALIZER
    assert "state.roster" not in NORMALIZER


def test_completed_fight_restores_before_global_state_is_initialized():
    fight = {
        "version": 1,
        "id": "saved-fight-123",
        "attacker": {
            "id": "marine-1", "side": "player", "label": "Deathwatch",
            "profile": {"name": "Power weapon"},
            "wounds": 7, "attackDice": [{"value": 6, "kind": "crit"}],
            "attackDiceComplete": True,
        },
        "defender": {
            "id": "necron-1", "side": "npo", "label": "Macrocyte",
            "profile": {"name": "Claws"},
            "wounds": 0, "attackDice": [{"value": 4, "kind": "normal"}],
            "attackDiceComplete": True,
        },
        "successes": {"attacker": [{"status": "resolved"}], "defender": []},
        "history": [{"type": "strike", "role": "attacker"}],
        "result": {"resultVersion": 2, "transactionId": "saved-fight-123"},
        "resultCommitted": True,
        "completed": True,
        "resultAcknowledged": False,
        "attackerWithinTwo": False,
    }
    script = (
        "'use strict';\n"
        "const state = undefined;\n"
        "const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value);\n"
        + NORMALIZER + "\n"
        + "const fight = " + json.dumps(fight) + ";\n"
        + "const restored = normalizeFightState(fight,[{id:'necron-1',type:'Canoptek Macrocyte Warrior'}]);\n"
        + "if(!restored.attackerWithinTwo)throw Error('Macrocyte proximity was lost');\n"
        + "if(restored.result.transactionId !== fight.result.transactionId)throw Error('Fight result lost');\n"
        + "if(!restored.completed || restored.resultAcknowledged)throw Error('Fight result display state lost');\n"
        + "if(restored.history.length !== 1 || !restored.attacker.attackDiceComplete)throw Error('Dice/history lost');\n"
        + "const other = normalizeFightState(fight,[{id:'necron-1',type:'Necron Warrior'}]);\n"
        + "if(other.attackerWithinTwo)throw Error('Non-Macrocyte proximity changed');\n"
        + "process.stdout.write('saved Fight restored');\n"
    )
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "saved Fight restored"
