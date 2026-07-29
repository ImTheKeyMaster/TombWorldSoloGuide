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

    def test_display_name_uses_stored_number_without_renumbering_casualties(self):
        player_name = APP[APP.index("function playerName(id)"):APP.index("function assignPlayerDisplayNumbers()")]
        self.assertIn("state.playerDisplayNumbers?.[id]", player_name)
        self.assertNotIn("playerCasualtyIds", player_name)
        self.assertNotIn("livingPlayerOperative", player_name)

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
