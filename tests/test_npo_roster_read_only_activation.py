import pathlib
import unittest


class NpoRosterReadOnlyActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = pathlib.Path("app.js").read_text()
        cls.styles = pathlib.Path("styles.css").read_text()

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

        self.assertIn("npoRosterCard(n,n.battlefieldState==='deployed'||n.wounds<=0)", roster)
        self.assertIn('data-delete="${n.id}">Remove NPO</button>', card)
        self.assertNotIn(">Delete</button>", card)

        wound_controls, removal_control = card.split('</div>`:\'\'}', 1)
        self.assertIn("controls?", wound_controls)
        self.assertNotIn("controls?", removal_control)

    def test_removal_action_is_anchored_without_placeholder_controls(self):
        self.assertIn(
            ".npo-roster-card{position:relative;display:flex;flex-direction:column;overflow:hidden;cursor:default}",
            self.styles,
        )
        self.assertIn(
            ".npo-roster-card .quick-actions{margin-top:auto;padding-top:10px}",
            self.styles,
        )

    def test_eliminated_npo_uses_themed_overlay_without_changing_player_overlay(self):
        self.assertIn('.operative-card.dead:after{content:"☠"', self.styles)
        self.assertIn(
            ".operative-card.dead:after,.npo-roster-card.dead:after{position:absolute;z-index:2",
            self.styles,
        )
        self.assertIn(
            '.npo-roster-card.dead:after{content:"";background:url("Assets/Images/eliminated-necron-skull.png") center/auto 6rem no-repeat;opacity:.16}',
            self.styles,
        )
        self.assertIn(".npo-roster-card>*{position:relative;z-index:1}", self.styles)


if __name__ == "__main__":
    unittest.main()
