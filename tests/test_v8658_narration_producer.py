import hashlib, importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]; TOOL=ROOT/'tools'/'narration-producer'
try:
 import flask, requests, dotenv, mutagen
except ImportError:
 server=None
else:
 spec=importlib.util.spec_from_file_location('producer_server',TOOL/'server.py'); server=importlib.util.module_from_spec(spec); sys.modules['producer_server']=server; spec.loader.exec_module(server)
@unittest.skipIf(server is None, 'Producer dependencies are installed by Windows setup')
class ProducerTests(unittest.TestCase):
 def setUp(self): self.client=server.app.test_client()
 def test_structure_and_local_binding(self):
  self.assertTrue((ROOT/'SETUP_NARRATION_PRODUCER.bat').exists()); self.assertTrue((ROOT/'RUN_NARRATION_PRODUCER.bat').exists())
  self.assertIn('127.0.0.1',(TOOL/'server.py').read_text()); self.assertNotIn("host='0.0.0.0'",(TOOL/'server.py').read_text())
  ignored=(ROOT/'.gitignore').read_text(); self.assertIn('narration-producer/.env',ignored); self.assertIn('narration-producer/.venv/',ignored)
 def test_canonical_library_and_hashes(self):
  records=server.library(); self.assertEqual(29,len(records)); self.assertEqual(28,sum(x['status']=='approved' for x in records))
  self.assertEqual(['mission.04.intro'],[x['id'] for x in records if x['status']=='draft'])
  for x in records: self.assertEqual(hashlib.sha256(server.normalize(x['script']).encode()).hexdigest(),x['scriptHash'])
  all_text=' '.join(x['script'] for x in records); self.assertNotIn('The mission is won. You have overcome',all_text)
 def test_dry_run_needs_no_key_and_blocks_draft(self):
  response=self.client.post('/api/dry-run',json={'ids':['mission.01.intro','mission.04.intro'],'settings':json.loads((ROOT/'Narration/producer-settings.json').read_text())})
  data=response.get_json(); self.assertEqual(2,data['totals']['selected']); self.assertEqual(1,data['totals']['blocked']); self.assertGreater(data['totals']['totalCharacters'],0)
 def test_generation_requires_confirmation(self):
  self.assertEqual(400,self.client.post('/api/generate',json={'ids':[]}).status_code)
 def test_manifest_has_no_audio(self):
  entries=json.loads((ROOT/'Assets/Audio/Narration/narration-manifest.json').read_text())['entries']; self.assertEqual(29,len(entries)); self.assertTrue(all(not x['available'] for x in entries.values()))
  self.assertFalse(list((ROOT/'Assets/Audio/Narration').rglob('*.mp3')))
 def test_status_does_not_expose_key(self):
  with mock.patch.object(server,'key',return_value='SECRET_TEST_KEY'):
   body=self.client.get('/api/status').get_data(as_text=True); self.assertNotIn('SECRET_TEST_KEY',body); self.assertIn('apiKeyConfigured',body)
if __name__=='__main__': unittest.main()
