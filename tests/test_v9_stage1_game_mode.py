import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


class Stage1GameModeTests(unittest.TestCase):
    def test_mode_chooser_precedes_unchanged_numeric_setup_steps(self):
        self.assertIn("gameMode:null", APP)
        self.assertIn("if(!state.gameMode){renderGameModeSelection();return;}", APP)
        self.assertIn('data-game-mode="solo"', APP)
        self.assertIn('data-game-mode="pvp"', APP)
        self.assertIn("state.gameMode=button.dataset.gameMode", APP)
        self.assertEqual(APP.count("steps=['mission','killzone']"), 1)
        self.assertIn("state.setupStep=0", APP)

    def test_presentation_api_drives_primary_surfaces(self):
        for helper in ("isPvpMode", "selectedPlayerTeamName", "playerSideLabel", "opponentSingularLabel", "opponentPluralLabel"):
            self.assertIn(f"function {helper}", APP)
        self.assertIn("<h2>${escapeHtml(teamName)} Activation</h2>", APP)
        self.assertIn("${escapeHtml(opponentSingularLabel())} Activation:", APP)
        self.assertIn("${escapeHtml(playerSideLabel())}<span", APP)
        self.assertIn("${escapeHtml(opponentSingularLabel())}<span", APP)
        self.assertIn("${escapeHtml(opponentSingularLabel())} Roster", APP)
        self.assertIn("${escapeHtml(playerSideLabel())} Roster", APP)
        self.assertIn("${escapeHtml(opponentSingularLabel())} Operatives", APP)
        self.assertIn("presentSideTerminology(j.text)", APP)
        self.assertIn("presentSideTerminology(overview+npoRoster+flow+ai+combat+quick)", APP)
        self.assertIn("${escapeHtml(selectedPlayerTeamName('Player'))} operatives", APP)

    def test_mode_persistence_backward_compatibility_and_reset(self):
        script = r'''
const assert=require('assert');
const p=require('./persistence.js');
const base={saveVersion:p.currentSaveVersion(),roster:[],playerRoster:[],setupStep:3,screen:'setup'};
assert.equal(p.migrateSave(base).gameMode,'solo');
assert.equal(p.migrateSave({...base,gameMode:'bad'}).gameMode,'solo');
assert.equal(p.migrateSave({...base,gameMode:'pvp'}).gameMode,'pvp');
assert.equal(p.migrateSave({...base,gameMode:null}).gameMode,null);
assert.equal(p.migrateSave(base).setupStep,3);
assert.equal(p.createPersistedSave({...base,gameMode:'pvp'}).gameMode,'pvp');
assert.equal(p.resetActiveBattle({...base,gameMode:'pvp'}).gameMode,'pvp');
assert.equal(p.resetActiveBattle(base).gameMode,'solo');
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_internal_npo_engine_and_stage_boundaries_remain_intact(self):
        for identity in ("npoActivated", "readyNpos", "activeNpoId", "npoAttackTargetId", "npoAttackSummary", "npoRuleState", "NPO_ACTION_TRANSITIONS", "npoDefinitions"):
            self.assertIn(identity, APP)
        mode_checks = APP.count("state.gameMode==='pvp'")
        self.assertEqual(mode_checks, 1)
        provider = APP[APP.index("async function requestDiceResults") : APP.index("diceEntryUndo.addEventListener")]
        self.assertNotIn("requestDiceResults(", APP[:APP.index("async function requestDiceResults")])
        self.assertIn("if(!isPvpMode())", provider)

    def test_true_new_game_uses_fresh_unselected_state(self):
        new_game = APP.split("function startNewGameSetup()", 1)[1].split("function confirmNewGame", 1)[0]
        self.assertIn("state=initialState();", new_game)
        self.assertIn("state.screen='setup';", new_game)
        self.assertLess(new_game.index("state=initialState();"), new_game.index("save();"))

    def test_mobile_chooser_uses_existing_touch_friendly_components(self):
        self.assertIn('class="team-select-grid game-mode-grid"', APP)
        self.assertIn('class="team-select-card" data-game-mode="solo"', APP)
        self.assertIn('.btn{', (ROOT / 'styles.css').read_text())
        self.assertIn('min-height:48px', (ROOT / 'styles.css').read_text())


if __name__ == "__main__":
    unittest.main()
