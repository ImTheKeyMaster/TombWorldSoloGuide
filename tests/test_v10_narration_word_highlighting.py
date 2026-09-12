import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")
TRANSCRIPT = (ROOT / "narration-transcript.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")


class NarrationWordHighlightingTests(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_release_and_stage_3_contracts_are_unchanged(self):
        self.assertIn(">V9.2.63<", INDEX)
        self.assertIn("const APP_VERSION = '9.2.63';", APP)
        self.assertIn("Skip This Narration", INDEX)
        self.assertIn("Stop All Narration", INDEX)
        self.assertIn("const SAVE_VERSION = 3;", PERSISTENCE)
        self.assertIn("const STORAGE_KEY = 'tombWorldBattleGuide.v1';", APP)
        self.assertIn("narration.pauseNarration()", TRANSCRIPT)
        self.assertIn("await narration.resumeNarration()", TRANSCRIPT)
        self.assertIn("narration.skipCurrent()", TRANSCRIPT)
        self.assertIn("narration.stop()", TRANSCRIPT)

    def test_mapping_preserves_authoritative_text_and_fails_atomically(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');
const context={};context.window=context;vm.createContext(context);
vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);
const api=context.TombWorldNarrationTranscript;
function element(){return {textContent:'',dataset:{},classes:[],classList:{add(...names){this.owner.classes.push(...names)}}}}
const document={createTextNode:text=>({textContent:text}),createElement:()=>{const value=element();value.classList.owner=value;return value}};
const transcript="Don't wake the long-sealed tomb.\n\nIt's waiting!";
const words=[
 {text:"Don't",startMs:100,endMs:300},{text:'wake',startMs:310,endMs:500},
 {text:'the',startMs:510,endMs:600},{text:'long',startMs:610,endMs:700},
 {text:'sealed',startMs:710,endMs:900},{text:'tomb.',startMs:910,endMs:1100},
 {text:"It's",startMs:1300,endMs:1450},{text:'waiting!',startMs:1460,endMs:1800}
];
const mapped=api.mapTranscriptWords(document,transcript,words);
if(!mapped)throw Error('valid mapping rejected');
if(mapped.nodes.map(node=>node.textContent).join('')!==transcript)throw Error('authoritative punctuation or paragraphs changed');
if(mapped.words.length!==words.length)throw Error('word spans missing');
if(mapped.words.some((word,index)=>word.element.dataset.wordIndex!==String(index)))throw Error('alignment indices missing');
if(api.mapTranscriptWords(document,'Alpha omitted Omega',[{text:'Alpha',startMs:0,endMs:1},{text:'Omega',startMs:2,endMs:3}])!==null)throw Error('partial mapping did not fail');
if(api.mapTranscriptWords(document,transcript,null)!==null)throw Error('missing alignment did not use fallback');
""")
        self.assertIn("document.createTextNode", TRANSCRIPT)
        self.assertIn("document.createElement('span')", TRANSCRIPT)
        self.assertIn("body.replaceChildren(...mapping.nodes)", TRANSCRIPT)
        self.assertNotIn("innerHTML", TRANSCRIPT)

    def test_timestamp_boundaries_gaps_and_final_state(self):
        self.run_node(r"""
const fs=require('fs'),vm=require('vm');const context={};context.window=context;vm.createContext(context);
vm.runInContext(fs.readFileSync('narration-transcript.js','utf8'),context);
const f=context.TombWorldNarrationTranscript.wordPositionAt;
const words=[{startMs:1000,endMs:1500},{startMs:1700,endMs:2000}];
const checks=[[999,-1,-1],[1000,0,-1],[1499,0,-1],[1500,-1,0],[1699,-1,0],[1700,1,0],[2000,-1,1]];
for(const [time,current,spoken] of checks){const got=f(words,time);if(got.current!==current||got.spokenThrough!==spoken)throw Error(`${time}: ${JSON.stringify(got)}`)}
""")
        self.assertIn("state.currentTimeMs", TRANSCRIPT)
        self.assertNotIn("setInterval", TRANSCRIPT)

    def test_single_loop_incremental_updates_and_hidden_catch_up(self):
        self.assertEqual(2, TRANSCRIPT.count("global.requestAnimationFrame(progressLoop)"))
        loop = TRANSCRIPT.split("function progressLoop()", 1)[1].split("function startProgressLoop()", 1)[0]
        self.assertIn("updateProgress(state)", loop)
        self.assertIn("updateWordHighlighting(state)", loop)
        self.assertNotIn("replaceChildren", loop)
        self.assertIn("if (!mappedTranscript || !dialogOpen()) return", TRANSCRIPT)
        self.assertIn("updateWordHighlighting(state, true)", TRANSCRIPT)
        self.assertIn("if (animationFrame === null && dialogOpen())", TRANSCRIPT)
        self.assertIn("currentTimeMs < previousCurrentTimeMs", TRANSCRIPT)
        self.assertIn("currentWordIndex !== position.current", TRANSCRIPT)

    def test_auto_follow_manual_override_and_reduced_motion(self):
        self.assertIn("viewport.height * 0.25", TRANSCRIPT)
        self.assertIn("viewport.height * 0.75", TRANSCRIPT)
        self.assertIn("const AUTO_FOLLOW_SUSPEND_MS = 4000", TRANSCRIPT)
        for event in ("wheel", "touchstart", "touchmove", "pointerdown", "scroll"):
            self.assertIn(f"body.addEventListener('{event}'", TRANSCRIPT)
        self.assertIn("programmaticScrollUntil", TRANSCRIPT)
        self.assertIn("prefers-reduced-motion: reduce", TRANSCRIPT)
        self.assertIn("? 'auto' : 'smooth'", TRANSCRIPT)

    def test_visual_and_accessibility_contract(self):
        for state in ("spoken", "current", "upcoming"):
            self.assertIn(f".narration-transcript-word--{state}", STYLES)
        self.assertIn("text-shadow", STYLES)
        self.assertIn("font-weight:inherit", STYLES)
        narration_dialog = INDEX.split('id="narrationTranscriptDialog"', 1)[1].split("</dialog>", 1)[0]
        self.assertNotIn("aria-live", narration_dialog)
        self.assertNotIn("tabIndex", TRANSCRIPT)
        self.assertNotIn("tabindex", TRANSCRIPT.lower())
        self.assertNotIn("role=", TRANSCRIPT)
        self.assertNotIn("playbackRate", TRANSCRIPT)
        self.assertNotIn("currentTime =", TRANSCRIPT)
        progress = INDEX.split('id="narrationTranscriptProgress"', 1)[1].split("</div>", 1)[0]
        self.assertNotIn("button", progress)
        self.assertNotIn("input", progress)


if __name__ == "__main__":
    unittest.main()
