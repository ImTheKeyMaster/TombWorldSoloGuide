from versioning import CURRENT_APP_VERSION
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


class DarkMapLoadingTests(unittest.TestCase):
    def test_release_version_and_map_cache_are_current(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f"Assets/Maps/mission-${{missionNumber}}.png?v=${{APP_VERSION}}", APP)
        self.assertIn("`./Assets/Maps/mission-01.png?v=${APP_VERSION}`", WORKER)

    def test_critical_css_makes_first_paint_shell_dark(self):
        critical = INDEX.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertIn("html,body,#gameWorkspace,#app", critical)
        self.assertIn("background:#06100c", critical)
        self.assertIn("min-height:100%", critical)
        self.assertIn("color-scheme:dark", critical)
        self.assertLess(INDEX.index("<style>"), INDEX.index('rel="stylesheet"'))

    def test_loaded_css_keeps_root_and_route_layers_dark(self):
        self.assertIn("html,body,.game-workspace,.app-shell{background-color:var(--bg)}", STYLES)
        self.assertIn("--bg:#06100c", STYLES)
        self.assertIn("min-height:100vh", STYLES)

    def test_map_wrapper_and_image_loading_surface_are_dark(self):
        card = STYLES.split(".official-map-card{", 1)[1].split("}", 1)[0]
        image = STYLES.split(".official-map-image{", 1)[1].split("}", 1)[0]
        self.assertRegex(card, r"background:\s*#07110c")
        self.assertRegex(image, r"background:\s*var\(--bg\)")
        self.assertNotRegex(card + image, r"#(?:fff(?:fff)?|e9e8e5)|white|lightgray")

    def test_map_dimensions_and_eager_loading_are_unchanged(self):
        image = STYLES.split(".official-map-image{", 1)[1].split("}", 1)[0]
        self.assertIn("display:block", image)
        self.assertIn("width:100%", image)
        self.assertIn("height:auto", image)
        self.assertRegex(APP, r'class="official-map-image"[^>]+loading="eager"')

    def test_no_loading_delay_fade_or_decode_gate_was_added(self):
        board = APP.split("function boardSvg(id){", 1)[1].split("function renderGuideMapMarker", 1)[0]
        self.assertNotIn("setTimeout", board)
        self.assertNotIn("decode()", board)
        self.assertNotIn("opacity", board)
        self.assertNotRegex(STYLES.split(".official-map-card{", 1)[1].split("/* v1.2.0", 1)[0], r"animation|transition")


if __name__ == "__main__":
    unittest.main()
