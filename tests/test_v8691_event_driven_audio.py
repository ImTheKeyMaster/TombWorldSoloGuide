import subprocess
import unittest
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
AMBIENT = (ROOT / "ambient.js").read_text(encoding="utf-8")


class EventDrivenAudioLifecycleTests(unittest.TestCase):
    def test_release_assets_and_preserved_audio_contracts(self):
        self.assertEqual((8, 6, 91), tuple(map(int, CURRENT_APP_VERSION.split("."))))
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "narration.js", "ambient.js", "app.js"):
            self.assertIn(f"{asset}?v={CURRENT_APP_VERSION}", index)
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", worker)
        self.assertIn('"file": "Ambient/caverns.ogg"', (ROOT / "Assets/Audio/Narration/ambient-config.json").read_text())
        self.assertIn("await cache.add(`./Assets/Audio/Narration/${file}`)", worker)
        self.assertIn("duckGain", AMBIENT)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())

    def test_audio_work_is_limited_to_coordinator_activation_points(self):
        render = APP[APP.index("function render(){"):APP.index("function guideInstructionsHtml")]
        menu = APP[APP.index("function showGameMenu(){"):APP.index("function showAbout()")]
        self.assertNotRegex(render, r"Audio|Narration|Ambient|reconcile")
        self.assertNotRegex(menu[:menu.index("$('#narrationToggle').onclick")], r"unlock|setActive|reconcile|\.stop\(")
        self.assertNotIn("addEventListener('click'", NARRATION)
        self.assertNotIn("addEventListener('click'", AMBIENT)
        self.assertEqual(1, APP.count("document.addEventListener('click',audioRecoveryHandler,true)"))
        self.assertIn("void applySelectedAudioFromGesture()", APP[APP.index("$$('.mission-choice')"):APP.index("$('#setupHome')")])

    def test_game_menu_cannot_disturb_any_production_narration(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={},players=[];let pauses=0,loads=0,plays=0;
class CustomEvent{constructor(type,o={}){this.type=type;this.detail=o.detail;}}
class Audio{constructor(){players.push(this);this.src='';this.currentTime=4;this.paused=true;this.ended=false;}play(){plays++;this.paused=false;return Promise.resolve();}pause(){pauses++;this.paused=true;}removeAttribute(n){if(n==='src')this.src='';}load(){loads++;}}
const manifest={entries:{
 'mission.01.intro':{available:true,file:'mission.mp3'},'event.alpha':{available:true,file:'event.mp3'},
 'outcome.01.victory':{available:true,file:'outcome.mp3'},'deadly.alpha':{available:true,file:'deadly.mp3',category:'deadly-encounter',deadlyEncounterFeatureId:'alpha'}
}};
const document={addEventListener:(t,h)=>listeners[t]=h,removeEventListener:(t,h)=>{if(listeners[t]===h)delete listeners[t];},dispatchEvent:e=>listeners[e.type]?.(e)};
const context={Audio,CustomEvent,URL,document,location:{href:'https://example.test/'},localStorage:{getItem:()=>null,setItem(){}},fetch:async()=>({ok:true,json:async()=>manifest}),dispatchEvent(){}};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;await n.init();
 const cases=[()=>n.playMissionIntro('shifting-labyrinth',true),()=>n.playEvent('alpha','event-1'),()=>n.playOutcome('shifting-labyrinth','victory'),()=>n.playDeadlyEncounter(['alpha'],'deadly-1')];
 for(const start of cases){n.stop(true);const pending=start();for(let i=0;i<8;i++)await Promise.resolve();const beforePause=pauses,beforeLoad=loads,player=players[0],src=player.src,time=player.currentTime;
  document.dispatchEvent({type:'click',target:{closest:()=>false}});player.currentTime+=1;
  if(player!==players[0]||player.src!==src||player.currentTime<=time||pauses!==beforePause||loads!==beforeLoad)throw Error('menu gesture disturbed narration');
  player.onended?.();await pending;
 }
 await n.playMissionIntro('shifting-labyrinth',true);const beforePause=pauses,beforeLoad=loads,src=players[0].src;
 await n.replayLast();document.dispatchEvent({type:'click',target:{closest:()=>false}});
 if(players[0].src!==src||pauses!==beforePause+1||loads!==beforeLoad+1)throw Error('replay was disturbed by menu click');
 if(listeners.click)throw Error('ordinary clicks have narration recovery work');
})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_real_playback_proves_unlock_and_silent_prime_is_separate(self):
        self.assertIn("let unlockAudio = null;", NARRATION)
        self.assertNotIn("audio.src = SILENT_UNLOCK_AUDIO", NARRATION)
        script = r"""
const fs=require('fs'),vm=require('vm');const players=[];let plays=0;
class Audio{constructor(){players.push(this);this.src='';this.paused=true;this.ended=false;}play(){plays++;return Promise.resolve();}pause(){}removeAttribute(){}load(){}}
const c={Audio,URL,document:{addEventListener(){},removeEventListener(){}},location:{href:'https://x/'},localStorage:{getItem:()=>null,setItem(){}},dispatchEvent(){},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'real.mp3'}}})})};c.window=c;vm.createContext(c);vm.runInContext(fs.readFileSync('narration.js','utf8'),c);
(async()=>{await c.TombWorldNarration.playMissionIntro('shifting-labyrinth');await c.TombWorldNarration.unlock({force:true});if(players.length!==1||plays!==1||players[0].src.includes('data:audio'))throw Error('successful real playback was silently primed');})().catch(e=>{console.error(e);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
