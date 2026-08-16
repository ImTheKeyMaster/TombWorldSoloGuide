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
        for relative in available:
            self.assertNotIn(f"'./Assets/Audio/Narration/{relative}'", worker)
        self.assertIn("Object.values(manifest.entries||{})", worker)
        self.assertIn("entry?.available===true", worker)

        script = r"""
const fs=require('fs'),vm=require('vm');
const manifest=JSON.parse(fs.readFileSync('Assets/Audio/Narration/narration-manifest.json','utf8'));
manifest.entries['test.future-entry']={available:true,file:'events/future-entry.mp3'};
manifest.entries['test.unavailable-entry']={available:false,file:'events/must-not-cache.mp3'};
manifest.entries['test.duplicate-entry']={available:true,file:'events/future-entry.mp3'};
const batches=[];
const cache={
  addAll:async files=>batches.push([...files]),
  match:async path=>path.includes('narration-manifest')?{json:async()=>manifest}:{json:async()=>({landscape:[]})}
};
const context={
  URL,Response,console,
  caches:{open:async()=>cache,keys:async()=>[]},
  self:{location:{origin:'https://example.test'},clients:{claim:async()=>{}},addEventListener:()=>{},skipWaiting:()=>{}}
};
vm.createContext(context);vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
(async()=>{
  await context.precacheNarration(cache);
  const files=batches.flat();
  for(const entry of Object.values(manifest.entries).filter(x=>x.available&&x.file)){
    const expected='./Assets/Audio/Narration/'+entry.file;
    if(!files.includes(expected))throw Error('missing '+expected);
  }
  if(files.includes('./Assets/Audio/Narration/events/must-not-cache.mp3'))throw Error('unavailable entry cached');
  if(files.filter(x=>x.endsWith('/events/future-entry.mp3')).length!==1)throw Error('dynamic entry was not deduplicated');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_bad_narration_manifest_does_not_reject_install_helper(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const context={URL,Response,console:{warn:()=>{}},caches:{},self:{location:{origin:'https://example.test'},addEventListener:()=>{}}};
vm.createContext(context);vm.runInContext(fs.readFileSync('service-worker.js','utf8'),context);
context.precacheNarration({match:async()=>({json:async()=>{throw Error('bad manifest')}}),addAll:async()=>{throw Error('should not run')}})
  .catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

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
  if(listeners.click)throw Error('global click unlock listener was installed');
  await context.TombWorldNarration.unlock();
  await new Promise(resolve=>setTimeout(resolve,0));
  if(!calls.some(x=>x.startsWith('play:data:audio/wav')))throw Error('explicit gesture did not unlock audio');
  await context.TombWorldNarration.init();
  if(!await context.TombWorldNarration.playOutcome('destroy-sarcophagus','victory'))throw Error('outcome playback failed after unlock');
  if(!calls.some(x=>x.includes('outcomes/04-victory.mp3')))throw Error('outcome audio was not played');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
