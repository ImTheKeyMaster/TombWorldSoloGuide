import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")


def section(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


class GradeNarrationReleaseTests(unittest.TestCase):
    def test_version_schema_and_persisted_first_visible_lifecycle(self):
        self.assertIn(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}", (ROOT / "README.md").read_text())
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        initial = section(APP, "const initialState", "let state;")
        normalize = section(APP, "function normalizeState", "function npoDefinition")
        threat = section(APP, "function setThreat", "function hud")
        visible = section(APP, "function narrateVisibleGradeMilestone", "function renderPlay")
        render = section(APP, "function renderPlay", "function activeEventEffectsHtml")
        self.assertIn("gradeMilestoneSequence:0", initial)
        self.assertIn("narrationSeen:tracked?raw.gradeMilestone.narrationSeen:true", normalize)
        self.assertIn("raw.gradeMilestone.instanceId.match(/^grade:\\d+:(\\d+)$/)", normalize)
        self.assertIn("Math.max(merged.gradeMilestoneSequence", normalize)
        self.assertIn("gradeMilestoneSequence=(state.gradeMilestoneSequence||0)+1", threat)
        self.assertIn("instanceId:`grade:${afterGrade}:${state.gradeMilestoneSequence}`", threat)
        self.assertIn("narrationSeen:false", threat)
        self.assertNotIn("playGradeEscalation", threat)
        self.assertIn("!$('.grade-milestone')", visible)
        self.assertLess(visible.index("milestone.narrationSeen=true"), visible.index("if(!save())return"))
        self.assertLess(visible.index("if(!save())return"), visible.index("playGradeEscalation"))
        self.assertIn("isPlaybackEnabled()", visible)
        self.assertLess(render.index("app.innerHTML="), render.index("requestAnimationFrame(narrateVisibleGradeMilestone)"))

    def test_dismiss_only_clears_visual_milestone(self):
        bind = section(APP, "function bindPlay", "function startTurningPoint")
        dismissal = "state.gradeMilestone=null;save();render();"
        self.assertIn(dismissal, bind)
        line = next(line for line in bind.splitlines() if dismissal in line)
        self.assertNotIn("TombWorldNarration", line)

    def test_runtime_mapping_queue_non_overlap_replay_pause_and_cleanup(self):
        script = r"""
const fs=require('fs'),vm=require('vm');const calls=[];let active=0;
class Audio{constructor(){this.src='';this.paused=true;this.ended=false;Audio.instance=this}play(){if(active)throw Error('overlap');active=1;this.paused=false;this.ended=false;calls.push(this.src);return Promise.resolve()}pause(){active=0;this.paused=true}load(){}removeAttribute(){this.src=''}end(){active=0;this.paused=true;this.ended=true;this.onended?.()}}
const entries={'event.e':{available:true,file:'events/e.mp3'},'grade.1.stirring':{available:true,file:'grades/1.mp3'},'grade.2.awakened':{available:true,file:'grades/2.mp3'},'grade.3.overrun':{available:true,file:'grades/3.mp3'}};
const c={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),localStorage:{getItem:()=>null,setItem(){}},dispatchEvent(){},CustomEvent:function(){}};c.window=c;vm.createContext(c);vm.runInContext(fs.readFileSync('narration.js','utf8'),c);const tick=()=>new Promise(r=>setTimeout(r,0));
(async()=>{const n=c.TombWorldNarration;if(await n.playGradeEscalation(0,'zero'))throw Error('grade zero played');
const event=n.playEvent('e','event-1');await tick();const grade=n.playGradeEscalation(2,'occurrence-1');await tick();if(calls.length!==1)throw Error('grade interrupted event');Audio.instance.end();await event;await tick();if(!calls.at(-1).endsWith('grades/2.mp3')||calls.length!==2)throw Error('queued grade missing');if(await n.playGradeEscalation(2,'occurrence-1'))throw Error('duplicate played');
n.setMasterEnabled(false);if(!Audio.instance.paused)throw Error('mute did not pause');n.setMasterEnabled(true);if(!await n.activateFromGesture())throw Error('unmute did not resume');if(!await n.replayLast())throw Error('replay failed');if(!calls.at(-1).endsWith('grades/2.mp3'))throw Error('grade not Replay Last');
const queued=n.playGradeEscalation(3,'stale');n.stop();if(await queued)throw Error('stale grade survived stop');
for(const [g,file] of [[1,'grades/1.mp3'],[3,'grades/3.mp3']]){const p=n.playGradeEscalation(g,'fresh-'+g);await tick();if(!calls.at(-1).endsWith(file))throw Error('mapping '+g);Audio.instance.end();await p;await tick()}
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_single_production_audio_and_existing_unlock_architecture(self):
        self.assertEqual(2, NARRATION.count("new global.Audio()"))
        self.assertIn("player = unlockAudio = new global.Audio()", NARRATION)
        self.assertNotIn("AudioContext", NARRATION)
        self.assertNotIn("webkitAudioContext", NARRATION)


if __name__ == "__main__":
    unittest.main()
