#!/usr/bin/env python3
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


class BoardSetupChecklistHighlightTests(unittest.TestCase):
    @staticmethod
    def source(start, end):
        return APP.split(start, 1)[1].split(end, 1)[0]

    def test_setup_checklist_rows_only_receive_the_normal_class(self):
        checklist = self.source("function setupChecklistHtml(checks)", "function setupContent(stepId)")

        self.assertIn('class="check-row"', checklist)
        self.assertNotIn("required-confirmation-row", checklist)
        self.assertNotIn("breach-points", checklist)
        self.assertNotRegex(checklist, r'class="check-row[^"\\]*\\$\\{')

    def test_intentional_required_confirmation_emphasis_remains(self):
        self.assertIn(
            ".required-confirmation-row:has(input:not(:checked))",
            STYLES,
        )
        self.assertIn(
            'class="check-row required-confirmation-row"><input id="endChecked"',
            APP,
        )
        self.assertIn(
            'class="check-row required-confirmation-row"><input id="tabletopCheckConfirmed"',
            APP,
        )

    def test_board_ready_completion_and_handlers_are_unchanged(self):
        killzone = self.source("if(stepId==='killzone')", "if(stepId==='team')")
        handlers = self.source("function bindSetup(stepId)", "function renderSetup()")

        self.assertIn(
            "const allChecked=checks.length>0&&checks.every(check=>state.setupChecks[check.id]);",
            killzone,
        )
        self.assertIn("id=\"setupNext\" ${allChecked?'':'disabled'}>Board Ready", killzone)
        self.assertIn(
            "state.setupChecks[c.dataset.check]=c.checked;save();render();",
            handlers,
        )
        self.assertIn(
            "missionSetupChecks('killzone').forEach(check=>{state.setupChecks[check.id]=true;});save();render();",
            handlers,
        )

    def test_release_versions_and_save_schema(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', index)
        self.assertTrue(readme.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)


if __name__ == "__main__":
    unittest.main()
