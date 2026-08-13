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
        setup_next = source("$('#setupNext')", "$$('[data-player-team]')")
        self.assertNotIn('playMissionIntro', begin_game)
        self.assertIn("if(stepId==='mission')void TombWorldNarration.playMissionIntro(state.missionId,true);", setup_next)
        self.assertEqual(1, APP.count('playMissionIntro('))

    def test_render_and_killzone_controls_do_not_start_intro(self):
        self.assertNotIn('playMissionIntro', source('function render()', 'function renderHome'))
        killzone = source("if(stepId==='killzone')", "if(stepId==='team')")
        self.assertNotIn('playMissionIntro', killzone)
        check_handlers = source("$$('[data-check]')", "$('#randomPlayerTeam')")
        self.assertNotIn('playMissionIntro', check_handlers)

    def test_back_and_mission_change_stop_current_audio(self):
        setup_back = source("$('#setupBack')", "$('#setupNext')")
        mission_choice = source("$$('.mission-choice')", "$('#setupHome')")
        self.assertIn("if(stepId==='killzone')TombWorldNarration.stop()", setup_back)
        self.assertIn('TombWorldNarration.stop()', mission_choice)

    def test_restart_allows_same_intro_after_back(self):
        self.assertIn('function playMissionIntro(missionId, restart = false)', NARRATION)
        self.assertIn("if (restart) automaticPlayback.delete(`mission:${missionId}`);", NARRATION)

    def test_event_and_outcome_hooks_are_unchanged(self):
        self.assertIn('TombWorldNarration.playEvent(event.definitionId,event.instanceId)', APP)
        self.assertIn('TombWorldNarration.playOutcome(state.missionId,outcome)', APP)

    def test_menu_keeps_replay_and_removes_duplicate_preference_controls(self):
        menu = source('function showGameMenu()', 'function showAbout()')
        self.assertNotIn('Dungeon Master Narration', menu)
        self.assertIn('replayNarration', menu)
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
