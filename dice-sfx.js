(() => {
  'use strict';

  const PREFERENCE_KEY = 'tombWorldSoloGuide.diceRollEnabled';
  const DICE_ROLL_SOURCE = 'Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms-50.mp3';
  const diceAudioPlayers = typeof Audio === 'function' ? [new Audio(), new Audio()] : [];
  let nextPlayerIndex = 0;
  let preferenceEnabled = readPreference();
  let masterEnabled = true;

  diceAudioPlayers.forEach(audio => {
    audio.preload = 'auto';
    audio.src = DICE_ROLL_SOURCE;
  });

  function readPreference() {
    try { return localStorage.getItem(PREFERENCE_KEY) !== 'false'; }
    catch { return true; }
  }

  function init() {
    let initialized = diceAudioPlayers.length === 2;
    diceAudioPlayers.forEach(audio => {
      try { audio.load(); }
      catch { initialized = false; }
    });
    return Promise.resolve(initialized);
  }

  function play() {
    if (!diceAudioPlayers.length || !masterEnabled || !preferenceEnabled) return Promise.resolve(false);
    const audio = diceAudioPlayers[nextPlayerIndex];
    try { audio.currentTime = 0; }
    catch { return Promise.resolve(false); }
    let request;
    try {
      request = audio.play();
    } catch { return Promise.resolve(false); }
    finally { nextPlayerIndex = (nextPlayerIndex + 1) % diceAudioPlayers.length; }
    try {
      return request && typeof request.then === 'function'
        ? request.then(() => true).catch(() => false)
        : Promise.resolve(true);
    } catch { return Promise.resolve(false); }
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
    if (!diceAudioPlayers.length || window.TombWorldAudioCapabilities?.supportsInAppVolumeControl() === false) return;
    const volume = Math.max(0, Math.min(1, Number(value) || 0));
    diceAudioPlayers.forEach(audio => {
      try { audio.volume = volume; }
      catch { /* This player remains at its source level if the volume write is rejected. */ }
    });
  }

  function stop() {
    if (!diceAudioPlayers.length) return;
    diceAudioPlayers.forEach(audio => {
      try { audio.pause(); }
      catch { /* Continue resetting this player and stopping the other player. */ }
      try { audio.currentTime = 0; }
      catch { /* Stopping dice audio must never interrupt New Game. */ }
    });
  }

  window.TombWorldDiceSfx = Object.freeze({
    init, play, setPreferenceEnabled, isPreferenceEnabled, setMasterEnabled, setVolumeMultiplier, stop
  });
})();
