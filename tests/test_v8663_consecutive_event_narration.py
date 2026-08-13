import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConsecutiveEventNarrationTests(unittest.TestCase):
    def test_grade_three_events_play_once_in_order_without_overlap(self):
        script = r"""
const fs = require('fs');
const vm = require('vm');
const calls = [];
let active = 0;

class Audio {
  constructor() { this.src = ''; this.volume = .8; this.onended = null; this.onerror = null; Audio.instance = this; }
  pause() { if (active) active = 0; }
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
(async () => {
  const narration = context.TombWorldNarration;
  await narration.init();

  const first = narration.playEvent('subjugation-glyphs', 'grade-3-event-1');
  const second = narration.playEvent('living-metal-flux', 'grade-3-event-2');
  await flush();
  if (calls.length !== 1 || !calls[0].endsWith('events/subjugation-glyphs.mp3')) throw new Error('first event did not start first');
  if (await narration.playEvent('subjugation-glyphs', 'grade-3-event-1')) throw new Error('duplicate event instance played');
  Audio.instance.end();
  await flush();
  if (calls.length !== 2 || !calls[1].endsWith('events/living-metal-flux.mp3')) throw new Error('second event did not follow first');
  Audio.instance.end();
  if (!await first || !await second) throw new Error('queued event playback was not reported');

  const queuedFirst = narration.playEvent('subjugation-glyphs', 'stop-event-1');
  const queuedSecond = narration.playEvent('living-metal-flux', 'stop-event-2');
  await flush();
  narration.stop();
  if (await queuedSecond) throw new Error('stop did not clear queued event');
  await flush();
  if (calls.length !== 3) throw new Error('queued event played after stop');
  await queuedFirst;

  if (!await narration.playMissionIntro('shifting-labyrinth', true)) throw new Error('mission intro behavior changed');
  if (!await narration.playOutcome('shifting-labyrinth', 'victory')) throw new Error('mission outcome behavior changed');
  if (calls.filter(src => src.endsWith('events/subjugation-glyphs.mp3')).length !== 2) throw new Error('first event track request count changed');
  if (calls.filter(src => src.endsWith('events/living-metal-flux.mp3')).length !== 1) throw new Error('second event track request count changed');
})().catch(error => { console.error(error); process.exit(1); });
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
