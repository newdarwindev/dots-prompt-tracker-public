import importlib.util
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generator',root/'generate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class SiteTest(unittest.TestCase):
    def test_real_input_rejected_public(self):
        with self.assertRaises(ValueError):mod.build({'classification':'private','tasks':[]},'public')
    def test_reaction_dedupe_owner_only_and_unknown_metrics(self):
        bot={'channel_id':'c','message_ts':'1','user_id':'bot','emoji':'👍'}
        owner={'channel_id':'c','message_ts':'2','user_id':'owner','emoji':'👍'}
        data={'classification':'synthetic','owner_user_id':'owner','tasks':[{'source_id':'x','prompt':'Sample','status':'done','sessions':[{'tokens':None,'messages':3}],'reactions':[bot,bot,owner]},{'source_id':'x','prompt':'Duplicate'}]}
        out=mod.build(data,'public')
        self.assertEqual(out.count('Sample'),1)
        self.assertNotIn('Duplicate',out)
        self.assertIn('Distinct reactions</span>',out)
        self.assertIn('approved · owner 👍 · 2',out)
        self.assertIn('unknown</strong><small>Tokens',out)
if __name__=='__main__':unittest.main()
