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


def test_scripts_use_exact_event_ids_and_approved_preproduction_state():
    scripts = event_scripts()
    for definition_id in EXPANSION_EVENTS:
        item = scripts[f"event.{definition_id}"]
        assert item["category"] == "event"
        assert item["status"] == "approved"
        assert item["outputFile"] == f"events/{definition_id}.mp3"
        assert item["scriptHash"]
        assert item["settingsHash"] is None
        assert item["generationHash"] is None
        assert item["audioHash"] is None


def test_unavailable_audio_is_not_fabricated_or_advertised():
    entries = manifest_entries()
    for definition_id in EXPANSION_EVENTS:
        item = entries[f"event.{definition_id}"]
        assert item["category"] == "event"
        assert item["eventDefinitionId"] == definition_id
        assert item["file"] == f"events/{definition_id}.mp3"
        assert item["available"] is False
        assert item["durationMs"] is None
        assert not (ROOT / "Assets/Audio/Narration" / item["file"]).exists()


def test_existing_event_audio_and_narration_categories_remain_available():
    entries = manifest_entries()
    existing = {
        key: item
        for key, item in entries.items()
        if key.startswith("event.") and key.removeprefix("event.") not in EXPANSION_EVENTS
    }
    assert len(existing) == 11
    assert all(item["available"] is True for item in existing.values())
    assert all((ROOT / "Assets/Audio/Narration" / item["file"]).stat().st_size > 0 for item in existing.values())
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


def test_release_version_and_save_schema_remain_at_production_baseline_until_audio_exists():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) < (9, 2, 16)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
