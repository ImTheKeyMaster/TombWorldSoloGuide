import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


def run_node(script):
    return subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)


class MasterAudioRecoveryTests(unittest.TestCase):
    def test_release_and_parallel_unlock_contract(self):
        self.assertEqual((8, 6, 89), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        master = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
        narration_call = master.index("TombWorldNarration.unlock({force:true})")
        ambient_call = master.index("TombWorldAmbient.unlock()")
        wait = master.index("await Promise.allSettled")
        self.assertLess(narration_call, wait)
        self.assertLess(ambient_call, wait)
        self.assertIn("TombWorldNarration.isPlaybackEnabled()", master)
        self.assertIn("shouldAmbientBeActive()", master)

    def test_category_unlocks_are_invoked_before_either_promise_settles(self):
        function_source = APP[APP.index("async function setGameAudioEnabled") : APP.index("function playPendingBoardSetupMissionIntro")]
        script = f"""
const calls=[];let narrationEnabled=true,ambientRequired=true;
let resolveNarration,resolveAmbient;
const TombWorldNarration={{setMasterEnabled:v=>calls.push('master:'+v),isPlaybackEnabled:()=>narrationEnabled,unlock:o=>{{calls.push('narration:'+o.force);return new Promise(r=>resolveNarration=r)}}}};
const TombWorldAmbient={{unlock:()=>{{calls.push('ambient');return new Promise(r=>resolveAmbient=r)}},stop:()=>calls.push('ambient-stop')}};
let ambientEnabled=true,appliedAmbientEnabled=false;
const shouldAmbientBeActive=()=>ambientRequired&&appliedAmbientEnabled;
const reconcileAmbientActiveState=()=>calls.push('reconcile');
const playPendingBoardSetupMissionIntro=()=>calls.push('intro');
const syncNarrationControls=()=>calls.push('sync');
{function_source}
(async()=>{{
 const pending=setGameAudioEnabled(true);
 await Promise.resolve();
 if(calls.join(',')!=='master:true,narration:true,ambient')throw Error('both unlocks were not synchronously initiated: '+calls);
 resolveAmbient(true);resolveNarration(true);await pending;
 narrationEnabled=false;ambientRequired=true;calls.length=0;resolveAmbient=null;
 const ambientOnly=setGameAudioEnabled(true);await Promise.resolve();
 if(calls.join(',')!=='master:true,ambient'||!resolveAmbient)throw Error('ambient-only path was delayed or primed narration');
 resolveAmbient(true);await ambientOnly;
 narrationEnabled=true;ambientRequired=false;calls.length=0;resolveNarration=null;
 const narrationOnly=setGameAudioEnabled(true);await Promise.resolve();
 if(calls.join(',')!=='master:true,narration:true'||!resolveNarration)throw Error('narration-only path touched ambient');
 resolveNarration(true);await narrationOnly;
 narrationEnabled=false;ambientRequired=false;calls.length=0;await setGameAudioEnabled(true);
 if(calls.includes('ambient')||calls.some(x=>x.startsWith('narration:')))throw Error('both-off path performed unlock work');
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_master_reenable_forces_new_narration_prime_and_failure_retries(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let plays=0,loads=0,fail=false;const listeners=new Map();
class Audio{constructor(){Audio.instance=this;this.src='';this.paused=true;this.ended=false}play(){plays++;return fail?Promise.reject(Error('blocked')):Promise.resolve()}pause(){this.paused=true}removeAttribute(){this.src=''}load(){loads++}}
const document={addEventListener:(t,h)=>listeners.set(t,h),removeEventListener:(t,h)=>{if(listeners.get(t)===h)listeners.delete(t)}};
const context={Audio,document,URL,location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:false})};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;
if(!await n.unlock())throw Error('initial prime failed');
n.setMasterEnabled(false);if(context.Audio.instance?.src||loads!==1)throw Error('master off did not reset media element');n.setMasterEnabled(true);
if(!await n.unlock({force:true})||plays!==2)throw Error('master re-enable did not freshly prime');
n.setMasterEnabled(false);n.setMasterEnabled(true);fail=true;
if(await n.unlock({force:true}))throw Error('failed prime reported success');
if(!listeners.has('click'))throw Error('failed prime was not retryable');
fail=false;await listeners.get('click')();await Promise.resolve();
if(plays!==4)throw Error('gesture retry did not prime again');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_suspended_and_interrupted_contexts_recover_and_failure_stays_retryable(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
async function scenario(initial,canRecover){
 const listeners=new Map();let resumes=0,suspends=0;
 class AudioContext{constructor(){this.state=initial;this.currentTime=0;this.destination={}}resume(){resumes++;if(canRecover&&(initial!=='interrupted'||suspends))this.state='running';return Promise.resolve()}suspend(){suspends++;this.state=canRecover?'suspended':'interrupted';return Promise.resolve()}decodeAudioData(){return Promise.resolve({duration:30})}createGain(){return {gain:{value:0,cancelScheduledValues(){},setValueAtTime(){},linearRampToValueAtTime(){}},connect(){}}}createBufferSource(){return {connect(){},disconnect(){},start(){},stop(){}}}}
 const config={schemaVersion:1,file:'Ambient/caverns.ogg',normalGain:.2,duckGain:.05,fadeInMs:1,fadeOutMs:1,duckAttackMs:1,duckReleaseMs:1,loopStartSeconds:0,loopEndSeconds:null};
 const document={visibilityState:'visible',addEventListener:(t,h)=>listeners.set(t,h),removeEventListener:(t,h)=>{if(listeners.get(t)===h)listeners.delete(t)}};
 const s={AudioContext,document,URL,location:{href:'https://example.test/'},TombWorldNarration:{isMasterEnabled:()=>true},addEventListener(){},setTimeout,clearTimeout,fetch:async u=>String(u).includes('ambient-config')?{ok:true,json:async()=>config}:{ok:true,arrayBuffer:async()=>new ArrayBuffer(1)}};s.window=s;
 vm.createContext(s);vm.runInContext(fs.readFileSync('ambient.js','utf8'),s);const ok=await s.TombWorldAmbient.unlock();
 if(ok!==canRecover)throw Error(initial+' recovery result wrong');
 if(!resumes||initial==='interrupted'&&canRecover&&!suspends)throw Error(initial+' recovery was not attempted');
 if(!canRecover&&!listeners.has('click'))throw Error('failure lost gesture fallback');
}
(async()=>{await scenario('suspended',true);await scenario('interrupted',true);await scenario('interrupted',false)})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_visibility_recovery_is_guarded_and_listener_is_unique(self):
        self.assertIn("document?.visibilityState !== 'visible'", AMBIENT)
        self.assertIn("context?.state === 'running'", AMBIENT)
        self.assertIn("resumeContextFromGesture(false)", AMBIENT)
        self.assertIn("if (gestureUnlockHandlerInstalled", AMBIENT)
        self.assertEqual(1, AMBIENT.count("global.document.addEventListener('click', onFirstAudioGesture, true)"))


if __name__ == "__main__":
    unittest.main()
