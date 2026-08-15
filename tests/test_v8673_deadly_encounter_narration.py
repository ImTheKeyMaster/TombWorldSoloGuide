import json
import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
NARRATION = (ROOT / "narration.js").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
MANIFEST_PATH = ROOT / "Assets/Audio/Narration/narration-manifest.json"


class DeadlyEncounterNarrationTests(unittest.TestCase):
    def test_pending_play_is_cancelled_cleanly_by_stop_or_priority_narration(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const pending=[];
class Audio {
  constructor(){this.src='';this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){}
  play(){return new Promise(resolve=>pending.push({src:this.src,resolve}));}
}
const entries={
  deadly:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-darkness',available:true,file:'deadly/room-darkness.mp3'},
  'mission.01.intro':{available:true,file:'missions/01.mp3'}
};
const context={Audio,URL,location:{href:'https://example.test/app/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
 localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
const settles=promise=>Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(Error('cancelled discovery remained pending')),100))]);
(async()=>{
 const n=context.TombWorldNarration;await n.init();
 const stopped=n.playDeadlyEncounter('room-darkness','stopped');await flush();
 if(pending.length!==1)throw Error('stopped discovery did not reach pending play');
 const stoppedHandler=Audio.instance.onended;
 n.stop();pending.shift().resolve();
 if(await settles(stopped)!==false)throw Error('stop did not cancel pending discovery');
 if(Audio.instance.onended!==stoppedHandler)throw Error('stop installed a stale completion handler');

 const preempted=n.playDeadlyEncounter('room-darkness','preempted');await flush();
 if(pending.length!==1)throw Error('preempted discovery did not reach pending play');
 const intro=n.playMissionIntro('shifting-labyrinth',true);await flush();
 if(pending.length!==2||!pending[1].src.endsWith('missions/01.mp3'))throw Error('priority narration did not preempt');
 const introHandler=Audio.instance.onended;
 pending.shift().resolve();
 if(await settles(preempted)!==false)throw Error('priority narration did not cancel pending discovery');
 if(Audio.instance.onended!==introHandler)throw Error('preempted discovery replaced the priority completion handler');
 pending.shift().resolve();
 if(!await intro)throw Error('priority narration did not complete');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_event_queued_between_deadly_encounters_plays_after_both_once(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const calls=[];
let active=false;
class Audio {
  constructor(){this.src='';this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){active=false;}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){}
  play(){if(active)throw Error('narration tracks overlapped');active=true;calls.push(this.src);return Promise.resolve();}
  end(){active=false;const ended=this.onended;if(ended)ended();}
}
const entries={
  first:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-darkness',available:true,file:'deadly/room-darkness.mp3'},
  second:{category:'deadly-encounter',deadlyEncounterFeatureId:'objective-control-node',available:true,file:'deadly/objective-control-node.mp3'},
  'event.pending':{available:true,file:'events/pending.mp3'}
};
const context={Audio,URL,location:{href:'https://example.test/app/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
 localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
 const n=context.TombWorldNarration;await n.init();
 const first=n.playDeadlyEncounter('room-darkness','discovery-1');await flush();
 const event=n.playEvent('pending','event-1');
 const second=n.playDeadlyEncounter('objective-control-node','discovery-2');await flush();
 if(calls.length!==1||!calls[0].endsWith('room-darkness.mp3'))throw Error('first discovery was interrupted');
 Audio.instance.end();await flush();
 if(calls.length!==2||!calls[1].endsWith('objective-control-node.mp3'))throw Error('second discovery did not play next');
 Audio.instance.end();await flush();
 if(calls.length!==3||!calls[2].endsWith('events/pending.mp3'))throw Error('pending event did not play after discoveries');
 Audio.instance.end();
 if(!await first||!await second||!await event)throw Error('queued narration was not reported');
 if(calls.filter(src=>src.endsWith('events/pending.mp3')).length!==1)throw Error('pending event did not play exactly once');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_consecutive_discoveries_wait_and_play_every_feature_once_in_order(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const calls=[];
let active=false;
class Audio {
  constructor(){this.src='';this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){active=false;}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){}
  play(){if(active)throw Error('narration tracks overlapped');active=true;calls.push(this.src);return Promise.resolve();}
  end(){active=false;const ended=this.onended;if(ended)ended();}
}
const entries={
  first:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-darkness',available:true,file:'deadly/room-darkness.mp3'},
  unusualFirst:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-crumbling-floor',available:true,file:'deadly/room-crumbling-floor.mp3'},
  unusualSecond:{category:'deadly-encounter',deadlyEncounterFeatureId:'objective-control-node',available:true,file:'deadly/objective-control-node.mp3'}
};
const context={Audio,URL,location:{href:'https://example.test/app/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
 localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
 const n=context.TombWorldNarration;await n.init();
 const first=n.playDeadlyEncounter(['room-darkness'],'discovery-1');await flush();
 const second=n.playDeadlyEncounter(['room-crumbling-floor','objective-control-node'],'discovery-2');await flush();
 if(calls.length!==1||!calls[0].endsWith('room-darkness.mp3'))throw Error('second discovery interrupted the first');
 Audio.instance.end();await flush();
 if(calls.length!==2||!calls[1].endsWith('room-crumbling-floor.mp3'))throw Error('second discovery did not wait its turn');
 Audio.instance.end();await flush();
 if(calls.length!==3||!calls[2].endsWith('objective-control-node.mp3'))throw Error('Unusual feature order changed');
 Audio.instance.end();
 if(!await first||!await second)throw Error('queued discovery playback was not reported');
 if(new Set(calls).size!==3)throw Error('a discovery clip played more than once');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_runtime_sequence_deduplication_controls_and_cancellation(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const calls=[];
class Audio {
  constructor(){this.src='';this.currentTime=0;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){this.paused=true;calls.push('pause:'+this.src+':'+this.currentTime);}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){this.currentTime=0;}
  play(){this.paused=false;this.ended=false;calls.push('play:'+this.src+':'+this.currentTime);return Promise.resolve();}
  end(){this.ended=true;this.paused=true;const ended=this.onended;if(ended)ended();}
}
const entries={
  roomNarration:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-darkness',available:true,file:'deadly/room-darkness.mp3'},
  objectiveNarration:{category:'deadly-encounter',deadlyEncounterFeatureId:'objective-control-node',available:true,file:'deadly/objective-control-node.mp3'},
  secondRoomNarration:{category:'deadly-encounter',deadlyEncounterFeatureId:'room-crumbling-floor',available:true,file:'deadly/room-crumbling-floor.mp3'},
  'event.old':{available:true,file:'events/old.mp3'},
  'mission.01.intro':{available:true,file:'missions/01.mp3'},
  'outcome.01.victory':{available:true,file:'outcomes/01-victory.mp3'}
};
const store=new Map();
const context={Audio,URL,location:{href:'https://example.test/app/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
 localStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value)},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
 const n=context.TombWorldNarration;await n.init();
 const room=n.playDeadlyEncounter('room-darkness','room-transaction');await flush();
 if(!calls.at(-1).includes('room-darkness.mp3'))throw Error('normal room did not play correct feature');
 Audio.instance.end();if(!await room)throw Error('room narration failed');
 const objective=n.playDeadlyEncounter(['objective-control-node'],'objective-transaction');await flush();
 if(!calls.at(-1).includes('objective-control-node.mp3'))throw Error('normal objective did not play correct feature');
 Audio.instance.end();await objective;
 const unusual=n.playDeadlyEncounter(['room-crumbling-floor','room-darkness'],'unusual-transaction');await flush();
 if(!calls.at(-1).includes('room-crumbling-floor.mp3'))throw Error('Unusual order changed');
 if(calls.some(call=>call.includes('unusual.mp3')))throw Error('Unusual narration requested');
 Audio.instance.end();await flush();if(!calls.at(-1).includes('room-darkness.mp3'))throw Error('second Unusual feature did not follow first');
 Audio.instance.end();await unusual;
 n.setMasterEnabled(false);
 if(Audio.instance.src||Audio.instance.currentTime!==0)throw Error('speaker OFF did not destructively stop narration');
 n.setMasterEnabled(true);
 const count=calls.filter(call=>call.startsWith('play:')).length;
 if(await n.playDeadlyEncounter(['room-crumbling-floor','room-darkness'],'unusual-transaction'))throw Error('duplicate discovery narrated');
 if(calls.filter(call=>call.startsWith('play:')).length!==count)throw Error('duplicate requested audio');
 if(!await n.replayLast())throw Error('Replay Last failed');
 if(!calls.at(-1).includes('room-darkness.mp3'))throw Error('Replay Last did not replay final feature');
 Audio.instance.end();
 const resetStart=calls.length;
 const active=n.playDeadlyEncounter(['room-darkness','room-crumbling-floor'],'reset-transaction');await flush();
 n.stop();Audio.instance.end();await flush();await active;
 if(calls.slice(resetStart).filter(call=>call.startsWith('play:')&&call.includes('room-crumbling-floor.mp3')).length)throw Error('second clip began after New Game stop');
 if(!await n.playMissionIntro('shifting-labyrinth',true))throw Error('Mission Intro changed');
 if(!await n.playOutcome('shifting-labyrinth','victory'))throw Error('outcome narration changed');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_app_narrates_only_after_committed_new_discovery(self):
        handler = APP.split("$('#confirmDeadlyDiscovery').onclick=", 1)[1].split("function showDeadlyResult", 1)[0]
        self.assertGreater(handler.index("playDeadlyEncounter"), handler.index("save();"))
        self.assertIn("result.entity&&!result.duplicate&&result.featureIds.length", handler)
        self.assertIn("DeadlyEncounters.transactionId(context)", handler)
        self.assertNotIn("playDeadlyEncounter", APP.split("function render()", 1)[1].split("function renderHome", 1)[0])
        self.assertIn("playDeadlyEncounter:()=>Promise.resolve(false)", APP)

    def test_manifest_has_all_real_features_and_no_unusual_clip(self):
        entries = json.loads(MANIFEST_PATH.read_text())["entries"]
        deadly = [entry for entry in entries.values() if entry.get("category") == "deadly-encounter"]
        self.assertEqual(16, len(deadly))
        self.assertEqual(16, len({entry["deadlyEncounterFeatureId"] for entry in deadly}))
        self.assertNotIn("unusual", {entry["deadlyEncounterFeatureId"] for entry in deadly})
        for entry in deadly:
            self.assertTrue(entry["available"])
            self.assertTrue((MANIFEST_PATH.parent / entry["file"]).is_file())

    def test_release_cache_and_save_versions(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn("const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;", WORKER)
        self.assertIn("await precacheNarration(cache);", WORKER)
        self.assertIn("Object.values(manifest.entries||{})", WORKER)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()
