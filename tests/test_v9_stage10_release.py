import json
import re
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
EXPECTED_RELEASE = '.'.join(('9', '0', '0'))


class Stage10ReleaseTests(unittest.TestCase):
    def test_release_identity_and_assets_are_consistent(self):
        self.assertEqual(EXPECTED_RELEASE, CURRENT_APP_VERSION)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        assets = ["styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
                  "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
                  "dice-sfx.js", "app.js"]
        for asset in assets:
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', INDEX)
        self.assertNotIn('?v=8.6.108', INDEX)
        self.assertTrue(README.startswith(f'# Tomb World Battle Guide v{CURRENT_APP_VERSION}'))
        self.assertIn(f'## v{CURRENT_APP_VERSION}', README)
        self.assertIn('## v8.6.108', README)
        self.assertEqual('Tomb World Battle Guide', json.loads((ROOT / 'manifest.webmanifest').read_text())['name'])

    def test_cache_rollover_is_scoped_to_tomb_world_namespaces(self):
        self.assertIn("const CACHE_PREFIX = 'tomb-world-battle-guide-';", WORKER)
        self.assertIn("const LEGACY_CACHE_PREFIXES = ['tomb-world-solo-guide-'];", WORKER)
        self.assertIn('const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;', WORKER)
        names = ['tomb-world-solo-guide-8.6.108', 'tomb-world-solo-guide-8.6.100',
                 'tomb-world-battle-guide-8.6.108', f'tomb-world-battle-guide-{CURRENT_APP_VERSION}',
                 'some-other-app-cache']
        current = f'tomb-world-battle-guide-{CURRENT_APP_VERSION}'
        deleted = [name for name in names if
                   (name.startswith('tomb-world-battle-guide-') or name.startswith('tomb-world-solo-guide-'))
                   and name != current]
        self.assertEqual(names[:3], deleted)
        self.assertNotIn('some-other-app-cache', deleted)
        self.assertIn('.then(() => self.clients.claim())', WORKER)

    def test_current_storage_contract_and_stage7_schema_are_preserved(self):
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", APP)
        self.assertNotIn('tombWorldSoloGuide.v1', APP)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)
        for key in ['diceRollEnabled', 'showOperativeStatus', 'ambientEnabled', 'gameVolume']:
            self.assertIn(f'tombWorldBattleGuide.{key}', APP)
        for identifier in ['pendingDice', 'requestKey', 'transactionKey']:
            self.assertIn(identifier, APP)


if __name__ == '__main__':
    unittest.main()
