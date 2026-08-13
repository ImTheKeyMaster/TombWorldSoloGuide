import tempfile
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION, read_app_version

ROOT = Path(__file__).resolve().parents[1]


class VersioningTests(unittest.TestCase):
    def test_release_references_match_canonical_app_version(self):
        app = (ROOT / "app.js").read_text()
        worker = (ROOT / "service-worker.js").read_text()
        index = (ROOT / "index.html").read_text()
        readme = (ROOT / "README.md").read_text()

        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", app)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', index)
        for asset in (
            "app.js",
            "deadly-encounters.js",
            "event-effects.js",
            "mission-engine.js",
            "narration.js",
            "persistence.js",
            "styles.css",
        ):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", index)
        self.assertIn(f"const CACHE_NAME = `${{CACHE_PREFIX}}${{APP_VERSION}}`;", worker)
        self.assertTrue(readme.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))

    def test_app_version_parser_rejects_missing_duplicate_and_malformed_declarations(self):
        invalid_sources = (
            "const OTHER_VERSION = '1.2.3';",
            "const APP_VERSION = '1.2.3';\nconst APP_VERSION = '1.2.4';",
            "const APP_VERSION = 'release-candidate';",
        )
        with tempfile.TemporaryDirectory() as directory:
            app_path = Path(directory) / "app.js"
            for source in invalid_sources:
                with self.subTest(source=source):
                    app_path.write_text(source)
                    with self.assertRaisesRegex(RuntimeError, "APP_VERSION"):
                        read_app_version(app_path)

    def test_current_version_is_not_hard_coded_in_test_modules(self):
        offenders = []
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if CURRENT_APP_VERSION in path.read_text():
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(
            offenders,
            [],
            "Current APP_VERSION must come from tests/versioning.py; hard-coded in: "
            + ", ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
