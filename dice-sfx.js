(() => {
  'use strict';

  const PREFERENCE_KEY = 'tombWorldSoloGuide.diceRollEnabled';
  const DICE_ROLL_SOURCE = 'Assets/Audio/Narration/SFX/dice-roll-flem0527-750ms.mp3';
  const audio = typeof Audio === 'function' ? new Audio() : null;
  let preferenceEnabled = readPreference();
  let masterEnabled = true;

  if (audio) {
    audio.preload = 'auto';
    audio.src = DICE_ROLL_SOURCE;
  }

  function readPreference() {
    try { return localStorage.getItem(PREFERENCE_KEY) !== 'false'; }
    catch { return true; }
  }

  function init() {
    try { audio?.load(); }
    catch { return Promise.resolve(false); }
    return Promise.resolve(Boolean(audio));
  }

  function play() {
    if (!audio || !masterEnabled || !preferenceEnabled) return Promise.resolve(false);
    try {
      audio.currentTime = 0;
      const request = audio.play();
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
    if (!audio || window.TombWorldAudioCapabilities?.supportsInAppVolumeControl() === false) return;
    try { audio.volume = Math.max(0, Math.min(1, Number(value) || 0)); }
    catch { /* Dice audio remains at its source level if volume writes are rejected. */ }
  }

  function stop() {
    if (!audio) return;
    try { audio.pause(); audio.currentTime = 0; }
    catch { /* Stopping dice audio must never interrupt New Game. */ }
  }

  window.TombWorldDiceSfx = Object.freeze({
    init, play, setPreferenceEnabled, isPreferenceEnabled, setMasterEnabled, setVolumeMultiplier, stop
  });
})();
