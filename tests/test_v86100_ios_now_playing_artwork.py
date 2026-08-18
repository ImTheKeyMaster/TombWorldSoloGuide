import json
import re
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class IosNowPlayingArtworkTests(unittest.TestCase):
    def test_icon_assets_exist_without_replacing_svg(self):
        for filename in ("icon.svg", "icon-180.png", "icon-192.png", "icon-512.png", "icon-1024.png"):
            asset = ROOT / "Assets" / filename
            self.assertTrue(asset.is_file(), filename)
            self.assertGreater(asset.stat().st_size, 0, filename)
        self.assertIn('<link rel="icon" href="Assets/icon.svg" type="image/svg+xml">', INDEX)
        self.assertIn('<img src="Assets/icon.svg" alt="" class="brand-icon">', INDEX)

    def test_apple_touch_icon_uses_dedicated_png(self):
        self.assertIn('<link rel="apple-touch-icon" sizes="180x180" href="Assets/icon-180.png">', INDEX)
        self.assertNotRegex(INDEX, r'<link rel="apple-touch-icon"[^>]+icon\.svg')

    def test_manifest_uses_supplied_png_icons(self):
        icons = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))["icons"]
        self.assertEqual([
            {"src": "Assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "Assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        ], icons)

    def test_media_session_metadata_is_passive_and_feature_detected(self):
        self.assertIn("'mediaSession' in navigator && 'MediaMetadata' in window", APP)
        self.assertIn("navigator.mediaSession.metadata = new MediaMetadata({", APP)
        self.assertIn("title: 'Tomb World Solo Guide'", APP)
        for size in (192, 512, 1024):
            self.assertIn(f"src:'Assets/icon-{size}.png',sizes:'{size}x{size}',type:'image/png'", APP)
        self.assertIn("catch (error)", APP)
        self.assertNotIn("setActionHandler", APP)

    def test_audio_architecture_remains_html_audio_only(self):
        runtime = "\n".join((ROOT / filename).read_text(encoding="utf-8") for filename in ("app.js", "narration.js", "ambient.js"))
        for forbidden in ("AudioContext", "webkitAudioContext", "MediaElementAudioSourceNode", "GainNode"):
            self.assertNotIn(forbidden, runtime)
        self.assertIn("new global.Audio()", (ROOT / "narration.js").read_text(encoding="utf-8"))
        self.assertIn("new global.Audio()", (ROOT / "ambient.js").read_text(encoding="utf-8"))
        self.assertIn('"file": "Ambient/caverns_25.ogg"', (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text(encoding="utf-8"))

    def test_all_artwork_is_precached_with_svg(self):
        for filename in ("icon.svg", "icon-180.png", "icon-192.png", "icon-512.png", "icon-1024.png"):
            self.assertIn(f"'./Assets/{filename}'", WORKER)

    def test_release_and_save_versions(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", INDEX)
        persistence = (ROOT / "persistence.js").read_text(encoding="utf-8")
        self.assertEqual("3", re.search(r"SAVE_VERSION = (\d+)", persistence).group(1))


if __name__ == "__main__":
    unittest.main()
