import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ButtonSfxTests(unittest.TestCase):
    def test_configuration_and_config_driven_offline_precache(self):
        config = json.loads((ROOT / "Assets/Audio/Narration/sfx-config.json").read_text())
        self.assertEqual(1, config["schemaVersion"])
        self.assertEqual("SFX/Btn_Click.wav", config["buttonClick"])
        self.assertEqual(0.35, config["buttonClickGain"])
        self.assertTrue((ROOT / "Assets/Audio/Narration" / config["buttonClick"]).is_file())

        worker = (ROOT / "service-worker.js").read_text()
        self.assertIn("cache.add(SFX_CONFIG)", worker)
        self.assertIn("precacheSfx(cache)", worker)
        self.assertNotIn("Btn_Click.wav", worker)
        self.assertIn("|wav)", worker)
        self.assertIn("(?!.*(?:^|\\/)\\.\\.(?:\\/|$))SFX\\/", worker)

    def test_single_delegated_runtime_handles_buttons_master_control_and_audio_isolation(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},sources=[],fetches=[];
let enabled=true,decodeCalls=0,resumeCalls=0,narrationEvents=0,ambientCalls=0;
class AudioContext {
  constructor(){this.state='suspended';this.destination={};}
  createGain(){return {gain:{value:0},connect(){}};}
  createBufferSource(){const source={connect(){},disconnect(){},startCalls:0,start(){this.startCalls++;}};sources.push(source);return source;}
  decodeAudioData(){decodeCalls++;return Promise.resolve({duration:.1});}
  resume(){resumeCalls++;this.state='running';return Promise.resolve();}
}
const config={schemaVersion:1,buttonClick:'SFX/Btn_Click.wav',buttonClickGain:.35};
const document={addEventListener(type,fn,capture){if(listeners[type])throw Error('more than one delegated click listener');listeners[type]={fn,capture};}};
const context={AudioContext,URL,location:{href:'https://example.test/app/'},document,
 TombWorldNarration:{isEnabled:()=>enabled,playMissionIntro(){narrationEvents++;}},
 TombWorldAmbient:{setActive(){ambientCalls++;}},
 fetch:async url=>{fetches.push(String(url));return String(url).includes('sfx-config')?{ok:true,json:async()=>config}:{ok:true,arrayBuffer:async()=>new ArrayBuffer(1)};}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('sfx.js','utf8'),context);
const button=(id='ordinary')=>({id,disabled:false,closest:selector=>selector==='button'?button.current:null});
const click=target=>listeners.click.fn({target});
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();await new Promise(resolve=>setImmediate(resolve));};
(async()=>{
 if(!listeners.click.capture)throw Error('unlock/delegation is not capture-phase');
 const first=button();button.current=first;click(first);await flush();
 if(sources.length!==1||sources[0].startCalls!==1)throw Error('enabled button did not play exactly once');
 const nested={closest:()=>first};click(nested);await flush();
 if(sources.length!==2)throw Error('nested SVG/span did not resolve to parent button exactly once');
 const disabled=button();disabled.disabled=true;button.current=disabled;click(disabled);await flush();
 click({closest:()=>null});await flush();
 if(sources.length!==2)throw Error('disabled or non-button click played SFX');
 const dynamic=button('dynamic');button.current=dynamic;click(dynamic);click(dynamic);await flush();
 if(sources.length!==4)throw Error('rapid/dynamic button clicks did not create overlapping sources');
 if(decodeCalls!==1||fetches.filter(url=>url.includes('Btn_Click.wav')).length!==1)throw Error('WAV was not decoded exactly once');
 enabled=false;click(dynamic);await flush();
 if(sources.length!==4)throw Error('Game Audio off did not suppress SFX');
 const start=button('gameAudioToggle');button.current=start;click(start);enabled=true;await flush();
 if(sources.length!==5)throw Error('Game Audio on did not restore SFX after unlock');
 const stop=button('gameAudioToggle');button.current=stop;click(stop);enabled=false;await flush();
 if(sources.length!==5)throw Error('Game Audio off control double-played or left stale SFX behavior');
 if(narrationEvents||ambientCalls)throw Error('SFX affected narration or ambient');
 if(resumeCalls<1)throw Error('Safari/PWA Web Audio unlock was not attempted from click');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_bad_config_and_missing_wav_fail_silently(self):
        for response in ("bad-config", "missing-wav"):
            script = r"""
const fs=require('fs'),vm=require('vm');
class AudioContext {constructor(){this.state='running';this.destination={};}resume(){return Promise.resolve();}createGain(){return {gain:{},connect(){}};}decodeAudioData(){throw Error('decode failed');}}
const mode=MODE,config={schemaVersion:1,buttonClick:'SFX/../narration.mp3',buttonClickGain:.35};
let request=0;const context={AudioContext,URL,location:{href:'https://example.test/'},TombWorldNarration:{isEnabled:()=>true},document:{addEventListener(){}},fetch:async()=>{request++;if(mode==='bad-config')return {ok:true,json:async()=>config};return request===1?{ok:true,json:async()=>({...config,buttonClick:'SFX/click.wav'})}:{ok:false};}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('sfx.js','utf8'),context);
(async()=>{if(await context.TombWorldSfx.init())throw Error('invalid SFX initialized');if(await context.TombWorldSfx.play())throw Error('invalid SFX played');})().catch(e=>{console.error(e);process.exit(1)});
""".replace("MODE", json.dumps(response), 1)
            result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_runtime_does_not_use_or_signal_narration_or_ambient(self):
        runtime = (ROOT / "sfx.js").read_text()
        self.assertNotIn("tombworldnarrationactivity", runtime)
        self.assertNotIn("TombWorldAmbient", runtime)
        self.assertNotIn("new global.Audio", runtime)
        self.assertEqual(1, runtime.count("document?.addEventListener?.('click'"))
        self.assertIn("event.target?.closest?.('button')", runtime)


if __name__ == "__main__":
    unittest.main()
