import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
CSS = (ROOT / 'styles.css').read_text()
INDEX = (ROOT / 'index.html').read_text()
PERSISTENCE = (ROOT / 'persistence.js').read_text()
README = (ROOT / 'README.md').read_text()
SERVICE_WORKER = (ROOT / 'service-worker.js').read_text()


class OperativeStatusToggleStateTests(unittest.TestCase):
    def test_aria_pressed_is_the_only_visual_state_source(self):
        self.assertIn('.operative-status-toggle[aria-pressed="false"]{border-color:var(--line);background:transparent;color:var(--line);opacity:1;box-shadow:none}', CSS)
        self.assertIn('.version{border:1px solid var(--line);', CSS)
        self.assertIn('.operative-status-toggle[aria-pressed="true"]{', CSS)
        self.assertNotIn('.operative-status-toggle.active', CSS)
        self.assertNotIn("operativeStatusToggle.classList.toggle('active'", APP)

    def test_off_pointer_interactions_do_not_override_dim_state(self):
        self.assertNotIn('.operative-status-toggle[aria-pressed="false"]:hover', CSS)
        self.assertNotIn('.operative-status-toggle[aria-pressed="false"]:active', CSS)

    def test_off_keyboard_focus_uses_outline_without_brightening_control(self):
        selector = '.operative-status-toggle[aria-pressed="false"]:focus-visible'
        rule = re.search(re.escape(selector) + r'\{([^}]+)\}', CSS).group(1)
        self.assertIn('outline:2px solid var(--green)', rule)
        self.assertIn('outline-offset:2px', rule)
        for property_name in ('border-color:', 'color:', 'background:', 'box-shadow:', 'opacity:'):
            self.assertNotIn(property_name, rule)

    def test_on_state_keeps_full_bright_active_treatment(self):
        rule = re.search(r'\.operative-status-toggle\[aria-pressed="true"\]\{([^}]+)\}', CSS).group(1)
        self.assertIn('border-color:var(--green)', rule)
        self.assertIn('color:var(--green)', rule)
        self.assertIn('opacity:1', rule)
        self.assertIn('background:rgba(118,245,168,.12)', rule)
        self.assertIn('box-shadow:0 0 0 2px rgba(118,245,168,.1)', rule)

    def test_toggle_remains_enabled_and_accessible(self):
        toggle = re.search(r'<button class="operative-status-toggle"[^>]+>', INDEX).group(0)
        self.assertIn('aria-label="Show operative status"', toggle)
        self.assertIn('aria-pressed="false"', toggle)
        self.assertNotIn('disabled', toggle)
        self.assertIn("setAttribute('aria-pressed',String(visible))", APP)
        self.assertIn("visible?'Hide operative status':'Show operative status'", APP)

    def test_behavior_persistence_and_responsive_visibility_are_unchanged(self):
        self.assertIn('showOperativeStatusPreference=!showOperativeStatusPreference', APP)
        self.assertIn('localStorage.setItem(OPERATIVE_STATUS_PREFERENCE_KEY,String(showOperativeStatusPreference))', APP)
        self.assertIn("state.screen==='game'&&operativeStatusMedia.matches", APP)
        self.assertIn("'(min-width: 900px) and (orientation: landscape), (min-width: 900px) and (hover: hover) and (pointer: fine)'", APP)
        self.assertIn('@media (max-width:899px), (orientation:portrait) and (hover:none), (orientation:portrait) and (pointer:coarse)', CSS)

    def test_release_version_and_save_version(self):
        self.assertIn("const APP_VERSION = '8.6.53';", APP)
        self.assertIn("const APP_VERSION = '8.6.53';", SERVICE_WORKER)
        self.assertIn('V8.6.53', INDEX)
        self.assertTrue(README.startswith('# Tomb World Solo Guide v8.6.53'))
        self.assertIn('## v8.6.53', README)
        self.assertIn('const SAVE_VERSION = 3;', PERSISTENCE)


if __name__ == '__main__':
    unittest.main()
