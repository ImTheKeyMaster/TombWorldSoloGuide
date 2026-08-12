(function (global) {
  'use strict';

  const MANIFEST_URL = 'Assets/Audio/Narration/narration-manifest.json';
  const ENABLED_KEY = 'tombWorldSoloGuide.narrationEnabled';
  const VOLUME_KEY = 'tombWorldSoloGuide.narrationVolume';
  const DEFAULT_VOLUME = 0.8;
  const SILENT_UNLOCK_AUDIO = 'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA==';
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
  let audioUnlocked = false;
  let playbackRequest = 0;
  const automaticPlayback = new Set();
  const eventQueue = [];
  let eventQueueRunning = false;
  let eventQueueGeneration = 0;
  let finishActiveEvent = null;

  function readPreference(key) {
    try { return global.localStorage?.getItem(key) ?? null; } catch { return null; }
  }

  function writePreference(key, value) {
    try { global.localStorage?.setItem(key, value); } catch { /* Preferences are optional. */ }
  }

  function isEnabled() {
    const saved = readPreference(ENABLED_KEY);
    return saved === null ? true : saved !== 'false';
  }

  function getVolume() {
    const saved = Number(readPreference(VOLUME_KEY));
    return Number.isFinite(saved) && saved >= 0 && saved <= 1 ? saved : DEFAULT_VOLUME;
  }

  function notify() {
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldnarrationchange', { detail: { canReplay: Boolean(lastEntry) } }));
    }
  }

  function ensureAudio() {
    if (!audio && typeof global.Audio === 'function') {
      try {
        audio = new global.Audio();
        audio.preload = 'none';
        audio.volume = getVolume();
      } catch { audio = null; }
    }
    return audio;
  }

  function stopAudio() {
    if (finishActiveEvent) finishActiveEvent();
    if (!audio) return;
    try {
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
    } catch { /* Audio cleanup must never affect gameplay. */ }
  }

  function stop() {
    eventQueueGeneration += 1;
    eventQueue.splice(0).forEach(item => item.resolve(false));
    eventQueueRunning = false;
    playbackRequest += 1;
    stopAudio();
  }

  function unlock() {
    if (audioUnlocked || lastEntry) {
      audioUnlocked = true;
      return Promise.resolve(true);
    }
    if (!isEnabled()) return Promise.resolve(false);
    const player = ensureAudio();
    if (!player) return Promise.resolve(false);
    try {
      player.volume = 0;
      player.src = SILENT_UNLOCK_AUDIO;
      const playback = player.play();
      if (!playback || typeof playback.then !== 'function') {
        audioUnlocked = true;
        player.volume = getVolume();
        return Promise.resolve(true);
      }
      return playback.then(() => {
        audioUnlocked = true;
        player.volume = getVolume();
        return true;
      }, () => {
        audioUnlocked = false;
        player.volume = getVolume();
        return false;
      });
    } catch {
      audioUnlocked = false;
      player.volume = getVolume();
      return Promise.resolve(false);
    }
  }

  function installUnlockOnGesture() {
    const doc = global.document;
    if (!doc || typeof doc.addEventListener !== 'function') return;
    const onGesture = () => {
      void unlock().then(unlocked => {
        if (unlocked && typeof doc.removeEventListener === 'function') doc.removeEventListener('click', onGesture, true);
      });
    };
    doc.addEventListener('click', onGesture, true);
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
    const request = ++playbackRequest;
    await init();
    if (request !== playbackRequest) return false;
    const entry = manifest?.entries?.[id];
    if (!entry?.available || !entry.file) return false;
    const player = ensureAudio();
    if (!player) return false;
    stopAudio();
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

  async function drainEventQueue(generation) {
    eventQueueRunning = true;
    while (generation === eventQueueGeneration && eventQueue.length) {
      const item = eventQueue.shift();
      const requestBeforePlayback = playbackRequest;
      const started = await playEntry(item.id, item.duplicateKey, true);
      item.resolve(started);
      if (!started) continue;

      await new Promise(resolve => {
        let finished = false;
        finishActiveEvent = () => {
          if (finished) return;
          finished = true;
          if (audio) {
            audio.onended = null;
            audio.onerror = null;
          }
          finishActiveEvent = null;
          resolve();
        };
        audio.onended = finishActiveEvent;
        audio.onerror = finishActiveEvent;
      });

      if (playbackRequest !== requestBeforePlayback + 1) break;
    }
    if (generation === eventQueueGeneration) eventQueueRunning = false;
  }

  function playMissionIntro(missionId, restart = false) {
    const number = missionNumbers[missionId];
    if (restart) automaticPlayback.delete(`mission:${missionId}`);
    return number ? playEntry(`mission.${number}.intro`, `mission:${missionId}`, false) : Promise.resolve(false);
  }

  function playEvent(definitionId, instanceId) {
    if (!definitionId || !instanceId || !isEnabled()) return Promise.resolve(false);
    const duplicateKey = `event:${instanceId}`;
    if (automaticPlayback.has(duplicateKey)) return Promise.resolve(false);
    automaticPlayback.add(duplicateKey);
    const result = new Promise(resolve => eventQueue.push({ id: `event.${definitionId}`, duplicateKey, resolve }));
    if (!eventQueueRunning) void drainEventQueue(eventQueueGeneration);
    return result;
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
    writePreference(ENABLED_KEY, String(Boolean(enabled)));
    if (!enabled) stop();
    notify();
  }

  function setVolume(volume) {
    const normalized = Math.min(1, Math.max(0, Number(volume)));
    if (!Number.isFinite(normalized)) return;
    writePreference(VOLUME_KEY, String(normalized));
    if (audio) audio.volume = normalized;
    notify();
  }

  global.TombWorldNarration = Object.freeze({
    init, unlock, playMissionIntro, playEvent, playOutcome, replayLast, stop,
    setEnabled, setVolume, isEnabled, getVolume,
    canReplay: () => Boolean(lastEntry)
  });

  installUnlockOnGesture();
})(typeof window === 'undefined' ? globalThis : window);
