import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")


class NarrationRuntimeStateTests(unittest.TestCase):
    def run_node(self, assertions, fetch_body=None, synchronous_fetch=False):
        fetch_body = fetch_body or "return {ok:true,json:async()=>url.includes('narration-manifest')?{entries}:alignment};"
        fetch_keyword = "" if synchronous_fetch else "async "
        script = f"""
const fs=require('fs'),vm=require('vm');
const events=[],fetches=[],plays=[];
const entry={{available:true,file:'missions/01.mp3',category:'mission-intro',durationMs:12000,scriptHash:'script',audioHash:'audio'}};
const entries={{'mission.01.intro':entry,'event.first':{{...entry,file:'events/first.mp3',category:'event'}},'event.second':{{...entry,file:'events/second.mp3',category:'event'}}}};
const alignment={{schemaVersion:1,id:'mission.01.intro',text:'Complete transcript',durationMs:12000,scriptHash:'script',audioHash:'audio',qualityStatus:'REVIEW',alignmentLoss:.2,words:[{{text:'Complete',startMs:0,endMs:500,loss:.1}},{{text:' ',startMs:500,endMs:550,loss:.01}},{{text:'transcript',startMs:550,endMs:1000,loss:.1}}]}};
class Audio{{constructor(){{this.src='';this.currentTime=0;this.duration=NaN;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this}}play(){{this.paused=false;this.ended=false;plays.push(this.src);return Promise.resolve()}}pause(){{this.paused=true}}removeAttribute(){{this.src=''}}load(){{this.currentTime=0}}end(){{this.paused=true;this.ended=true;if(this.onended)this.onended()}}}}
const context={{Audio,URL,location:{{href:'https://example.test/app/'}},localStorage:{{getItem:()=>null,setItem:()=>{{}}}},CustomEvent:function(type,options){{this.type=type;this.detail=options?.detail}},dispatchEvent:event=>events.push(event),fetch:{fetch_keyword}url=>{{fetches.push(String(url));{fetch_body}}}}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{{const n=context.TombWorldNarration;{assertions}}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_lazy_valid_alignment_snapshot_timing_duration_and_defensive_copy(self):
        self.run_node(r"""
await n.init();
if(fetches.length!==1)throw Error('alignment fetched during init');
if(!await n.playMissionIntro('shifting-labyrinth'))throw Error('audio did not start');await flush();
if(fetches.length!==2||!fetches[1].endsWith('/alignment/mission.01.intro.json'))throw Error('wrong lazy alignment URL '+fetches);
const state=n.getPlaybackState();
if(!state.active||!state.playing||state.paused||state.id!=='mission.01.intro'||state.category!=='mission-intro')throw Error('active state incorrect');
if(!state.transcriptAvailable||state.transcript!=='Complete transcript'||state.alignment.qualityStatus!=='REVIEW'||state.alignment.words.length!==3)throw Error('valid REVIEW transcript unavailable');
if(state.durationMs!==12000)throw Error('manifest duration fallback failed');
Audio.instance.currentTime=2.345;Audio.instance.duration=11.5;
if(n.getPlaybackState().currentTimeMs!==2345||n.getPlaybackState().durationMs!==11500)throw Error('Audio timing authority not used');
state.alignment.words[0].startMs=999999;state.manifest.category='changed';
const safe=n.getPlaybackState();if(safe.alignment.words[0].startMs!==0||safe.category!=='mission-intro')throw Error('snapshot mutated internals');
if(!events.some(e=>e.type==='tombworldnarrationstatechange'&&e.detail.transcriptAvailable))throw Error('alignment state event missing');
""")

    def test_pause_resume_master_mute_stop_and_natural_end(self):
        self.run_node(r"""
await n.playMissionIntro('shifting-labyrinth');await flush();const player=Audio.instance;player.currentTime=4.2;
if(!n.pauseNarration()||!player.paused)throw Error('user pause failed');
let state=n.getPlaybackState();if(!state.active||!state.paused||!state.pausedByUser||state.pausedByMaster||state.currentTimeMs!==4200)throw Error('user pause state wrong');
n.setMasterEnabled(false);n.setMasterEnabled(true);await n.activateFromGesture();if(!player.paused)throw Error('master path resumed user pause');
if(!await n.resumeNarration()||player.paused||player.currentTime!==4.2)throw Error('user resume failed');
n.stop();state=n.getPlaybackState();if(state.active||state.transcriptAvailable||state.lastEndReason!=='stop'||player.src)throw Error('stop state wrong');
if(!await n.replayLast())throw Error('Replay Last failed');await flush();if(n.getPlaybackState().id!=='mission.01.intro')throw Error('Replay Last active entry wrong');
player.end();state=n.getPlaybackState();if(state.active||state.lastEndReason!=='natural')throw Error('natural end state wrong');
""")

    def test_valid_alignment_is_cached_for_replay(self):
        self.run_node(r"""
await n.playMissionIntro('shifting-labyrinth');await flush();n.stop();
if(!await n.replayLast())throw Error('replay failed');await flush();
if(fetches.filter(url=>url.includes('/alignment/')).length!==1||!n.getPlaybackState().transcriptAvailable)throw Error('alignment cache not reused');
""")

    def test_invalid_missing_and_malformed_alignment_never_block_audio(self):
        cases = {
            "schema": "return {ok:true,json:async()=>({...alignment,schemaVersion:2})};",
            "script hash": "return {ok:true,json:async()=>({...alignment,scriptHash:'wrong'})};",
            "audio hash": "return {ok:true,json:async()=>({...alignment,audioHash:'wrong'})};",
            "duration": "return {ok:true,json:async()=>({...alignment,durationMs:1})};",
            "wrong id": "return {ok:true,json:async()=>({...alignment,id:'other'})};",
            "words": "return {ok:true,json:async()=>({...alignment,words:[{text:'bad',startMs:2,endMs:1}]})};",
            "missing": "return {ok:false,json:async()=>alignment};",
            "malformed": "return {ok:true,json:async()=>{throw Error('bad json')}};",
            "offline": "throw Error('offline');",
        }
        for label, alignment_response in cases.items():
            with self.subTest(label=label):
                fetch_body = f"if(url.includes('narration-manifest'))return {{ok:true,json:async()=>({{entries}})}};{alignment_response}"
                self.run_node(r"""
if(!await n.playMissionIntro('shifting-labyrinth'))throw Error('audio blocked');await flush();
if(plays.length!==1||!n.getPlaybackState().active||n.getPlaybackState().transcriptAvailable)throw Error('fallback failed');
""", fetch_body)

    def test_synchronous_alignment_fetch_failure_cannot_reject_audio_playback(self):
        self.run_node(r"""
if(!await n.playMissionIntro('shifting-labyrinth'))throw Error('synchronous fetch failure blocked audio');await flush();
const state=n.getPlaybackState();
if(!state.active||!state.playing||state.transcriptAvailable||plays.length!==1)throw Error('audio-only fallback state incorrect');
""", "if(url.includes('narration-manifest'))return Promise.resolve({ok:true,json:async()=>({entries})});throw Error('synchronous offline failure');", True)

    def test_queued_audio_error_is_not_reported_as_natural_completion(self):
        self.run_node(r"""
const queued=n.playEvent('first','error-1');await flush();
Audio.instance.onerror();await queued;await flush();
const state=n.getPlaybackState();
if(state.active||state.lastEndReason!=='stop')throw Error('audio error was labeled as natural completion');
""")

    def test_stale_queue_callback_cannot_finish_a_new_entry(self):
        self.run_node(r"""
const first=n.playEvent('first','stale-1');await flush();const staleEnded=Audio.instance.onended;
n.stop();await first;
const second=n.playEvent('second','stale-2');await flush();
staleEnded();
if(n.getPlaybackState().id!=='event.second'||!n.getPlaybackState().active)throw Error('stale callback finished the new entry');
Audio.instance.end();if(!await second)throw Error('new queued entry failed');
""")

    def test_repeated_master_mute_preserves_master_pause_resume(self):
        self.run_node(r"""
await n.playMissionIntro('shifting-labyrinth');const player=Audio.instance;player.currentTime=3.5;
n.setMasterEnabled(false);n.setMasterEnabled(false);
let state=n.getPlaybackState();if(!state.pausedByMaster||!state.paused||!player.paused)throw Error('repeated mute lost master pause');
n.setMasterEnabled(true);if(!await n.activateFromGesture())throw Error('master resume failed');
state=n.getPlaybackState();if(state.pausedByMaster||state.paused||!state.playing||player.currentTime!==3.5)throw Error('master resume state incorrect');
""")

    def test_late_alignment_cannot_replace_new_active_entry_and_queue_continues(self):
        fetch_body = """
if(url.includes('narration-manifest'))return {ok:true,json:async()=>({entries})};
if(url.includes('event.first'))return {ok:true,json:()=>new Promise(resolve=>context.resolveFirst=()=>resolve({...alignment,id:'event.first'}))};
return {ok:false,json:async()=>null};
"""
        self.run_node(r"""
const firstResult=n.playEvent('first','queue-1');const queued=n.playEvent('second','queue-2');await flush();const first=Audio.instance;
first.end();await firstResult;await flush();
if(n.getPlaybackState().id!=='event.second')throw Error('queued entry did not become active');
context.resolveFirst();await flush();if(n.getPlaybackState().transcriptAvailable)throw Error('late alignment attached to new entry');
Audio.instance.end();if(!await queued)throw Error('alignment failure stalled queue');
""", fetch_body)

    def test_runtime_boundaries_and_v1001_production_version(self):
        self.assertIn(".replace(/[^A-Za-z0-9._-]/g, '_')", NARRATION)
        self.assertNotIn("elevenlabs", NARRATION.lower())
        self.assertNotRegex(NARRATION, r"(?i)api[_-]?key")
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text(encoding="utf-8"))
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", (ROOT / "app.js").read_text(encoding="utf-8"))
        self.assertEqual((10, 0, 1), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", (ROOT / "app.js").read_text(encoding="utf-8"))
        self.assertIn("narrationAlignmentFiles(narrationManifest)",
                      (ROOT / "service-worker.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
