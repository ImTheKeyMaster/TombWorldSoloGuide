import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
CAPABILITIES = (ROOT / "audio-capabilities.js").read_text(encoding="utf-8")


class IosAudioRegressionTests(unittest.TestCase):
    def test_release_and_save_version(self):
        self.assertEqual(".".join(map(str, (8, 6, 95))), CURRENT_APP_VERSION)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_mission_choice_primes_selected_audio_synchronously(self):
        handler = APP[APP.index("$$('.mission-choice')") : APP.index("$('#setupHome')")]
        unlock = "TombWorldNarration.activateFromGesture()"
        self.assertIn("TombWorldNarration.isPlaybackEnabled()", handler)
        self.assertIn(unlock, handler)
        self.assertLess(handler.index(unlock), handler.index("reconcileAmbientActiveState()"))
        self.assertLess(handler.index(unlock), handler.index("TombWorldAmbient.playFromGesture()"))
        self.assertLess(handler.index("TombWorldAmbient.playFromGesture()"), handler.index("render()"))
        self.assertLess(handler.index("render()"), handler.index("Promise.allSettled"))
        self.assertLess(handler.index("Promise.allSettled"), handler.index("setTimeout"))
        self.assertNotIn("await", handler)

    def test_forced_unlock_replays_the_dedicated_silent_player(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let plays=0;
class Audio{constructor(){this.paused=true;this.ended=false;this.src=''}play(){plays++;return Promise.resolve()}pause(){}removeAttribute(){}load(){}}
const s={Audio,URL,location:{href:'https://example.test/'},document:{},localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:true,json:async()=>({entries:{}})})};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('narration.js','utf8'),s);
(async()=>{const n=s.TombWorldNarration;if(!await n.unlock())throw Error('initial unlock failed');if(!await n.unlock({force:true}))throw Error('forced unlock failed');if(plays!==2)throw Error(`forced unlock did not replay: ${plays}`)})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_ios_detection_includes_touch_capable_ipados_macs(self):
        self.assertIn("iPhone|iPad|iPod", CAPABILITIES)
        self.assertIn("maxTouchPoints", CAPABILITIES)
        script = r"""
const fs=require('fs'),vm=require('vm');
for(const navigator of [
  {platform:'iPhone',userAgent:'Mobile Safari',maxTouchPoints:5},
  {platform:'MacIntel',userAgent:'Safari',maxTouchPoints:5},
  {platform:'MacIntel',userAgent:'Safari',maxTouchPoints:0},
  {platform:'Win32',userAgent:'Chrome',maxTouchPoints:10}
]){
  const s={navigator};s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync('audio-capabilities.js','utf8'),s);
  const supported=s.TombWorldAudioCapabilities.supportsInAppVolumeControl();
  const expected=navigator.platform==='MacIntel'&&navigator.maxTouchPoints===0||navigator.platform==='Win32';
  if(supported!==expected)throw Error(`${navigator.platform}/${navigator.maxTouchPoints}: ${supported}`);
}
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_game_menu_omits_unsupported_ios_volume_row(self):
        menu = APP[APP.index("function showGameMenu") : APP.index("function showAbout")]
        self.assertIn("supportsInAppVolumeControl()?", menu)
        self.assertIn('id="gameVolume" type="range" min="0" max="100" step="1"', menu)
        self.assertNotIn("Use device volume buttons", menu)
        self.assertIn("if(gameVolume)gameVolume.oninput", menu)
        self.assertNotIn("game-volume-device-message\">${", menu)

    def test_ios_players_do_not_receive_volume_writes_or_ramps(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let writes=0,frames=0,pauses=0;const players=[];
class Audio{constructor(){this._volume=1;this.paused=true;this.currentTime=4;this.listeners={};players.push(this)}set volume(v){writes++;this._volume=v}get volume(){return this._volume}addEventListener(t,h){this.listeners[t]=h}load(){}play(){this.paused=false;return Promise.resolve()}pause(){pauses++;this.paused=true}removeAttribute(){}}
const navigator={platform:'iPhone',userAgent:'Mobile Safari',maxTouchPoints:5};
const document={addEventListener(){},removeEventListener(){}};
const s={Audio,navigator,document,URL,location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},CustomEvent:function(){},fetch:async url=>({ok:true,json:async()=>url.includes('ambient-config')?{schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.22,duckGain:.055,fadeInMs:1500,fadeOutMs:800,duckAttackMs:250,duckReleaseMs:700,loopStartSeconds:0,loopEndSeconds:null}:{entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}}}),requestAnimationFrame(){frames++;return 1},cancelAnimationFrame(){},setTimeout,clearTimeout,addEventListener(){},dispatchEvent(){}};s.window=s;vm.createContext(s);
for(const file of ['audio-capabilities.js','narration.js','ambient.js'])vm.runInContext(fs.readFileSync(file,'utf8'),s);
(async()=>{s.TombWorldNarration.setVolumeMultiplier(.3);await s.TombWorldNarration.playMissionIntro('shifting-labyrinth');s.TombWorldNarration.setVolumeMultiplier(.7);await s.TombWorldAmbient.init();s.TombWorldAmbient.setActive(true);await s.TombWorldAmbient.playFromGesture();s.TombWorldAmbient.setVolumeMultiplier(.2);s.TombWorldAmbient.stop();if(writes||frames)throw Error(`writes=${writes}, frames=${frames}`);if(pauses<1)throw Error('ambient mute did not pause')})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_architecture_assets_and_neutral_menu_remain_intact(self):
        self.assertNotIn("AudioContext", AMBIENT)
        self.assertNotIn("webkitAudioContext", AMBIENT)
        self.assertIn("new global.Audio()", AMBIENT)
        self.assertIn('"file": "Ambient/caverns.ogg"', (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        worker = (ROOT / "service-worker.js").read_text()
        self.assertIn("await precacheAmbient(cache)", worker)
        menu = APP[APP.index("function showGameMenu") : APP.index("function showAbout")]
        for audio_operation in (".play(", ".pause(", ".load(", "currentTime", "unlock("):
            self.assertNotIn(audio_operation, menu)
        self.assertNotIn("click-sfx", (APP + AMBIENT + NARRATION).lower())


if __name__ == "__main__":
    unittest.main()
