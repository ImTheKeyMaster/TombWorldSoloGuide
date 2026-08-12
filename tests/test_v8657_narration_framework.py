import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
NARRATION = (ROOT / "narration.js").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


class NarrationIntegrationTests(unittest.TestCase):
    def test_release_version_changes_without_save_schema_change(self):
        self.assertIn("const APP_VERSION = '8.6.63';", APP)
        self.assertIn("const APP_VERSION = '8.6.63';", WORKER)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())
        self.assertIn('narration.js?v=8.6.63', INDEX)

    def test_intro_only_runs_from_mission_to_killzone_transition(self):
        begin = source("$('#beginGame')", "function runStartingNpoGeneration")
        transition = source("$('#setupNext')", "$$('[data-player-team]')")
        self.assertNotIn('playMissionIntro', begin)
        self.assertIn("if(stepId==='mission')void TombWorldNarration.playMissionIntro(state.missionId,true);", transition)
        self.assertEqual(APP.count('playMissionIntro('), 1)
        self.assertNotIn('playMissionIntro', source('function render()', 'function renderHome'))

    def test_accepted_events_use_definition_and_instance_identity(self):
        begin = source('function narrateAcceptedEvent', 'function redrawCurrentEvent')
        self.assertIn('TombWorldNarration.playEvent(event.definitionId,event.instanceId)', begin)
        self.assertRegex(begin, r"if\(wounded\.length>1\).*narrateAcceptedEvent\(event\).*return;")
        redraw = source('function redrawCurrentEvent', 'function resolveStrategyEvent')
        self.assertNotIn('TombWorldNarration', redraw)
        self.assertIn("{instanceId:'awakened-warrior-1',definitionId:'awakened-warrior'}", APP)
        self.assertIn("{instanceId:'awakened-warrior-2',definitionId:'awakened-warrior'}", APP)

    def test_outcome_runs_after_successful_battle_end_hook(self):
        finalization = source('async function finalizeMissionCompletion', 'function completeMission')
        self.assertGreater(finalization.index('playOutcome'), finalization.index('battleEndHookComplete=true'))
        failure = finalization[finalization.index('if(hookResult===null)'):finalization.index('battleEndHookComplete=true')]
        self.assertNotIn('playOutcome', failure)
        self.assertIn('TombWorldNarration.playOutcome(state.missionId,outcome)', finalization)

    def test_preferences_are_not_game_save_fields(self):
        persistence = (ROOT / 'persistence.js').read_text()
        self.assertNotIn('narrationEnabled', persistence)
        self.assertNotIn('narrationVolume', persistence)
        self.assertIn('tombWorldSoloGuide.narrationEnabled', NARRATION)
        self.assertIn('tombWorldSoloGuide.narrationVolume', NARRATION)


class NarrationManifestTests(unittest.TestCase):
    def test_manifest_availability_matches_generated_source_status(self):
        manifest = json.loads((ROOT / 'Assets/Audio/Narration/narration-manifest.json').read_text())
        entries = manifest['entries']
        self.assertEqual(len(entries), 29)
        self.assertEqual(len(set(entries)), 29)
        self.assertEqual(sum(key.startswith('mission.') for key in entries), 6)
        self.assertEqual(sum(key.startswith('event.') for key in entries), 11)
        self.assertEqual(sum(key.startswith('outcome.') for key in entries), 12)
        records = {}
        for name in ('missions.json', 'events.json', 'outcomes.json'):
            records.update((item['id'], item) for item in json.loads((ROOT / 'Narration/scripts' / name).read_text())['scripts'])
        self.assertEqual(set(records), set(entries))
        for script_id, entry in entries.items():
            generated = records[script_id]['status'] == 'generated'
            self.assertEqual(generated, entry['available'], script_id)
            self.assertEqual(records[script_id]['outputFile'] if generated else None, entry['file'], script_id)

    def test_both_awakened_warriors_share_one_manifest_entry(self):
        entries = json.loads((ROOT / 'Assets/Audio/Narration/narration-manifest.json').read_text())['entries']
        self.assertIn('event.awakened-warrior', entries)
        self.assertEqual(sum(key == 'event.awakened-warrior' for key in entries), 1)

    def test_production_scripts_preserve_entry_count_draft_and_approved_copy(self):
        records = []
        for name in ('missions.json', 'events.json', 'outcomes.json'):
            records.extend(json.loads((ROOT / 'Narration/scripts' / name).read_text())['scripts'])
        self.assertEqual(len(records), 29)
        self.assertEqual(['mission.04.intro'], [item['id'] for item in records if item['status'] == 'draft'])
        draft = next(item for item in records if item['id'] == 'mission.04.intro')
        self.assertFalse(any(draft.get(key) for key in ('settingsHash', 'generationHash', 'audioHash', 'voiceId', 'modelId')))
        reanimation = next(item for item in records if item['id'] == 'event.reanimation-protocols')
        self.assertEqual(reanimation['script'], "The fallen begin to move.\n\nEmerald light returns to darkened eyes. Bodies that should lie silent rise again, driven by ancient systems that refuse to accept their destruction.\n\nFor a time, death may not be enough to stop the tomb’s defenders.")


class NarrationManagerRuntimeTests(unittest.TestCase):
    def run_node(self, assertions):
        script = f"""
const fs=require('fs'),vm=require('vm');
const store=new Map(), calls=[];
class Audio {{ constructor(){{this.src='';this.volume=0;}} pause(){{calls.push('pause')}} removeAttribute(){{this.src=''}} load(){{}} play(){{calls.push('play:'+this.src);return this.fail?Promise.reject(new Error('missing')):Promise.resolve();}} }}
const entries={{
  'mission.01.intro':{{available:true,file:'missions/01.mp3'}},
  'event.awakened-warrior':{{available:true,file:'events/awakened.mp3'}}
}};
const context={{Audio,URL,location:{{href:'https://example.test/app/'}},fetch:async()=>({{ok:true,json:async()=>({{entries}})}}),localStorage:{{getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(k,v)}},dispatchEvent:()=>{{}},CustomEvent:function(){{}}}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{{const n=context.TombWorldNarration;await n.init();{assertions}}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_disabled_volume_overlap_deduplication_and_replay(self):
        self.run_node("""
n.setEnabled(false);if(await n.playMissionIntro('shifting-labyrinth'))throw Error('disabled played');
n.setEnabled(true);n.setVolume(.35);if(n.getVolume()!==.35)throw Error('volume did not persist');
if(!await n.playEvent('awakened-warrior','copy-1'))throw Error('first play failed');
if(await n.playEvent('awakened-warrior','copy-1'))throw Error('duplicate played');
if(!await n.replayLast())throw Error('replay failed');
if(calls.filter(x=>x.startsWith('play:')).length!==2)throw Error('unexpected play count');
if(calls.filter(x=>x==='pause').length<2)throw Error('new playback did not stop prior audio');
""")

    def test_missing_manifest_entry_fails_silently(self):
        self.run_node("""if(await n.playEvent('not-generated','copy-2'))throw Error('missing entry played');""")

    def test_blocked_preference_storage_fails_silently(self):
        script = """
const fs=require('fs'),vm=require('vm');
const context={Audio:function(){throw Error('audio blocked')},fetch:async()=>{throw Error('offline')},localStorage:{getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{const n=context.TombWorldNarration;n.setEnabled(false);n.setVolume(.5);await n.init();await n.playMissionIntro('shifting-labyrinth');n.stop();})().catch(error=>{console.error(error);process.exit(1)});
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
