import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


class IOSAmbientForegroundRecoveryTests(unittest.TestCase):
    def test_release_version_and_save_schema(self):
        self.assertEqual((8, 6, 91), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))

    def test_foreground_recovery_states_failures_and_guards(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
async function scenario(initial,{ambient=true,master=true,fail=false,startFail=false,suspendThrows=false,multiple=false}={}){
 const handlers={},windowHandlers={},listenerAdds={},sources=[],recoveryEvents=[];let context,resumes=0,suspends=0,shouldFail=false,shouldFailStart=false;
 class AudioContext{
  constructor(){context=this;this.state='suspended';this.currentTime=0;this.destination={}}
  resume(){resumes++;if(!shouldFail)this.state='running';return shouldFail?Promise.reject(Error('blocked')):Promise.resolve()}
  suspend(){suspends++;if(suspendThrows)throw Error('unsupported transition');if(!shouldFail)this.state='suspended';return shouldFail?Promise.reject(Error('blocked')):Promise.resolve()}
  decodeAudioData(){return Promise.resolve({duration:30})}
  createGain(){return {gain:{value:0,cancelScheduledValues(){},setValueAtTime(v){this.value=v},linearRampToValueAtTime(v){this.value=v}},connect(){}}}
  createBufferSource(){const node={starts:0,stops:0,connect(){},disconnect(){},start(){if(shouldFailStart)throw Error('stale session');this.starts++},stop(){this.stops++}};sources.push(node);return node}
 }
 const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.2,duckGain:.05,fadeInMs:1,fadeOutMs:1,duckAttackMs:1,duckReleaseMs:1,loopStartSeconds:0,loopEndSeconds:null};
 const document={visibilityState:'visible',addEventListener:(t,h)=>{listenerAdds[t]=(listenerAdds[t]||0)+1;handlers[t]=h},removeEventListener:(t,h)=>{if(handlers[t]===h)delete handlers[t]}};
 const sandbox={AudioContext,document,URL,location:{href:'https://example.test/'},TombWorldNarration:{isMasterEnabled:()=>master},addEventListener:(t,h)=>windowHandlers[t]=h,dispatchEvent:e=>{recoveryEvents.push(e);windowHandlers[e.type]?.(e)},CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail}},setTimeout,clearTimeout,fetch:async u=>String(u).includes('ambient-config')?{ok:true,json:async()=>config}:{ok:true,arrayBuffer:async()=>new ArrayBuffer(1)}};sandbox.window=sandbox;
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync('ambient.js','utf8'),sandbox);const a=sandbox.TombWorldAmbient;
 if(ambient){a.setActive(true);await a.unlock();for(let i=0;i<12;i++)await Promise.resolve()}
 if(ambient&&master&&sources.length!==1)throw Error('initial ambient source missing');
 shouldFail=fail;
 shouldFailStart=startFail;
 if(context)context.state=initial;
 document.visibilityState='hidden';handlers.visibilitychange();document.visibilityState='visible';handlers.visibilitychange();
 if(multiple){document.visibilityState='hidden';handlers.visibilitychange();document.visibilityState='visible';handlers.visibilitychange()}
 if(typeof handlers.click==='function')throw Error('ambient installed a click recovery listener');
 if(recoveryEvents.some(e=>e.type==='tombworldaudiorecoveryrequired'))await a.unlock();
 for(let i=0;i<12;i++)await Promise.resolve();
 return {sources,resumes,suspends,recoverySignaled:recoveryEvents.some(e=>e.type==='tombworldaudiorecoveryrequired'),listenerAdds,context};
}
(async()=>{
 for(const state of ['running','suspended','interrupted']){
  const r=await scenario(state);
  if(r.sources.length!==2||r.sources[0].stops!==1||r.sources[1].starts!==1)throw Error(state+' did not replace exactly one source');
  if(!r.resumes)throw Error(state+' did not resume');
  if(state==='running'&&!r.suspends)throw Error('running context did not receive forced recovery cycle');
 }
 const failed=await scenario('running',{fail:true});
 if(failed.sources.length!==1||!failed.recoverySignaled)throw Error('failed recovery changed source or disarmed retry');
 const failedSource=await scenario('running',{startFail:true});
 if(!failedSource.recoverySignaled||failedSource.sources[1].starts!==0)throw Error('failed source rebuild reported healthy or disarmed retry');
 const unsupportedSuspend=await scenario('running',{suspendThrows:true});
 if(unsupportedSuspend.sources.length!==2||unsupportedSuspend.sources[1].starts!==1)throw Error('synchronous suspend failure prevented resume recovery');
 const repeated=await scenario('running',{multiple:true});
 if(repeated.sources.length!==2||repeated.sources[1].starts!==1||repeated.listenerAdds.click)throw Error('visibility events duplicated handlers or sources');
 const disabled=await scenario('running',{ambient:false});
 if(disabled.sources.length)throw Error('Ambient OFF created a source');
 const muted=await scenario('running',{master:false});
 if(muted.sources.length!==0)throw Error('master OFF recovered ambient');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_narration_is_not_started_or_modified_by_ambient_recovery(self):
        ambient = (ROOT / "ambient.js").read_text(encoding="utf-8")
        self.assertNotIn("playMissionIntro", ambient)
        self.assertNotIn("setPreferenceEnabled", ambient)
        self.assertIn("tombworldnarrationactivity", ambient)


if __name__ == "__main__":
    unittest.main()
