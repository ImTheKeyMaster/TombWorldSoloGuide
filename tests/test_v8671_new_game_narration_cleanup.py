import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def source(start, end):
    begin = APP.index(start)
    return APP[begin:APP.index(end, begin)]


class NewGameNarrationCleanupTests(unittest.TestCase):
    def test_every_actual_new_game_uses_centralized_cleanup(self):
        start_new_game = source("function startNewGameSetup(){", "function confirmNewGame")
        confirm_new_game = source("function confirmNewGame(){", "function exportSave")

        self.assertEqual(1, start_new_game.count("TombWorldNarration.stop();"))
        self.assertEqual(1, start_new_game.count("clearPendingBoardSetupMissionIntro();"))
        self.assertNotIn("TombWorldNarration.stop", confirm_new_game)
        self.assertIn("$('#newGameBtn').onclick=startNewGameSetup", APP)
        self.assertIn("$('#confirmNewGame').onclick=()=>{closeModal();startNewGameSetup();}", confirm_new_game)

    def test_opening_and_canceling_confirmation_do_not_stop_narration(self):
        confirm_new_game = source("function confirmNewGame(){", "function exportSave")
        script = f"""
let modalHtml='';
let started=0;
const confirmButton={{onclick:null}};
const showModal=(title,html)=>{{modalHtml=html;}};
const $=selector=>selector==='#confirmNewGame'?confirmButton:null;
const closeModal=()=>{{}};
const startNewGameSetup=()=>{{started++;}};
{confirm_new_game}
confirmNewGame();
if(started!==0)throw Error('opening confirmation started a new game');
if(!modalHtml.includes('data-close>Cancel'))throw Error('confirmation no longer provides non-destructive Cancel');
if(typeof confirmButton.onclick!=='function')throw Error('confirmation handler missing');
confirmButton.onclick();
if(started!==1)throw Error('confirmed transition did not start exactly once');
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_stop_destroys_playing_or_toggle_paused_audio_and_clears_queue(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const store=new Map();
const calls=[];
class Audio {
  constructor(){this.src='';this.currentTime=0;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){calls.push('pause');this.paused=true;}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){calls.push('load');this.currentTime=0;}
  play(){calls.push(`play:${this.src}:${this.currentTime}`);this.paused=false;return Promise.resolve();}
}
const entries={
  'event.first':{available:true,file:'events/first.mp3'},
  'event.second':{available:true,file:'events/second.mp3'}
};
const context={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
  localStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value)},
  dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
  const narration=context.TombWorldNarration;
  await narration.init();
  const first=narration.playEvent('first','old-event-1');
  const queued=narration.playEvent('second','old-event-2');
  await flush();
  const player=Audio.instance;
  player.currentTime=9.25;
      narration.setPreferenceEnabled(false);
      if(player.paused||!player.src||player.currentTime!==9.25)throw Error('preference toggle disturbed live playback');
  const playsBeforeStop=calls.filter(call=>call.startsWith('play:')).length;
  narration.stop();
  if(player.src||player.currentTime!==0)throw Error('stop did not destroy paused playback');
  if(!calls.includes('pause')||!calls.includes('load'))throw Error('stop cleanup was incomplete');
  if(await queued!==false)throw Error('queued Tomb Event narration was not cleared');
      narration.setPreferenceEnabled(true);
  await flush();
  if(calls.filter(call=>call.startsWith('play:')).length!==playsBeforeStop)throw Error('old narration resumed after New Game cleanup');
  if(store.get('tombWorldSoloGuide.narrationEnabled')!=='true')throw Error('stop changed the narration preference');
  await first;
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
