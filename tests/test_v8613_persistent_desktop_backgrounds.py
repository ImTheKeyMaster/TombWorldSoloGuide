import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
STYLES = (ROOT / "styles.css").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
BACKGROUND_DIR = ROOT / "Assets" / "Images" / "Backgrounds"


class PersistentDesktopBackgroundTests(unittest.TestCase):
    def test_version_and_save_schema(self):
        self.assertIn("const APP_VERSION = '8.6.52';", APP)
        self.assertIn("V8.6.52", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.52"))
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_manifest_matches_current_landscape_images_in_natural_order(self):
        manifest = json.loads((BACKGROUND_DIR / "manifest.json").read_text())
        current = [
            path.name
            for path in BACKGROUND_DIR.iterdir()
            if re.fullmatch(r"Landscape-\d{2,}\.png", path.name)
        ]
        natural = sorted(current, key=lambda name: int(re.search(r"\d+", name).group()))
        self.assertEqual(natural, manifest["landscape"])

    def test_selection_is_created_for_setup_or_game_and_persisted(self):
        self.assertIn("backgroundSelection:null", APP)
        self.assertIn("['setup','game'].includes(state.screen)", APP)
        self.assertIn("sourceState.backgroundSelection={landscape:selected}", APP)
        self.assertIn("ensureGameBackgroundSelection();", APP)
        self.assertNotIn("backgroundSelection", PERSISTENCE.split("NON_PERSISTED_FIELDS", 1)[1].split("]", 1)[0])

    def test_selection_is_not_part_of_render_navigation_or_update_logic(self):
        render = APP.split("function render(){", 1)[1].split("function guideInstructionsHtml", 1)[0]
        self.assertNotIn("chooseBackground", render)
        self.assertIn("updateGameBackground();", render)
        self.assertNotIn("backgroundSelection", APP.split("function registerServiceWorker", 1)[1].split("registerServiceWorker();", 1)[0])

    def test_restore_import_battle_complete_and_offline_keep_selection(self):
        self.assertIn("ensureGameBackgroundSelection();", APP)
        self.assertIn("ensureGameBackgroundSelection();if(!save())", APP)
        battle_complete = APP.split("function renderGame(){", 1)[1].split("function renderPlay", 1)[0]
        self.assertNotIn("chooseBackground", battle_complete)
        self.assertIn("using the standard background", APP)
        self.assertNotIn("state.backgroundSelection=null", APP)

    def test_invalid_saved_filename_is_repaired_with_a_warning(self):
        self.assertIn("isValidLandscapeBackground(current)", APP)
        self.assertIn("Saved landscape", APP)
        self.assertIn("selected a replacement", APP)

    def test_new_game_state_clears_the_previous_selection(self):
        self.assertIn("state=initialState()", APP)
        self.assertIn("$('#beginGame')?.addEventListener('click',async()=>", APP)
        self.assertIn("selectRandomLandscapeBackground()", APP)
        self.assertIn("backgroundSelection:null", PERSISTENCE.split("function resetActiveBattle", 1)[1].split("function normalizeSave", 1)[0])

    def test_desktop_only_layer_is_decorative_and_preloaded(self):
        self.assertIn('<div id="gameBackground" aria-hidden="true"></div>', INDEX)
        self.assertIn("(hover: hover) and (pointer: fine) and (min-width: 769px)", APP)
        self.assertIn("const image=new Image()", APP)
        self.assertIn("loadingBackgroundFilename===filename", APP)
        self.assertIn("pointer-events:none", STYLES)
        self.assertIn("position:fixed", STYLES)
        self.assertIn("forced-colors:active", STYLES)

    def test_mobile_gradient_is_unchanged_and_no_portrait_logic_exists(self):
        self.assertIn("radial-gradient(circle at 80% 0,#123326 0,transparent 32%),var(--bg)", STYLES)
        combined = APP + INDEX + STYLES + WORKER
        self.assertNotRegex(combined, r"Portrait-\d")
        self.assertIn("orientationchange", APP)

    def test_offline_cache_is_generated_from_the_manifest(self):
        self.assertIn("'./Assets/Images/Backgrounds/manifest.json'", WORKER)
        self.assertIn("(manifest.landscape||[]).map", WORKER)
        self.assertIn("await cache.addAll(backgrounds)", WORKER)

    def test_generator_supports_larger_numbers_and_ignores_unrelated_files(self):
        spec = importlib.util.spec_from_file_location(
            "background_manifest", ROOT / "tools" / "generate-background-manifest.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for name in ("Landscape-100.png", "Landscape-05.png", "Landscape-12.png", "Portrait-01.png", "notes.txt"):
                (temp / name).touch()
            self.assertEqual(
                ["Landscape-05.png", "Landscape-12.png", "Landscape-100.png"],
                module.landscape_filenames(temp),
            )

    def test_release_notes_document_manifest_regeneration(self):
        self.assertIn("## v8.6.25", README)
        self.assertIn("python3 tools/generate-background-manifest.py", README)


if __name__ == "__main__":
    unittest.main()
