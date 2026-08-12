import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NarrationMobileOfflineTests(unittest.TestCase):
    def test_all_available_narration_assets_are_precached(self):
        manifest = json.loads((ROOT / 'Assets/Audio/Narration/narration-manifest.json').read_text())['entries']
        worker = (ROOT / 'service-worker.js').read_text()
        available = [entry['file'] for entry in manifest.values() if entry.get('available')]
        self.assertEqual(5, len(available))
        for relative in available:
            self.assertIn(f"'./Assets/Audio/Narration/{relative}'", worker)

    def test_player_unlocks_on_explicit_click_before_async_outcome(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={};
const calls=[];
class Audio {
  constructor(){this.src='';this.volume=.8;}
  pause(){calls.push('pause');}
  removeAttribute(){this.src='';}
  load(){}
  play(){calls.push('play:'+this.src);return Promise.resolve();}
}
const entries={'outcome.04.victory':{available:true,file:'outcomes/04-victory.mp3'}};
const document={
  addEventListener(type,handler){listeners[type]=handler;},
  removeEventListener(type,handler){if(listeners[type]===handler)delete listeners[type];}
};
const context={Audio,URL,document,location:{href:'https://example.test/app/'},fetch:async()=>({ok:true,json:async()=>({entries})}),localStorage:{getItem:()=>null,setItem:()=>{}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{
  if(typeof listeners.click!=='function')throw Error('click unlock listener missing');
  await listeners.click();
  await new Promise(resolve=>setTimeout(resolve,0));
  if(!calls.some(x=>x.startsWith('play:data:audio/wav')))throw Error('gesture did not unlock audio');
  await context.TombWorldNarration.init();
  if(!await context.TombWorldNarration.playOutcome('destroy-sarcophagus','victory'))throw Error('outcome playback failed after unlock');
  if(!calls.some(x=>x.includes('outcomes/04-victory.mp3')))throw Error('outcome audio was not played');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
