import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NarrationUnlockRegressionTests(unittest.TestCase):
    def test_new_game_preserves_gesture_unlock_and_still_plays_board_intro(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const calls=[];
let resolveUnlock;
class Audio {
  constructor(){this.src='';this.currentTime=0;this.paused=true;this.ended=false;Audio.instance=this;}
  pause(){calls.push('pause');this.paused=true;}
  removeAttribute(name){calls.push('remove:'+name);if(name==='src')this.src='';}
  load(){calls.push('load');this.currentTime=0;}
  play(){
    calls.push('play:'+this.src);
    this.paused=false;
    if(this.src.startsWith('data:audio/wav'))return new Promise(resolve=>{resolveUnlock=resolve;});
    return Promise.resolve();
  }
}
let captureClick;
const document={
  addEventListener:(type,handler,capture)=>{if(type==='click'&&capture===true)captureClick=handler;},
  removeEventListener:()=>{}
};
const entries={'mission.01.intro':{available:true,file:'missions/01-intro.mp3'}};
const context={Audio,document,URL,location:{href:'https://example.test/'},
  fetch:async()=>({ok:true,json:async()=>({entries})}),
  localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{
  const narration=context.TombWorldNarration;
  await narration.init();
  if(typeof captureClick!=='function')throw Error('capture-phase unlock listener missing');

  // The first New Game click reaches the capture listener before startNewGameSetup calls stop().
  captureClick();
  const player=Audio.instance;
  if(!player.src.startsWith('data:audio/wav'))throw Error('first gesture did not begin silent unlock');
  narration.stop();
  if(!player.src.startsWith('data:audio/wav'))throw Error('New Game destroyed silent unlock source');
  if(calls.includes('pause')||calls.includes('load')||calls.includes('remove:src'))throw Error('silent unlock was destructively reset');
  resolveUnlock();
  await Promise.resolve();

  // Mission Selection -> Next -> Board Setup requests the Mission Intro.
  if(!await narration.playMissionIntro('shifting-labyrinth',true))throw Error('Board Setup Mission Intro failed');
  const introPlays=calls.filter(call=>call.includes('missions/01-intro.mp3'));
  if(introPlays.length!==1)throw Error('Mission Intro did not play exactly once');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_new_game_destroys_real_playing_and_paused_audio_but_allows_new_intro(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
async function scenario(paused){
  const calls=[];
  const store=new Map();
  class Audio {
    constructor(){this.src='';this.currentTime=0;this.paused=true;this.ended=false;Audio.instance=this;}
    pause(){calls.push('pause');this.paused=true;}
    removeAttribute(name){if(name==='src')this.src='';}
    load(){calls.push('load');this.currentTime=0;}
    play(){calls.push('play:'+this.src+':'+this.currentTime);this.paused=false;this.ended=false;return Promise.resolve();}
  }
  const entries={
    'event.old':{available:true,file:'events/old.mp3'},
    'mission.01.intro':{available:true,file:'missions/01-intro.mp3'}
  };
  const context={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
    localStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value)},
    dispatchEvent:()=>{},CustomEvent:function(){}};
  context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
  const narration=context.TombWorldNarration;
  await narration.init();
  void narration.playEvent('old','old-instance');
  await new Promise(resolve=>setTimeout(resolve,0));
  const player=Audio.instance;
  player.currentTime=8;
  if(paused)await narration.setEnabled(false);
  narration.stop();
  if(player.src||player.currentTime!==0)throw Error('old real narration was not destroyed');
  const oldPlayCount=calls.filter(call=>call.includes('events/old.mp3')).length;
  if(paused){
    await narration.setEnabled(true);
    if(calls.filter(call=>call.includes('events/old.mp3')).length!==oldPlayCount)throw Error('old paused narration resumed');
  }
  if(!await narration.playMissionIntro('shifting-labyrinth',true))throw Error('new game narration was unusable');
  if(calls.filter(call=>call.includes('missions/01-intro.mp3')).length!==1)throw Error('new Mission Intro count changed');
}
(async()=>{await scenario(false);await scenario(true);})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
