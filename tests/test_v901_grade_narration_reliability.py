import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")


class GradeNarrationReliabilityTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_app_milestone_failure_retry_in_flight_modes_and_dismissal(self):
        script = r"""
const fs=require('fs');const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('async function narrateVisibleGradeMilestone()');
const fnSource=source.slice(start,source.indexOf('\n\n  function renderPlay()',start));
function harness(gameMode,grade,enabled=true){
 const state={gameMode,gradeMilestone:{grade,instanceId:`grade:${grade}:1`,narrationSeen:false}};
 const calls=[],pending=[],gradeNarrationInFlight=new Set();let saves=0,recoveries=0;
 const TombWorldNarration={isPlaybackEnabled:()=>enabled,playGradeEscalation:(g,id)=>{calls.push([g,id]);return new Promise(resolve=>pending.push(resolve))}};
 const $=()=>true,save=()=>{saves++;return true},armAudioGestureRecovery=()=>{recoveries++},narrationGestureRecoveryRequired=false;
 const narrate=new Function('state','gradeNarrationInFlight','TombWorldNarration','$','save','armAudioGestureRecovery','narrationGestureRecoveryRequired',`return (${fnSource})`)(state,gradeNarrationInFlight,TombWorldNarration,$,save,armAudioGestureRecovery,narrationGestureRecoveryRequired);
 return {state,calls,pending,narrate,saves:()=>saves,recoveries:()=>recoveries};
}
(async()=>{
 for(const grade of [1,2,3]){
  const h=harness(grade===1?'pvp':'solo',grade);const first=h.narrate();const parallel=h.narrate();
  if(h.calls.length!==1)throw Error(`parallel grade ${grade}`);if(await parallel)throw Error('parallel reported success');
  h.pending.shift()(false);if(await first)throw Error('failure reported success');
  if(h.state.gradeMilestone.narrationSeen||h.saves()!==0||h.recoveries()!==1)throw Error(`failure consumed grade ${grade}`);
  const retry=h.narrate();if(h.calls.length!==2)throw Error(`grade ${grade} did not retry`);h.pending.shift()(true);
  if(!await retry||!h.state.gradeMilestone.narrationSeen||h.saves()!==1)throw Error(`grade ${grade} success not saved`);
  await h.narrate();if(h.calls.length!==2)throw Error(`grade ${grade} replayed after success`);
 }
 const disabled=harness('pvp',1,false);if(await disabled.narrate()||disabled.calls.length||disabled.state.gradeMilestone.narrationSeen)throw Error('disabled audio marked heard');
 const dismissed=harness('pvp',1);const pending=dismissed.narrate();dismissed.state.gradeMilestone=null;dismissed.pending.shift()(true);await pending;
 if(dismissed.saves()!==0){throw Error('dismissed milestone saved narration state')}await dismissed.narrate();if(dismissed.calls.length!==1)throw Error('dismissed milestone replayed invisibly');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        self.run_node(script)

    def test_duplicate_keys_release_on_failure_and_stick_on_success(self):
        script = r"""
const fs=require('fs'),vm=require('vm');let plays=0,fail=true;
class Audio{constructor(){this.paused=true;Audio.instance=this}play(){plays++;this.paused=false;return fail?Promise.reject(Error('blocked')):Promise.resolve()}pause(){this.paused=true}load(){}removeAttribute(){} }
const entries={'grade.1.stirring':{available:true,file:'g1.mp3'}};
const c={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),localStorage:{getItem:()=>null,setItem(){}},dispatchEvent(){},CustomEvent:function(){}};c.window=c;
vm.createContext(c);vm.runInContext(fs.readFileSync('narration.js','utf8'),c);const n=c.TombWorldNarration;
(async()=>{
 if(await n.playGradeEscalation(1,'grade:1:1'))throw Error('blocked attempt succeeded');
 fail=false;if(!await n.playGradeEscalation(1,'grade:1:1'))throw Error('failed key was not released');
 if(await n.playGradeEscalation(1,'grade:1:1'))throw Error('successful key was released');
 Audio.instance.onended?.();
 if(!await n.playGradeEscalation(1,'grade:1:2'))throw Error('different occurrence suppressed');
 if(plays!==3)throw Error(`unexpected physical starts ${plays}`);
})().catch(e=>{console.error(e);process.exit(1)});
"""
        self.run_node(script)

    def test_recovery_hook_and_release_surfaces_are_focused(self):
        self.assertEqual((9, 2, 1), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        coordinator = APP[APP.index("async function applySelectedAudioFromGesture"):APP.index("function handleNarrationUsable")]
        usable = APP[APP.index("function handleNarrationUsable"):APP.index("function syncNarrationControls")]
        self.assertIn("void narrateVisibleGradeMilestone()", coordinator)
        self.assertIn("void narrateVisibleGradeMilestone()", usable)
        self.assertIn("if (!started) automaticPlayback.delete(duplicateKey)", NARRATION)
        event = NARRATION[NARRATION.index("function playEvent"):NARRATION.index("function playGradeEscalation")]
        self.assertNotIn("automaticPlayback.delete", event)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
