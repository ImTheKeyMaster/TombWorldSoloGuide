(function (global) {
  'use strict';

  const CONFIG_URL = 'Assets/Audio/Narration/ambient-config.json';
  const AUDIO_ROOT_URL = 'Assets/Audio/Narration/';
  const audio = new global.Audio();
  audio.loop = true;
  audio.preload = 'auto';

  let config = null;
  let initialization = null;
  let desiredActive = false;
  let narrationActive = false;
  let rampFrame = null;
  let pauseTimer = null;
  let recoveryHandler = null;
  let volumeMultiplier = 1;

  function effectiveVolume(gain) {
    return gain * volumeMultiplier;
  }

  function validConfig(value) {
    const file = value?.file;
    const gainsValid = ['normalGain', 'duckGain'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0 && value[key] <= 1);
    const timesValid = ['fadeInMs', 'fadeOutMs', 'duckAttackMs', 'duckReleaseMs'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0);
    return value?.schemaVersion === 1 && typeof file === 'string'
      && /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file)
      && gainsValid && timesValid && Number.isFinite(value.loopStartSeconds) && value.loopStartSeconds >= 0
      && (value.loopEndSeconds === null || (Number.isFinite(value.loopEndSeconds) && value.loopEndSeconds > value.loopStartSeconds));
  }

  function init() {
    if (initialization) return initialization;
    const attempt = (async () => {
      if (typeof global.fetch !== 'function') return false;
      try {
        const response = await global.fetch(CONFIG_URL);
        const value = response.ok ? await response.json() : null;
        if (!validConfig(value)) return false;
        config = value;
        audio.src = new URL(value.file, new URL(AUDIO_ROOT_URL, global.location?.href || 'http://localhost/')).href;
        audio.loop = value.loopEndSeconds === null;
        audio.preload = 'auto';
        audio.volume = 0;
        audio.load();
        return true;
      } catch { return false; }
    })();
    initialization = attempt;
    attempt.then(ready => { if (!ready && initialization === attempt) initialization = null; });
    return attempt;
  }

  function cancelRamp() {
    if (rampFrame !== null) global.cancelAnimationFrame?.(rampFrame);
    rampFrame = null;
  }

  function rampTo(target, duration, onComplete) {
    cancelRamp();
    const startVolume = audio.volume;
    if (!duration || typeof global.requestAnimationFrame !== 'function') {
      audio.volume = target;
      onComplete?.();
      return;
    }
    const started = global.performance?.now?.() ?? Date.now();
    const step = now => {
      const current = now ?? global.performance?.now?.() ?? Date.now();
      const progress = Math.min(1, (current - started) / duration);
      audio.volume = startVolume + (target - startVolume) * progress;
      if (progress < 1) rampFrame = global.requestAnimationFrame(step);
      else { rampFrame = null; onComplete?.(); }
    };
    rampFrame = global.requestAnimationFrame(step);
  }

  function removeGestureRecovery() {
    if (recoveryHandler) global.document?.removeEventListener('click', recoveryHandler, true);
    recoveryHandler = null;
  }

  function armGestureRecovery() {
    if (recoveryHandler || !desiredActive) return;
    recoveryHandler = () => { void playFromGesture(); };
    global.document?.addEventListener('click', recoveryHandler, true);
    if (typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldaudiorecoveryrequired', { detail: { category: 'ambient' } }));
    }
  }

  function playFromGesture() {
    if (!desiredActive) return Promise.resolve(false);
    if (!config) {
      void init();
      armGestureRecovery();
      return Promise.resolve(false);
    }
    global.clearTimeout(pauseTimer);
    pauseTimer = null;
    let result;
    try {
      result = audio.play();
    } catch {
      armGestureRecovery();
      return Promise.resolve(false);
    }
    return Promise.resolve(result).then(() => {
      removeGestureRecovery();
      rampTo(effectiveVolume(narrationActive ? config.duckGain : config.normalGain), config.fadeInMs);
      return true;
    }, () => {
      armGestureRecovery();
      return false;
    });
  }

  function setActive(isActive) {
    desiredActive = Boolean(isActive);
    if (!desiredActive) removeGestureRecovery();
  }

  function setVolumeMultiplier(value) {
    volumeMultiplier = Math.min(1, Math.max(0, Number.isFinite(Number(value)) ? Number(value) : 1));
    if (config && desiredActive && !audio.paused) {
      rampTo(effectiveVolume(narrationActive ? config.duckGain : config.normalGain), 0);
    }
  }

  function stop() {
    desiredActive = false;
    removeGestureRecovery();
    global.clearTimeout(pauseTimer);
    pauseTimer = null;
    if (!config || audio.paused) { cancelRamp(); audio.volume = 0; return; }
    rampTo(0, config.fadeOutMs);
    pauseTimer = global.setTimeout(() => {
      pauseTimer = null;
      if (!desiredActive) audio.pause();
    }, config.fadeOutMs);
  }

  function reset() {
    desiredActive = false;
    removeGestureRecovery();
    cancelRamp();
    global.clearTimeout(pauseTimer);
    pauseTimer = null;
    audio.pause();
    audio.volume = 0;
    try { audio.currentTime = config?.loopStartSeconds || 0; } catch { /* Metadata may not be loaded yet. */ }
  }

  function onNarrationActivity(event) {
    narrationActive = event.detail?.active === true;
    if (!config || !desiredActive || audio.paused) return;
    rampTo(effectiveVolume(narrationActive ? config.duckGain : config.normalGain), narrationActive ? config.duckAttackMs : config.duckReleaseMs);
  }

  function enforceCustomLoop(event) {
    if (!config || config.loopEndSeconds === null || (event?.type !== 'ended' && audio.currentTime < config.loopEndSeconds)) return;
    audio.currentTime = config.loopStartSeconds;
    if (desiredActive && audio.paused) armGestureRecovery();
  }

  function onVisibilityChange() {
    if (global.document?.visibilityState === 'visible' && desiredActive && audio.paused) armGestureRecovery();
  }

  audio.addEventListener('timeupdate', enforceCustomLoop);
  audio.addEventListener('ended', enforceCustomLoop);
  global.addEventListener?.('tombworldnarrationactivity', onNarrationActivity);
  global.document?.addEventListener?.('visibilitychange', onVisibilityChange);

  global.TombWorldAmbient = Object.freeze({ init, playFromGesture, setActive, setVolumeMultiplier, stop, reset, removeGestureRecovery });
})(typeof window === 'undefined' ? globalThis : window);
