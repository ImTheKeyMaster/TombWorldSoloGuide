import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text()
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
NARRATION = (ROOT / "narration.js").read_text()
DISABLED_ICON = ROOT / "Assets/Icons/narration-icon-disabled.svg"


class NarrationPauseResumeTests(unittest.TestCase):
    def test_header_uses_wave_and_outline_speaker_x_icons(self):
        self.assertIn('id="narrationSpeakerBtn"', INDEX)
        self.assertRegex(INDEX, r'narration-icon-enabled[^>]*>.*M16 8\.5.*M19 6')
        disabled = ET.parse(DISABLED_ICON).getroot()
        paths = disabled.findall('{http://www.w3.org/2000/svg}path')
        self.assertEqual('0 0 24 24', disabled.attrib['viewBox'])
        self.assertEqual('M4 9v6h4l5 4V5L8 9H4z', paths[0].attrib['d'])
        self.assertEqual('none', paths[0].attrib['fill'])
        self.assertEqual('1.8', paths[0].attrib['stroke-width'])
        self.assertEqual(['M16 9 L21 15', 'M21 9 L16 15'], [path.attrib['d'] for path in paths[1:]])
        self.assertTrue(all(path.attrib['stroke-width'] == '2.4' for path in paths[1:]))
        self.assertNotRegex(' '.join(path.attrib['d'] for path in paths), r'M3 3|18 18|8\.5|M19 6')
        for path in paths:
            self.assertIn(f'd="{path.attrib["d"]}"', INDEX)
        self.assertNotIn('M3 3l18 18', INDEX)
        self.assertIn("stroke-width:2.4", CSS)
        self.assertIn("aria-pressed", INDEX)

    def test_removed_volume_and_duplicate_menu_controls_do_not_return(self):
        for source in (INDEX, APP, CSS, NARRATION):
            for obsolete in (
                "narrationPopover", "headerNarrationEnabled", "headerNarrationVolume",
                "headerNarrationVolumeValue", "narrationVolumeValue", "getVolume", "setVolume",
            ):
                self.assertNotIn(obsolete, source)
        self.assertNotIn('type="range"', INDEX)
        menu = APP[APP.index("function showGameMenu()"):APP.index("function showAbout()")]
        self.assertNotIn('<legend>Narration</legend>', menu)
        self.assertIn('Replay Last Narration', menu)

    def test_pause_resume_queue_persistence_and_destructive_stop(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const store=new Map([['tombWorldSoloGuide.narrationVolume','0']]);
const calls=[];
class Audio {
  constructor(){this.src='';this.currentTime=0;this.volume=.2;this.paused=true;this.ended=false;this.onended=null;this.onerror=null;Audio.instance=this;}
  pause(){calls.push('pause');this.paused=true;}
  removeAttribute(name){if(name==='src')this.src='';}
  load(){calls.push('load');this.currentTime=0;}
  play(){calls.push('play:'+this.src+':'+this.currentTime);this.paused=false;this.ended=false;return Promise.resolve();}
  end(){this.paused=true;this.ended=true;if(this.onended)this.onended();}
}
const entries={
  'event.first':{available:true,file:'events/first.mp3'},
  'event.second':{available:true,file:'events/second.mp3'},
  'event.ignored':{available:true,file:'events/ignored.mp3'}
};
const context={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries})}),
  localStorage:{getItem:key=>store.has(key)?store.get(key):null,setItem:(key,value)=>store.set(key,value)},
  dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
  const n=context.TombWorldNarration;
  await n.init();
  const first=n.playEvent('first','event-1');
  const second=n.playEvent('second','event-2');
  await flush();
  const player=Audio.instance;
  if(player.volume!==1)throw Error('legacy volume changed media volume');
  player.currentTime=12.5;
  const src=player.src;
  const loadCount=calls.filter(call=>call==='load').length;
  n.setEnabled(false);
  if(store.get('tombWorldSoloGuide.narrationEnabled')!=='false')throw Error('off preference missing');
  if(!player.paused)throw Error('active narration was not paused');
  if(player.src!==src)throw Error('pause removed the source');
  if(player.currentTime!==12.5)throw Error('pause reset playback position');
  if(!n.canReplay())throw Error('pause removed Replay Last state');
  if(calls.filter(call=>call==='load').length!==loadCount)throw Error('pause used destructive stop cleanup');
  if(await n.playEvent('ignored','event-off'))throw Error('disabled event was accepted');

  n.setEnabled(true);
  await flush();
  if(store.get('tombWorldSoloGuide.narrationEnabled')!=='true')throw Error('on preference missing');
  if(player.paused)throw Error('paused narration did not resume');
  if(!calls.includes('play:'+src+':12.5'))throw Error('narration restarted instead of resuming');
  player.end();
  await flush();
  if(!player.src.endsWith('events/second.mp3'))throw Error('existing queue did not survive pause');
  player.end();
  if(!await first||!await second)throw Error('queued narration result changed');
  if(calls.some(call=>call.includes('events/ignored.mp3')))throw Error('disabled event accumulated');

  void n.playEvent('ignored','event-stop');
  await flush();
  n.stop();
  if(player.src)throw Error('explicit stop did not remove source');
  if(player.currentTime!==0)throw Error('explicit stop did not reset playback');
  const playCount=calls.filter(call=>call.startsWith('play:')).length;
  n.setEnabled(false);
  n.setEnabled(true);
  await flush();
  if(calls.filter(call=>call.startsWith('play:')).length!==playCount)throw Error('enabling without a pause started playback');
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_toggle_races_do_not_lose_the_paused_session(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
let resolvePlay;
class Audio {
  constructor(){this.src='';this.currentTime=0;this.volume=1;this.paused=true;this.ended=false;Audio.instance=this;}
  pause(){this.paused=true;}
  removeAttribute(){this.src='';}
  load(){}
  play(){this.paused=false;return new Promise(resolve=>{resolvePlay=resolve;});}
}
const context={Audio,URL,location:{href:'https://example.test/'},fetch:async()=>({ok:true,json:async()=>({entries:{'mission.01.intro':{available:true,file:'intro.mp3'}}})}),
  localStorage:{value:null,getItem(){return this.value},setItem(key,value){this.value=value}},dispatchEvent:()=>{},CustomEvent:function(){}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
const flush=()=>new Promise(resolve=>setTimeout(resolve,0));
(async()=>{
  const n=context.TombWorldNarration;
  await n.init();
  const started=n.playMissionIntro('shifting-labyrinth');
  await flush();
  const player=Audio.instance;
  player.currentTime=7;
  n.setEnabled(false);
  if(!player.paused)throw Error('pending play was not paused');
  resolvePlay();
  if(!await started)throw Error('play request did not finish');
  n.setEnabled(true);
  n.setEnabled(false);
  resolvePlay();
  await flush();
  if(!player.paused)throw Error('stale resume overrode a later OFF toggle');
  n.setEnabled(true);
  if(player.paused)throw Error('later ON did not retain a resumable session');
  if(player.currentTime!==7)throw Error('race reset playback position');
  resolvePlay();
})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
