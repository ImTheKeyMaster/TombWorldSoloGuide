import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NarrationQueuePreemptionTests(unittest.TestCase):
    def test_non_event_narration_clears_pending_event_queue(self):
        script = r"""
const fs = require('fs');
const vm = require('vm');
const calls = [];
let active = 0;

class Audio {
  constructor() { this.src = ''; this.volume = .8; this.onended = null; this.onerror = null; Audio.instance = this; }
  pause() { active = 0; }
  removeAttribute() { this.src = ''; }
  load() {}
  play() {
    if (active) throw new Error('narration tracks overlapped');
    active = 1;
    calls.push(this.src);
    return Promise.resolve();
  }
  end() { active = 0; if (this.onended) this.onended(); }
}

const entries = {
  'event.subjugation-glyphs': { available: true, file: 'events/subjugation-glyphs.mp3' },
  'event.living-metal-flux': { available: true, file: 'events/living-metal-flux.mp3' },
  'mission.01.intro': { available: true, file: 'missions/01.mp3' },
  'outcome.01.victory': { available: true, file: 'outcomes/01-victory.mp3' }
};
const context = {
  Audio, URL, location: { href: 'https://example.test/app/' },
  fetch: async () => ({ ok: true, json: async () => ({ entries }) }),
  localStorage: { getItem: () => null, setItem: () => {} },
  dispatchEvent: () => {}, CustomEvent: function () {}
};
context.window = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('narration.js', 'utf8'), context);
const flush = () => new Promise(resolve => setTimeout(resolve, 0));

async function settleActive() {
  Audio.instance.end();
  await flush();
}

async function runPreemption(label, preempt, expectedSuffix) {
  const narration = context.TombWorldNarration;
  const first = narration.playEvent('subjugation-glyphs', `${label}-first`);
  const queued = narration.playEvent('living-metal-flux', `${label}-queued`);
  await flush();
  if (!calls.at(-1)?.endsWith('events/subjugation-glyphs.mp3')) throw new Error(`${label}: first event did not start`);
  const before = calls.length;
  const result = await preempt();
  if (!result) throw new Error(`${label}: preempting narration did not start`);
  if (await queued) throw new Error(`${label}: queued event was not cleared`);
  await first;
  await flush();
  if (!calls.at(-1)?.endsWith(expectedSuffix)) throw new Error(`${label}: wrong preempting narration`);
  if (calls.slice(before).some(src => src.endsWith('events/living-metal-flux.mp3'))) throw new Error(`${label}: stale queued event played`);
  await settleActive();
}

(async () => {
  const narration = context.TombWorldNarration;
  await narration.init();

  await runPreemption('intro', () => narration.playMissionIntro('shifting-labyrinth', true), 'missions/01.mp3');
  await runPreemption('outcome', () => narration.playOutcome('shifting-labyrinth', 'victory'), 'outcomes/01-victory.mp3');

  const replayFirst = narration.playEvent('subjugation-glyphs', 'replay-first');
  const replayQueued = narration.playEvent('living-metal-flux', 'replay-queued');
  await flush();
  const beforeReplay = calls.length;
  if (!await narration.replayLast()) throw new Error('Replay Last did not start');
  if (await replayQueued) throw new Error('Replay Last did not clear queued event');
  await replayFirst;
  await flush();
  if (!calls.at(-1)?.endsWith('events/subjugation-glyphs.mp3')) throw new Error('Replay Last did not replay active event');
  if (calls.slice(beforeReplay).some(src => src.endsWith('events/living-metal-flux.mp3'))) throw new Error('stale queued event played after Replay Last');
  await settleActive();

  const stopFirst = narration.playEvent('subjugation-glyphs', 'stop-first');
  const stopQueued = narration.playEvent('living-metal-flux', 'stop-queued');
  await flush();
  narration.stop();
  if (await stopQueued) throw new Error('stop() did not clear queued event');
  await stopFirst;

  const fresh = narration.playEvent('living-metal-flux', 'fresh-after-stop');
  await flush();
  if (!calls.at(-1)?.endsWith('events/living-metal-flux.mp3')) throw new Error('fresh event did not start after cleanup');
  await settleActive();
  if (!await fresh) throw new Error('fresh event was not reported as played');
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
