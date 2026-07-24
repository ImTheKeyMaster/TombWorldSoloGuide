import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RosterWoundRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text()

    def source(self, start, end):
        return self.app.split(start, 1)[1].split(end, 1)[0]

    def test_player_healing_preserves_activation_history(self):
        adjustment = self.source("function adjustPlayerWounds", "function adjustWounds")
        restoration = adjustment.split("else if(before===0)", 1)[1]

        self.assertIn("casualties.delete(id)", restoration)
        self.assertNotIn("playerActivatedIds", restoration)
        self.assertIn("if(!state.playerActivatedIds.includes(id))state.playerActivatedIds.push(id)", adjustment)

    def test_out_of_action_npo_cannot_restore_above_active_limit(self):
        adjustment = self.source("function adjustWounds", "function toggleReady")

        self.assertIn("wasOut&&wounds>0&&activeNpos().length>=MAX_NPOS", adjustment)
        self.assertIn("Only ${MAX_NPOS} active NPOs can be on the battlefield.", adjustment)
        self.assertLess(adjustment.index("activeNpos().length>=MAX_NPOS"), adjustment.index("n.wounds=wounds"))

    def test_valid_npo_restoration_is_deployed_dormant_and_not_ready(self):
        adjustment = self.source("function adjustWounds", "function toggleReady")
        restoration = adjustment.split("else if(wasOut){", 1)[1]

        self.assertIn("n.deployed=true", restoration)
        self.assertIn("n.battlefieldState='deployed'", restoration)
        self.assertIn("n.dormant=true", restoration)
        self.assertIn("n.ready=false", restoration)


if __name__ == "__main__":
    unittest.main()
