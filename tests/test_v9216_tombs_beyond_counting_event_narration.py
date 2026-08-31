import hashlib
import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
NARRATION = (ROOT / "narration.js").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
EXPANSION_EVENTS = {
    "flesh-hunger": "flayer-curse",
    "rewards-of-annihilation": "destroyer-cult",
    "enforcer-of-the-phaerons": "crownworld",
}
EXPANSION_AUDIO = {
    "flesh-hunger": (345696, 21577, "15c0154438931de42d5b4dbf48828132d0168e221112ffe99039cfe3c3f85d4b"),
    "rewards-of-annihilation": (349457, 21812, "14b536f59c010d71e3affb35b27f652c0bba814f1db6fc6030a643cea056cc2e"),
    "enforcer-of-the-phaerons": (321872, 20088, "a03981aeed019413b90807997d522ac0e2ddcdfaa764cfb5eaeed4b027e322c4"),
}


def event_scripts():
    data = json.loads((ROOT / "Narration/scripts/events.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["scripts"]}


def manifest_entries():
    data = json.loads(
        (ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text(encoding="utf-8")
    )
    return data["entries"]


def app_section(start, end):
    start_at = APP.index(start)
    return APP[start_at:APP.index(end, start_at)]


def test_all_event_scripts_are_generated_with_complete_production_metadata():
    scripts = event_scripts()
    assert len(scripts) == 14
    assert all(item["status"] == "generated" for item in scripts.values())
    for definition_id in EXPANSION_EVENTS:
        item = scripts[f"event.{definition_id}"]
        assert item["category"] == "event"
        assert item["outputFile"] == f"events/{definition_id}.mp3"
        assert all(item[field] for field in ("scriptHash", "settingsHash", "generationHash", "audioHash"))


def test_all_event_audio_is_available_and_release_audio_metadata_matches_files():
    entries = manifest_entries()
    event_entries = {key: item for key, item in entries.items() if key.startswith("event.")}
    assert len(event_entries) == 14
    assert all(item["available"] is True for item in event_entries.values())
    for definition_id in EXPANSION_EVENTS:
        item = entries[f"event.{definition_id}"]
        expected_size, expected_duration, expected_hash = EXPANSION_AUDIO[definition_id]
        audio = ROOT / "Assets/Audio/Narration" / item["file"]
        assert item["category"] == "event"
        assert item["eventDefinitionId"] == definition_id
        assert item["file"] == f"events/{definition_id}.mp3"
        assert item["durationMs"] == expected_duration
        assert item["audioHash"] == expected_hash
        assert audio.stat().st_size == expected_size
        assert hashlib.sha256(audio.read_bytes()).hexdigest() == expected_hash


def test_other_narration_categories_remain_available():
    entries = manifest_entries()
    for prefix in ("mission.", "grade.", "outcome.", "deadly."):
        assert any(key.startswith(prefix) and item["available"] for key, item in entries.items())


def test_generic_playback_mapping_queue_deduplication_and_replay_last():
    play_event = NARRATION[NARRATION.index("function playEvent"):NARRATION.index("function playGradeEscalation")]
    assert "`event.${definitionId}`" in play_event
    assert "`event:${instanceId}`" in play_event
    assert "automaticPlayback.has(duplicateKey)" in play_event
    assert "eventQueue.push" in play_event
    assert "function replayLast()" in NARRATION
    assert "playEntry(lastEntry.id, lastEntry.duplicateKey, true)" in NARRATION

    entries = ",".join(
        f"'event.{definition_id}':{{available:true,file:'events/{definition_id}.mp3'}}"
        for definition_id in EXPANSION_EVENTS
    )
    script = f"""
const fs=require('fs'),vm=require('vm'); const calls=[];
class Audio {{ constructor(){{Audio.instance=this;this.volume=1;}} pause(){{}} removeAttribute(){{}} load(){{}} play(){{calls.push(this.src);return Promise.resolve();}} }}
const context={{Audio,URL,location:{{href:'https://example.test/'}},fetch:async()=>({{ok:true,json:async()=>({{entries:{{{entries}}}}})}}),localStorage:{{getItem:()=>null,setItem:()=>{{}}}},dispatchEvent:()=>{{}},CustomEvent:function(){{}}}};
context.window=context;vm.createContext(context);vm.runInContext(fs.readFileSync('narration.js','utf8'),context);
(async()=>{{const n=context.TombWorldNarration;await n.init();
const finish=()=>{{if(Audio.instance.onended)Audio.instance.onended();}};
if(!await n.playEvent('flesh-hunger','flesh-1'))throw Error('mapping failed');finish();await new Promise(resolve=>setTimeout(resolve,0));
if(await n.playEvent('flesh-hunger','flesh-1'))throw Error('duplicate played');
if(!await n.playEvent('flesh-hunger','flesh-2'))throw Error('separate instance failed');finish();await new Promise(resolve=>setTimeout(resolve,0));
if(!await n.playEvent('rewards-of-annihilation','rewards-1'))throw Error('rewards mapping failed');finish();await new Promise(resolve=>setTimeout(resolve,0));
if(!await n.playEvent('enforcer-of-the-phaerons','enforcer-1'))throw Error('enforcer mapping failed');finish();await new Promise(resolve=>setTimeout(resolve,0));
if(!await n.replayLast())throw Error('Replay Last failed');
if(calls.length!==5||!calls.at(-1).endsWith('events/enforcer-of-the-phaerons.mp3'))throw Error('unexpected playback');
}})().catch(error=>{{console.error(error);process.exit(1)}});
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_variant_event_decks_are_unchanged_and_mode_independent():
    registry = app_section("const inertVariantHooks", "function currentTombWorldVariant")
    for event_id, variant_id in EXPANSION_EVENTS.items():
        assert registry.count(f"eventId:'{event_id}'") == 1
        assert f"id:'{variant_id}'" in APP
    assert "eventDeckAdditions:()=>[]" in registry
    assert "eventDeckAdditions:()=>eventId?[{instanceId:`${eventId}-1`" in registry
    narration_trigger = app_section("function narrateAcceptedEvent", "function beginCurrentEvent")
    assert "TombWorldNarration.playEvent(event.definitionId,event.instanceId)" in narration_trigger
    assert "gameMode" not in narration_trigger


def test_redraw_timing_master_settings_and_manifest_driven_offline_cache_are_preserved():
    visibility = app_section("function narrateVisibleStrategyEvents", "function beginCurrentEvent")
    redraw = app_section("async function redrawCurrentEvent", "function processReinforcementStage")
    assert "filter(event=>event.status!=='redrawn')" in visibility
    assert "event.status='redrawn'" in redraw
    assert "narrateAcceptedEvent" not in redraw
    assert "if (!definitionId || !instanceId || !isPlaybackEnabled())" in NARRATION
    assert "if (!masterEnabled)" in NARRATION
    assert ".filter(entry=>entry?.available===true" in WORKER
    assert "await precacheNarration(cache);" in WORKER


def test_release_version_and_save_schema_are_finalized():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 16)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
