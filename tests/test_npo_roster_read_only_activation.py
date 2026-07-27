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

    def test_eliminated_cards_share_prominent_overlay_styling(self):
        self.assertIn('.operative-card.dead:after{content:"☠"', self.styles)
        self.assertIn(
            ".operative-card.dead,.npo-roster-card.dead{opacity:.5}",
            self.styles,
        )
        self.assertIn(
            ".operative-card.dead:after,.npo-roster-card.dead:after{--elimination-overlay-size:6rem;position:absolute;z-index:2",
            self.styles,
        )
        self.assertIn(
            'font-size:var(--elimination-overlay-size);opacity:1;pointer-events:none',
            self.styles,
        )
        self.assertIn(
            '.npo-roster-card.dead:after{content:"";background:url("Assets/Images/eliminated-necron-skull.png") center/auto var(--elimination-overlay-size) no-repeat;filter:brightness(1.4) contrast(1.2) drop-shadow(0 0 2px rgba(255,255,255,.55))}',
            self.styles,
        )
        self.assertIn(".npo-roster-card>*{position:relative;z-index:1}", self.styles)

    def test_eliminated_roster_cards_reuse_activation_tracker_border(self):
        self.assertIn(
            ".tracker-operative.eliminated,\n"
            ".operative-card.dead,\n"
            ".npo-roster-card.dead{\n"
            "  border:2px solid var(--danger);\n"
            "  border-radius:10px;\n"
            "}",
            self.styles,
        )


if __name__ == "__main__":
    unittest.main()
