import pathlib
import unittest


class NpoRosterReadOnlyActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = pathlib.Path("app.js").read_text()

    def function_source(self, start, end):
        return self.app[self.app.index(start):self.app.index(end)]

    def test_roster_preserves_status_badges_without_activation_controls(self):
        roster = self.function_source("function renderRoster()", "function renderPlayerRoster()")
        card = self.function_source("function npoRosterCard", "function operativeCard")

        self.assertNotIn("data-ready", roster)
        self.assertNotIn("data-ready", card)
        self.assertNotIn(">Expend<", card)
        self.assertIn("operative-status-badge", card)
        self.assertIn("n.ready?'READY':'ACTIVATED'", card)

    def test_automatic_activation_logic_remains_available(self):
        self.assertIn("function nextNpo(){return readyNpos()", self.app)
        self.assertIn("n.ready=false", self.app)
        self.assertNotIn("function toggleReady", self.app)

    def test_every_npo_roster_status_exposes_the_same_removal_action(self):
        roster = self.function_source("function renderRoster()", "function renderPlayerRoster()")
        card = self.function_source("function npoRosterCard", "function operativeCard")

        self.assertIn("state.roster.map(n=>npoRosterCard(n,true))", roster)
        self.assertIn('data-delete="${n.id}">Remove NPO</button>', card)
        self.assertNotIn(">Delete</button>", card)


if __name__ == "__main__":
    unittest.main()
