import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class Stage8ModeAndOwnershipTests(unittest.TestCase):
    def test_versions_and_branding_remain_at_stage8_boundary(self):
        self.assertRegex(APP, r"const APP_VERSION = '[0-9]+\.[0-9]+\.[0-9]+';")
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        self.assertIn("Tomb World Solo Guide", APP)
        self.assertNotIn("Tomb World Battle Guide", APP)

    def test_mode_defaults_and_import_normalization_remain_compatible(self):
        self.assertIn("const gameMode=save.gameMode==='pvp'?'pvp':'solo';", PERSISTENCE)
        self.assertIn("merged.gameMode=raw.gameMode===null?null:(raw.gameMode==='pvp'?'pvp':'solo');", APP)
        self.assertIn("if(!state.gameMode){renderGameModeSelection();return;}", APP)

    def test_solo_and_pvp_keep_one_dice_provider(self):
        provider = re.search(r"async function requestDiceResults\(request\)\{(.+?)\n  \}", APP, re.S)
        self.assertIsNotNone(provider)
        self.assertIn("if(!isPvpMode())return rollDice", provider.group(1))
        self.assertIn("requestManualDiceResults", provider.group(1))
        self.assertNotIn("soloCombat", APP)
        self.assertNotIn("pvpCombat", APP)

    def test_pvp_necron_path_does_not_use_ai_recommendations(self):
        picker = re.search(r"function renderHumanNpoActionPicker\(n\)\{(.+?)\n  \}", APP, re.S)
        self.assertIsNotNone(picker)
        self.assertIn("legalHumanNpoActions", picker.group(1))
        self.assertNotIn("recommendedNpoActions", picker.group(1))
        self.assertNotIn("chooseNpoDecision", picker.group(1))
        self.assertIn("isPvpMode()?humanNpoDecision(n,pendingAction.name):chooseNpoDecision", APP)

    def test_solo_ai_ranking_and_target_priority_remain_available(self):
        for function_name in (
            "npoBehavior", "rankLegalNpoActions", "recommendedNpoActions",
            "chooseNpoDecision", "npoMovementInquiry",
        ):
            self.assertIn(f"function {function_name}(", APP)
        self.assertIn("const targetPriority=!isPvpMode()", APP)
        self.assertIn("if(isPvpMode()){", APP)


class Stage8TerminologyTests(unittest.TestCase):
    def test_presentation_helpers_preserve_internal_npo_model(self):
        self.assertIn("function opponentSingularLabel(){return isPvpMode()?'Necron':'NPO';}", APP)
        self.assertIn("function opponentPluralLabel(){return isPvpMode()?'Necrons':'NPOs';}", APP)
        self.assertIn("function presentSideTerminology(text)", APP)
        self.assertIn("function npoBehavior(", APP)
        self.assertIn("function renderNpoDecisionResult(", APP)

    def test_pvp_roster_uses_mode_aware_labels(self):
        self.assertIn("Add ${escapeHtml(opponentSingularLabel())}", APP)
        self.assertIn("Remove ${escapeHtml(opponentSingularLabel())}", APP)
        self.assertIn("No ${escapeHtml(opponentPluralLabel())} are currently", APP)
        self.assertNotIn(">Add NPO</button>", APP)
        self.assertNotIn(">Remove NPO</button>", APP)

    def test_mission_side_labels_are_mode_aware(self):
        self.assertIn("<small>Starting ${escapeHtml(opponentPluralLabel())}</small>", APP)
        self.assertIn("missionFirstInitiative(m)==='npo'?opponentPluralLabel():playerSideLabel()", APP)
        self.assertIn("<strong>${escapeHtml(opponentSingularLabel())} deployment:</strong>", APP)
        self.assertNotIn("<small>Starting NPOs</small>", APP)
        self.assertNotIn("<strong>NPO deployment:</strong>", APP)

    def test_mission_event_and_journal_text_translate_only_at_rendering(self):
        self.assertIn("presentSideTerminology(event.text)", APP)
        self.assertIn("presentSideTerminology(description)", APP)
        self.assertIn("presentSideTerminology(m.victory?.win", APP)
        self.assertIn("presentSideTerminology(j.text)", APP)

    def test_help_is_conceptually_mode_specific(self):
        self.assertIn("The second player controls the Necrons", APP)
        self.assertIn("it does not choose Necron actions or targets", APP)
        self.assertIn("A non-player operative controlled by the Guide’s decision tree.", APP)
        self.assertIn("The Guide rolls gameplay dice automatically.", APP)
        self.assertIn("Roll physical dice and enter each result when prompted.", APP)


class Stage8DeadlyEncountersTests(unittest.TestCase):
    def test_deadly_encounters_is_non_destructively_gated_to_solo(self):
        self.assertIn("function deadlyEncountersActive(){return !isPvpMode()&&state.deadlyEncountersEnabled===true;}", APP)
        self.assertIn("if(deadlyEncountersActive())log('Deadly Encounters", APP)
        self.assertIn("if(!deadlyEncountersActive())return;", APP)
        self.assertIn("Unavailable (Solo only)", APP)
        self.assertNotIn("merged.deadlyEncountersEnabled=false", APP)

    def test_pvp_setup_cannot_enable_deadly_encounters(self):
        self.assertIn("const deadlyOption=isPvpMode()?", APP)
        self.assertIn("is available in Solo battles only", APP)
        self.assertIn("if(isPvpMode())return;state.deadlyEncountersEnabled=e.target.checked", APP)

    def test_restless_tomb_remains_available_in_both_modes(self):
        listener = "state.restlessTombEnabled=e.target.checked;save();render();"
        self.assertIn(listener, APP)
        self.assertNotIn("isPvpMode()&&state.restlessTombEnabled", APP)


class Stage8PersistenceAndInteractionTests(unittest.TestCase):
    def test_pending_dice_remains_pvp_only_and_resume_kinds_are_preserved(self):
        self.assertIn("if(!pending||!isPvpMode()||state.completed||state.gameEnd)return false;", APP)
        self.assertIn("if(!isPvpMode())return rollDice", APP)
        for kind in ("mission", "event", "strategy", "combat", "player-activation", "hot", "npo-special-action", "breach-sarcophagus"):
            self.assertIn(f"resumeKind:'{kind}'", APP)

    def test_new_game_still_clears_pending_dice_and_returns_to_mode_selection(self):
        self.assertIn("pendingDice:null", PERSISTENCE)
        self.assertIn("state.gameMode=null", APP)
        self.assertIn("renderGameModeSelection", APP)

    def test_touch_and_manual_dice_accessibility_guards_remain(self):
        self.assertIn("document.addEventListener('touchend'", APP)
        self.assertIn("e.target?.closest?.('button, input, select, textarea", APP)
        self.assertIn('aria-live="polite"', APP)
        self.assertIn("Commit Results", INDEX)
        self.assertIn("Undo", INDEX)
        self.assertIn("modal.addEventListener('keydown'", APP)


if __name__ == "__main__":
    unittest.main()
