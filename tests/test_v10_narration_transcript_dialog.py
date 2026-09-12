import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
TRANSCRIPT = (ROOT / "narration-transcript.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")


class NarrationTranscriptDialogTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_dedicated_controls_and_script_order(self):
        self.assertIn('id="narrationTranscriptDialog"', INDEX)
        self.assertIn('id="narrationTranscriptReopen"', INDEX)
        self.assertIn('aria-label="Hide transcript"', INDEX)
        self.assertIn('aria-labelledby="narrationTranscriptCategory"', INDEX)
        self.assertNotIn('id="narrationTranscriptTitle"', INDEX)
        self.assertNotIn('<h2 id="narrationTranscriptTitle">Narration</h2>', INDEX)
        self.assertIn('id="narrationTranscriptSkip" class="btn ghost" type="button">Skip This Narration</button>', INDEX)
        self.assertIn('id="narrationTranscriptStop" class="btn danger" type="button">Stop All Narration</button>', INDEX)
        self.assertLess(INDEX.index(f"narration.js?v={CURRENT_APP_VERSION}"), INDEX.index(f"narration-transcript.js?v={CURRENT_APP_VERSION}"))
        self.assertLess(INDEX.index(f"narration-transcript.js?v={CURRENT_APP_VERSION}"), INDEX.index(f"app.js?v={CURRENT_APP_VERSION}"))

    def test_static_safe_transcript_player_contract(self):
        self.assertIn("paragraph.textContent = text", TRANSCRIPT)
        self.assertIn("body.replaceChildren(...paragraphs)", TRANSCRIPT)
        self.assertNotIn("innerHTML", TRANSCRIPT)
        self.assertIn("Loading transcript…", TRANSCRIPT)
        self.assertIn("Transcript unavailable.", TRANSCRIPT)
        self.assertIn("currentTimeMs / durationMs", TRANSCRIPT)
        self.assertIn("requestAnimationFrame(progressLoop)", TRANSCRIPT)
        self.assertNotIn("setInterval", TRANSCRIPT)
        self.assertIn("state.alignment?.words", TRANSCRIPT)
        self.assertNotIn("elevenlabs", TRANSCRIPT.lower())
        for label in ("MISSION BRIEFING", "TOMB WORLD EVENT", "THREAT ESCALATION",
                      "MISSION OUTCOME", "DEADLY ENCOUNTER"):
            self.assertIn(label, TRANSCRIPT)
        self.assertNotIn("category.textContent = state.id", TRANSCRIPT)

    def test_controls_use_only_public_narration_actions(self):
        self.assertIn("narration.pauseNarration()", TRANSCRIPT)
        self.assertIn("await narration.resumeNarration()", TRANSCRIPT)
        self.assertIn("narration.skipCurrent()", TRANSCRIPT)
        self.assertIn("narration.stop()", TRANSCRIPT)
        hide_handler = TRANSCRIPT.split("function hideTranscript()", 1)[1].split("hide.addEventListener", 1)[0]
        self.assertNotIn(".stop(", hide_handler)
        self.assertIn("event.preventDefault()", TRANSCRIPT)
        self.assertIn("narration.isMasterEnabled?.() === false", TRANSCRIPT)
        self.assertIn("if (global.document.activeElement !== reopen) previousFocus = global.document.activeElement;", TRANSCRIPT)

    def test_time_formatter_handles_boundaries(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');
const context={};context.window=context;vm.createContext(context);
vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);
const f=context.TombWorldNarrationTranscript.formatTime;
for(const [value,want] of [[0,'0:00'],[2486,'0:02'],[23236,'0:23'],[61000,'1:01'],[-1,'0:00'],[NaN,'0:00'],[Infinity,'0:00']]){
 if(f(value)!==want)throw Error(`${value}: ${f(value)} != ${want}`);
}
""")

    def test_reopen_preserves_original_focus_for_playback_end(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');
const listeners={};let state={active:false,id:null,currentTimeMs:0,durationMs:0};
const listenerCounts={};
const document={readyState:'complete',activeElement:null,getElementById:id=>elements[id],createElement:tag=>({tag,textContent:''})};
function element(id){return elements[id]={id,hidden:false,open:false,isConnected:true,style:{},attributes:{},children:[],listeners:{},addEventListener(type,fn){this.listeners[type]=fn},setAttribute(name,value){this.attributes[name]=value},removeAttribute(name){delete this.attributes[name]},replaceChildren(...children){this.children=children},focus(){document.activeElement=this},close(){this.open=false},showModal(){this.open=true},querySelector(){return fill}}}
const elements={},fill={style:{}};
for(const id of ['narrationTranscriptDialog','narrationTranscriptReopen','narrationTranscriptCategory','narrationTranscriptBody','narrationTranscriptProgress','narrationTranscriptTime','narrationTranscriptHide','narrationTranscriptPause','narrationTranscriptSkip','narrationTranscriptStop','narrationTranscriptPauseHelp'])element(id);
const origin=element('origin');document.activeElement=origin;
let skipCalls=0,stopCalls=0;
const narration={getPlaybackState:()=>state,isMasterEnabled:()=>true,pauseNarration(){},resumeNarration(){},skipCurrent(){skipCalls++},stop(){stopCalls++}};
const context={document,TombWorldNarration:narration,requestAnimationFrame:()=>1,cancelAnimationFrame(){},addEventListener:(type,fn)=>{listeners[type]=fn;listenerCounts[type]=(listenerCounts[type]||0)+1},CustomEvent:function(){}};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);
context.TombWorldNarrationTranscript.init();
if(listenerCounts.tombworldnarrationstatechange!==1)throw Error('init attached duplicate state listeners');
state={active:true,id:'mission.01.intro',category:'mission-intro',currentTimeMs:0,durationMs:1000,transcriptAvailable:true,transcript:'First paragraph.\n\nSecond paragraph.'};listeners.tombworldnarrationstatechange({detail:state});
if(elements.narrationTranscriptCategory.textContent!=='MISSION BRIEFING')throw Error('category eyebrow was not updated');
if(elements.narrationTranscriptBody.children.length!==2||elements.narrationTranscriptBody.children[1].textContent!=='Second paragraph.')throw Error('paragraph structure was not preserved');
elements.narrationTranscriptSkip.listeners.click();elements.narrationTranscriptStop.listeners.click();
if(skipCalls!==1||stopCalls!==1)throw Error('transcript controls changed narration actions');
elements.narrationTranscriptHide.listeners.click();
if(document.activeElement!==elements.narrationTranscriptReopen)throw Error('hide did not focus reopen');
elements.narrationTranscriptReopen.listeners.click();
state={active:false,id:null,currentTimeMs:0,durationMs:0,lastEndReason:'natural'};listeners.tombworldnarrationstatechange({detail:state});
if(document.activeElement!==origin)throw Error('playback end did not restore original app focus');
""")

    def test_skip_advances_event_and_deadly_queues_while_paused(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');const calls=[];
class Audio{constructor(){this.src='';this.currentTime=0;this.duration=10;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this}pause(){this.paused=true}removeAttribute(){this.src=''}load(){}play(){this.paused=false;this.ended=false;calls.push(this.src);return Promise.resolve()}}
const entries={
 'event.one':{category:'event',available:true,file:'one.mp3',durationMs:10000},
 'event.two':{category:'event',available:true,file:'two.mp3',durationMs:10000},
 deadly1:{category:'deadly-encounter',deadlyEncounterFeatureId:'first',available:true,file:'first.mp3',durationMs:10000},
 deadly2:{category:'deadly-encounter',deadlyEncounterFeatureId:'second',available:true,file:'second.mp3',durationMs:10000}
};
const context={Audio,URL,location:{href:'https://example.test/'},fetch:async url=>url.includes('manifest')?{ok:true,json:async()=>({entries})}:{ok:false,json:async()=>null},localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);const n=context.TombWorldNarration,flush=()=>new Promise(r=>setTimeout(r,0));
(async()=>{
 const event1=n.playEvent('one','one'),event2=n.playEvent('two','two');await flush();n.pauseNarration();if(!n.skipCurrent())throw Error('paused event was not skipped');await flush();
 if(!calls.at(-1).endsWith('two.mp3')||n.getPlaybackState().id!=='event.two')throw Error('event queue did not advance');
 n.skipCurrent();await Promise.all([event1,event2]);if(n.getPlaybackState().lastEndReason!=='skip')throw Error('skip reason missing');
 const deadly=n.playDeadlyEncounter(['first','second'],'deadly');await flush();n.skipCurrent();await flush();
 if(!calls.at(-1).endsWith('second.mp3')||n.getPlaybackState().id!=='deadly2')throw Error('deadly queue did not advance');
 n.skipCurrent();if(!await deadly)throw Error('deadly result changed');
})().catch(error=>{console.error(error);process.exit(1)});
""")

    def test_mobile_layout_and_persistence_boundaries(self):
        self.assertIn(".narration-transcript-body", STYLES)
        self.assertIn("overflow:auto", STYLES)
        self.assertIn("@media(max-width:480px)", STYLES)
        self.assertIn("env(safe-area-inset-bottom)", STYLES)
        transcript_body_rule = STYLES.split(".narration-transcript-body{", 1)[1].split("}", 1)[0]
        self.assertIn("min-height:0", transcript_body_rule)
        self.assertIn("line-height:1.5", transcript_body_rule)
        self.assertIn("white-space:pre-wrap", transcript_body_rule)
        self.assertIn(".narration-transcript-body p{margin:0 0 .75em}", STYLES)
        self.assertIn(".narration-transcript-body p:last-child{margin-bottom:0}", STYLES)
        mobile_rule = STYLES.split("@media(max-width:480px)", 1)[1].split("@media", 1)[0]
        self.assertIn("grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr)", mobile_rule)
        self.assertIn(".narration-transcript-controls .danger{grid-column:1/-1}", mobile_rule)
        self.assertNotIn("narration-transcript.js", WORKER)
        self.assertIn(f">V{CURRENT_APP_VERSION}<", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", (ROOT / "app.js").read_text())

    def test_cogitator_polish_is_lightweight_and_mobile_safe(self):
        dialog_rule = STYLES.split(".narration-transcript-dialog{", 1)[1].split("}", 1)[0]
        body_rule = STYLES.split(".narration-transcript-body{", 1)[1].split("}", 1)[0]
        progress_rule = STYLES.split(".narration-transcript-progress{", 1)[1].split("}", 1)[0]
        reopen_rule = STYLES.split(".narration-transcript-reopen{", 1)[1].split("}", 1)[0]

        self.assertIn("linear-gradient", dialog_rule)
        self.assertIn("border-radius:17px", dialog_rule)
        self.assertIn("background-size:100% 4px", body_rule)
        self.assertIn("repeating-linear-gradient", progress_rule)
        self.assertIn("max-width:calc(100% - 20px)", STYLES)
        self.assertIn("border-left:3px solid var(--green)", reopen_rule)
        self.assertNotIn("animation:", "\n".join((dialog_rule, body_rule, progress_rule, reopen_rule)))


if __name__ == "__main__":
    unittest.main()
