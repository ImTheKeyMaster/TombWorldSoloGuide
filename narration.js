(function (global) {
  'use strict';

  const MANIFEST_URL = 'Assets/Audio/Narration/narration-manifest.json';
  const ALIGNMENT_DIRECTORY_URL = 'Assets/Audio/Narration/alignment/';
  const ENABLED_KEY = 'tombWorldBattleGuide.narrationEnabled';
  const MASTER_ENABLED_KEY = 'tombWorldBattleGuide.gameAudioEnabled';
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
  let unlockAudio = null;
  let manifest = null;
  let initialization = null;
  let lastEntry = null;
  let activeEntryId = null;
  let activeManifestEntry = null;
  let activeAlignment = null;
  let lastEndReason = null;
  let userPaused = false;
  const alignmentCache = new Map();
  const alignmentLoads = new Map();
  let audioUnlocked = false;
  let playbackRequest = 0;
  const automaticPlayback = new Set();
  const eventQueue = [];
  let eventQueueRunning = false;
  let eventQueueGeneration = 0;
  let finishActiveEvent = null;
  const deadlyEncounterQueue = [];
  let deadlyEncounterQueueRunning = false;
  let deadlyEncounterGeneration = 0;
  let activePlayback = false;
  let pausedByMaster = false;
  let notifiedPlaybackActivity = false;
  let volumeMultiplier = 1;
  let masterEnabled = readPreference(MASTER_ENABLED_KEY) !== 'false';
  let appliedPreferenceEnabled = masterEnabled && isPreferenceEnabled();

  function supportsInAppVolumeControl() {
    return global.TombWorldAudioCapabilities?.supportsInAppVolumeControl() !== false;
  }

  function readPreference(key) {
    try { return global.localStorage?.getItem(key) ?? null; } catch { return null; }
  }

  function writePreference(key, value) {
    try { global.localStorage?.setItem(key, value); } catch { /* Preferences are optional. */ }
  }

  function isPreferenceEnabled() {
    const saved = readPreference(ENABLED_KEY);
    return saved === null ? true : saved !== 'false';
  }

  function isMasterEnabled() {
    return masterEnabled;
  }

  function isPlaybackEnabled() {
    return masterEnabled && appliedPreferenceEnabled;
  }

  function notify() {
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldnarrationchange', { detail: { canReplay: Boolean(lastEntry) } }));
    }
  }

  function notifyPlaybackActivity(active) {
    const nextActive = Boolean(active);
    if (nextActive === notifiedPlaybackActivity) return;
    notifiedPlaybackActivity = nextActive;
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldnarrationactivity', { detail: { active: nextActive } }));
    }
  }

  function alignmentUrl(id) {
    return `${ALIGNMENT_DIRECTORY_URL}${String(id).replace(/[^A-Za-z0-9._-]/g, '_')}.json`;
  }

  function cloneAlignment(alignment) {
    if (!alignment) return null;
    return {
      schemaVersion: alignment.schemaVersion,
      qualityStatus: alignment.qualityStatus ?? null,
      alignmentLoss: alignment.alignmentLoss ?? null,
      words: alignment.words.map(word => ({ ...word }))
    };
  }

  function getPlaybackState() {
    const player = audio;
    const currentTime = activeEntryId && Number.isFinite(player?.currentTime) && player.currentTime >= 0
      ? Math.round(player.currentTime * 1000)
      : 0;
    const audioDuration = Number(player?.duration);
    const manifestDuration = Number(activeManifestEntry?.durationMs);
    const durationMs = activeEntryId
      ? (Number.isFinite(audioDuration) && audioDuration >= 0
          ? Math.round(audioDuration * 1000)
          : (Number.isFinite(manifestDuration) && manifestDuration >= 0 ? Math.round(manifestDuration) : 0))
      : 0;
    const paused = Boolean(activeEntryId && (userPaused || pausedByMaster || player?.paused === true));
    return {
      active: Boolean(activeEntryId),
      playing: Boolean(activeEntryId && activePlayback && !paused && player?.ended !== true),
      paused,
      pausedByMaster: Boolean(activeEntryId && pausedByMaster),
      pausedByUser: Boolean(activeEntryId && userPaused),
      id: activeEntryId,
      category: activeManifestEntry?.category ?? null,
      currentTimeMs: currentTime,
      durationMs,
      transcriptAvailable: Boolean(activeAlignment),
      transcript: activeAlignment?.text ?? null,
      alignment: cloneAlignment(activeAlignment),
      manifest: activeManifestEntry ? { ...activeManifestEntry } : null,
      lastEndReason
    };
  }

  function notifyPlaybackState() {
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldnarrationstatechange', { detail: getPlaybackState() }));
    }
  }

  function clearActivePlayback(reason) {
    activePlayback = false;
    activeEntryId = null;
    activeManifestEntry = null;
    activeAlignment = null;
    pausedByMaster = false;
    userPaused = false;
    lastEndReason = reason;
    notifyPlaybackState();
  }

  function validAlignment(alignment, id, entry) {
    const validDuration = Number.isFinite(alignment?.durationMs) && alignment.durationMs >= 0
      && alignment.durationMs === entry.durationMs;
    return alignment?.schemaVersion === 1
      && alignment.id === id
      && typeof alignment.text === 'string' && alignment.text.trim().length > 0
      && validDuration
      && alignment.scriptHash === entry.scriptHash
      && alignment.audioHash === entry.audioHash
      && Array.isArray(alignment.words) && alignment.words.length > 0
      && alignment.words.every(word => typeof word?.text === 'string' && word.text.length > 0
        && Number.isFinite(word.startMs) && Number.isFinite(word.endMs)
        && word.startMs >= 0 && word.startMs <= word.endMs);
  }

  function loadAlignment(id, entry, request) {
    const cached = alignmentCache.get(id);
    const loading = cached
      ? Promise.resolve(cached)
      : (alignmentLoads.get(id) || (typeof global.fetch === 'function'
          ? Promise.resolve().then(() => global.fetch(alignmentUrl(id)))
            .then(response => response.ok ? response.json() : Promise.reject(new Error('Alignment unavailable')))
            .then(data => {
              if (!validAlignment(data, id, entry)) throw new Error('Invalid alignment');
              alignmentCache.set(id, data);
              alignmentLoads.delete(id);
              return data;
            })
            .catch(error => {
              alignmentLoads.delete(id);
              throw error;
            })
          : Promise.reject(new Error('Alignment unavailable'))));
    if (!cached && !alignmentLoads.has(id)) alignmentLoads.set(id, loading);
    loading.then(alignment => {
      if (request !== playbackRequest || activeEntryId !== id) return;
      activeAlignment = alignment;
      notifyPlaybackState();
    }, () => {
      if (request !== playbackRequest || activeEntryId !== id) return;
      activeAlignment = null;
      notifyPlaybackState();
    });
  }

  function ensureAudio() {
    if (!audio && typeof global.Audio === 'function') {
      try {
        audio = new global.Audio();
        audio.preload = 'none';
        if (supportsInAppVolumeControl()) audio.volume = volumeMultiplier;
      } catch { audio = null; }
    }
    return audio;
  }

  function stopAudio() {
    if (finishActiveEvent) finishActiveEvent('stop');
    const hadActivePlayback = Boolean(activeEntryId);
    if (hadActivePlayback) clearActivePlayback('stop');
    else {
      activePlayback = false;
      pausedByMaster = false;
      userPaused = false;
    }
    if (!audio) return;
    try {
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
    } catch { /* Audio cleanup must never affect gameplay. */ }
  }

  function setVolumeMultiplier(value) {
    volumeMultiplier = Math.min(1, Math.max(0, Number.isFinite(Number(value)) ? Number(value) : 1));
    if (audio && supportsInAppVolumeControl()) audio.volume = volumeMultiplier;
  }

  function clearEventQueue() {
    eventQueueGeneration += 1;
    eventQueue.splice(0).forEach(item => item.resolve(false));
    eventQueueRunning = false;
  }

  function clearDeadlyEncounterQueue() {
    deadlyEncounterGeneration += 1;
    deadlyEncounterQueue.splice(0).forEach(item => item.resolve(false));
    deadlyEncounterQueueRunning = false;
  }

  function stop(resetAudio = false) {
    clearEventQueue();
    clearDeadlyEncounterQueue();
    playbackRequest += 1;
    if (activePlayback || resetAudio) stopAudio();
    else {
      activePlayback = false;
      if (activeEntryId) clearActivePlayback('stop');
      else notifyPlaybackState();
    }
    notifyPlaybackActivity(false);
  }

  function pauseNarration() {
    const player = audio;
    if (!player || !activePlayback || player.ended || player.paused === true) return false;
    try {
      player.pause();
      userPaused = true;
      notifyPlaybackActivity(false);
      notifyPlaybackState();
      return true;
    } catch { return false; }
  }

  function resumeNarration() {
    const player = audio;
    if (!player || !activePlayback || !userPaused || pausedByMaster || !isPlaybackEnabled() || player.ended || !player.src) {
      return Promise.resolve(false);
    }
    let playback;
    try { playback = player.play(); }
    catch { return Promise.resolve(false); }
    return Promise.resolve(playback).then(() => {
      userPaused = false;
      audioUnlocked = true;
      notifyPlaybackActivity(true);
      notifyPlaybackState();
      return true;
    }, () => false);
  }

  function pauseForMasterMute() {
    const player = audio;
    if (!player || !activePlayback || player.ended) {
      pausedByMaster = false;
      notifyPlaybackActivity(false);
      return false;
    }
    if (pausedByMaster) {
      notifyPlaybackActivity(false);
      return true;
    }
    if (userPaused || player.paused) {
      pausedByMaster = false;
      notifyPlaybackActivity(false);
      notifyPlaybackState();
      return false;
    }
    try {
      if (!player.paused) player.pause();
      pausedByMaster = true;
      notifyPlaybackActivity(false);
      notifyPlaybackState();
      return true;
    } catch { return false; }
  }

  function activateFromGesture() {
    if (!isPlaybackEnabled()) {
      if (pausedByMaster) stopAudio();
      return Promise.resolve(false);
    }
    const player = audio;
    if (pausedByMaster && player && activePlayback && !player.ended && player.src) {
      let playback;
      try { playback = player.play(); }
      catch {
        audioUnlocked = false;
        return Promise.resolve(false);
      }
      notifyPlaybackActivity(true);
      return Promise.resolve(playback).then(() => {
        pausedByMaster = false;
        audioUnlocked = true;
        if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
          global.dispatchEvent(new global.CustomEvent('tombworldnarrationusable'));
        }
        notifyPlaybackState();
        return true;
      }, () => {
        audioUnlocked = false;
        notifyPlaybackActivity(false);
        notifyPlaybackState();
        return false;
      });
    }
    return unlock({ force: true });
  }

  function unlock(options = {}) {
    if (audioUnlocked && !options.force) {
      audioUnlocked = true;
      return Promise.resolve(true);
    }
    if (!isPlaybackEnabled()) return Promise.resolve(false);
    let player = unlockAudio;
    if (!player && typeof global.Audio === 'function') {
      try {
        player = unlockAudio = new global.Audio();
        player.preload = 'none';
      } catch { player = null; }
    }
    if (!player) return Promise.resolve(false);
    try {
      player.volume = 1;
      player.src = SILENT_UNLOCK_AUDIO;
      const playback = player.play();
      if (!playback || typeof playback.then !== 'function') {
        audioUnlocked = true;
        player.volume = 1;
        return Promise.resolve(true);
      }
      return playback.then(() => {
        audioUnlocked = true;
        player.volume = 1;
        return true;
      }, () => {
        audioUnlocked = false;
        player.volume = 1;
        return false;
      });
    } catch {
      audioUnlocked = false;
      player.volume = 1;
      return Promise.resolve(false);
    }
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

  async function playEntry(id, duplicateKey, manual, preemptQueues = true) {
    if (!isPlaybackEnabled()) return false;
    if (!manual && automaticPlayback.has(duplicateKey)) return false;
    if (!manual) automaticPlayback.add(duplicateKey);
    if (preemptQueues) {
      clearEventQueue();
      clearDeadlyEncounterQueue();
    }
    const request = ++playbackRequest;
    await init();
    if (request !== playbackRequest) return false;
    const entry = manifest?.entries?.[id];
    if (!entry?.available || !entry.file) return false;
    const player = ensureAudio();
    if (!player) return false;
    stopAudio();
    if (supportsInAppVolumeControl()) player.volume = volumeMultiplier;
    player.src = new URL(entry.file, new URL(MANIFEST_URL, global.location?.href || 'http://localhost/')).href;
    activePlayback = true;
    activeEntryId = id;
    activeManifestEntry = entry;
    activeAlignment = null;
    userPaused = false;
    pausedByMaster = false;
    lastEndReason = null;
    player.onended = () => {
      if (request !== playbackRequest) return;
      clearActivePlayback('natural');
      notifyPlaybackActivity(false);
      if (eventQueue.length && !eventQueueRunning && !deadlyEncounterQueueRunning) void drainEventQueue(eventQueueGeneration);
    };
    try {
      const playback = player.play();
      loadAlignment(id, entry, request);
      await playback;
      if (request !== playbackRequest || !isPlaybackEnabled()) return false;
      audioUnlocked = true;
      notifyPlaybackActivity(true);
      notifyPlaybackState();
      if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
        global.dispatchEvent(new global.CustomEvent('tombworldnarrationusable'));
      }
      lastEntry = { id, duplicateKey };
      notify();
      return true;
    } catch {
      if (request === playbackRequest) {
        clearActivePlayback('stop');
        notifyPlaybackActivity(false);
      }
      return false;
    }
  }

  async function drainEventQueue(generation) {
    eventQueueRunning = true;
    while (generation === eventQueueGeneration && eventQueue.length) {
      const item = eventQueue.shift();
      const requestBeforePlayback = playbackRequest;
      const started = await playEntry(item.id, item.duplicateKey, true, false);
      item.resolve(started);
      if (!started) continue;

      await new Promise(resolve => {
        let finished = false;
        finishActiveEvent = (reason = 'natural') => {
          if (finished) return;
          finished = true;
          if (audio) {
            audio.onended = null;
            audio.onerror = null;
          }
          finishActiveEvent = null;
          clearActivePlayback(reason);
          notifyPlaybackActivity(false);
          resolve();
        };
        const finish = finishActiveEvent;
        audio.onended = () => finish('natural');
        audio.onerror = () => finish('stop');
      });

      if (playbackRequest !== requestBeforePlayback + 1) break;
    }
    if (generation === eventQueueGeneration) eventQueueRunning = false;
    if (!activePlayback && !deadlyEncounterQueueRunning) notifyPlaybackActivity(false);
  }

  function playMissionIntro(missionId, restart = false) {
    const number = missionNumbers[missionId];
    if (restart) automaticPlayback.delete(`mission:${missionId}`);
    return number ? playEntry(`mission.${number}.intro`, `mission:${missionId}`, false) : Promise.resolve(false);
  }

  function playEvent(definitionId, instanceId) {
    if (!definitionId || !instanceId || !isPlaybackEnabled()) return Promise.resolve(false);
    const duplicateKey = `event:${instanceId}`;
    if (automaticPlayback.has(duplicateKey)) return Promise.resolve(false);
    automaticPlayback.add(duplicateKey);
    const result = new Promise(resolve => eventQueue.push({ id: `event.${definitionId}`, duplicateKey, resolve }));
    if (!eventQueueRunning && !deadlyEncounterQueueRunning) void drainEventQueue(eventQueueGeneration);
    return result;
  }

  function playGradeEscalation(grade, occurrenceId) {
    const ids = { 1: 'grade.1.stirring', 2: 'grade.2.awakened', 3: 'grade.3.overrun' };
    const id = ids[grade];
    if (!id || !occurrenceId || !isPlaybackEnabled()) return Promise.resolve(false);
    const duplicateKey = `grade:${occurrenceId}`;
    if (automaticPlayback.has(duplicateKey)) return Promise.resolve(false);
    automaticPlayback.add(duplicateKey);
    const result = new Promise(resolve => eventQueue.push({ id, duplicateKey, resolve }));
    if (!eventQueueRunning && !deadlyEncounterQueueRunning && !activePlayback) void drainEventQueue(eventQueueGeneration);
    return result.then(started => {
      if (!started) automaticPlayback.delete(duplicateKey);
      return started;
    });
  }

  function playOutcome(missionId, outcome) {
    const number = missionNumbers[missionId];
    return number && ['victory', 'defeat'].includes(outcome)
      ? playEntry(`outcome.${number}.${outcome}`, `outcome:${missionId}:${outcome}`, false)
      : Promise.resolve(false);
  }

  function deadlyEncounterEntryId(featureId) {
    return Object.entries(manifest?.entries || {}).find(([, entry]) =>
      entry?.category === 'deadly-encounter' && entry.deadlyEncounterFeatureId === featureId
    )?.[0] || null;
  }

  async function drainDeadlyEncounterQueue(generation) {
    deadlyEncounterQueueRunning = true;
    await init();
    while (generation === deadlyEncounterGeneration && deadlyEncounterQueue.length) {
      const item = deadlyEncounterQueue.shift();
      const entryIds = item.featureIds.map(deadlyEncounterEntryId);
      let played = false;
      if (!entryIds.some(id => !id)) {
        for (const id of entryIds) {
          if (generation !== deadlyEncounterGeneration) break;
          const requestBeforePlayback = playbackRequest;
          const started = await playEntry(id, item.duplicateKey, true, false);
          if (!started) continue;
          if (generation !== deadlyEncounterGeneration || playbackRequest !== requestBeforePlayback + 1) {
            item.resolve(false);
            return;
          }
          played = true;
          await new Promise(resolve => {
            let finished = false;
            finishActiveEvent = (reason = 'natural') => {
              if (finished) return;
              finished = true;
              if (audio) {
                audio.onended = null;
                audio.onerror = null;
              }
              finishActiveEvent = null;
              clearActivePlayback(reason);
              notifyPlaybackActivity(false);
              resolve();
            };
            const finish = finishActiveEvent;
            audio.onended = () => finish('natural');
            audio.onerror = () => finish('stop');
          });
          if (generation !== deadlyEncounterGeneration || playbackRequest !== requestBeforePlayback + 1) break;
        }
      }
      item.resolve(played);
    }
    if (generation === deadlyEncounterGeneration) {
      deadlyEncounterQueueRunning = false;
      if (eventQueue.length && !eventQueueRunning) void drainEventQueue(eventQueueGeneration);
      else if (!activePlayback) notifyPlaybackActivity(false);
    }
  }

  function playDeadlyEncounter(featureIds, discoveryKey) {
    const orderedFeatureIds = (Array.isArray(featureIds) ? featureIds : [featureIds])
      .filter(featureId => typeof featureId === 'string' && featureId !== 'unusual');
    if (!orderedFeatureIds.length || !discoveryKey || !isPlaybackEnabled()) return Promise.resolve(false);
    const duplicateKey = `deadly:${discoveryKey}`;
    if (automaticPlayback.has(duplicateKey)) return Promise.resolve(false);
    automaticPlayback.add(duplicateKey);
    if (!deadlyEncounterQueueRunning) clearEventQueue();
    const result = new Promise(resolve => deadlyEncounterQueue.push({ featureIds: orderedFeatureIds, duplicateKey, resolve }));
    if (!deadlyEncounterQueueRunning) void drainDeadlyEncounterQueue(deadlyEncounterGeneration);
    return result;
  }

  function replayLast() {
    return lastEntry ? playEntry(lastEntry.id, lastEntry.duplicateKey, true) : Promise.resolve(false);
  }

  function setPreferenceEnabled(enabled) {
    writePreference(ENABLED_KEY, String(Boolean(enabled)));
    notify();
  }

  function setMasterEnabled(enabled) {
    masterEnabled = Boolean(enabled);
    writePreference(MASTER_ENABLED_KEY, String(masterEnabled));
    appliedPreferenceEnabled = masterEnabled && isPreferenceEnabled();
    if (!masterEnabled) {
      pauseForMasterMute();
      audioUnlocked = false;
    }
    notifyPlaybackState();
    notify();
  }

  global.TombWorldNarration = Object.freeze({
    init, unlock, activateFromGesture, playMissionIntro, playEvent, playGradeEscalation, playOutcome, playDeadlyEncounter, replayLast, stop, pauseNarration, resumeNarration, getPlaybackState,
    setPreferenceEnabled, isPreferenceEnabled, setMasterEnabled, isMasterEnabled, isPlaybackEnabled, setVolumeMultiplier,
    canReplay: () => Boolean(lastEntry)
  });
})(typeof window === 'undefined' ? globalThis : window);
