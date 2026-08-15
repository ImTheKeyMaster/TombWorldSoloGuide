import re
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class HeaderNarrationControlTests(unittest.TestCase):
    def test_release_metadata_uses_central_version(self):
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "app.js"):
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', INDEX)

    def test_header_has_accessible_enabled_and_disabled_speaker_states(self):
        self.assertIn('id="narrationSpeakerBtn"', INDEX)
        self.assertIn('class="narration-icon-enabled"', INDEX)
        self.assertIn('class="narration-icon-disabled"', INDEX)
        self.assertIn("enabledIcon.toggleAttribute('hidden',!masterEnabled)", APP)
        self.assertIn("disabledIcon.toggleAttribute('hidden',masterEnabled)", APP)
        self.assertNotIn(".querySelector('.narration-icon-enabled').hidden", APP)
        self.assertNotIn(".querySelector('.narration-icon-disabled').hidden", APP)
        self.assertIn("narrationSpeakerBtn.setAttribute('aria-label',`Master audio ${masterEnabled?'on':'off'}`)", APP)
        self.assertIn("narrationSpeakerBtn.setAttribute('aria-pressed',String(masterEnabled))", APP)
        self.assertIn("narrationSpeakerBtn.title=`Master audio ${masterEnabled?'on':'off'}`", APP)

    def test_header_button_uses_shared_game_audio_toggle(self):
        button = APP[APP.index("narrationSpeakerBtn.addEventListener('click'"):APP.index('function handleNarrationChange')]
        self.assertIn('const enabled=!TombWorldNarration.isMasterEnabled()', button)
        self.assertIn('await setGameAudioEnabled(enabled)', button)
        self.assertIn('TombWorldNarration.setMasterEnabled(enabled)', APP)
        self.assertIn('playPendingBoardSetupMissionIntro()', APP)
        self.assertIn("window.addEventListener('tombworldnarrationchange'", APP)
        self.assertIn("syncNarrationControls();", APP)

    def test_control_visibility_and_accessibility_follow_enabled_state(self):
        sync_source = APP[APP.index('function syncNarrationControls()'):APP.index("narrationSpeakerBtn.addEventListener", APP.index('function syncNarrationControls()'))]
        script = f"""
let enabled=true;
const makeIcon=()=>{{
  const attributes=new Set();
  return {{
    hasAttribute:name=>attributes.has(name),
    toggleAttribute:(name,force)=>force?attributes.add(name):attributes.delete(name)
  }};
}};
const icons={{'.narration-icon-enabled':makeIcon(),'.narration-icon-disabled':makeIcon()}};
const attributes={{}};
const narrationSpeakerBtn={{classList:{{toggle:(name,value)=>attributes[name]=value}},querySelector:selector=>icons[selector],setAttribute:(name,value)=>attributes[name]=value,title:''}};
const globalThis={{document:{{querySelector:()=>null}}}};
const TombWorldNarration={{isMasterEnabled:()=>enabled,isPreferenceEnabled:()=>true}};
let ambientEnabled=true;
{sync_source}
function verify(expectedEnabled){{
  syncNarrationControls();
  if(icons['.narration-icon-enabled'].hasAttribute('hidden')===expectedEnabled)throw Error('enabled icon visibility mismatch');
  if(icons['.narration-icon-disabled'].hasAttribute('hidden')!==expectedEnabled)throw Error('disabled icon visibility mismatch');
  if(attributes['is-muted']!==!expectedEnabled)throw Error('muted class mismatch');
  const word=expectedEnabled?'on':'off';
  if(attributes['aria-label']!==`Master audio ${{word}}`||attributes['aria-pressed']!==String(expectedEnabled)||narrationSpeakerBtn.title!==`Master audio ${{word}}`)throw Error('accessible state mismatch');
}}
verify(true);enabled=false;verify(false);
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_popover_and_volume_controls_are_removed(self):
        for source in (INDEX, APP, CSS):
            for removed in ('narrationPopover', 'headerNarrationVolume', 'headerNarrationVolumeValue', 'headerNarrationEnabled'):
                self.assertNotIn(removed, source)
        for attribute in ('aria-haspopup', 'aria-expanded', 'aria-controls'):
            self.assertNotIn(attribute, INDEX)

    def test_game_menu_uses_audio_toggle_without_duplicate_preferences(self):
        menu = APP[APP.index('function showGameMenu()'):APP.index('function showAbout()')]
        self.assertIn('id="narrationToggle"', menu)
        self.assertIn('role="switch" aria-labelledby="narrationLabel" aria-checked=', menu)
        self.assertNotIn('id="gameAudioToggle"', menu)
        self.assertNotIn('id="narrationVolume"', menu)
        self.assertNotIn('narrationVolumeValue', menu)

    def test_existing_unversioned_enabled_preference_is_the_only_source_of_truth(self):
        self.assertEqual(NARRATION.count("tombWorldSoloGuide.narrationEnabled"), 1)
        self.assertNotIn("tombWorldSoloGuide.narrationVolume", NARRATION)
        for source in (INDEX, APP, CSS, PERSISTENCE):
            self.assertNotIn("tombWorldSoloGuide.narrationEnabled", source)
            self.assertNotIn("tombWorldSoloGuide.narrationVolume", source)
        self.assertNotRegex(NARRATION, r"narrationEnabled.*APP_VERSION")
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)

    def test_mobile_header_keeps_compact_touch_target_without_taller_header(self):
        self.assertIn("width:40px;height:40px", CSS)
        header_rule = re.search(r"\.app-header\{[^}]+\}", CSS).group(0)
        self.assertNotIn("height:", header_rule)
        self.assertIn(".brand h1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}", CSS)


if __name__ == "__main__":
    unittest.main()
