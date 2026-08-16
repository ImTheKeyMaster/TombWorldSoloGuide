(function (global) {
  'use strict';

  const CONFIG_URL = 'Assets/Audio/Narration/ambient-config.json';
  const AUDIO_ROOT_URL = 'Assets/Audio/Narration/';
  const AudioContext = global.AudioContext || global.webkitAudioContext;
  let context = null;
  let gainNode = null;
  let buffer = null;
  let config = null;
  let initialization = null;
  let source = null;
  let stopTimer = null;
  let contextUnlocked = false;
  let activeBattle = false;
  let narrationActive = false;
  let generation = 0;
  let recoveryRequired = false;
  let unlockAttempt = null;

  const RECOVERY_TIMEOUT_MS = 1500;

  function ensureContext() {
    if (!context && AudioContext) context = new AudioContext();
    return context;
  }

  async function settleWithTimeout(operation) {
    let timer = null;
    try {
      return await Promise.race([
        Promise.resolve().then(operation).then(() => true, () => false),
        new Promise(resolve => { timer = global.setTimeout(() => resolve(false), RECOVERY_TIMEOUT_MS); })
      ]);
    } catch { return false; }
    finally { if (timer !== null) global.clearTimeout(timer); }
  }

  async function resumeContextFromGesture(forceRecovery = false) {
    if (!context || context.state === 'closed') return false;
    if (context.state === 'running' && !forceRecovery) return true;
    if (forceRecovery && typeof context.suspend === 'function') {
      await settleWithTimeout(() => context.suspend());
    } else if (context.state === 'interrupted' && typeof context.suspend === 'function') {
      await settleWithTimeout(() => context.suspend());
    }
    if (typeof context.resume !== 'function') return context.state === 'running';
    const resumed = await settleWithTimeout(() => context.resume());
    return resumed && context.state === 'running';
  }

  function masterEnabled() {
    try { return global.TombWorldNarration?.isMasterEnabled() !== false; } catch { return true; }
  }

  function validConfig(value) {
    const file = value?.file;
    const gainsValid = ['normalGain', 'duckGain'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0);
    const timesValid = ['fadeInMs', 'fadeOutMs', 'duckAttackMs', 'duckReleaseMs'].every(key => Number.isFinite(value?.[key]) && value[key] >= 0);
    return value?.schemaVersion === 1 && typeof file === 'string'
      && /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))Ambient\/[A-Za-z0-9._-]+\.(?:mp3|ogg)$/i.test(file)
      && gainsValid && timesValid && Number.isFinite(value.loopStartSeconds) && value.loopStartSeconds >= 0
      && (value.loopEndSeconds === null || (Number.isFinite(value.loopEndSeconds) && value.loopEndSeconds > value.loopStartSeconds));
  }

  async function init() {
    if (initialization) return initialization;
    const attempt = (async () => {
      if (!AudioContext || typeof global.fetch !== 'function') return false;
      try {
        const response = await global.fetch(CONFIG_URL);
        const value = response.ok ? await response.json() : null;
        if (!validConfig(value)) return false;
        const audioResponse = await global.fetch(new URL(value.file, new URL(AUDIO_ROOT_URL, global.location?.href || 'http://localhost/')).href);
        if (!audioResponse.ok) return false;
        const audioContext = ensureContext();
        const decodedBuffer = await audioContext.decodeAudioData(await audioResponse.arrayBuffer());
        const loopEnd = value.loopEndSeconds === null ? decodedBuffer.duration : value.loopEndSeconds;
        if (!(loopEnd > value.loopStartSeconds) || loopEnd > decodedBuffer.duration) return false;
        const ambientGain = audioContext.createGain();
        ambientGain.gain.value = 0;
        ambientGain.connect(audioContext.destination);
        buffer = decodedBuffer;
        gainNode = ambientGain;
        config = { ...value, loopEndSeconds: loopEnd };
        return true;
      } catch { return false; }
    })();
    initialization = attempt;
    const ready = await attempt;
    if (!ready && initialization === attempt) initialization = null;
    return ready;
  }

  function rampTo(value, milliseconds) {
    if (!context || !gainNode) return;
    const now = context.currentTime;
    const gain = gainNode.gain;
    gain.cancelScheduledValues(now);
    gain.setValueAtTime(gain.value, now);
    gain.linearRampToValueAtTime(value, now + milliseconds / 1000);
  }

  function stopSource(expectedGeneration, delayMs) {
    global.clearTimeout(stopTimer);
    stopTimer = global.setTimeout(() => {
      if (expectedGeneration !== generation || !source) return;
      try { source.stop(); } catch { /* The source may already have stopped. */ }
      source.disconnect();
      source = null;
      stopTimer = null;
    }, delayMs);
  }

  function fadeOutAndStop() {
    if (!source || !config) return;
    const expectedGeneration = generation;
    rampTo(0, config.fadeOutMs);
    stopSource(expectedGeneration, config.fadeOutMs + 25);
  }

  function startSource() {
    if (source || !context || !gainNode || !buffer || !config) return;
    global.clearTimeout(stopTimer);
    stopTimer = null;
    generation += 1;
    source = context.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    source.loopStart = config.loopStartSeconds;
    source.loopEnd = config.loopEndSeconds;
    source.connect(gainNode);
    gainNode.gain.cancelScheduledValues(context.currentTime);
    gainNode.gain.setValueAtTime(0, context.currentTime);
    source.start(0, config.loopStartSeconds);
    rampTo(narrationActive ? config.duckGain : config.normalGain, config.fadeInMs);
  }

  function discardStaleSource() {
    global.clearTimeout(stopTimer);
    stopTimer = null;
    generation += 1;
    if (!source) return;
    try { source.stop(); } catch { /* The interrupted source may already be stopped. */ }
    try { source.disconnect(); } catch { /* WebKit may have already disconnected it. */ }
    source = null;
  }

  async function reconcile() {
    const token = generation;
    const ready = await init();
    if (!ready || token !== generation) return false;
    if (activeBattle && contextUnlocked && masterEnabled()) {
      if (!await resumeContextFromGesture()) return false;
      if (context.state !== 'running' || !activeBattle || !masterEnabled()) return false;
      if (source) {
        if (!stopTimer) return true;
        global.clearTimeout(stopTimer);
        stopTimer = null;
        generation += 1;
        rampTo(narrationActive ? config.duckGain : config.normalGain, config.fadeInMs);
      } else startSource();
      return Boolean(source);
    }
    fadeOutAndStop();
    return false;
  }

  function unlock() {
    if (unlockAttempt) return unlockAttempt;
    if (contextUnlocked && !recoveryRequired && context?.state === 'running' && buffer && config && gainNode) return Promise.resolve(true);
    unlockAttempt = (async () => {
      // Construct and resume from the shared click gesture for Safari/PWA audio permission.
      ensureContext();
      const recovering = recoveryRequired;
      const resumePromise = resumeContextFromGesture(recovering);
      const ready = await init();
      if (!context) return false;
      const recovered = await resumePromise;
      contextUnlocked = recovered;
      if (!recovered && !recovering) contextUnlocked = await resumeContextFromGesture();
      if (contextUnlocked && ready) {
        if (recovering) {
          discardStaleSource();
          recoveryRequired = false;
          const playbackRecovered = await reconcile();
          if (activeBattle && masterEnabled() && !playbackRecovered) {
            contextUnlocked = false;
            recoveryRequired = true;
            return false;
          }
        } else {
          void reconcile();
        }
      } else if (recovering) recoveryRequired = true;
      return contextUnlocked && ready;
    })().catch(() => {
      contextUnlocked = false;
      recoveryRequired = true;
      return false;
    }).finally(() => { unlockAttempt = null; });
    return unlockAttempt;
  }

  function setActive(isActive) {
    const nextActive = Boolean(isActive);
    if (nextActive === activeBattle) return;
    activeBattle = nextActive;
    void reconcile();
  }

  function onVisibilityChange() {
    if (global.document?.visibilityState !== 'visible') {
      recoveryRequired = true;
      return;
    }
    recoveryRequired = true;
    if (activeBattle && masterEnabled() && typeof global.dispatchEvent === 'function' && typeof global.CustomEvent === 'function') {
      global.dispatchEvent(new global.CustomEvent('tombworldaudiorecoveryrequired', { detail: { category: 'ambient' } }));
    }
  }

  function stop() {
    activeBattle = false;
    contextUnlocked = false;
    recoveryRequired = true;
    generation += 1;
    global.clearTimeout(stopTimer);
    stopTimer = null;
    if (source) {
      rampTo(0, config?.fadeOutMs || 0);
      const oldSource = source;
      source = null;
      global.setTimeout(() => { try { oldSource.stop(); oldSource.disconnect(); } catch {} }, (config?.fadeOutMs || 0) + 25);
    }
  }

  function onNarrationActivity(event) {
    narrationActive = event.detail?.active === true;
    if (source && activeBattle && masterEnabled() && config) {
      rampTo(narrationActive ? config.duckGain : config.normalGain, narrationActive ? config.duckAttackMs : config.duckReleaseMs);
    }
  }

  global.addEventListener?.('tombworldnarrationactivity', onNarrationActivity);
  global.document?.addEventListener?.('visibilitychange', onVisibilityChange);

  global.TombWorldAmbient = Object.freeze({ init, unlock, setActive, stop });
})(typeof window === 'undefined' ? globalThis : window);
