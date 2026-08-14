import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


class AmbientInteractionIdempotencyTests(unittest.TestCase):
    def test_release_version_and_save_schema(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', index)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', index)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertTrue(readme.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}"))
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))

    def test_ui_interaction_does_not_reconcile_or_modify_playing_ambient(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const windowEvents={},documentEvents={},ramps=[],sources=[],timers=new Map();
let enabled=true,timerId=0,resumeCalls=0;
class CustomEvent { constructor(type,options={}){this.type=type;this.detail=options.detail;} }
class AudioContext {
  constructor(){this.currentTime=2;this.state='suspended';this.destination={};}
  createGain(){return {gain:{value:0,cancelCalls:0,cancelScheduledValues(){this.cancelCalls++;},setValueAtTime(v){this.value=v;},linearRampToValueAtTime(v,t){this.value=v;ramps.push([v,t]);}},connect(){}};}
  createBufferSource(){const node={connect(){},disconnect(){},startCalls:[],stopCalls:0,start(...args){this.startCalls.push(args);},stop(){this.stopCalls++;}};sources.push(node);return node;}
  decodeAudioData(){return Promise.resolve({duration:120});}
  resume(){resumeCalls++;this.state='running';return Promise.resolve();}
}
const config={schemaVersion:1,file:'Ambient/Forgoten_tombs.mp3',normalGain:.22,duckGain:.055,fadeInMs:1500,fadeOutMs:800,duckAttackMs:250,duckReleaseMs:700,loopStartSeconds:0,loopEndSeconds:null};
const document={
 addEventListener:(type,fn)=>documentEvents[type]=fn,
 removeEventListener:(type,fn)=>{if(documentEvents[type]===fn)delete documentEvents[type];},
 dispatchEvent:event=>documentEvents[event.type]?.(event)
};
const context={AudioContext,CustomEvent,URL,location:{href:'https://example.test/app/'},document,
 TombWorldNarration:{isEnabled:()=>enabled},
 fetch:async url=>String(url).includes('ambient-config')?{ok:true,json:async()=>config}:{ok:true,arrayBuffer:async()=>new ArrayBuffer(1)},
 addEventListener:(type,fn)=>windowEvents[type]=fn,dispatchEvent:event=>windowEvents[event.type]?.(event),
 setTimeout:fn=>{const id=++timerId;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id)};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('ambient.js','utf8'),context);
(async()=>{
 const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
 const ambient=context.TombWorldAmbient;

 // A battle render may mark ambient active before Safari grants audio permission.
 ambient.setActive(true);await flush();
 if(sources.length)throw Error('ambient started without a user gesture');
 if(typeof documentEvents.click!=='function')throw Error('one-time Safari gesture fallback was not installed');
 document.dispatchEvent({type:'click',target:{tagName:'BUTTON'}});await flush();
 if(sources.length!==1||sources[0].startCalls.length!==1)throw Error('first valid gesture did not unlock and start ambient');
 if(documentEvents.click)throw Error('fallback gesture listener remained after successful unlock');
 if(resumeCalls<1)throw Error('Safari AudioContext was not resumed');

 const originalSource=sources[0], baselineRamps=ramps.length, baselineGain=ramps.at(-1)[0], baselineResumes=resumeCalls;
 await ambient.unlock();await ambient.unlock();await flush();
 ambient.setActive(true);ambient.setActive(true);await flush();
 if(sources.length!==1||sources[0]!==originalSource||originalSource.startCalls.length!==1)throw Error('no-op unlock/render replaced or restarted source');
 if(ramps.length!==baselineRamps||ramps.at(-1)[0]!==baselineGain)throw Error('no-op unlock/render scheduled a gain ramp');
 if(resumeCalls!==baselineResumes)throw Error('already-running unlock resumed context again');

 // Ordinary delegated UI events have no ambient listener and cannot reconcile playback.
 document.dispatchEvent({type:'click',target:{tagName:'BUTTON'}});
 document.dispatchEvent({type:'change',target:{tagName:'SELECT',value:'option-2'}});await flush();
 if(sources[0]!==originalSource||ramps.length!==baselineRamps)throw Error('button/select interaction disturbed ambient');

 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:true}}));
 if(ramps.at(-1)[0]!==config.duckGain)throw Error('narration did not duck ambient');
 const duckRampCount=ramps.length;
 document.dispatchEvent({type:'click',target:{tagName:'BUTTON'}});
 document.dispatchEvent({type:'change',target:{tagName:'SELECT'}});
 ambient.setActive(true);await flush();
 if(ramps.length!==duckRampCount||ramps.at(-1)[0]!==config.duckGain)throw Error('UI/render interaction disturbed narration ducking');
 context.dispatchEvent(new CustomEvent('tombworldnarrationactivity',{detail:{active:false}}));
 if(ramps.at(-1)[0]!==config.normalGain)throw Error('narration completion did not restore ambient');

 enabled=false;context.dispatchEvent(new CustomEvent('tombworldnarrationchange'));await flush();
 if(ramps.at(-1)[0]!==0||timers.size!==1)throw Error('Game Audio OFF did not fade and schedule a stop');
 for(const [id,fn] of [...timers]){timers.delete(id);fn();}
 if(originalSource.stopCalls!==1)throw Error('Game Audio OFF did not stop the source');
 enabled=true;context.dispatchEvent(new CustomEvent('tombworldnarrationchange'));await flush();
 if(sources.length!==2||sources[1]===originalSource||ramps.at(-1)[0]!==config.normalGain)throw Error('Game Audio ON did not restart and restore ambient');
 ambient.stop();
 if(ramps.at(-1)[0]!==0)throw Error('New Game did not stop ambient');
})().catch(error=>{console.error(error);process.exit(1);});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
