import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
CATALOG = APP.split("const npoDefinitions = {", 1)[1].split(
    "\n  };\n\n  // Official 2D6 table", 1
)[0]


def function_source(name, next_name):
    return APP.split(f"function {name}", 1)[1].split(f"function {next_name}", 1)[0]


class NpoPortraitRemovalTests(unittest.TestCase):
    def test_catalog_and_profiles_have_no_portrait_dependency(self):
        self.assertNotRegex(CATALOG, r"(?i)(?:image|portrait)(?:path|url|file)?\s*:")
        self.assertEqual(CATALOG.count("physicalQuantity:"), 7)
        self.assertNotIn("npoPortrait", APP)

    def test_npo_ui_is_text_only_without_portrait_containers(self):
        roster = function_source("npoRosterCard", "operativeCard")
        deployment = function_source("setupContent", "bindSetup")
        activation = function_source("renderNpoDecisionResult", "completeNpoActivation")
        attack = function_source("showNpoAttackWizard", "spinnerField")
        for source in (roster, deployment, activation, attack):
            self.assertNotIn("<img", source)
            self.assertNotRegex(source, r"(?i)npo[-_ ]?portrait|portrait[-_ ]?container|thumbnail")

    def test_npo_selectors_remain_text_only_and_stably_identified(self):
        add_npo = function_source("showAddNpo", "changeNpoLoadout")
        target_selection = function_source("renderNpoDecisionResult", "completeNpoActivation")
        self.assertNotIn("<img", add_npo + target_selection)
        self.assertIn('<option value="${escapeHtml(type)}"', add_npo)
        self.assertIn('<option value="${escapeHtml(id)}"', target_selection)

    def test_no_npo_portrait_assets_or_requests_remain(self):
        self.assertFalse((ROOT / "Assets/Images/Canoptek Circle").exists())
        production_files = [ROOT / name for name in (
            "app.js", "index.html", "styles.css", "service-worker.js",
            "manifest.webmanifest", "Player_Operatives/manifest.json",
        )]
        repository_text = "\n".join(path.read_text() for path in production_files)
        self.assertNotIn("Assets/Images/Canoptek Circle", repository_text)
        self.assertNotRegex(WORKER, r"(?i)canoptek[^\n]*(?:jpe?g|png|webp)")

    def test_non_portrait_images_and_elimination_treatment_are_preserved(self):
        player_portraits = list((ROOT / "Assets/Images/Death Korps").glob("*.jpg"))
        self.assertTrue(player_portraits)
        self.assertIn('Assets/Maps/mission-${missionNumber}.png', APP)
        self.assertIn("function npoIcon", APP)
        self.assertTrue((ROOT / "Assets/Images/eliminated-necron-skull.png").is_file())
        self.assertIn('Assets/Images/eliminated-necron-skull.png', CSS)
        self.assertIn(".npo-roster-card.dead{", CSS)
        self.assertIn("border:2px solid var(--danger)", CSS)
        self.assertIn("z-index:2", CSS)

    def test_eliminated_state_is_available_as_text_and_not_only_an_icon(self):
        roster = function_source("npoRosterCard", "operativeCard")
        self.assertIn("eliminated?'ELIMINATED'", roster)
        self.assertIn("operative-status-badge", roster)
        self.assertIn("${status}", roster)

    def test_compact_layout_wraps_names_without_a_reserved_image_column(self):
        self.assertIn(".npo-roster-card{position:relative;display:flex;flex-direction:column", CSS)
        self.assertIn(".operative-identity{min-width:0;overflow-wrap:anywhere}", CSS)
        self.assertIn("grid-template-columns:1fr", CSS)
        self.assertNotRegex(CSS, r"(?i)\.npo[^,{]*(?:portrait|thumbnail|image)")

    def test_ordering_and_gameplay_identifiers_are_unchanged(self):
        self.assertIn("sortedNposForDisplay(state.roster)", APP)
        self.assertIn("localeCompare(String(displayName(b)||''),undefined,{numeric:true,sensitivity:'base'})", APP)
        self.assertIn("state.activationHistory.unshift", APP)
        for type_id in (
            "canoptek-scarab-swarm", "necron-warrior", "canoptek-tomb-crawler",
            "geomancer", "canoptek-macrocyte-warrior",
            "canoptek-macrocyte-accelerator", "canoptek-macrocyte-reanimator",
        ):
            self.assertIn(f"id:'{type_id}'", CATALOG)

    def test_offline_shell_and_release_versions_are_synchronized(self):
        self.assertIn("const APP_VERSION = '8.7.5';", APP)
        self.assertIn("const APP_VERSION = '8.7.5';", WORKER)
        self.assertIn("V8.7.5", INDEX)
        for asset in ("app.js", "mission-engine.js", "persistence.js", "styles.css"):
            self.assertIn(f"{asset}?v=8.7.5", INDEX)
        self.assertIn("cache.addAll(PRECACHE_ASSETS)", WORKER)

    def test_matrix_interface_remains_excluded(self):
        self.assertNotIn("obelisk node matrix support", APP.lower())


if __name__ == "__main__":
    unittest.main()
