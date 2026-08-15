import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AmbientAudioTests(unittest.TestCase):
    def test_configuration_selects_track_without_ui_and_offline_cache_is_config_driven(self):
        config = json.loads((ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        self.assertEqual("Ambient/caverns.ogg", config["file"])
        self.assertTrue((ROOT / "Assets/Audio/Narration" / config["file"]).is_file())
        index = (ROOT / "index.html").read_text()
        self.assertIn("ambient.js?v=", index)
        self.assertNotIn("ambient-config", index)
        worker = (ROOT / "service-worker.js").read_text()
        self.assertIn("cache.add(AMBIENT_CONFIG)", worker)
        self.assertIn("precacheAmbient(cache)", worker)
        self.assertNotIn("Forgoten_tombs.mp3", worker)
        self.assertIn("(?!.*(?:^|\\/)\\.\\.(?:\\/|$))", worker)

    def test_runtime_lifecycle_loop_master_control_ducking_and_failure_isolation(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const events={},ramps=[],sources=[],fetches=[];
let enabled=true,timerId=0;
class CustomEvent { constructor(type,options){this.type=type;this.detail=options.detail;} }
class AudioContext {
  constructor(){this.currentTime=1;this.state='suspended';this.destination={};}
  createGain(){return {gain:{value:0,cancelScheduledValues(){},setValueAtTime(v){this.value=v;},linearRampToValueAtTime(v,t){this.value=v;ramps.push([v,t]);}},connect(){}};}
  createBufferSource(){const source={connect(){},disconnect(){},startCalls:[],stopCalls:0,start(...args){this.startCalls.push(args);},stop(){this.stopCalls++;}};sources.push(source);return source;}
  decodeAudioData(){return Promise.resolve({duration:123});}
  resume(){this.state='running';return Promise.resolve();}
}
const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.22,duckGain:.055,fadeInMs:1500,fadeOutMs:800,duckAttackMs:250,duckReleaseMs:700,loopStartSeconds:0,loopEndSeconds:null};
const context={AudioContext,CustomEvent,URL,location:{href:'https://example.test/app/'},TombWorldNarration:{isEnabled:()=>enabled},
 fetch:async url=>{fetches.push(String(url));return String(url).includes('ambient-config')?{ok:true,json:async()=>config}:{ok:true,arrayBuffer:async()=>new ArrayBuffer(1)};},
 addEventListener:(type,fn)=>events[type]=fn,dispatchEvent:event=>events[event.type]?.(event),document:{addEventListener:(type,fn)=>events['document:'+type]=fn},
 setTimeout:fn=>{context.pendingTimer=fn;return ++timerId;},clearTimeout:()=>{context.pendingTimer=null;}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('ambient.js','utf8'),context);
(async()=>{
 const flush=async()=>{for(let i=0;i<5;i++)await Promise.resolve();};
 const ambient=context.TombWorldAmbient;
 await ambient.init();
 ambient.setActive(false);await Promise.resolve();
 if(sources.length)throw Error('ambient started on home screen');
 await ambient.unlock();ambient.setActive(true);await flush();
 if(sources.length!==1)throw Error('active battle did not start one source');
 const source=sources[0];
 if(!source.loop||source.loopStart!==0||source.loopEnd!==123||source.startCalls.length!==1)throw Error('seamless configured looping not established');
 ambient.setActive(true);ambient.setActive(true);await Promise.resolve();
 if(sources.length!==1||source.startCalls.length!==1)throw Error('render/navigation restarted ambient');
 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:true}}));
 if(ramps.at(-1)[0]!==.055)throw Error('narration did not duck ambient');
 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:false}}));
 if(ramps.at(-1)[0]!==.22)throw Error('ambient did not restore after narration');
 // Every narration category uses this centralized event, so intros, events, encounters, outcomes and Replay Last share the same ducking path.
 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:true}}));
 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:true}}));
 if(ramps.slice(-2).some(r=>r[0]!==.055))throw Error('consecutive narration restored between clips');
 enabled=false;context.dispatchEvent(new CustomEvent('tombworldnarrationchange',{detail:{}}));await flush();
 if(ramps.at(-1)[0]!==0)throw Error('speaker off did not fade ambient to silence');
 enabled=true;context.dispatchEvent(new CustomEvent('tombworldnarrationchange',{detail:{}}));await flush();
 if(sources.length!==1)throw Error('speaker on restarted source before fade completed');
 ambient.stop();
 if(ramps.at(-1)[0]!==0)throw Error('New Game did not cancel ambient');
 if(fetches.filter(url=>url.includes('caverns.ogg')).length!==1)throw Error('ambient track was not decoded exactly once');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_configuration_fails_silently(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const context={fetch:async()=>{throw Error('offline')},AudioContext:class{},addEventListener(){},document:{addEventListener(){}},TombWorldNarration:{isEnabled:()=>true},setTimeout,clearTimeout};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('ambient.js','utf8'),context);
(async()=>{if(await context.TombWorldAmbient.init())throw Error('bad config initialized');context.TombWorldAmbient.setActive(true);context.TombWorldAmbient.stop();})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
