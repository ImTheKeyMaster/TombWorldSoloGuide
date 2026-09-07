import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_escape_objective_and_battle_completion_are_separate():
    result_body = re.search(
        r"function shiftingLabyrinthResult\(.*?\n  \}", APP, re.DOTALL
    ).group(0)
    assert "removed.size<total" in result_body
    assert "escaped.size>=requiredEscapes" in result_body
    assert "OBJECTIVE MET" in APP
    assert "escapeObjectiveMet" in APP


def test_escape_target_dialog_shows_distinct_counts_and_extraction_copy():
    assert "✓ Mission Objective Achieved" in APP
    assert "Escape Requirement:" in APP
    assert "Total Escaped:" in APP
    assert "Operatives Remaining:" in APP
    assert "Continue Extraction" in APP
    assert "Continue until every operative has left the killzone." not in APP


def test_escape_target_is_announced_and_logged_once():
    assert "objectiveAchieved:false" in APP
    assert "!state.missionState.objectiveAchieved" in APP
    assert "state.missionState.objectiveAchieved=true" in APP
    assert (
        "Mission objective achieved: ${model.target} operatives escaped. "
        "Extraction may continue."
    ) in APP


def test_escape_target_is_suppressed_only_after_continue_extraction():
    assert "objectiveAcknowledged:false" in APP
    assert "raw.objectiveAcknowledged||raw.objectiveAchieved" in APP
    assert "model?.completed&&!state.missionState.objectiveAcknowledged" in APP
    assert 'id="continueExtraction"' in APP
    assert "state.missionState.objectiveAcknowledged=true" in APP


def test_shifting_labyrinth_definition_does_not_end_battle_at_target():
    definition = json.loads(
        (ROOT / "Missions/definition-01-shifting-labyrinth.json").read_text(
            encoding="utf-8"
        )
    )
    assert definition["completion"]["endsBattle"] is False
    assert definition["dialogs"]["objectiveComplete"]["title"] == "ESCAPE TARGET MET"
