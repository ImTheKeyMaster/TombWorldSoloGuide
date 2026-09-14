import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
TRANSCRIPT = (ROOT / "narration-transcript.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def run_node(source):
    result = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_prepare_start_pause_resume_failure_master_queue_and_activity():
    run_node(r"""
const fs=require('fs'),vm=require('vm');
const plays=[],events=[];let rejectPlay=false;
class Audio { constructor(){this.src='';this.currentTime=0;this.duration=12;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this}
 play(){plays.push(this.src);if(rejectPlay){this.paused=true;return Promise.reject(Error('blocked'))}this.paused=false;this.ended=false;return Promise.resolve()}
 pause(){this.paused=true} removeAttribute(){this.src=''} load(){this.currentTime=0} end(){this.paused=true;this.ended=true;this.onended?.()} }
const base={available:true,file:'clip.mp3',durationMs:12000,scriptHash:'s',audioHash:'a'};
const entries={
 'mission.01.intro':{...base,category:'mission-intro'},'event.one':{...base,file:'one.mp3',category:'event'},
 'event.two':{...base,file:'two.mp3',category:'event'},'grade.1.stirring':{...base,category:'grade'},
 'outcome.01.victory':{...base,category:'outcome'},deadly:{...base,category:'deadly-encounter',deadlyEncounterFeatureId:'room'}
};
const alignment={schemaVersion:1,id:'mission.01.intro',text:'First word',durationMs:12000,scriptHash:'s',audioHash:'a',words:[{text:'First',startMs:0,endMs:500},{text:'word',startMs:501,endMs:900}]};
const context={Audio,URL,location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},CustomEvent:function(type,o){this.type=type;this.detail=o?.detail},dispatchEvent:e=>events.push(e),fetch:async url=>url.includes('manifest')?{ok:true,json:async()=>({entries})}:{ok:true,json:async()=>({...alignment,id:String(url).match(/([^/]+)\.json$/)[1]})}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const n=context.TombWorldNarration,flush=()=>new Promise(r=>setTimeout(r,0));
(async()=>{
 if(!await n.playMissionIntro('shifting-labyrinth'))throw Error('mission was not prepared');await flush();
 let state=n.getPlaybackState();
 if(plays.length||!state.active||state.started||state.playing||state.paused||state.pausedByUser||state.currentTimeMs!==0)throw Error('invalid prepared state '+JSON.stringify(state));
 if(!state.transcriptAvailable)throw Error('alignment did not load before Play');
 if(events.some(e=>e.type==='tombworldnarrationactivity'&&e.detail.active))throw Error('ambient ducked during preparation');
 rejectPlay=true;if(await n.startNarration())throw Error('failed Play succeeded');state=n.getPlaybackState();
 if(state.started||state.playing||!state.active)throw Error('failed Play discarded or started narration');
 rejectPlay=false;if(!await n.startNarration())throw Error('Play failed');state=n.getPlaybackState();
 if(!state.started||!state.playing||state.paused)throw Error('successful Play state incorrect');
 Audio.instance.currentTime=4.25;if(!n.pauseNarration())throw Error('Pause failed');state=n.getPlaybackState();
 if(!state.started||state.playing||!state.paused||!state.pausedByUser||state.currentTimeMs!==4250)throw Error('Pause state incorrect');
 if(!await n.resumeNarration()||Audio.instance.currentTime!==4.25)throw Error('Resume lost position');
 n.stop();
 await n.playMissionIntro('shifting-labyrinth',true);n.setMasterEnabled(false);
 if(await n.startNarration())throw Error('master-off Play succeeded');n.setMasterEnabled(true);
 if(n.getPlaybackState().started||plays.length!==3)throw Error('master restoration autoplayed prepared narration');
 n.stop();
 const first=n.playEvent('one','one'),second=n.playEvent('two','two');await flush();
 if(plays.some(src=>src.endsWith('one.mp3'))||n.getPlaybackState().id!=='event.one')throw Error('queued first entry autoplayed');
 if(n.getPlaybackState().id==='event.two')throw Error('queue advanced on preparation');
 if(!n.skipCurrent())throw Error('skip-before-Play failed');await flush();
 if(n.getPlaybackState().id!=='event.two'||n.getPlaybackState().started)throw Error('next queue entry did not wait for Play');
 n.stop();await Promise.all([first,second]);
})().catch(e=>{console.error(e);process.exit(1)});
""")


def test_transcript_uses_three_state_control_and_unstarted_words_are_upcoming():
    assert "pause.textContent = !state.started ? 'Play'" in TRANSCRIPT
    assert "if (!state.started) await narration.startNarration();" in TRANSCRIPT
    assert "if (!state.started) {" in TRANSCRIPT
    assert "setWordState(index, 'upcoming')" in TRANSCRIPT
    assert "if (state.started) animationFrame" in TRANSCRIPT


def test_release_surfaces_and_save_contract():
    assert CURRENT_APP_VERSION == "10.0.10"
    assert "const APP_VERSION = '10.0.10';" in (ROOT / "service-worker.js").read_text()
    assert '<div class="version">V10.0.10</div>' in INDEX
    assert INDEX.count("?v=10.0.10") == 11
    assert "analytics.js?release=10.0.10" in INDEX
    assert README.startswith("# Tomb World Battle Guide v10.0.10\n\n## v10.0.10")
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text()
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in (ROOT / "app.js").read_text()


def test_prepare_path_has_no_player_play_call_and_public_start_api_owns_it():
    prepare = NARRATION.split("async function playEntry", 1)[1].split("function startNarration", 1)[0]
    start = NARRATION.split("function startNarration", 1)[1].split("async function drainEventQueue", 1)[0]
    assert "player.play()" not in prepare
    assert "player.play()" in start
    assert "startNarration" in NARRATION.split("global.TombWorldNarration", 1)[1]
