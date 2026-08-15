import json
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


class AmbientToggleRecoveryTests(unittest.TestCase):
    def test_release_source_preference_and_accessible_switch_contract(self):
        config = json.loads((ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual("Ambient/caverns.ogg", config["file"])
        self.assertIn("precacheAmbient(cache)", worker)
        self.assertNotIn("Forgoten_tombs.mp3", worker)
        self.assertIn("const AMBIENT_ENABLED_PREFERENCE_KEY = 'tombWorldSoloGuide.ambientEnabled';", APP)
        self.assertIn("localStorage.getItem(AMBIENT_ENABLED_PREFERENCE_KEY)!=='false'", APP)
        self.assertIn("localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY,String(ambientEnabled))", APP)
        self.assertIn('role="switch"', APP)
        self.assertIn('aria-checked="${ambientEnabled}"', APP)
        self.assertIn("Ambient Noise", APP)
        self.assertIn("function shouldAmbientBeActive()", APP)
        self.assertNotIn("TombWorldAmbient.setActive(Boolean(state.missionId)", APP)
        self.assertNotIn("removeItem(AMBIENT_ENABLED_PREFERENCE_KEY)", APP)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        self.assertIn(f"V{CURRENT_APP_VERSION}", index)

    def test_failed_fetch_and_decode_retry_without_losing_gesture_fallback(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},sources=[];let attempts=0,decodeAttempts=0,context;
class AudioContext{constructor(){this.state='suspended';this.currentTime=0;this.destination={};context=this}resume(){this.state='running';return Promise.resolve()}createGain(){return {gain:{value:0,cancelScheduledValues(){},setValueAtTime(v){this.value=v},linearRampToValueAtTime(v){this.value=v}},connect(){}}}createBufferSource(){const s={connect(){},disconnect(){},start(){},stop(){}};sources.push(s);return s}decodeAudioData(){decodeAttempts++;return decodeAttempts===1?Promise.reject(Error('decode')):Promise.resolve({duration:60})}}
const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.22,duckGain:.055,fadeInMs:1500,fadeOutMs:800,duckAttackMs:250,duckReleaseMs:700,loopStartSeconds:0,loopEndSeconds:null};
const document={addEventListener:(t,f)=>listeners[t]=f,removeEventListener:(t,f)=>{if(listeners[t]===f)delete listeners[t]}};
const sandbox={AudioContext,URL,location:{href:'https://example.test/'},document,TombWorldNarration:{isEnabled:()=>true},addEventListener(){},setTimeout,clearTimeout,
fetch:async url=>{if(String(url).includes('ambient-config')){attempts++;if(attempts===1)throw Error('offline');return {ok:true,json:async()=>config}}return {ok:true,arrayBuffer:async()=>new ArrayBuffer(1)}}};
sandbox.window=sandbox;vm.createContext(sandbox);vm.runInContext(fs.readFileSync('ambient.js','utf8'),sandbox);
(async()=>{const a=sandbox.TombWorldAmbient;a.setActive(true);for(let i=0;i<8;i++)await Promise.resolve();if(!listeners.click)throw Error('fallback removed after fetch failure');await a.unlock();if(!listeners.click)throw Error('fallback removed after decode failure');if(await a.unlock()!==true)throw Error('later retry did not initialize');for(let i=0;i<8;i++)await Promise.resolve();if(listeners.click)throw Error('fallback retained after full success');if(sources.length!==1)throw Error('successful retry did not play exactly once')})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_off_state_ignores_narration_and_active_reconciliation(self):
        self.assertIn("if (source && activeBattle && masterEnabled() && config)", AMBIENT)
        self.assertIn("ambientEnabled&&TombWorldNarration.isEnabled()", APP)
        self.assertIn("if(ambientEnabled&&shouldAmbientBeActive())await TombWorldAmbient.unlock();", APP)


if __name__ == "__main__":
    unittest.main()
