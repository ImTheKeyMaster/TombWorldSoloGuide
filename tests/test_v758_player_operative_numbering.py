import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()


class PlayerOperativeNumberingTests(unittest.TestCase):
    def test_finalized_numbers_are_persisted_by_operative_id(self):
        self.assertIn("playerDisplayNumbers:{}", APP)
        self.assertIn("if(stepId==='playerRoster')assignPlayerDisplayNumbers()", APP)
        self.assertIn("state.playerDisplayNumbers[id]=allocateDisplayNumber(used)", APP)
        self.assertIn("merged.playerDisplayNumbers=isRecord(raw?.playerDisplayNumbers)", APP)

    def test_player_and_npo_numbering_share_the_same_allocator(self):
        self.assertIn("function allocateDisplayNumber(usedNumbers,preferredNumber)", APP)
        self.assertIn("npo.displayNumber=allocateDisplayNumber(used,preferredNumber)", APP)
        self.assertIn("state.playerDisplayNumbers[id]=allocateDisplayNumber(used)", APP)

    def test_display_name_uses_current_roster_without_renumbering_casualties(self):
        operative_name = APP[APP.index("function operativeName"):APP.index("function allocateDisplayNumber")]
        self.assertIn("state.playerRoster||[]", operative_name)
        self.assertIn("state.roster||[]", operative_name)
        self.assertNotIn("playerCasualtyIds", operative_name)
        self.assertNotIn("livingPlayerOperative", operative_name)

    def test_player_and_npo_names_use_one_shared_formatter(self):
        self.assertIn("return operativeName(id,'player')", APP)
        self.assertIn("return operativeName(n,'npo')", APP)

    def test_special_action_messages_do_not_bypass_the_shared_formatter(self):
        self.assertNotIn("target.name||npoName(target)", APP)
        self.assertIn("action.target?.side==='enemy'?playerName(targetId):npoName(target)", APP)

    def test_roster_and_auxiliary_views_use_canonical_player_name(self):
        for expected in (
            "chosen?playerName(o.id):o.name",
            "selectedDefs.map(o=>escapeHtml(playerName(o.id)))",
            "map(id=>escapeHtml(playerName(id)))",
            "<h4>${escapeHtml(playerName(id))}</h4>",
            "label:`Player — ${playerName(operative.id)}`",
        ):
            self.assertIn(expected, APP)


if __name__ == "__main__":
    unittest.main()
