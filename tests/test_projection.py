import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('projection',root/'generate_projection.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
data=json.loads((root/'projection.json').read_text())
class ProjectionTest(unittest.TestCase):
 def test_verified_counts_and_separate_blocker(self):
  out=mod.build(data)
  for phrase in ('34','1072','19 notebook tests','157 tests','0 / 0 / 0','Blocked','Manual snapshot'):
   self.assertIn(phrase,out)
  self.assertNotIn('16640',out)
  self.assertNotIn('demo-mac',out)
  self.assertNotIn('github.com/newdarwindev',out)
 def test_leak_fields_rejected(self):
  for key,value in [('raw_slack_text','private'),('private_repo_url','https://example.com/private'),('session_id','x'),('actor_id','owner')]:
   bad=deepcopy(data);bad[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):mod.build(bad)
 def test_stage_leak_and_wrong_claim_rejected(self):
  bad=deepcopy(data);bad['stages'][0]['message']='raw text'
  with self.assertRaises(ValueError):mod.build(bad)
  bad=deepcopy(data);bad['stages'][3]['ready_for_optimizer']=True
  with self.assertRaises(ValueError):mod.build(bad)
 def test_public_fixture_only(self):
  self.assertEqual(data['classification'],'public_aggregate')
  self.assertEqual(data['refresh_mode'],'manual')
if __name__=='__main__':unittest.main()
