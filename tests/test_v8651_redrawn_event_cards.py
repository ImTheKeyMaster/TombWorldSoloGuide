import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()


class RedrawnEventCardTests(unittest.TestCase):
    def test_redrawn_class_is_status_specific(self):
        event_html = APP.split("function strategyEventHtml", 1)[1].split("function activationTracker", 1)[0]
        self.assertIn("event.status==='redrawn'?' tomb-world-event-card--redrawn':''", event_html)
        self.assertIn("tomb-world-event-card${cardStatusClass}", event_html)

    def test_redrawn_card_is_dimmed_by_twenty_five_percent_with_a_diagonal_overlay(self):
        self.assertIn(".tomb-world-event-card--redrawn{filter:brightness(.75)", CSS)
        self.assertIn(".tomb-world-event-card--redrawn::after", CSS)
        self.assertIn("linear-gradient(135deg", CSS)

    def test_redrawn_badge_and_content_remain_above_overlay(self):
        self.assertIn(".tomb-world-event-card--redrawn>*{position:relative;z-index:1}", CSS)
        self.assertIn(".tomb-world-event-card--redrawn .strategy-event-status", CSS)


if __name__ == "__main__":
    unittest.main()
