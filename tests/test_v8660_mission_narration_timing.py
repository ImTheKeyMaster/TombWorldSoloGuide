from versioning import CURRENT_APP_VERSION
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.js').read_text()
NARRATION = (ROOT / 'narration.js').read_text()
INDEX = (ROOT / 'index.html').read_text()
WORKER = (ROOT / 'service-worker.js').read_text()
README = (ROOT / 'README.md').read_text()


def source(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class MissionNarrationTimingTests(unittest.TestCase):
    def test_intro_moves_from_begin_game_to_explicit_mission_next(self):
        begin_game = source("$('#beginGame')", 'function runStartingNpoGeneration')
        setup_next = source('function advanceSetupStep', 'function bindSetup')
        self.assertNotIn('playMissionIntro', begin_game)
        self.assertIn("if(stepId==='mission')enterBoardSetup();", setup_next)
        self.assertIn('function playPendingBoardSetupMissionIntro()', APP)
        self.assertEqual(1, APP.count('playMissionIntro('))

    def test_render_and_killzone_controls_do_not_start_intro(self):
        self.assertNotIn('playMissionIntro', source('function render()', 'function renderHome'))
        killzone = source("if(stepId==='killzone')", "if(stepId==='team')")
        self.assertNotIn('playMissionIntro', killzone)
        check_handlers = source("$$('[data-check]')", "$('#randomPlayerTeam')")
        self.assertNotIn('playMissionIntro', check_handlers)

    def test_back_stops_current_audio_without_stopping_mission_selection(self):
        setup_back = source("$('#setupBack')", "$('#setupNext')")
        mission_choice = source("$$('.mission-choice')", "$('#setupHome')")
        self.assertIn("if(stepId==='killzone'){clearPendingBoardSetupMissionIntro();TombWorldNarration.stop();}", setup_back)
        self.assertNotIn('TombWorldNarration.stop()', mission_choice)

    def test_preference_values_preserve_enabled_semantics(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const store=new Map();
const context={localStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value)}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const n=context.TombWorldNarration;
if(!n.isEnabled())throw Error('missing preference was not enabled');
if(store.has('tombWorldSoloGuide.narrationEnabled'))throw Error('startup wrote a preference');
store.set('tombWorldSoloGuide.narrationEnabled','false');if(n.isEnabled())throw Error('false preference was enabled');
store.set('tombWorldSoloGuide.narrationEnabled','true');if(!n.isEnabled())throw Error('true preference was disabled');
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_board_setup_intro_pending_toggle_and_navigation_behavior(self):
        board_intro = source('async function setGameAudioEnabled', "narrationSpeakerBtn.addEventListener")
        speaker_toggle = source("narrationSpeakerBtn.addEventListener('click'", 'function handleNarrationChange')
        advance_setup = source('function advanceSetupStep', 'function bindSetup')
        setup_back = source("$('#setupBack')", "$('#setupNext')")
        script = f"""
const calls=[];
let setupNavigationInProgress=false;
const state={{screen:'setup',setupStep:0,missionId:'shifting-labyrinth'}};
let enabled=true;
let resumeNext=false;
let ambientEnabled=true;
const TombWorldNarration={{isEnabled:()=>enabled,setEnabled:async value=>{{enabled=value;return resumeNext;}},playMissionIntro:(id,restart)=>calls.push(`play:${{id}}:${{restart}}`),stop:()=>calls.push('stop')}};
const TombWorldAmbient={{unlock:async()=>true,setActive:value=>calls.push(`ambient:${{value}}`),stop:()=>calls.push('ambient:stop')}};
const syncNarrationControls=()=>{{}};
const shouldAmbientBeActive=()=>ambientEnabled&&enabled&&Boolean(state.missionId)&&['setup','game'].includes(state.screen);
const reconcileAmbientActiveState=()=>TombWorldAmbient.setActive(shouldAmbientBeActive());
const currentSetupStepId=()=>state.setupStep===0?'mission':'killzone';
const activeSetupSteps=()=>['mission','killzone'];
const canBuildPlayerRoster=()=>true,showToast=()=>{{}},assignPlayerDisplayNumbers=()=>{{}},save=()=>{{}};
const render=()=>calls.push('render:'+currentSetupStepId());
let speakerClick;
const narrationSpeakerBtn={{addEventListener:(event,handler)=>{{speakerClick=handler;}}}};
const $=()=>null;
let pendingBoardSetupMissionIntro=null;
{board_intro}
{speaker_toggle}
{advance_setup}
(async()=>{{
advanceSetupStep('mission');
if(calls.filter(call=>call.startsWith('play:')).length!==1)throw Error('enabled entry did not play once');
render();
if(calls.filter(call=>call.startsWith('play:')).length!==1)throw Error('rerender replayed completed intro');

state.setupStep=0;enabled=false;advanceSetupStep('mission');
if(calls.filter(call=>call.startsWith('play:')).length!==1||pendingBoardSetupMissionIntro!=='shifting-labyrinth')throw Error('disabled entry was not pending');
resumeNext=false;await speakerClick();
if(calls.filter(call=>call.startsWith('play:')).length!==2||pendingBoardSetupMissionIntro!==null)throw Error('pending intro did not start exactly once');

state.setupStep=0;enabled=false;advanceSetupStep('mission');
resumeNext=true;await speakerClick();
if(calls.filter(call=>call.startsWith('play:')).length!==2||pendingBoardSetupMissionIntro!=='shifting-labyrinth')throw Error('pending intro preempted resumed narration');
enabled=false;resumeNext=false;await speakerClick();
if(calls.filter(call=>call.startsWith('play:')).length!==3||pendingBoardSetupMissionIntro!==null)throw Error('pending intro did not start after no narration resumed');

state.setupStep=0;enabled=false;advanceSetupStep('mission');
if(!pendingBoardSetupMissionIntro)throw Error('new disabled visit was not pending');
const stepId='killzone';
const setupBack={{addEventListener:(event,handler)=>handler()}};
eval(`const $=selector=>selector==='#setupBack'?setupBack:null;{setup_back}`);
if(pendingBoardSetupMissionIntro!==null||!calls.includes('stop')||state.setupStep!==0)throw Error('Back did not clear and stop Board Setup narration');
resumeNext=false;await speakerClick();
if(calls.filter(call=>call.startsWith('play:')).length!==3)throw Error('stale pending intro played after Back');
}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_restart_allows_same_intro_after_back(self):
        self.assertIn('function playMissionIntro(missionId, restart = false)', NARRATION)
        self.assertIn("if (restart) automaticPlayback.delete(`mission:${missionId}`);", NARRATION)

    def test_event_and_outcome_hooks_are_unchanged(self):
        self.assertIn('TombWorldNarration.playEvent(event.definitionId,event.instanceId)', APP)
        self.assertIn('TombWorldNarration.playOutcome(state.missionId,outcome)', APP)

    def test_menu_uses_unified_audio_toggle_without_duplicate_preference_controls(self):
        menu = source('function showGameMenu()', 'function showAbout()')
        self.assertNotIn('Dungeon Master Narration', menu)
        self.assertIn('gameAudioToggle', menu)
        self.assertIn('Stop Game Audio', menu)
        self.assertNotIn('narrationEnabled', menu)
        self.assertNotIn('narrationVolume', menu)

    def test_release_and_save_versions(self):
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", APP)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f'<div class="version">V{CURRENT_APP_VERSION}</div>', INDEX)
        self.assertTrue(README.startswith(f'# Tomb World Solo Guide v{CURRENT_APP_VERSION}'))
        self.assertIn('const SAVE_VERSION = 3;', (ROOT / 'persistence.js').read_text())
        for asset in ('styles.css', 'mission-engine.js', 'persistence.js', 'deadly-encounters.js', 'event-effects.js', 'narration.js', 'app.js'):
            self.assertIn(f'{asset}?v={CURRENT_APP_VERSION}', INDEX)

    def test_available_mp3s_are_discovered_from_the_manifest(self):
        self.assertIn("Object.values(manifest.entries||{})", WORKER)
        self.assertIn("entry?.available===true", WORKER)
        self.assertIn("`./Assets/Audio/Narration/${entry.file}`", WORKER)

    def test_restart_runtime_stops_and_replays_from_start(self):
        script = r"""
const fs=require('fs'),vm=require('vm');const calls=[];
class Audio {constructor(){this.src='';this.volume=.8;}pause(){calls.push('pause');}removeAttribute(){this.src='';}load(){}play(){calls.push('play:'+this.src);return Promise.resolve();}}
const entries={'mission.01.intro':{available:true,file:'missions/01.mp3'}};
const context={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;await n.init();if(!await n.playMissionIntro('shifting-labyrinth',true))throw Error('first intro failed');n.stop();if(!await n.playMissionIntro('shifting-labyrinth',true))throw Error('restart failed');if(calls.filter(x=>x.startsWith('play:')).length!==2)throw Error('intro did not replay');})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
