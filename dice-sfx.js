(() => {
  'use strict';

  const PREFERENCE_KEY = 'tombWorldBattleGuide.diceRollEnabled';
  const DICE_ROLL_SOURCE = 'Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3';
  let diceAudioContext = null;
  let diceGainNode = null;
  let decodedDiceBuffer = null;
  let bufferInitialization = null;
  let preferenceEnabled = readPreference();
  let masterEnabled = true;
  let volumeMultiplier = 1;
  const activeSources = new Set();

  function readPreference() {
    try { return localStorage.getItem(PREFERENCE_KEY) !== 'false'; }
    catch { return true; }
  }

  function ensureAudioContext() {
    if (diceAudioContext) return diceAudioContext;
    const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
    if (typeof AudioContextConstructor !== 'function') return null;
    try {
      const context = new AudioContextConstructor();
      const gainNode = context.createGain();
      gainNode.gain.value = volumeMultiplier;
      gainNode.connect(context.destination);
      diceAudioContext = context;
      diceGainNode = gainNode;
      return diceAudioContext;
    } catch { return null; }
  }

  function initializeBuffer() {
    const context = ensureAudioContext();
    if (!context) return Promise.resolve(false);
    if (decodedDiceBuffer) return Promise.resolve(true);
    if (bufferInitialization) return bufferInitialization;
    let fetchRequest;
    try { fetchRequest = fetch(DICE_ROLL_SOURCE); }
    catch { return Promise.resolve(false); }
    bufferInitialization = Promise.resolve(fetchRequest)
      .then(response => {
        if (!response.ok) throw new Error('Dice SFX fetch failed');
        return response.arrayBuffer();
      })
      .then(data => context.decodeAudioData(data))
      .then(buffer => {
        decodedDiceBuffer = buffer;
        return true;
      })
      .catch(() => false)
      .then(initialized => {
        bufferInitialization = null;
        return initialized;
      });
    return bufferInitialization;
  }

  function init() {
    return initializeBuffer();
  }

  function startSource() {
    if (!decodedDiceBuffer || !diceAudioContext || !diceGainNode || !masterEnabled || !preferenceEnabled) return false;
    let source;
    try {
      source = diceAudioContext.createBufferSource();
      source.buffer = decodedDiceBuffer;
      source.connect(diceGainNode);
      source.onended = () => activeSources.delete(source);
      activeSources.add(source);
      source.start(0);
      return true;
    } catch {
      if (source) activeSources.delete(source);
      return false;
    }
  }

  function resumeThenStart(context) {
    let resumeRequest;
    try { resumeRequest = context.resume(); }
    catch { return Promise.resolve(false); }
    return Promise.resolve(resumeRequest)
      .then(() => decodedDiceBuffer ? startSource() : initializeBuffer().then(startSource))
      .catch(() => false);
  }

  function play() {
    if (!masterEnabled || !preferenceEnabled) return Promise.resolve(false);
    const context = ensureAudioContext();
    if (!context) return Promise.resolve(false);
    if (context.state === 'suspended') return resumeThenStart(context);
    if (decodedDiceBuffer) return Promise.resolve(startSource());
    return initializeBuffer().then(initialized => initialized && startSource()).catch(() => false);
  }

  function activateFromGesture() {
    const context = ensureAudioContext();
    if (!context) return Promise.resolve(false);
    void initializeBuffer();
    if (context.state !== 'suspended') return Promise.resolve(true);
    try { return Promise.resolve(context.resume()).then(() => true).catch(() => false); }
    catch { return Promise.resolve(false); }
  }

  function setPreferenceEnabled(enabled) {
    preferenceEnabled = Boolean(enabled);
    try { localStorage.setItem(PREFERENCE_KEY, String(preferenceEnabled)); }
    catch { /* The setting remains active for this session when storage is unavailable. */ }
  }

  function isPreferenceEnabled() { return preferenceEnabled; }
  function setMasterEnabled(enabled) {
    masterEnabled = Boolean(enabled);
    if (!masterEnabled) stop();
  }

  function setVolumeMultiplier(value) {
    volumeMultiplier = Math.max(0, Math.min(1, Number(value) || 0));
    try { if (diceGainNode) diceGainNode.gain.value = volumeMultiplier; }
    catch { /* Dice playback remains nonfatal if a platform rejects the gain write. */ }
  }

  function stop() {
    activeSources.forEach(source => {
      try { source.stop(); }
      catch { /* Continue stopping the remaining one-shot sources. */ }
    });
    activeSources.clear();
  }

  window.TombWorldDiceSfx = Object.freeze({
    init, activateFromGesture, play, setPreferenceEnabled, isPreferenceEnabled,
    setMasterEnabled, setVolumeMultiplier, stop
  });
})();
