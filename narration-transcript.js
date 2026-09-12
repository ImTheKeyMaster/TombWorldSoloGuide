(function (global) {
  'use strict';

  const CATEGORY_LABELS = Object.freeze({
    'mission-intro': 'MISSION BRIEFING',
    event: 'TOMB WORLD EVENT',
    grade: 'THREAT ESCALATION',
    outcome: 'MISSION OUTCOME',
    'deadly-encounter': 'DEADLY ENCOUNTER'
  });
  let initialized = false;

  function formatTime(milliseconds) {
    const safeMilliseconds = Number.isFinite(Number(milliseconds)) && Number(milliseconds) > 0
      ? Number(milliseconds)
      : 0;
    const seconds = Math.floor(safeMilliseconds / 1000);
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  }

  function init() {
    if (initialized) return;
    const narration = global.TombWorldNarration;
    const dialog = global.document?.getElementById('narrationTranscriptDialog');
    const reopen = global.document?.getElementById('narrationTranscriptReopen');
    if (!narration || !dialog || !reopen) return;

    const category = global.document.getElementById('narrationTranscriptCategory');
    const body = global.document.getElementById('narrationTranscriptBody');
    const progress = global.document.getElementById('narrationTranscriptProgress');
    const progressFill = progress.querySelector('span');
    const time = global.document.getElementById('narrationTranscriptTime');
    const hide = global.document.getElementById('narrationTranscriptHide');
    const pause = global.document.getElementById('narrationTranscriptPause');
    const skip = global.document.getElementById('narrationTranscriptSkip');
    const stop = global.document.getElementById('narrationTranscriptStop');
    const pauseHelp = global.document.getElementById('narrationTranscriptPauseHelp');
    let hiddenForPlayback = false;
    let previousActive = false;
    let previousId = null;
    let previousFocus = null;
    let animationFrame = null;

    function dialogOpen() {
      return dialog.open === true;
    }

    function cancelProgressLoop() {
      if (animationFrame !== null) global.cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }

    function updateProgress(state) {
      const currentTimeMs = Number.isFinite(Number(state.currentTimeMs)) && Number(state.currentTimeMs) > 0
        ? Number(state.currentTimeMs)
        : 0;
      const durationMs = Number.isFinite(Number(state.durationMs)) && Number(state.durationMs) > 0
        ? Number(state.durationMs)
        : 0;
      const ratio = durationMs ? Math.min(1, Math.max(0, currentTimeMs / durationMs)) : 0;
      const percent = Math.round(ratio * 100);
      progress.setAttribute('aria-valuenow', String(percent));
      progressFill.style.width = `${percent}%`;
      time.textContent = `${formatTime(currentTimeMs)} / ${formatTime(durationMs)}`;

      const masterDisabled = narration.isMasterEnabled?.() === false || state.pausedByMaster;
      pause.textContent = masterDisabled ? 'Paused' : (state.pausedByUser ? 'Resume' : 'Pause');
      pause.disabled = masterDisabled;
      if (masterDisabled) pause.setAttribute('aria-describedby', 'narrationTranscriptPauseHelp');
      else pause.removeAttribute('aria-describedby');
      pauseHelp.hidden = !masterDisabled;
    }

    function progressLoop() {
      animationFrame = null;
      const state = narration.getPlaybackState();
      if (!state.active || !dialogOpen()) return;
      updateProgress(state);
      animationFrame = global.requestAnimationFrame(progressLoop);
    }

    function startProgressLoop() {
      if (animationFrame === null && dialogOpen()) {
        animationFrame = global.requestAnimationFrame(progressLoop);
      }
    }

    function closeDialog(restoreToReopen) {
      cancelProgressLoop();
      if (dialogOpen()) dialog.close();
      if (restoreToReopen) {
        reopen.hidden = false;
        reopen.focus();
      } else if (previousFocus?.isConnected && !previousFocus.hidden) {
        previousFocus.focus();
      }
    }

    function openDialog(state, resetScroll) {
      reopen.hidden = true;
      if (!dialogOpen()) {
        if (global.document.activeElement !== reopen) previousFocus = global.document.activeElement;
        dialog.showModal();
      }
      if (resetScroll) body.scrollTop = 0;
      updateProgress(state);
      startProgressLoop();
      hide.focus();
    }

    function renderTranscript(state) {
      category.textContent = CATEGORY_LABELS[state.category] || 'NARRATION';
      body.textContent = state.transcriptAvailable
        ? state.transcript
        : (state.transcriptLoading ? 'Loading transcript…' : 'Transcript unavailable.');
    }

    function handleState(state = narration.getPlaybackState()) {
      const newPlayback = state.active && (!previousActive || state.id !== previousId);
      if (!state.active) {
        hiddenForPlayback = false;
        reopen.hidden = true;
        closeDialog(false);
      } else {
        renderTranscript(state);
        updateProgress(state);
        if (newPlayback) {
          hiddenForPlayback = false;
          openDialog(state, true);
        } else if (hiddenForPlayback) {
          reopen.hidden = false;
          cancelProgressLoop();
        } else if (dialogOpen()) {
          startProgressLoop();
        }
      }
      previousActive = state.active;
      previousId = state.id;
    }

    function hideTranscript() {
      const state = narration.getPlaybackState();
      hiddenForPlayback = state.active;
      closeDialog(state.active);
    }

    hide.addEventListener('click', hideTranscript);
    dialog.addEventListener('cancel', event => {
      event.preventDefault();
      hideTranscript();
    });
    reopen.addEventListener('click', () => {
      const state = narration.getPlaybackState();
      if (!state.active) return;
      hiddenForPlayback = false;
      openDialog(state, false);
    });
    pause.addEventListener('click', async () => {
      const state = narration.getPlaybackState();
      if (!state.active || narration.isMasterEnabled?.() === false || state.pausedByMaster) return;
      if (state.pausedByUser) await narration.resumeNarration();
      else narration.pauseNarration();
      handleState();
    });
    skip.addEventListener('click', () => narration.skipCurrent());
    stop.addEventListener('click', () => narration.stop());
    global.addEventListener('tombworldnarrationstatechange', event => handleState(event.detail));
    global.addEventListener('pagehide', cancelProgressLoop, { once: true });
    initialized = true;
    handleState();
  }

  global.TombWorldNarrationTranscript = Object.freeze({ formatTime, init });
  if (global.document?.readyState === 'loading') global.document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})(typeof window === 'undefined' ? globalThis : window);
