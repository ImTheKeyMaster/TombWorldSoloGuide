(function (global) {
  'use strict';

  const MANIFEST_URL = 'Assets/Audio/Narration/narration-manifest.json';
  const ENABLED_KEY = 'tombWorldSoloGuide.narrationEnabled';
  const VOLUME_KEY = 'tombWorldSoloGuide.narrationVolume';
  const DEFAULT_VOLUME = 0.8;
  const missionNumbers = {
    'shifting-labyrinth': '01',
    'demolition-protocol': '02',
    'recover-transponder': '03',
    'destroy-sarcophagus': '04',
    'scout-sub-crypt': '05',
    regroup: '06'
  };

  let audio = null;
  let manifest = null;
  let initialization = null;
  let lastEntry = null;
  const automaticPlayback = new Set();

  function storage() {
    try { return global.localStorage; } catch { return null; }
  }

  function isEnabled() {
    const saved = storage()?.getItem(ENABLED_KEY);
    return saved === null ? true : saved !== 'false';
  }

  function getVolume() {
    const saved = Number(storage()?.getItem(VOLUME_KEY));
    return Number.isFinite(saved) && saved >= 0 && saved <= 1 ? saved : DEFAULT_VOLUME;
  }

  function notify() {
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldnarrationchange', { detail: { canReplay: Boolean(lastEntry) } }));
    }
  }

  function ensureAudio() {
    if (!audio && typeof global.Audio === 'function') {
      audio = new global.Audio();
      audio.preload = 'none';
      audio.volume = getVolume();
    }
    return audio;
  }

  function stop() {
    if (!audio) return;
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
  }

  function init() {
    ensureAudio();
    if (!initialization) {
      initialization = typeof global.fetch === 'function'
        ? global.fetch(MANIFEST_URL).then(response => response.ok ? response.json() : null).then(data => { manifest = data; }).catch(() => { manifest = null; })
        : Promise.resolve();
    }
    return initialization;
  }

  async function playEntry(id, duplicateKey, manual) {
    if (!isEnabled()) return false;
    if (!manual && automaticPlayback.has(duplicateKey)) return false;
    if (!manual) automaticPlayback.add(duplicateKey);
    await init();
    const entry = manifest?.entries?.[id];
    if (!entry?.available || !entry.file) return false;
    const player = ensureAudio();
    if (!player) return false;
    stop();
    player.volume = getVolume();
    player.src = new URL(entry.file, new URL(MANIFEST_URL, global.location?.href || 'http://localhost/')).href;
    try {
      await player.play();
      lastEntry = { id, duplicateKey };
      notify();
      return true;
    } catch {
      return false;
    }
  }

  function playMissionIntro(missionId) {
    const number = missionNumbers[missionId];
    return number ? playEntry(`mission.${number}.intro`, `mission:${missionId}`, false) : Promise.resolve(false);
  }

  function playEvent(definitionId, instanceId) {
    return definitionId && instanceId
      ? playEntry(`event.${definitionId}`, `event:${instanceId}`, false)
      : Promise.resolve(false);
  }

  function playOutcome(missionId, outcome) {
    const number = missionNumbers[missionId];
    return number && ['victory', 'defeat'].includes(outcome)
      ? playEntry(`outcome.${number}.${outcome}`, `outcome:${missionId}:${outcome}`, false)
      : Promise.resolve(false);
  }

  function replayLast() {
    return lastEntry ? playEntry(lastEntry.id, lastEntry.duplicateKey, true) : Promise.resolve(false);
  }

  function setEnabled(enabled) {
    storage()?.setItem(ENABLED_KEY, String(Boolean(enabled)));
    if (!enabled) stop();
    notify();
  }

  function setVolume(volume) {
    const normalized = Math.min(1, Math.max(0, Number(volume)));
    if (!Number.isFinite(normalized)) return;
    storage()?.setItem(VOLUME_KEY, String(normalized));
    if (audio) audio.volume = normalized;
    notify();
  }

  global.TombWorldNarration = Object.freeze({
    init, playMissionIntro, playEvent, playOutcome, replayLast, stop,
    setEnabled, setVolume, isEnabled, getVolume,
    canReplay: () => Boolean(lastEntry)
  });
})(typeof window === 'undefined' ? globalThis : window);
