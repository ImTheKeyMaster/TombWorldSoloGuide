#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationPr5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / 'app.js').read_text()

    def function_source(self, name, next_name):
        return self.app.split(f'function {name}(', 1)[1].split(f'function {next_name}(', 1)[0]

    def test_complete_physical_deck_and_duplicate_weighting(self):
        deck = self.app.split('const eventDeck = [', 1)[1].split('\n  ];', 1)[0]
        self.assertEqual(len(re.findall(r"instanceId:'", deck)), 12)
        self.assertEqual(len(re.findall(r"definitionId:'awakened-warrior'", deck)), 2)
        for title in ('Subjugation Glyphs', 'Transdimensional Relocation', 'My Will Be Done',
                      'Reanimation Protocols', 'Dark of the Tomb', 'Countertemporal Shifting',
                      'Living Metal Flux', 'The Maze Reforms', 'Stirrings of Horror',
                      'A Chittering Drone', 'Awakened Warrior'):
            self.assertIn(f"title:'{title}'", self.app)

    def test_official_draw_timing_and_count(self):
        source = self.function_source('processEventStage', 'eventRecord')
        self.assertIn('state.turningPoint>1&&d.grade===3', source)
        self.assertIn("d.suggestedInitiative==='npo'||state.threat===15?2:1", source)
        self.assertNotIn('&&state.threat===15?3', source)

    def test_draws_without_replacement_and_recycles_in_ready(self):
        draw = self.function_source('drawEvent', 'currentEvent')
        self.assertIn('state.eventState.available.splice(index,1)[0]', draw)
        self.assertIn('state.eventState.used.push(instanceId)', draw)
        ready = self.function_source('processReadyStep', 'applyMissionReadyHooks')
        self.assertIn('recycleUsedEvents();', ready)

    def test_active_effects_persist_and_expire(self):
        initial = self.app.split('const initialState = () => ({', 1)[1].split('\n  });', 1)[0]
        self.assertIn('eventState:{available:eventDeck.map(card=>card.instanceId),used:[],active:[]}', initial)
        execution = self.function_source('beginCurrentEvent', 'completeCurrentEvent')
        self.assertIn('state.eventState.active.push', execution)
        self.assertIn('expiresAfterTurningPoint:state.turningPoint', execution)
        self.assertIn('state.eventState.active=state.eventState.active.filter', self.app)

    def test_legacy_saves_are_normalized(self):
        normalize = self.function_source('normalizeState', 'npoDefinition')
        self.assertIn('raw?.eventState', normalize)
        self.assertIn('validInstances', normalize)
        self.assertIn('eventDefinitions[event?.definitionId]', normalize)

    def test_manual_geometry_blocks_reinforcements_until_confirmed(self):
        execution = self.function_source('beginCurrentEvent', 'completeCurrentEvent')
        self.assertIn('d.eventPending=true', execution)
        resolution = self.function_source('resolveStrategyEvent', 'randomReinforcement')
        self.assertIn("result='Tabletop effect confirmed.'", resolution)
        self.assertIn('completeCurrentEvent(result)', resolution)
        self.assertNotIn('coordinates', resolution)


if __name__ == '__main__':
    unittest.main()
