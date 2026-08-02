import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()
CSS = (ROOT / "styles.css").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()
ABOUT = APP[APP.index("function showAbout()") : APP.index("function startNewGameSetup()")]
MENU = APP[APP.index("function showGameMenu()") : APP.index("function showAbout()")]


class AboutScreenV8619Tests(unittest.TestCase):
    def test_01_application_displays_version_8619(self):
        self.assertIn("const APP_VERSION = '8.6.20';", APP)
        self.assertIn("V8.6.20", INDEX)

    def test_02_game_menu_contains_about_button(self):
        self.assertIn('id="menuAbout" type="button">About</button>', MENU)

    def test_03_about_button_opens_about_screen(self):
        self.assertIn("$('#menuAbout').onclick=showAbout", MENU)
        self.assertIn("showModal('About'", ABOUT)

    def test_04_author_is_identified(self):
        self.assertIn("Created by J.R. Benning", ABOUT)

    def test_05_about_version_uses_app_version(self):
        self.assertIn("Version ${APP_VERSION}", ABOUT)
        self.assertNotIn("Version 8.6.20", ABOUT)

    def test_06_project_is_unofficial(self):
        self.assertIn("unofficial fan-created project", ABOUT)

    def test_07_not_affiliated(self):
        self.assertIn("not affiliated with", ABOUT)

    def test_08_not_endorsed(self):
        self.assertIn("endorsed by", ABOUT)

    def test_09_not_licensed_or_approved(self):
        self.assertIn("licensed by, or approved by Games Workshop", ABOUT)

    def test_10_games_workshop_ownership_acknowledged(self):
        self.assertIn("intellectual property of Games Workshop Limited and/or its licensors", ABOUT)

    def test_11_warhammer_ownership_acknowledged(self):
        self.assertIn("Games Workshop, Warhammer, Warhammer 40,000", ABOUT)

    def test_12_kill_team_ownership_acknowledged(self):
        self.assertIn("Kill Team, Necron, Tomb World", ABOUT)

    def test_13_does_not_replace_official_rules(self):
        self.assertIn("not a replacement for the official rules", ABOUT)

    def test_14_requires_lawful_access(self):
        self.assertIn("otherwise have lawful access", ABOUT)

    def test_15_official_source_controls(self):
        self.assertIn("the official source controls", ABOUT)

    def test_16_no_guaranteed_fair_use_claim(self):
        self.assertNotRegex(ABOUT.lower(), r"fair use|protected by fair use")

    def test_17_no_claim_of_games_workshop_authorization(self):
        self.assertNotIn("Games Workshop allows this", ABOUT)
        self.assertNotIn("authorized by Games Workshop", ABOUT)

    def test_18_as_is_disclaimer(self):
        self.assertIn("provided &quot;as is&quot; and &quot;as available,&quot;", ABOUT)

    def test_19_limitation_of_liability(self):
        self.assertIn("will not be liable for any direct, indirect, incidental, consequential", ABOUT)

    def test_20_nonwaivable_liability_preserved(self):
        self.assertIn("where doing so would be prohibited by applicable law", ABOUT)

    def test_21_privacy_matches_local_only_implementation(self):
        self.assertIn("does not intentionally collect or transmit personal information", ABOUT)
        self.assertIn("stored locally in the user’s browser", ABOUT)
        self.assertIn("localStorage.setItem", APP)
        self.assertNotRegex(INDEX + APP, r"sendBeacon|document\.cookie|google-analytics|googletagmanager")

    def test_22_repository_link_is_safe_and_external(self):
        self.assertIn('href="https://github.com/ImTheKeyMaster/TombWorldSoloGuide"', ABOUT)
        self.assertIn('target="_blank" rel="noopener noreferrer"', ABOUT)
        self.assertIn("opens in a new tab", ABOUT)

    def test_23_back_returns_to_game_menu(self):
        self.assertRegex(ABOUT, r"aboutBack[\s\S]+showGameMenu\(\)")

    def test_24_back_restores_about_focus(self):
        self.assertIn("$('#menuAbout')?.focus({preventScroll:true})", ABOUT)

    def test_25_opening_about_does_not_alter_gameplay_state(self):
        self.assertNotRegex(ABOUT, r"state\.|\bsave\(|localStorage")

    def test_26_about_available_during_setup(self):
        self.assertIn("!['setup','game'].includes(state.screen)", APP)

    def test_27_about_available_during_active_game(self):
        self.assertIn("!['setup','game'].includes(state.screen)", APP)

    def test_28_about_available_at_battle_complete(self):
        visibility = re.search(r"gameMenuBtn\.hidden\s*=\s*([^;]+);", APP).group(1)
        self.assertNotIn("gameEnd", visibility)

    def test_29_about_content_is_offline(self):
        self.assertIn("function showAbout()", APP)
        self.assertIn("`./app.js?v=${APP_VERSION}`", WORKER)
        self.assertNotIn("fetch(", ABOUT)

    def test_30_ip_asset_audit_exists(self):
        self.assertTrue((ROOT / "docs/IP_ASSET_AUDIT.md").is_file())

    def test_31_audit_includes_every_deployed_image(self):
        audit = (ROOT / "docs/IP_ASSET_AUDIT.md").read_text()
        for path in re.findall(r"'\./(Assets/[^']+\.(?:png|svg|jpg))'", WORKER):
            self.assertIn(path, audit)
        for filename in (ROOT / "Assets/Images/Backgrounds/manifest.json").read_text().split('"'):
            if filename.endswith('.png'):
                self.assertIn(f"Assets/Images/Backgrounds/{filename}", audit)

    def test_32_save_version_is_unchanged(self):
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_33_release_version_references_are_consistent(self):
        self.assertIn("const APP_VERSION = '8.6.20';", WORKER)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.20"))
        self.assertIn("## v8.6.20", README)
        for asset in ("styles.css", "app.js", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js"):
            self.assertIn(f"{asset}?v=8.6.20", INDEX)

    def test_34_about_uses_semantic_sections_and_readable_text(self):
        for heading in ("Project Status", "Games Workshop Notice", "Official Rules and Materials", "Project Content", "Software Disclaimer", "User Responsibility", "Privacy", "Contact"):
            self.assertIn(f"<section><h3>{heading}</h3>", ABOUT)
        self.assertIn("user-select:text", CSS)

    def test_35_controls_retain_visible_keyboard_focus(self):
        self.assertIn(".btn:focus-visible", CSS)
        self.assertIn("outline:2px solid var(--green)", CSS)


if __name__ == "__main__":
    unittest.main()
